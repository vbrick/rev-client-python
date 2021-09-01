#%%
import aiohttp
from aiohttp import FormData, ClientError
import asyncio
#from requests import HTTPError
from urllib.parse import urljoin
import re
from datetime import datetime, timezone
from types import TracebackType
from typing import Any, AsyncIterator, Awaitable, Callable, List, Optional, Type


#%%
iso_re = re.compile('([\d:T-]+\.\d\d\d)\d*(\+\d+:\d+|Z)?')

def parse_iso(val):
    cleaned = iso_re.match(val)
    return datetime.fromisoformat((cleaned[1] + '+00:00') if cleaned else val)

def format_iso(val):
    return val.isoformat(timespec='milliseconds').replace('+00:00', 'Z')

def now_iso():
    return datetime.now(timezone.utc)

def omit(items, omit_keys, asItems=False):
    if isinstance(items, dict):
        items = items.items()
    result = [ var for var in items if var[0] not in omit_keys ]
    if asItems:
        return result
    else:
        return dict(result)


#%%
class RevSession():
    def __init__(self, apiKey = None, secret = None, username = None, password = None, **kwargs):
        self.token = None
        self.expires = None
        self.userId = None

        self.apiKey = None
        self.secret = None
        self.username = None
        self.password = None

        # assign other attributes if specified
        [ setattr(self, var[0], var[1]) for var in omit(vars(), ['self', 'kwargs'], asItems=True)]

    def update(self, payload):
        if 'token' in payload:
            self.token = payload['token']
        if 'id' in payload:
            self.userId = payload['id']
        if 'expiration' in payload:
            self.expires = parse_iso(payload['expiration'])
    def clear(self):
        self.token = None
        self.expires = None

    @property
    def is_expired(self):
        if not self.expires:
            return True
        return now_iso() > self.expires

    @property
    def seconds_till_expires(self):
        if not self.expires:
            return -1
        return (self.expires - now_iso()).total_seconds()
    
    def add_headers(self, headers):
        if self.token:
            headers['Authorization'] = f'VBrick {self.token}'

    def login_request(self):
        if self.username and self.password:
            return {
                'method': 'POST',
                'endpoint': '/api/v2/user/login',
                'payload': { 'username': self.username, 'password': self.password }
            }
        elif self.apiKey and self.secret:
            return {
                'method': 'POST',
                'endpoint': '/api/v2/authenticate',
                'payload': { 'apiKey': self.apiKey, 'secret': self.secret }
            }
        else:
            raise AssertionError("authentication details not set")

    def logoff_request(self):
        if self.username and self.userId:
            return {
                'method': 'POST',
                'endpoint': '/api/v2/user/logoff',
                'payload': { 'userId': self.userId }
            }
        elif self.apiKey:
            return {
                'method': 'DELETE',
                'endpoint': f'/api/v2/tokens/{self.apiKey}'
            }
        else:
            return None

    def extend_request(self):
        if self.apiKey:
            return {
                'method': 'POST',
                'endpoint': f'/api/v2/auth/extend-session-timeout/{self.apiKey}'
            }
        else:
            return {
                'method': 'POST',
                'endpoint': '/api/v2/user/extend-session-timeout',
                'payload': { 'userId': self.userId }
            }
        return None

