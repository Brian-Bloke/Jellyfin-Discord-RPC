import socket
import json
import time
import os
import struct
import requests


"""
JELLYFIN DISCORD RPC VER 1
    -A custom rpc script designed to show your jellyfin status in your Discord profile
    -Supports Movies, Shows and Songs 
    -Hit me up if you face any errors. Ill try to fix it 
"""

#README provides the instrunctions to obtain the required API keys
#PIPE_PATH may differ. It's discord-rpc-0. The last number and the directory may vary. (Eg:- /tmp/, /var/). For linux and mac this will most likely be the case. For windows I am not sure whether Windows treats pipes as files 

PIPE_PATH="/run/user/1000/discord-ipc-0"
TMDB_API_KEY = ""
JELLYFIN_API_KEY = ""
JELLYFIN_SERVER = "http://192.168.1.2:8096/Sessions"
DISCORD_API_KEY = ""

#All the information about the media will be stored in this array
info=["Media_Name","watch_state","start","end","showname","duration","Production_Year","Genres","Media_type","song_artist","poster_url","was_playing"]




"""
We're using this function to obtain a poster url for the song If the media is a song. We're using our info array in global scope.(we'll be writing to it) 
We have two parameters for this function the name of the song and the artists name. 
First we check if we have the song in the info array 
    - if yes we just use the one from our info array 
    - if not 
        - we import the song into our info array.
        - then we seperate each words from the song name and the artists name and make it into a string with "+" being in the middle only
        - then we're adding the string into the search field of the url. We're using itunes btw.
        - then we're using requests to make a request to the api and parsing the results to json
        - then we're implementing some error avoiding mechanism.
            -We first check if we got a reply from the api endpoint 
            -if yes
                - we see if we have the link to our poster image in the response if yes we return the link and save it to the info array and if not we use a custom jellyfin logo image as our poster (also saving it to info but it's not necessary)
            -if not
                - we just return the same jellyfin logo as our poster image
Every 5 seconds this will repeat itself and if the same song is being played , it won't request the api all over again it will just use the one
previously saved to the info array. So we don't spam the api endpoint.
Btw props to itunes for allowing us to use their api without an api key
"""
def get_song_poster(song_name,artists_name):
    global info
    if info[11] != (song_name + " " + " ".join(artists_name)):
        info[11] = song_name +  " " + " ".join(artists_name)
        text=""
        title=song_name.split(" ")
        for i in title:
            text = text + i + "+"
        for i in artists_name:
            a = i.split(" ")
            for b in a:
                text = text + b + "+"
        text = text[:-1]
        url=f"https://itunes.apple.com/search?term={text}&entity=song&limit=1"
        response = requests.get(url).json()
        if response['results']:
            try:
                info[10]=response['results'][0]['artworkUrl100']
                return response['results'][0]['artworkUrl100']
            except:
                info[10]="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR9hELYbRA5IB6-ci3AzpkvOTJ3BAq6-_LmMg&s"
                return info[10]
        else:
            info[10]="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR9hELYbRA5IB6-ci3AzpkvOTJ3BAq6-_LmMg&s"
            return info[10]
    else:
        return info[10]






"""
We're using this to obtain a poster image if the media is a movie. It's using te same concept as above to stop spamming the api endpoint.
Same error handling techniques. 
However, TMDB api does require an api key. It's free and fairly easy to generate an api key, follow the README to get one.
There's another problem which is the image they provide is rectangular. You are only allowed to ask for the width and the height will automatically be
adjusted according to the aspect ratio. If we provide that image to discord, it will crop the image into a square one instead of resizing it. 
So this script is using a publically available cdn to resize the image to 500x500 in my case. Discord will happily accept that
"""
def get_movie_poster(title,year):
    global info
    if info[11] != title + " " + str(year):
        info[11]=title + " " + str(year)
        search_url = f"https://api.themoviedb.org/3/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "query": title,
            "year":year
        }

        response = requests.get(search_url, params=params).json()

        if response['results']:
            try:
                poster_path=response['results'][0]['poster_path']
            except:
                info[10] = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR9hELYbRA5IB6-ci3AzpkvOTJ3BAq6-_LmMg&s"
                return info[10]
            if not(poster_path is None):
                info[10] = "https://images.weserv.nl/?url="+ "https://image.tmdb.org/t/p/w500"+ poster_path + "&w=500&h=500&fit=fill"
                return info[10]
            else:
                info[10] = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR9hELYbRA5IB6-ci3AzpkvOTJ3BAq6-_LmMg&s"
                return info[10]
        else:
            info[10]="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR9hELYbRA5IB6-ci3AzpkvOTJ3BAq6-_LmMg&s"
            return info[10]
    else:
        return info[10]



