import requests
import json

access = 'a1b7d603813dec6c449007c4f8b92df46c0d126208f29f28141dfa5aa5ee9940'
instance = 'https://canor.synology.me'
headers = {'Authorization':'Bearer '+access}
data = dict()

def upload_url_image(url):
    img_url = requests.get(url).content
    files = {'file':img_url}
    media = requests.post(instance+'/api/v1/media',headers=headers,files=files)
    return media.content.decode('utf-8')

def toot(status, args):
    data['status'] = status
    media = list()
    for arg in args:
        media.append(arg)
    data['media_ids[]'] = media
    requests.post(instance+'/api/v1/statuses',headers=headers,data=data)
