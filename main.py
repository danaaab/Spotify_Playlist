from flask import Flask, render_template, request, redirect, url_for, flash, session
import requests
from bs4 import BeautifulSoup
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

CLIENT_ID = os.environ.get('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.environ.get('SPOTIPY_CLIENT_SECRET')
URL = "https://www.billboard.com/charts/hot-100"


def create_spotify_playlist(date):
    try:
        header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0"}
        response = requests.get(url=f"{URL}/{date}", headers=header)
        data = response.text

        soup = BeautifulSoup(data, "html.parser")
        song_names_spans = soup.select("li ul li h3")
        song_names = [song.getText().strip() for song in song_names_spans]

        sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                scope="playlist-modify-private",
                redirect_uri=os.environ.get('SPOTIPY_REDIRECT_URI'),
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                show_dialog=True,
                cache_path="token.txt",
                username=os.environ.get('SPOTIPY_USERNAME'),
            )
        )
        user_id = sp.current_user()["id"]

        song_uris = []
        year = date.split("-")[0]
        for song in song_names:
            result = sp.search(q=f"track:{song} year:{year}", type="track")
            try:
                uri = result["tracks"]["items"][0]["uri"]
                song_uris.append(uri)
            except IndexError:
                print(f"{song} doesn't exist in Spotify. Skipped.")

        playlist = sp.user_playlist_create(user=user_id, name=f"{date} Billboard 100", public=False)
        sp.playlist_add_items(playlist_id=playlist["id"], items=song_uris)
        return playlist["external_urls"]["spotify"]
    except Exception as e:
        return str(e)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        date = request.form.get("date")
        try:
            datetime.strptime(date, '%Y-%m-%d')
            playlist_url = create_spotify_playlist(date)
            if "spotify.com" in playlist_url:
                flash("Playlist created successfully!", "success")
                return render_template("index.html", playlist_url=playlist_url)
            else:
                flash(f"Error: {playlist_url}", "error")
        except ValueError:
            flash("Please enter a valid date in YYYY-MM-DD format.", "error")
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=False)