"""
We're using this to obtain a poster image if the media is a series. Exactly similar to the above function but here we are using /search/tv instead of
/search/movie for search_url cus this is a tv show and not a movie other than that the rest is similar
"""
def get_show_poster(title,year):
    global info
    if info[11] != title + " " + str(year):
        info[11]=title + " " + str(year)
        search_url = f"https://api.themoviedb.org/3/search/tv"
        params = {
            "api_key": TMDB_API_KEY,
            "query": title,
            "first_air_date_year":year
        }

        response = requests.get(search_url, params=params).json()

        if response['results']:
            try:
                poster_path=response['results'][0]['poster_path']
            except:
                info[10] = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR9hELYbRA5IB6-ci3AzpkvOTJ3BAq6-_LmMg&s"
                return info[10]
            if not(poster_path is None):
                info[10] = "https://images.weserv.nl/?url="+ "https://image.tmdb.org/t/p/w500"+ poster_path + "&w=500&h=500&fit=fill"
                return info[10]
            else:
                info[10] = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR9hELYbRA5IB6-ci3AzpkvOTJ3BAq6-_LmMg&s"
                return info[10]
        else:
            info[10]="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR9hELYbRA5IB6-ci3AzpkvOTJ3BAq6-_LmMg&s"
            return info[10]
    else:
        return info[10]




"""
This function is being used to construct the frame to send to the discord rpc pipe.
This is how the raw data should look like
[4 bytes opcode][4 bytes length][JSON payload bytes]
[         header               ][       data       ]
We're only using the opcode 0 and 1 here. 0-handshake(using our discord key to verify) and 1-Frame(to send the actual data)
And the length is the basically the count of the number of bytes in data
The opcode and length should each be 4 bytes long so we convert both to a 4 byte integer and we arrive with the header.
We send json data through the payload parameter.
We convert that payload into a json string then we encode that string into raw bytes.
Then we can send the combined (header + data) through the pipe.
"""
def send_frame(sock, opcode, payload):
    data = json.dumps(payload).encode()
    header = struct.pack("<II", opcode, len(data))
    sock.sendall(header + data)



"""
We use this function to populate the info array with all the necessary data.
First we make a request to our jellyfin server and parse the response into a json array.
Then we get the first active session.
https://api.jellyfin.org/ all the jellyfin api requests and responses can be found there

Jellyfin uses ticks to show the progress and durations of the playing media(1 second = 10000000 ticks)
The start and end fields are the actual fields discord rpc uses.
We should provide each with a unix timestamp.(no floats)
here's how it works.
    In discord's POV it calculates the total duration by this formula (end - start) which should be int(duration)
    It finds the elapsed time by seeing how far off start is from int(time.time())  
    [int(time.time()) basically returns the seconds between January 1, 1970 to now]

    Eg:- 
        let's say
            start = int(time.time()) - 4
            end = int(time.time()) - 4 + 10
            Discord will think that we're watching a 10 seconds long media and 4 seconds has elapsed so far 
"""
def fetch_jellyfin_api():
    global info
    sessions = requests.get(JELLYFIN_SERVER, headers={"X-Emby-Token": JELLYFIN_API_KEY}).json()
    session=sessions[0]
    duration=session["NowPlayingItem"].get("RunTimeTicks", 0) / 10000000
    progress = session["PlayState"]["PositionTicks"] / 10000000
    start = int(time.time()) - int(progress)
    end = int(time.time()) + int(duration) - int(progress)
    show_info = "S" + str(session["NowPlayingItem"].get('ParentIndexNumber', 'Unknown')) + " E" + str(session["NowPlayingItem"].get('IndexNumber', 'Unknown'))
    info[:10] = [session["NowPlayingItem"].get('Name', 'Unknown'),  "Paused" if session["PlayState"]["IsPaused"] else "Playing", start,end,session["NowPlayingItem"].get('SeriesName', 'Unknown'),show_info, session["NowPlayingItem"].get('ProductionYear', 'Unknown'), session["NowPlayingItem"].get('Genres', 'Unknown'), session["NowPlayingItem"]["Type"], session["NowPlayingItem"].get("Artists", 'Unknown')]
    return info



