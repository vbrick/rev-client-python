# Rev Python Client Library (beta)

This is a python client library for interacting with the [Vbrick Rev API](https://revdocs.vbrick.com/reference).


## Requirements

* Python >=3.6
* `requests` library

## Installation

This library isn't (yet) published to pip. In the interim:

* unzip archive contents into local folder
* open a shell session and navigate to the extracted contents
* `pip install .`

## Example

```python
from revclient import RevClient

url = "https://YOUR_REV_TENANT_URL"

apiKey = "user.api.key"
secret = "user.secret"
rev = RevClient(url, username = username, password = password, apiKey=apiKey, secret=secret)

# or use username/password login
# username = 'my.rev.username'
# password = 'my.rev.password'
# rev = RevClient(url, username = username, password = password)

# login to Rev
rev.connect()

# create a category
resp = rev.post("/api/v2/categories", { "name": "Created Via API" })
categoryId = resp["categoryId"]

# get details about this category
category_details = rev.get("/api/v2/categories/" + categoryId)
print(category_details)

# create a new user
resp = rev.post('/api/v2/users', {
	"username": "new.user.python",
	"firstname": "new",
	"lastname": "user"
})
userId = resp["userId"]

# upload a video, and assign 'new.user.python' as the owner of that video, and add to the category created above
resp = rev.video.upload("/path/to/local/video.mp4", {
	"uploader": "new.python.user",
	"title": "video uploaded via the API",
	"categories": [ category_details["name"] ],
	# could also specify category by ID:
	# "categoryIds": [ "categoryId" ],
	"unlisted": True,
	"isActive": True
	# ...any additional metadata
})
video_id = resp["videoId"]
print('Video uploaded! ' + video_id)

rev.disconnect()

```

## API

### RevClient

#### `RevClient(url, apiKey = None, secret = None, username = None, password = None)`
Create new Rev Client. You **must** specify either apiKey + secret or username + password

### Session Methods

#### `connect()`
Login to Rev using supplied credentials

#### `disconnect()`
Call Logoff API command and clear session

#### `extend_session()`
Extend session timeout

#### `verify_session()`
Returns `True`/`False` if session token is valid

#### `lazy_extend_session(refresh_threshold_minutes = 3, verify = True)`
Automatically extend the session if it will expire within `refresh_threshold_minutes` minutes from now. Or, if session has expired call `connect()`. If `verify` is `True` *(default)* then test the session validity even if the session hasn't expired yet.

#### `session.is_expired`

`True` if not logged in or session has expired

#### `session.expires`

`datetime` that session will expire

### HTTP Methods

#### `request(method='GET', endpoint='', payload=None, options={}, payload_only=True, json=None, data=None, files=None)`

Make an arbitrary request to Rev, adding the authentication token as needed and decoding the body.

If method is `GET` then `payload` will be the query parameters of the request. For `POST`/`PUT`/`PATCH` endpoints you can pass `json`,`data`, or `payload` *(autodetect type of input)* to set the request body. Use `files` to attach files to request

**Returns** - response body, unless `payload_only` is set to False, in which case return the `requests.Response` object

#### `get(endpoint, payload=None, options={})`
#### `post(endpoint, payload=None, options={})`
#### `put(endpoint, payload=None, options={})`
#### `patch(endpoint, payload=None, options={})`
#### `delete(endpoint, payload=None, options={})`

Make HTTP requests to Rev at specified `endpoint`. Convenience wrapper around `request` for different HTTP Verbs

### Video Methods

Collection of helpers for Video API endpoints

#### `video.status(video_id) -> Dict`
#### `video.details(video_id) -> Dict`
#### `video.update(video_id, metadata: dict) -> None`
#### `video.migrate(video_id, username = None, when_uploaded = None, when_published = None) -> Dict`

#### `video.patch(video_id: str, metadata: dict, strict = False) -> None`
#### `video.upload(file, metadata: dict, filename = None, content_type = None) -> Dict`
#### `video.upload_transcription(video_id: str, file, language: str = 'en', filename: str = 'subtitle.srt', content_type: str = 'application/x-subrip') -> None`
#### `video.search_stream(query: dict = {}, max_results = None, on_page = None) -> Generator`
#### `video.search(query: dict = {}, max_results = None, on_page = None) -> [Dict]`


---

## Disclaimer
This code is distributed "as is", with no warranty expressed or implied, and no guarantee for accuracy or applicability to your purpose.