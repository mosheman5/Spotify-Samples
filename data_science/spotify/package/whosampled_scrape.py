from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
http = urllib3.PoolManager()
from tqdm import tqdm

def retrieve_song_link(song_name, artist_name=None):
    song_name = song_name + ' ' + artist_name
    query = song_name.replace(' ', '%20')
    url = 'https://www.whosampled.com/search/tracks/?q={}'.format(query)
    r = http.request('GET', url)
    content = r.data
    soup = BeautifulSoup(content, 'html.parser')
    stuff = soup.findAll('li', attrs={'class': "listEntry"})
    if stuff:
        link = [i.a for i in stuff][0].get('href')
        return link
    # else:
#         print('{} not found on whosampled'.format(song_name))

def retrieve_samples_v2(song_name, link):
    samples = []
    sampled_by = []
    s = http.request('GET', 'https://www.whosampled.com'+link)
    content1 = s.data
    soup = BeautifulSoup(content1, 'html.parser')
    listed = [i.text for i in soup.findAll('div', attrs={'class':'list bordered-list'})]
    if len(listed) == 2:
        there_in = [i.split('\n') for i in list(filter(None, listed[0].split('\t')))][:-1]
        there_out = [i.split('\n') for i in list(filter(None, listed[1].split('\t')))][:-1]
        for j in there_in:
            sampled_by.append({'query':song_name, 'type':j[-7], 'genre':j[-6], 'title':j[-3], 'artist':j[-2].replace('by ', '').split(' (')[0], 'year': j[-2].replace('by ', '').split(' (')[1].replace(')', '')})
    else:
        there_out = [i.split('\n') for i in list(filter(None, listed[0].split('\t')))][:-1]
    for i in there_out:
        try:
            samples.append({'query':song_name, 'type':i[-7], 'genre':i[-6], 'title':i[-3], 'artist':i[-2].replace('by ', '').split(' (')[0], 'year': i[-2].replace('by ', '').split(' (')[1].replace(')', '')})
        except:
            pass
    return samples, sampled_by

def getme_thesamples(song_name, artist_name):
    link = retrieve_song_link(song_name, artist_name)
    if link:
        samples, sampled_by = retrieve_samples_v2(song_name, link)
        return samples, sampled_by
    else:
        return [], []

def get_whosampled_playlist(loaded_playlist, verbose=False):
    new_playlist = []
    print('SPOTIFY PLAYLIST DISCOVERED: \n')
    if verbose:
        for i in loaded_playlist:
            print(i['track']+' by '+i['artist'][0])
    for i in tqdm(loaded_playlist):
        orig_song = {'spotify_id': i['spotify_id']}
        try:
            samples, sampled_by = getme_thesamples(i['track'], i['artist'][0])
        except:
            continue
        orig_song['samples'] = samples
        orig_song['sampled_by'] = sampled_by
        if len(samples) + len(sampled_by):
            new_playlist.append(orig_song)

    return new_playlist