"""
This is the main function.
We're initiating the handshake firstly by sending our DISCORD_API_KEY to the pipe.
Then we're trying to see whether there is any active sessions playing media. If yes it will exit the loop if not it will wait for it to become active
Meanwhile we're sending a null activity to discord so that it will clear the previous activity if there was any
SET_ACTIVITY is the cmd type to use to set an activity. pid is there to tell discord what rpc to clear as we can have multiple apps display their own
presence at the same time. we're sending null as activity. nonce is only needed when we're trying to receivce the response from the pipe otherwise it's not necessary
Then we're trying to find the type of the current media.
    -Movie(for movies)
    -Audio(for songs)
    -Episode(for shows)
In the json block type means the thing we're doing. 3 means watching and 2 means listening. Here we don't really need nonce cus we're not dealing with the response allthough we should listen to the response to see if the SET_ACTIVITY was successfull or not but it doesn't really matter especially since we're resending SET_ACTIVITY evry 5 seconds. So one or two failed requests doesn't really matter. The rest is pretty self explanatory 
"""
def main():
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(PIPE_PATH)
    send_frame(sock, 0, {"v": 1, "client_id": DISCORD_API_KEY}) 
    while True:
        while True:
            try:
                info = fetch_jellyfin_api()
                break
            except:
                print("Waiting For Media")
                presence_clear= {
                    "cmd": "SET_ACTIVITY",
                    "args": {
                        "pid": os.getpid(),
                        "activity": None
                    },
                    "nonce": "clear_activity"
                }
                send_frame(sock, 1, presence_clear)
                time.sleep(1)
        print(info)
        if info[8] == "Movie":
            presence_watching = {
                    "cmd": "SET_ACTIVITY",
                    "args": {
                        "activity": {
                            "details": f"{info[0]} ({info[6]})",
                            "state": f"{', '.join(info[7])}",
                            "name": info[0],
                            "timestamps": {
                                "start": info[2],
                                "end": info[3]
                                },
                            "assets": {
                                "large_image": f"{get_movie_poster(info[0],info[6])}",
                                },
                            "type": 3
                            },
                        "pid": os.getpid()
                        },
                    "nonce": str(int(time.time() * 1000))
                    }
            presence_paused = {
                    "cmd": "SET_ACTIVITY",
                    "args": {
                        "activity": {
                            "details": f"{info[0]} ({info[6]})",
                            "state": f"{', '.join(info[7])} ⏸ ",
                            "name": info[0],
                            "assets": {
                                "large_image": f"{get_movie_poster(info[0],info[6])}",
                                },
                            "type": 3
                            },
                        "pid": os.getpid()
                        },
                    "nonce": str(int(time.time() * 1000))
                    }
            if info[1] == "Playing":
                send_frame(sock, 1, presence_watching)
            if info[1] == "Paused":
                send_frame(sock, 1, presence_paused)
            time.sleep(5)  
        if info[8] == "Audio":
            presence_listening = {
                    "cmd": "SET_ACTIVITY",
                    "args": {
                        "activity": {
                            "details": f"{info[0]} ({', '.join(info[9])})",
                            "name": info[0],
                            "timestamps": {
                                "start": info[2],
                                "end": info[3]
                                },
                            "assets": {
                                "large_image": f"{get_song_poster(info[0],info[9])}",
                                },
                            "type": 2
                            },
                        "pid": os.getpid()
                        },
                    "nonce": str(int(time.time() * 1000))
                    }
            presence_paused = {
                    "cmd": "SET_ACTIVITY",
                    "args": {
                        "activity": {
                            "details": f"{info[0]} ({', '.join(info[9])})",
                            "state": "paused ⏸ ",
                            "name": info[0],
                            "assets": {
                                "large_image": f"{get_song_poster(info[0],info[9])}",
                                },
                            "type": 2
                            },
                        "pid": os.getpid()
                        },
                    "nonce": str(int(time.time() * 1000))
                    }
            if info[1] == "Playing":
                send_frame(sock, 1, presence_listening)
            if info[1] == "Paused":
                send_frame(sock, 1, presence_paused)
            time.sleep(5)  
        if info[8] == "Episode":
            presence_watching = {
                    "cmd": "SET_ACTIVITY",
                    "args": {
                        "activity": {
                            "details": f"{info[4]} -{info[5]}",
                            "state": f"{', '.join(info[7])}",
                            "name": info[4],
                            "timestamps": {
                                "start": info[2],
                                "end": info[3]
                                },
                            "assets": {
                                "large_image": f"{get_show_poster(info[4],info[6])}",
                                },
                            "type": 3
                            },
                        "pid": os.getpid()
                        },
                    "nonce": str(int(time.time() * 1000))
                    }
            presence_paused = {
                    "cmd": "SET_ACTIVITY",
                    "args": {
                        "activity": {
                            "details": f"{info[4]} -{info[5]}",
                            "state": f"{', '.join(info[7])} ⏸ ",
                            "name": info[4],
                            "assets": {
                                "large_image": f"{get_show_poster(info[4],info[6])}",
                                },
                            "type": 3
                            },
                        "pid": os.getpid()
                        },
                    "nonce": str(int(time.time() * 1000))
                    }
            if info[1] == "Playing":
                send_frame(sock, 1, presence_watching)
            if info[1] == "Paused":
                send_frame(sock, 1, presence_paused)
            time.sleep(5)  
        time.sleep(5)
    sock.close()

if __name__ == "__main__":
    main()
