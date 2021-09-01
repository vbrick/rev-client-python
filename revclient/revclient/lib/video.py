from datetime import datetime
from io import IOBase
import json
from posixpath import join
import re
from os.path import basename
from typing import Dict
from .utils import NamespacedClient, format_iso, parse_iso

is_date_re = re.compile('\d\d\d\d-\d\d-\d\d')

def append_path(key, val):
    if isinstance(val, (list, tuple)):
        return f'/{key.title()}/-'
    else:
        return f'/{key.title()}'

class VideoClient(NamespacedClient):
    def status(self, video_id: str) -> Dict:
        return self.client.get(f'/api/v2/videos/{video_id}/status')

    def details(self, video_id: str) -> Dict:
        return self.client.get(f'/api/v2/videos/{video_id}/details')

    def update(self, video_id: str, metadata: dict) -> None:
        self.client.put(f'/api/v2/videos/{video_id}', metadata)

    def migrate(self, video_id: str, username = None, when_uploaded = None, when_published = None) -> Dict:
        params = {}
        if username:
            params['UserName'] = username
        if when_uploaded:
            if (isinstance(when_uploaded, datetime)):
                when_uploaded = format_iso(when_uploaded)
            params['whenUploaded'] = when_uploaded
        if when_published:
            if isinstance(when_published, datetime):
                # only want date part (YYYY-MM-DD), so coerce into correct format
                when_published = format_iso(when_published)
            elif not isinstance(when_published, str):
                raise TypeError("Invalid value for when_published")
            elif not is_date_re.fullmatch(when_published):
                when_published = format_iso(parse_iso(when_published))
            
                # only date part (0->10)
            params['whenPublished'] = when_published[:10]
        self.client.put(f'/api/v2/videos/{video_id}/migration', json = params)

    def patch(self, video_id: str, metadata: dict, strict = False) -> None:
        def add_op(key, val):
            return { 'op': 'add', 'path': f'/{key.title()}', 'value': val }
        def arr_op(key, val):
            # array items have values added to the end by appending /- to the key
            if isinstance(val, (list, tuple)):
                return add_op(f'{key}/-', val)
            else:
                return add_op(key, val)
        def bool_op(key, val):
            add_op(key, bool(val))
        def date_op(key, val):
            if not val:
                return []
            if isinstance(val, datetime):
                val = format_iso(val)
            elif not is_date_re.match(val):
                val = format_iso(parse_iso(val))
            # truncate datetime string to just date (YYYY-MM-DD)
            return add_op(key, val[0:10])


        schema = dict(
            # /Title
            Title = add_op,
            Categories = arr_op,
            Description = add_op,
            Tags = arr_op,
            IsActive = bool_op,
            ExpirationDate = date_op,
            EnableRatings = bool_op,
            EnableDownloads = bool_op,
            EnableComments = bool_op,
            VideoAccessControl = add_op,
            AccessControlEntities = arr_op,
            CustomFields = arr_op,
            Unlisted = bool_op,
            UserTags = arr_op
        )
        
        operations = []
        invalid = {}
        
        for key, val in metadata.items():
            op_func = schema[key]
            if op_func:
                operations.append(op_func(key, val))
            else:
                if strict:
                    raise TypeError(f'Invalid attribute {key} for Patch operation')
                invalid[key] = val
        
        if (len(operations) > 0):
            self.client.patch(f'/api/v2/videos/{video_id}', json=operations)
        
        if len(invalid) > 0:
            return { 'invalid': invalid }
        else:
            return {}
    
    def upload(self, file, metadata: dict, filename = None, content_type = None):
        if not 'uploader' in metadata:
            if self.client.session.username:
                metadata = metadata.copy()
                metadata['uploader'] = self.client.session.username
            else:
                raise TypeError('metadata must include uploader parameter')

        if isinstance(file, tuple):
            if len(file) >= 3:
                if not content_type:
                    content_type = file[2]
            if len(file) >= 2:
                if not filename:
                    filename = file[0]
                file = file[1]
            else:
                file = file[0]

        if isinstance(file, str):
            if not filename:
                filename = basename(file)
            file = open(file, 'rb')

        if not filename:
            filename = 'video'
        # just assume mp4 if not otherwise found
        if not content_type:
            content_type = 'video/mp4'
            filename = f'{filename}.mp4'

        # COMBAK no guarantees filename/content_type is right
        files = { 'VideoFile': (filename, file, content_type) }
        data = { 'video': json.dumps(metadata) }

        resp = self.client.post('/api/v2/uploads/videos', files=files, data=data)
        return resp.get('videoId')

    def upload_transcription(self, video_id: str, file, language: str = 'en', filename: str = 'subtitle.srt', content_type: str = 'application/x-subrip'):
        # set vars from file if already in requests format
        if isinstance(file, tuple):
            if len(file) >= 3:
                filename, file, content_type = file
            elif len(file) >= 2:
                filename, file = file
            else:
                file = file[0]
        
        # Rev expects correct filename format, so assume srt if no extension
        if not (filename.endswith('srt') or filename.endswith('vtt')):
            filename += '.srt'
        
        # validate language
        supported_languages = { 'de', 'en', 'en-gb', 'es-es', 'es-419', 'es', 'fr', 'fr-ca', 'id', 'it', 'ko', 'ja', 'nl', 'no', 'pl', 'pt', 'pt-br', 'th', 'tr', 'fi', 'sv', 'ru', 'el', 'zh', 'zh-tw', 'zh-cmn-hans' }

        language = language.lower()
        if not language in supported_languages:
            # try removing trailing language specifier
            if language[:2] in supported_languages:
                language = language[:2]
            else:
                raise TypeError(f'Invalid language {language} - supported values are { supported_languages}')

        json_payload = {'files': [{ 'language': language, 'fileName': filename }]}

        files = {'File': (filename, file, content_type)}
        data = {'TranscriptionFiles': json.dumps(json_payload)}
        
        return self.client.post(f'/api/uploads/transcription-files/{video_id}', files = files, data = data)


    def search_stream(self, query: dict = {}, max_results = None, on_page = None):
        pager = self.client._scroll('/api/v2/videos/search', 'totalVideos', 'videos', query, max_results=max_results)

        for page in pager:
            if on_page:
                on_page(page)
            for vid in page.items:
                yield vid
        
    def search(self, query: dict = {}, max_results = None, on_page = None):
        return [ vid for vid in self.search_stream(query, max_results, on_page) ]