#%%
is_text_mime_re = re.compile('text|application/(xml|javascript|x-subrip)')
class RevClient():
    def __init__(self, url, apiKey = None, secret = None, username = None, password = None, **kwargs):
        self.url = url
        self._client = None

        # populate session from input arguments (apiKey etc.)
        self.session = RevSession(**omit(vars(), 'self'))

    @property
    def client(self):
        if not self._client or self._client.closed:
            self._client = aiohttp.ClientSession()
        return self._client
    
    async def request(self, method='GET', endpoint='', payload=None, options={}, payload_only=True, json=None, data=None, **kwargs):
        url = urljoin(self.url, endpoint)

        method = method.upper()
        assert method in ['GET', 'HEAD', 'DELETE', 'POST', 'PUT', 'PATCH', 'OPTIONS']
        
        options = options.copy() if options else {}
        headers = options['headers'].copy() if 'headers' in options else {}
        
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'
        
        # add token if not already specified
        if 'Authorization' not in headers:
            self.session.add_headers(headers)

        if 'Accept' not in headers:
            headers['Accept'] = 'application/json'

        req_opts = options
        req_opts['headers'] = headers
        if payload:
            if method == 'GET':
                req_opts['params'] = payload
            elif isinstance(payload, FormData):
                req_opts['data'] = payload
            else:
                req_opts['json'] = payload
        elif json:
            req_opts['json'] = json
        elif data:
            req_opts['data'] = data

        async with self.client.request(method, url, **req_opts) as resp:
            # if return actual response object
            if not payload_only:
                return resp

            # throw error if not okay
            resp.raise_for_status()

            # return stream objects as file-like
            if req_opts.get('stream', False):
                return resp.content

            # empty response
            # if len(resp.content) == 0:
            #     return None

            # if no mimetype in response then assume JSON unless otherwise specified
            content_type = resp.headers.get('Content-Type') or headers.get('Accept') or ''
            
            if content_type.startswith('application/json'):
                return await resp.json()

            if is_text_mime_re.match(content_type):
                return await resp.text()

            return await resp.read()
    
    async def get(self, endpoint='', payload=None, options={}, payload_only=True, **kwargs):
        return await self.request('GET', endpoint, payload, options, payload_only, **kwargs)
    async def post(self, endpoint='', payload=None, options={}, payload_only=True, **kwargs):
        return await self.request('POST', endpoint, payload, options, payload_only, **kwargs)
    async def put(self, endpoint='', payload=None, options={}, payload_only=True, **kwargs):
        return await self.request('PUT', endpoint, payload, options, payload_only, **kwargs)
    async def patch(self, endpoint='', payload=None, options={}, payload_only=True, **kwargs):
        return await self.request('PATCH', endpoint, payload, options, payload_only, **kwargs)
    async def delete(self, endpoint='', payload=None, options={}, payload_only=True, **kwargs):
        return await self.request('DELETE', endpoint, payload, options, payload_only, **kwargs)
    
    async def login(self):
        # make sure the authorization header isn't added
        self.session.clear()

        req_args = self.session.login_request()

        # Rarely the login call will fail on first attempt, therefore this code attempts to login multiple times
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                response = await self.request(**req_args)
                # includes token, expiration and id
                self.session.update(response)
                return response
            except ClientError as err:
                status = err.response.status_code
                # Do not re-attempt logins with invalid user/password - it can lock out the user
                if status == 401 or status == 429:
                    raise

                # retry again up to 3 times
                if attempt < max_attempts - 1:
                    continue
                else:
                    raise
    async def logoff(self):
        req_args = self.session.logoff_request()

        try:
            await self.request(**req_args)
        except ClientError as err:
            # TODO log error correctly
            print(f'Error in logging off, ignoring: {err}')
        finally:
            self.session.clear()
    async def extend_session(self):
        req_args = self.session.extend_request()

        response = await self.request(**req_args)
        # update expires time
        self.session.update(response)
    async def verify_session(self):
        response = await self.get('/api/v2/user/session', payload_only=False)
        # ends up with a error status code if not valid session
        return response.ok

    # extends / does a login only if necessary
    async def lazy_extend_session(self, refresh_threshold_minutes = 3):
        time_till_expires = self.session.seconds_till_expires

        do_login = False
        did_refresh = False
        if time_till_expires < 0:
            do_login = True
        elif time_till_expires < refresh_threshold_minutes * 60000:
            try:
                await self.extend_session()
                did_refresh = True
            except Exception as err:
                # TODO log error correctly
                print(f'Error extending session - re-logging in {err}')
                do_login = True
        else:
            # need to login if verify fails
            do_login = not await self.verify_session()

        if do_login:
            await self.login()
            did_refresh = True
        return did_refresh
    
    async def close(self):
        if self._client:
            await self._client.close()
        self._client = None
    
    def closeSync(self) -> None:
        if self._client:
            if not self._client.closed:
                if self._client._connector_owner:
                    try:
                        self._client._connector._close()
                    except Exception:
                        self._client._connector.close()
                self._client._connector = None
            self._client = None
    def __del__(self):
        self.closeSync()
    async def __aenter__(self) -> 'RevClient':
        return self
    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]:
        await self.close()
        return None
    
    @property
    def token(self):
        return self.session.token
    
    @property
    def seconds_till_expires(self):
        return self.session.seconds_till_expires

    


# %%

url = "https://lukeselden.rev-eu.demo.vbrick.com"
username = "robot"
password = "robotpassword"
yo = {}
async def main():
    async with RevClient(url, username = username, password = password) as client:
        yo['client'] = client
        await client.login()
        print('did it!')

#loop = asyncio.get_event_loop()
#loop.run_until_complete(main())
print('all that happened')
# %%
#client.login()
# %%
