# 📸 InstaLens - Advanced Instagram ID Converter

[![Vercel Deploy](https://img.shields.io/badge/Vercel-Deployed-success?style=for-the-badge&logo=vercel)](https://your-vercel-link-here.vercel.app/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)

InstaLens is a sleek, serverless OSINT web application that instantly converts Instagram Usernames to their permanent numeric User IDs, and vice versa. It bypasses basic bot protections to fetch rich profile data, wrapped in a premium, fully responsive Dark Mode UI.

### 🌐 Live Demo: [InstaLens Web App](https://your-vercel-link-here.vercel.app/) *(Add your Vercel link here once deployed)*
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Facessrdpgg%2FInstaLens)

---

## ✨ Features

- **🔄 Two-Way Conversion:** Seamlessly swap between Username ➡️ ID and ID ➡️ Username.
- **⚡ Request Chaining:** When searching by ID, the backend intelligently extracts the username and chains a secondary request to pull full profile statistics.
- **🛡️ Bot Bypass Engine:** Utilizes `cloudscraper` to bypass basic JavaScript/Cloudflare challenges seamlessly.
- **📱 Responsive Glassmorphism UI:** Built with Tailwind CSS, ensuring a pixel-perfect, native-feeling experience on desktop, iOS, and Android.
- **💾 State Preservation:** Switch between tabs without losing your previous search data.
- **📋 Smart Clipboard:** One-click copy functionality for IDs and Profile Picture URLs.

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI, Cloudscraper, Uvicorn
- **Frontend:** HTML5, Vanilla JavaScript, Tailwind CSS
- **Deployment:** Vercel (Serverless Functions)

---

## 🚀 Local Development Setup

Want to run or modify InstaLens on your local machine? Follow these steps:

### 1. Clone the Repository
```bash
git clone https://github.com/acessrdpgg/InstaLens.git
cd InstaLens
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Local Server
```bash
uvicorn api.index:app --reload
```
Once running, open your browser and navigate to `http://127.0.0.1:8000`.

---

## 📡 API Endpoints

InstaLens also functions as a REST API. You can hit these endpoints directly if running locally or via your Vercel deployment URL.

### Get ID from Username
```http
GET /api/username-to-id?username=instagram
```
**Response:**
```json
{
  "success": true,
  "data": {
    "pk": "25025320",
    "username": "instagram",
    "full_name": "Instagram",
    "follower_count": 668000000,
    ...
  }
}
```

### Get Username from ID
```http
GET /api/id-to-username?user_id=25025320
```

---

## ☁️ Deployment (Vercel)

This project is pre-configured for **Vercel Serverless Functions** via the `vercel.json` file.

1. Push your code to GitHub.
2. Log into [Vercel](https://vercel.com/) and click **Import Project**.
3. Select this repository.
4. Leave the "Framework Preset" as **Other**.
5. Click **Deploy**.

Vercel will automatically route `/api/*` requests to the Python FastAPI backend and serve `public/index.html` on the root domain!

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
**Developed with ❤️ by [acessrdpgg](https://github.com/acessrdpgg)**