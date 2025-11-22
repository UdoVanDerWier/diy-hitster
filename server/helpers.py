from fastapi import Request
from fastapi.responses import RedirectResponse, JSONResponse
import secrets

class Helpers:
    def __init__(self, oauth_states, sessions, spotify):
        self.oauth_states = oauth_states
        self.sessions = sessions
        self.spotify = spotify

    async def require_session_dep(self, request: Request):
        session_id = request.cookies.get("session_id")
        path_state = request.url.path or "/docs"
        print(path_state)

        if not session_id or session_id not in self.sessions:
            state_id = secrets.token_hex(16)
            self.oauth_states[state_id] = path_state
            return RedirectResponse(f"http://127.0.0.1:8000/spotify/login?state={state_id}")

        access_token = self.sessions[session_id]["access_token"]
        self.spotify.setAccessToken(access_token)
        return self.sessions[session_id]

    def handle_spotify_response(self, data: dict, redirect_path: str):
        if data.get("status_code") == 401:
            state_id = secrets.token_hex(16)
            self.oauth_states[state_id] = redirect_path
            return RedirectResponse(f"http://127.0.0.1:8000/spotify/login?state={state_id}")
        return JSONResponse(content=data)

