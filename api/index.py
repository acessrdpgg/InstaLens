from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from curl_cffi import requests
import json
import re
import time

app = FastAPI()

# Allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- PASTE YOUR EXACT InstagramToolkit CLASS HERE ---
class InstagramToolkit:
    def __init__(self):
        self.session = requests.Session(impersonate="chrome")
        self.cp_cookies = {"fontsLoaded": "true", "PHPSESSID": "06q0gfb9qbt3vg5s1s5hfmculj", "ezoab_186623": "mod1",
                           "ezoadgid_186623": "-1"}
        self.cp_headers = {"accept": "*/*", "referer": "https://commentpicker.com/instagram-username.php"}

    @staticmethod
    def _find_target_in_json(obj, target_key="xig_user_by_username"):
        if isinstance(obj, dict):
            if target_key in obj: return obj[target_key]
            for value in obj.values():
                res = InstagramToolkit._find_target_in_json(value, target_key)
                if res: return res
        elif isinstance(obj, list):
            for item in obj:
                res = InstagramToolkit._find_target_in_json(item, target_key)
                if res: return res
        return None

    @staticmethod
    def _decode_token(token):
        return token.replace('I', '1').replace('A', '4').replace('B', '8')

    def get_info_from_username(self, username):
        global resp
        try:
            url = f"https://www.instagram.com/{username}/"
            resp = self.session.get(url, timeout=10, allow_redirects=True)

            print("STATUS:", resp.status_code)
            print("URL:", resp.url)
            print("CONTENT TYPE:", resp.headers.get("content-type"))
            print("LENGTH:", len(resp.text))
            print("FIRST 500:", resp.text[:500])

            # if "Login" in resp.text: return {"error": "Instagram blocked the request (Login wall)."}
            scripts = re.findall(r'<script type="application/json"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
            for script in scripts:
                if "xig_user_by_username" in script:
                    try:
                        return self._find_target_in_json(json.loads(script))
                    except:
                        continue
            return {"error": "User not found. / Request Blocked by Instagram.", "status_code": resp.status_code}
        except Exception as e:
            return {"error": str(e), "status_code": resp.status_code}

    def get_info_from_id(self, user_id):
        global data_resp
        try:
            token_url = "https://commentpicker.com/actions/token.php?id=2026"
            token_resp = self.session.get(token_url, headers=self.cp_headers, cookies=self.cp_cookies, timeout=10, allow_redirects=True)

            print("STATUS:", resp.status_code)
            print("URL:", resp.url)
            print("CONTENT TYPE:", resp.headers.get("content-type"))
            print("LENGTH:", len(resp.text))
            print("FIRST 500:", resp.text[:500])

            decoded_token = self._decode_token(token_resp.text.strip())

            action_url = f"https://commentpicker.com/actions/instagram-username-action.php?userid={user_id}&token={decoded_token}"
            for _ in range(3):
                data_resp = self.session.get(action_url, headers=self.cp_headers, cookies=self.cp_cookies, allow_redirects=True)

                print("STATUS:", resp.status_code)
                print("URL:", resp.url)
                print("CONTENT TYPE:", resp.headers.get("content-type"))
                print("LENGTH:", len(resp.text))
                print("FIRST 500:", resp.text[:500])

                if data_resp.text.startswith('{'):
                    data = data_resp.json()
                    return data if "cpStatus" not in data else {"error": "API Error. Session might be expired."}
                time.sleep(1.5)
            return {"error": "Failed to bypass challenge.", "status_code": data_resp.status_code}
        except Exception as e:
            return {"error": str(e), "status_code": resp.status_code}


toolkit = InstagramToolkit()


# --- API ENDPOINTS ---
@app.get("/api/username-to-id")
def get_id(username: str):
    data = toolkit.get_info_from_username(username.replace("@", ""))
    if data and "error" not in data:
        return {"success": True, "data": data}
    raise HTTPException(status_code=data.get("status_code", 400), detail=data.get("error", "Failed to fetch user."))


@app.get("/api/id-to-username")
def get_user(user_id: str):
    data = toolkit.get_info_from_id(user_id)
    if data and "error" not in data:
        return {"success": True, "data": data}
    raise HTTPException(status_code=data.get("status_code", 400), detail=data.get("error", "Failed to fetch user."))


# --- LOCAL TESTING SETUP ---
# This tells FastAPI to serve the HTML file when running locally.
# Vercel will ignore this in production thanks to vercel.json.
if os.path.exists("public"):
    app.mount("/public", StaticFiles(directory="public"), name="public")


    @app.get("/")
    async def serve_frontend():
        return FileResponse("public/index.html")
