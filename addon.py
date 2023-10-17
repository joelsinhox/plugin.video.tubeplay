import sys
import os
import json
import requests
from urllib.parse import urlparse, parse_qs, quote, unquote, quote_plus, unquote_plus, urlencode
from resources.lib.api import Tube
from resources.lib import scrapetube
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs 

plugin = sys.argv[0]
handle = int(sys.argv[1])
addon = xbmcaddon.Addon()
addonname = addon.getAddonInfo('name')
addonid = addon.getAddonInfo('id')
icon = addon.getAddonInfo('icon')
translate = xbmcvfs.translatePath
home = translate(addon.getAddonInfo('path'))
profile = translate(addon.getAddonInfo('profile'))
listitem = xbmcgui.ListItem
adddirectory = xbmcplugin.addDirectoryItem
enddirectory = xbmcplugin.endOfDirectory
content = xbmcplugin.setContent
player = xbmcplugin.setResolvedUrl
dialog = xbmcgui.Dialog()
keyboard = xbmc.Keyboard
string = addon.getLocalizedString
limit = addon.getSetting("maxsearch")



def kversion():
    full_version_info = xbmc.getInfoLabel('System.BuildVersion')
    baseversion = full_version_info.split(".")
    intbase = int(baseversion[0])
    return intbase

def route(r):
    route_decorator = r.split('/')[1] # function name from route
    plugin_route = plugin.split('/')[3:] # command from sys
    route_sys = plugin_route[0] # function name from sys
    def decorator(f):
        params = {}
        try:
            param_root = plugin_route[1] # params from sys
            param_root = unquote_plus(param_root).split('&')
            for command in param_root:
                if '=' in command:
                    split_command = command.split('=')
                    key = split_command[0]
                    value = split_command[1]
                    params[key] = value
                else:
                    params[command] = ''
        except:
            pass
        if not route_decorator and not route_sys:
            try:
                f(params)
            except:
                f()
        elif route_decorator == route_sys:
            try:
                f(params)
            except:
                f()
    return decorator

def to_unicode(text, encoding='utf-8', errors='strict'):
    """Force text to unicode"""
    if isinstance(text, bytes):
        return text.decode(encoding, errors=errors)
    return text

def get_search_string(heading='', message=''):
    """Ask the user for a search string"""
    search_string = None
    k = keyboard(message, heading)
    k.doModal()
    if k.isConfirmed():
        search_string = to_unicode(k.getText())
    return search_string

def search():
    vq = get_search_string(heading=string(30014), message="")        
    if ( not vq ): return False
    return vq


def item(params, destiny, folder=True):
    try:
        destiny = destiny.split('/')[1]
    except:
        pass
    u = f'plugin://{plugin.split("/")[2]}/{destiny}/{quote_plus(urlencode(params))}'
    liz = listitem(params['name'])
    liz.setArt({'fanart': params.get('fanart', ''), 'thumb': params.get('iconimage', ''), 'icon': "DefaultFolder.png"})
    if kversion() > 19:
        info = liz.getVideoInfoTag()
        info.setTitle(params.get('name'))
        info.setMediaType('video')
        info.setPlot(params.get('description', ''))
    else:
        liz.setInfo(type="Video", infoLabels={"Title": params.get('name', ''), 'mediatype': 'video', "Plot": params.get('description', '')})
    if params.get('playable', 'false') == 'true':
        liz.setProperty('IsPlayable', 'true')
    adddirectory(handle=handle, url=u, listitem=liz, isFolder=folder)

