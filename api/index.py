import json
import os
import re
import time
from bs4 import BeautifulSoup
from curl_cffi import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class InstagramToolkit:
    def __init__(self, use_proxy=False, proxy_url="https://redribbon.pythonanywhere.com/instagram"):
        self.session = requests.Session(impersonate="chrome")
        self.use_proxy = use_proxy
        self.proxy_url = proxy_url

        # CommentPicker auth details
        self.cp_cookies = {"fontsLoaded": "true", "PHPSESSID": "06q0gfb9qbt3vg5s1s5hfmculj", "ezoab_186623": "mod1",
                           "ezoadgid_186623": "-1"}
        self.cp_headers = {"accept": "*/*", "referer": "https://commentpicker.com/instagram-username.php"}

    def get_info_from_username(self, username):
        try:
            # 1. Proxy vs Direct Routing
            if self.use_proxy:
                resp = self.session.get(self.proxy_url, params={"username": username}, timeout=10, allow_redirects=True)
            else:
                resp = self.session.get(f"https://www.instagram.com/{username}/", timeout=10, allow_redirects=True)

            if resp.status_code not in [200, 301, 302]:
                return {"error": f"Request Blocked (HTTP {resp.status_code})", "status_code": resp.status_code}

            user_data = {}

            # 2. Try JSON Parsing first (Fastest/Cleanest)
            scripts = re.findall(r'<script type="application/json"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
            for script in scripts:
                if "xig_user_by_username" in script:
                    try:
                        extracted = self._find_key(json.loads(script), "xig_user_by_username")
                        if extracted:
                            user_data = {
                                "id": extracted.get("id") or extracted.get("pk"),
                                "pk": extracted.get("id") or extracted.get("pk"),
                                "username": extracted.get("username"),
                                "full_name": extracted.get("full_name", ""),
                                "biography": extracted.get("biography", ""),
                                "profile_pic_url": extracted.get("profile_pic_url_hd") or extracted.get(
                                    "profile_pic_url"),
                                "is_verified": extracted.get("is_verified", False),
                                "is_private": extracted.get("is_private", False),
                                "follower_count": extracted.get("follower_count"),
                                "following_count": extracted.get("following_count")
                            }
                            break
                    except Exception:
                        continue

            # 3. Fallback to BeautifulSoup if JSON is missing or stripped of follower counts
            if not user_data or user_data.get("follower_count") is None:
                soup = BeautifulSoup(resp.text, 'html.parser')

                # Initialize empty structure if JSON failed completely
                if not user_data:
                    user_data = {"username": username, "follower_count": None, "following_count": None, "full_name": "",
                                 "biography": "", "profile_pic_url": None, "is_verified": False, "is_private": False,
                                 "id": None, "pk": None}

                # Basic DOM Extractions
                img = soup.find('img', alt=re.compile(r'profile picture', re.I))
                if img and not user_data.get("profile_pic_url"):
                    user_data["profile_pic_url"] = img.get('src', '').replace("&amp;", "&")

                if soup.find('svg', {'aria-label': 'Verified'}):
                    user_data["is_verified"] = True

                h2 = soup.find('h2')
                if h2 and not user_data.get("full_name"):
                    user_data["full_name"] = h2.get_text(strip=True)

                id_match = re.search(r'"profile_id":"(\d+)"', resp.text) or re.search(r'"id":"(\d+)"', resp.text)
                if id_match and not user_data.get("id"):
                    user_data["id"] = user_data["pk"] = id_match.group(1)

                # Followers, Following, & Bio
                for a in soup.find_all('a'):
                    txt = a.get_text(strip=True).lower()
                    if 'followers' in txt:
                        title_span = a.find('span', title=True)
                        user_data["follower_count"] = int(
                            title_span['title'].replace(',', '')) if title_span else self._parse_num(
                            txt.replace('followers', ''))
                    elif 'following' in txt:
                        user_data["following_count"] = self._parse_num(txt.replace('following', ''))

                for span in soup.find_all('span', dir="auto"):
                    txt = span.get_text(strip=True)
                    if txt and txt != user_data.get(
                            "full_name") and txt.lower() != username.lower() and "followers" not in txt.lower() and "following" not in txt.lower():
                        if not user_data.get("biography"):
                            user_data["biography"] = txt
                            break

            # 4. Final Validation
            if user_data.get("id") or user_data.get("profile_pic_url"):
                return user_data

            return {"error": "User not found or Instagram blocked the IP.", "status_code": resp.status_code}

        except Exception as e:
            return {"error": str(e), "status_code": 500}

    def get_info_from_id(self, user_id):
        try:
            token_url = "https://commentpicker.com/actions/token.php?id=2026"
            token_resp = self.session.get(token_url, headers=self.cp_headers, cookies=self.cp_cookies, timeout=10)

            # Inline token decoding
            decoded_token = token_resp.text.strip().replace('I', '1').replace('A', '4').replace('B', '8')

            action_url = f"https://commentpicker.com/actions/instagram-username-action.php?userid={user_id}&token={decoded_token}"
            for _ in range(3):
                data_resp = self.session.get(action_url, headers=self.cp_headers, cookies=self.cp_cookies, timeout=10)
                if data_resp.text.startswith('{'):
                    data = data_resp.json()
                    return data if "cpStatus" not in data else {"error": "API Error. Session expired."}
                time.sleep(1.5)

            return {"error": "Failed to bypass CommentPicker challenge.", "status_code": data_resp.status_code}
        except Exception as e:
            return {"error": str(e), "status_code": 500}

    @staticmethod
    def _find_key(obj, key):
        """Tiny recursive JSON dictionary searcher."""
        if isinstance(obj, dict):
            if key in obj: return obj[key]
            for v in obj.values():
                res = InstagramToolkit._find_key(v, key)
                if res: return res
        elif isinstance(obj, list):
            for item in obj:
                res = InstagramToolkit._find_key(item, key)
                if res: return res
        return None

    @staticmethod
    def _parse_num(s):
        """Converts strings like '1.5M' or '10K' to integer counts."""
        s = re.sub(r'[^\d\.MK]', '', s.upper())
        if not s: return None
        try:
            if 'M' in s: return int(float(s.replace('M', '')) * 1000000)
            if 'K' in s: return int(float(s.replace('K', '')) * 1000)
            return int(s)
        except Exception:
            return None


# Init Toolkit (use_proxy=True uses pythonanywhere, False goes direct)
toolkit = InstagramToolkit(use_proxy=True)


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
if os.path.exists("public"):
    app.mount("/public", StaticFiles(directory="public"), name="public")


    @app.get("/")
    async def serve_frontend():
        return FileResponse("public/index.html")
