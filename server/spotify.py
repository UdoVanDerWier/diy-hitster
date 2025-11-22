from fastapi import FastAPI, Response
from fastapi.responses import RedirectResponse, JSONResponse
import httpx
import urllib
import base64

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_URL = "https://api.spotify.com/v1"

class Spotify() :
    def __init__(self, access_token: str=None) : 
        self.access_token = access_token

    def setAccessToken(self, access_token: str) : 
        self.access_token = access_token

    async def getUser(self):
        return await self._request("/me")

    async def getPlayLists(self):
        return await self._request("/me/playlists")

    async def getPlayList(self, id):
        return await self._request(f"/playlists/{id}")

    async def setSong(self, uri):
        return await self._request(f"/me/player/play", method="PUT", json={"uris": [uri]})

    async def _request(
        self,
        endpoint: str,
        method: str = "GET",
        *,
        params: dict | None = None,
        data: dict | None = None,
        json: dict | None = None,
        headers: dict | None = None,
    ):
        final_headers = {
            "Authorization": f"Bearer {self.access_token}",
            **(headers or {})
        }

        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method,
                f"{API_URL}{endpoint}",
                params=params,
                data=data,
                json=json,
                headers=final_headers
            )

        return {
            "status_code": resp.status_code,
            "data": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else None,
            "text": resp.text,
        }


class SpotifyAuthenticate () : 
    def __init__(self, client_id: str, client_secret: str, callback: str) : 
        # TODO : safe credentials in database using the user_id and email
        self.client_id = client_id
        self._secret = client_secret
        self._callback = callback
        self.scope = " ".join([
            "user-read-private",
            "user-read-email",
            "user-read-playback-state",
            "playlist-read-private",
            "user-modify-playback-state"
        ])
        self.access_token = None
        self.refresh_token = None

    def getAccessToken(self) : 
        print(f"self.accestoken {self.access_token}")
        return self.access_token

    def getparams(self, state) : 
        return {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self._callback,
            "scope": self.scope,
            "show_dialog": True,
            "state": state,
        }

    async def login(self, state):
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self._callback,
            "scope": self.scope,
            "show_dialog": True,
            "state": state
        }
        return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    async def callback(self, code=None):
        if not code : 
            return JSONResponse({"error": "code is None"})

        auth_header = base64.b64encode(f"{self.client_id}:{self._secret}".encode()).decode()
        headers = {"Authorization": f"Basic {auth_header}"}
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self._callback,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(TOKEN_URL, data=data, headers=headers)
            if resp.status_code == 200 :
                token_data = resp.json()
            else : 
                return JSONResponse({"code": resp.status_code})

        if "access_token" in token_data:
            self.access_token = token_data["access_token"]
            self.refresh_token = token_data.get("refresh_token")

            return JSONResponse({
                "message": "Spotify credentials saved!",
            })
        else:
            return JSONResponse({"error": token_data})
