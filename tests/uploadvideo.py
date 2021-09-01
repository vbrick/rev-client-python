# %%
import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../revclient")
# %%
import requests
from revclient.lib.client import RevClient
# %%
# client config values - get from environment variables
url = os.getenv('REV_URL', 'https://my.rev.url')
username = os.getenv('REV_USERNAME', '')
password = os.getenv('REV_PASSWORD', '')
apiKey = os.getenv('REV_APIKEY', '')
secret = os.getenv('REV_SECRET', '')

# upload video config
# REQUIRED - change me!
filename = "/path/to/video.mp4"
video_metadata = {
	# REQUIRED - change me!
	'uploader': 'uploader.username',
	'title': 'new video'
}

client = RevClient(url, username = username, password = password, apiKey=apiKey, secret=secret)
client.login()

with open(filename, "rb") as f:
	try:
		resp = client.video.upload(f, video_metadata)
		print(resp)
	except Exception as e:
		print('failed')
		print(e)

client.logoff()
print('done!')
# %%
