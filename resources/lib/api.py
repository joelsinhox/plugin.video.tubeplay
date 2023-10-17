import requests
import re

class Tube:
    def __init__(self,url):
        self.api = 'https://www.youtube.com/youtubei/v1/player'
        self.key = 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'
        self.length = 0
        self.title = ''
        self.author = ''
        self.thumbnail = ''
        self.url = ''
        self.headers = {'User-Agent': 'com.google.android.apps.youtube.music/', 'Accept-Language': 'en-US,en'}
        self.result = self.scrape_api(self.get_id(url)) if url else {}                    
        
    def get_id(self,url):
        video_id = ''
        video_id_match = re.search(r'v=([A-Za-z0-9_-]+)', url)
        if video_id_match:
            id_ = video_id_match.group(1)
            try:
                id_ = id_.split("&")[0]
            except:
                pass
            video_id = id_
        return video_id
    
    def pick_source(self,sources):
        quality_max = 0
        url_max = ''
        for quality, url in sources:
            quality = quality.replace('p', '')
            if int(quality) > quality_max:
                quality_max = int(quality)
                url_max = url
        return url_max               
    
    def scrape_api(self,video_id):
        api = f'{self.api}?videoId={video_id}&key={self.key}&contentCheckOk=True&racyCheckOk=True'
        json_music = {
            "context": {
                "client": {
                    "androidSdkVersion": 30,
                    "clientName": "ANDROID_MUSIC",
                    "clientVersion": "5.16.51"
                }
            }
        }
        json_normal = {
            "context": {
                "client": {
                    "androidSdkVersion": 30,
                    "clientName": "ANDROID_EMBEDDED_PLAYER",
                    "clientScreen": "EMBED",
                    "clientVersion": "17.31.35"
                }
            }
        }
        result = {}
        response_music = requests.post(api, headers=self.headers, json=json_music)
        if response_music.status_code == 200:
            r = response_music.json()
            details = r['videoDetails']
            self.length = int(details['lengthSeconds'])
            self.title = details['title']
            self.author = details['author']
            thumb = details['thumbnail']['thumbnails']
            try:
                select_thumb = [image['url'] for image in thumb][-1]
                self.thumbnail = select_thumb
            except:
                pass
            ok_music = r.get("streamingData", False)
            if ok_music:
                result = r
        if not result:
            response_normal = requests.post(api, headers=self.headers, json=json_normal)
            if response_normal.status_code == 200:
                r = response_normal.json()
                ok_normal = r.get("streamingData", False)
                if ok_normal:
                    result = r
        if result:
            try:
                videos = result['streamingData']['formats']
                sources = [(v['qualityLabel'], v['url']) for v in videos]
                self.url = self.pick_source(sources)
            except:
                pass

        return result