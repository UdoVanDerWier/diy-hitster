from typing import Optional
from fastapi import FastAPI, Response, Request, Cookie, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from spotify import Spotify, SpotifyAuthenticate
from database import Database
from helpers import Helpers
from dotenv import load_dotenv
import os, secrets

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
call_back = os.getenv("REDIRECT")
url = os.getenv("URL")
app_secret = os.getenv("APP_SECRET")
mode = os.getenv("MODE")
raw_origins = os.getenv("CORS_ORIGINS", "")
origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

auth = SpotifyAuthenticate(client_id, client_secret, call_back)
spotify = Spotify()
database = Database()
database.init_tables()

sessions = {}
oauth_states = {}

helpers = Helpers(spotify=spotify, sessions=sessions, oauth_states=oauth_states)

@app.get("/spotify/login")
async def spotify_login(state: Optional[str] = None):
    auth_url = await auth.login(state=state or "/docs")
    return RedirectResponse(auth_url)

@app.get("/spotify/callback")
async def spotify_callback(request: Request, code: str, state: Optional[str] = None):
    await auth.callback(code)
    access_token = auth.getAccessToken()
    session_id = secrets.token_hex(16)

    sessions[session_id] = {"access_token": access_token}

    redirect_path = oauth_states.pop(state, "/docs") if state else "/docs"
    response = RedirectResponse(redirect_path)
    response.set_cookie(
        "session_id",
        value=session_id,
        httponly=mode == "production",
        secure=mode == "production",      # allowed on localhost
        samesite="Lax"     # or "None", but Secure is then required
    )
    return response

@app.get("/spotify/params")
async def spotify_params(state) : 
    state_id = secrets.token_hex(16)
    oauth_states[state_id] = state
    auth_params = auth.getparams(state_id)
    return JSONResponse(auth_params)

@app.get("/spotify/play/{uri}")
async def set_song(uri: str, session: dict = Depends(helpers.require_session_dep)):
    if isinstance(session, Response):
        return session
    data = await spotify.setSong(uri)
    return helpers.handle_spotify_response(data, f"/spotify/play/{uri}")

@app.get("/spotify/getPlayLists")
async def get_playlists(session: dict = Depends(helpers.require_session_dep)):
    if isinstance(session, Response):
        return session
    data = await spotify.getPlayLists()
    return helpers.handle_spotify_response(data, f"/spotify/getPlayLists")

@app.get("/spotify/getPlayLists/{playlist_id}")
async def get_playlist(playlist_id: str, session: dict = Depends(helpers.require_session_dep)):
    if isinstance(session, Response):
        return session
    data = await spotify.getPlayList(playlist_id)
    return helpers.handle_spotify_response(data, f"/spotify/getPlayLists/{playlist_id}")

