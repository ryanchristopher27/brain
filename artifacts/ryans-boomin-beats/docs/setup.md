# Setup Guide — Ryan's Boomin' Beats

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Conda | Any | Miniconda or Anaconda |
| Node.js | 18+ | Confirmed working on v18.17.1 |
| npm | 9+ | Bundled with Node |
| Spotify Developer Account | — | [Create one here](https://developer.spotify.com/dashboard) |

---

## 1. Clone the Repo

```bash
git clone <repo-url>
cd ryans-boomin-beats
```

---

## 2. Python Environment

Create and activate the conda environment from the project root:

```bash
conda env create -f environment.yml
conda activate ryans-boomin-beats
```

To update the environment after dependency changes:

```bash
conda env update -f environment.yml --prune
```

---

## 3. Spotify Developer Setup

The app requires a Spotify app registered in the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).

1. Create a new app in the dashboard
2. Add `http://127.0.0.1:5173/profile` as a Redirect URI (`localhost` is blocked by Spotify — must use the IP literal)
3. Copy your **Client ID** and **Client Secret**
4. Copy the env template and fill in your credentials:

```bash
cp src/web/backend/.env.example src/web/backend/.env
```

Then open `src/web/backend/.env` and set:

```
SPOTIFY_CLIENT_ID=your-client-id
SPOTIFY_CLIENT_SECRET=your-client-secret
```

---

## 4. Run the Backend

The backend is a FastAPI app served by Uvicorn.

```bash
cd src/web/backend
uvicorn main:app --reload --port 8005
```

API docs are available at [http://127.0.0.1:8005/docs](http://127.0.0.1:8005/docs) once running.

---

## 5. Run the Frontend

In a separate terminal:

```bash
cd src/web/frontend
npm install
npm run dev
```

The app will be available at [http://localhost:5173](http://localhost:5173).

---

## 6. First Run

1. Open the app at [http://localhost:5173](http://localhost:5173)
2. Navigate to **Profile** and click **Login with Spotify** to authenticate
3. Grant the requested permissions — you'll be redirected back to the app

---

## 7. Last.fm API Key Setup

The Explore page uses Last.fm to pull song tags and metadata.

1. Create a free account at [last.fm](https://www.last.fm)
2. Register an API application at [last.fm/api/account/create](https://www.last.fm/api/account/create)
3. Copy your **API Key**
4. Add it to `src/web/backend/.env`:

```
LASTFM_API_KEY=your-api-key
```

The app works without this key — the LLM analysis will still run, but tag data won't be available.

---

## 8. AI Playlist Builder Setup

The playlist builder requires your own API key from Claude or OpenAI.

1. Navigate to **Playlist Builder**
2. Click the **⚙ gear icon** in the top-right header
3. Select your provider (Claude or OpenAI)
4. Paste your API key and click **Connect**

The key is validated immediately and stored for the session. It is not persisted after the browser tab closes.

**Getting an API key:**
- Claude: [console.anthropic.com](https://console.anthropic.com)
- OpenAI: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

---

## Project Structure

```
ryans-boomin-beats/
├── environment.yml                  # Conda environment
├── docs/                            # Design and setup docs
│   ├── setup.md                     # This file
│   ├── brainstorm.md
│   └── plan.md
└── src/web/
    ├── backend/                     # FastAPI backend
    │   ├── main.py                  # App entry point
    │   ├── config.py                # Spotify credentials + shared constants
    │   ├── requirements.txt         # Python dependencies
    │   ├── routers/                 # One file per feature area
    │   └── services/                # LLM client, Spotify validator
    └── frontend/                    # SvelteKit frontend
        └── src/
            ├── routes/              # Pages (Home, Profile, Playlist Builder)
            └── lib/components/      # Shared UI components
```

---

## Common Issues

**"Spotipy cache error" on backend start**
Spotipy writes a `.cache` file during the OAuth flow. If it's corrupted, delete `src/web/backend/.cache` and re-authenticate.

**"No active device" when queuing songs**
Open Spotify on any device (desktop app, mobile, browser) and start playing something. Then retry the queue action.

**Frontend can't reach backend**
Make sure the backend is running on port 8005 before starting the frontend. Both servers must be running simultaneously.

**Conda env not found**
Run `conda env create -f environment.yml` from the project root (where `environment.yml` lives), not from inside `src/`.
