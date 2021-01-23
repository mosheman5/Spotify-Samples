import spotipy
from spotipy import util
from whosampled_scrape import *
from config import *
from tqdm import tqdm


def call_api(username, scope='playlist-modify-public'):
    ### define client_id, client secret and redirect uri as environment variables
    token = util.prompt_for_user_token(username, scope)
    return token


def make_description(spot_dict):
    unfound=spot_dict['unfound']
    rate=spot_dict['rate']
    summary = 'Samples Not on Spotify: {} \nPercentage of Samples Added: {}%'.format(unfound, round(rate, 3))
    return summary


def get_full_results(sp, results_obj):
    final_results = results_obj['items']
    while results_obj['next']:
        results_obj = sp.next(results_obj)
        final_results.extend(results_obj['items'])
    return final_results


def read_playlist(uri, sp):
    playlist_id = uri.split(':')[2]
    og_tracks = []
    results = sp.playlist_items(playlist_id=playlist_id)
    results = get_full_results(sp, results)  # Needed to extract more than 100 songs from the playlist
    for i in results:
        artists = [j['name'] for j in i['track']['artists']]
        og_tracks.append({'artist' : artists, 'track':i['track']['name'].replace('Instrumental', '')})
    return og_tracks


def get_sample_data(uri, sp):
    loaded_playlist = read_playlist(uri, sp)
    new_playlist_tracks = get_whosampled_playlist(loaded_playlist)
    return new_playlist_tracks

def get_spotify_ids(whosampled_playlist, sp):
    id_list = []
    unfound_list= []
    for i in tqdm(whosampled_playlist):
        try:
            sub_list = []
            artist = i['artist'].lower()
    #         print('NEW SAMPLE: {} by {}'.format(i['title'], artist))
            result = sp.search(i['title'], limit=50)['tracks']['items']
            for j in result:
                if j['artists'][0]['name'].lower() == artist:
                    sub_list.append(j['id'])
                    break

            if sub_list:
    #             print('FOUND ON SPOTIFY')
                id_list.append(sub_list[0])
            else:
    #             print('NO ID FOUND FOR {} by {}'.format(i['title'], artist))
                unfound_list.append((i['title']+' by '+artist))
        except:
            pass
    location_rate=1 - len(unfound_list)/len(whosampled_playlist)
    return {'ids': id_list, 'unfound': unfound_list, 'rate': location_rate}

def create_and_populate(username, new_playlist_name, spotify_dict, sp):
    _ = sp.user_playlist_create(username, new_playlist_name)
    newest_id = sp.user_playlists(username)['items'][0]['id'] #get ID of playlist just created

    from itertools import zip_longest

    def grouper(iterable, n, fillvalue=None):
        args = [iter(iterable)] * n
        return zip_longest(*args, fillvalue=fillvalue)

    new_lists = grouper(spotify_dict['ids'], 100)

    for par_list in new_lists:
        try:
            print(len(par_list))
            sp.user_playlist_add_tracks(username, newest_id, par_list, None) #populate playlist with all samples
        except:
            pass


def get_new_sample_playlist(uri, new_playlist_name, user, verbose=False):

    token = call_api(user, 'playlist-modify-public')
    sp2 = spotipy.Spotify(auth=token)
    new_playlist_tracks = get_sample_data(uri, sp2)
    print('\nChecking Spotify for Samples:\n')
    if verbose:
        for i in new_playlist_tracks:
            print(i['title']+' by '+ i['artist'])
    spotify_dict = get_spotify_ids(new_playlist_tracks, sp2)
    create_and_populate(user, new_playlist_name, spotify_dict, sp2)
    print('\nNew playlist "{}" created!'.format(new_playlist_name))
#     sp2.user_playlist_change_details(username, playlist_id, name=new_playlist_name, public=None, collaborative=None,description=description)
    pass

def run_program():
    uri = "spotify:playlist:6iZZgDcyTS23fAmyjxqIz8"
    name = "demo"
    username = '31yln7gos65hk5lwn5chxi225yqq'
    # playlist_id = uri.split(':')[4]
    get_new_sample_playlist(uri, name, username)
    pass

run_program()
