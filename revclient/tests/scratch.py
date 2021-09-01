# %%
import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../revclient")
# %%
import requests
from revclient.lib.client import RevClient
# %%
    
url = "https://lukeselden.rev-eu.demo.vbrick.com"
username = os.getenv('REV_USER', 'my.username')
password = os.getenv('REV_PASS', 'my.password')

client = RevClient(url, username = username, password = password)
# %%
client.login()
# %%
video_id = 'b1fffa4e-03dd-4b67-ae37-30c718f3eb69'

#%%
q = {}
file = open("E:\\Downloads\\asvtt.srt", "rb")
filename = 'hello.srt'
content_type = 'application/x-subrip'
langulage = 'en'
#%%
with open("E:\\Downloads\\asvtt.srt", "rb") as f:
	try:
		resp = client.video.upload_transcription(video_id, file = f, language='en')
		print(resp)
		q['resp'] = resp
	except Exception as e:
		print('failed')
		q['e'] = e
	#response = requests.post(url, headers=headers, files=files, data=data)

print('done!')
# %%