def play_item(params):
    name = unquote_plus(params['name'])
    youtube = unquote_plus(params['url'])
    description = unquote_plus(params.get('description', ''))
    info = Tube(youtube)
    stream = info.url
    if stream:        
        liz = listitem(params['name'])
        if kversion() > 19:
            info = liz.getVideoInfoTag()
            info.setTitle(name)
            info.setMediaType('video')
            info.setPlot(description)
        else:
            liz.setInfo(type="Video", infoLabels={"Title": name, 'mediatype': 'video', "Plot": description})     
        liz.setPath(stream) 
        player(int(sys.argv[1]), True, liz)
    else:
        dialog.notification(addonname, string(30013), xbmcgui.NOTIFICATION_INFO, 3000, sound=False)


def cache_save(key, videos):
    if not os.path.exists(profile):
        os.mkdir(profile)
    c = os.path.join(profile, 'cache.json')
    cache_ = {}
    cache_[key] = videos
    with open(c, 'w') as f:
        json.dump(cache_, f)

def cache_read(key):
    c = os.path.join(profile, 'cache.json')
    if os.path.exists(c):
        with open(c, 'r') as f:
            data = json.load(f)
            videos = list(data[key])
            return videos
    return False


def cache_clear():
    c = os.path.join(profile, 'cache.json')
    if os.path.exists(c):
        os.remove(c)


content(handle, 'videos')

@route('/')
def main():
    for i in range(6):
        i += 1
        playlisturl = addon.getSetting(f"playlisturl{str(i)}")
        if playlisturl:
            item({'name': string(30012)}, destiny='/playlist_user', folder=True)
            break
    item({'name': string(30009)}, destiny='/search_videos', folder=True)
    item({'name': string(30010)}, destiny='/settings', folder=True)
    enddirectory(handle,cacheToDisc=False)


@route('/playlist_user')
def playlist_user():
    cache_clear()
    for i in range(6):
        i += 1
        playlisturl = addon.getSetting(f"playlisturl{str(i)}")
        if playlisturl:
            item({'name': f'{string(30011)} {str(i)}', 'url': playlisturl}, destiny='/open_playlist', folder=True)
    enddirectory(handle)

@route('/open_playlist')
def open_playlist(params):
    k = unquote_plus(params['name'])
    url = unquote_plus(params['url'])
    videos = cache_read(k)
    if not videos:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
        if response.status_code == 200:
            parse = urlparse(response.url)
            playlist_id = parse_qs(parse.query)['list'][0]
            videos = list(scrapetube.get_playlist(playlist_id))
            cache_save(k, videos)
    if videos:    
        for video in videos:
            video_id = video['videoId']
            name = video['title']['runs'][0]['text']
            iconimage = [img['url'] for img in video['thumbnail']['thumbnails']][-1]
            youtube = f'https://www.youtube.com/watch?v={video_id}' 
            item({'name': name, 'url': youtube, 'iconimage': iconimage, 'playable': 'true'}, destiny='/play', folder=False)         
        enddirectory(handle)


@route('/search_videos')
def search_videos(params):
    k = search()
    if k:
        cache_clear()
        item({'name': f'{string(30011)}: {k}', 'key': k}, destiny='/search_playlist', folder=True)
        enddirectory(handle) 
        
    

@route('/search_playlist')
def search_playlist(params):
    k = params['key']
    videos = cache_read(k)
    if not videos:
        max = {'0': 15, '1': 30, '2': 50, '3': 70, '4': 100, '5': 150, '6': 200, '7': 300, '8': 500, '9': 700, '10': 1000}[str(limit)]
        videos = list(scrapetube.get_search(k, limit=max, results_type='video'))
        cache_save(k, videos)
    if videos:    
        for video in videos:
            video_id = video['videoId']
            name = video['title']['runs'][0]['text']
            iconimage = [img['url'] for img in video['thumbnail']['thumbnails']][-1]
            youtube = f'https://www.youtube.com/watch?v={video_id}' 
            item({'name': name, 'url': youtube, 'iconimage': iconimage, 'playable': 'true'}, destiny='/play', folder=False)         
        enddirectory(handle)   


@route('/play')
def play(params):
    play_item(params)

@route('/settings')
def settings():
    addon.openSettings()
