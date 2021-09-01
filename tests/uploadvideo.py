# %%
import sys
import os

import requests
from revclient import RevClient
# %%
# client config values - get from environment variables
url = os.getenv('REV_URL', 'https://my.rev.url')
username = os.getenv('REV_USERNAME', '')
password = os.getenv('REV_PASSWORD', '')
apiKey = os.getenv('REV_APIKEY', '')
secret = os.getenv('REV_SECRET', '')

# upload video config - get from environment variables
filename = os.getenv('UPLOAD_FILE', "/path/to/video.mp4")
video_metadata = {
	'uploader': os.getenv('UPLOAD_USER', username),
	'title': os.getenv('UPLOAD_TITLE', 'new video')
}

rev = RevClient(url, username = username, password = password, apiKey=apiKey, secret=secret)
rev.connect()
print('logged in. Session expires: ' + str(rev.session.expires))

# %%

result = {}

with open(filename, "rb") as file:
	try:
		resp = rev.video.upload(file, video_metadata)
		result['resp'] = resp
		print('Upload Complete - video id = ' + resp)
	except Exception as err:
		print('failed')
		print(err)
		result['err'] = err

# %%

rev.disconnect()
print('done!')
# %%
