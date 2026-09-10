# InterviewIQ — Production Deployment Guide

This guide details how to deploy **InterviewIQ** to production.

---

## Architecture Overview

```text
[ React Frontend ] (Vercel / Netlify / CDN)
        │
        ▼ HTTPS REST calls
[ FastAPI Backend ] (Render / Railway / AWS EC2 / Docker)
        │
        ├──────────► [ MongoDB Atlas Cloud ] (Database)
        ├──────────► [ Groq Cloud LPU ] (LLM Inference)
        └──────────► [ LangSmith ] (Tracing & Observability)
```

---

## Option 1: Managed Cloud (Recommended — Free & Easiest)

This setup requires zero server maintenance and deploys automatically on every `git push`.

### Step 1: Deploy Backend to Render or Railway

#### On Render (https://render.com):
1. Sign up / log in to Render and click **New +** → **Web Service**.
2. Connect your GitHub repository: `AI_Driven_InterViewPlatfrom`.
3. Configure settings:
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. In **Environment Variables**, add:
   - `GROQ_API_KEY`: `your_groq_api_key`
   - `GROQ_MODEL`: `openai/gpt-oss-20b`
   - `MONGODB_URI`: `your_mongodb_atlas_connection_string`
   - `MONGODB_DB_NAME`: `shubhamanand70497049_db_user`
   - `ALLOWED_ORIGINS`: `*` (or your frontend Vercel URL once created)
   - `LANGCHAIN_TRACING_V2`: `true`
   - `LANGCHAIN_API_KEY`: `your_langsmith_key`
   - `LANGCHAIN_PROJECT`: `InterviewIQ`
5. Click **Deploy Web Service**.
6. Copy your live backend URL (e.g. `https://interviewiq-api.onrender.com`).

---

### Step 2: Deploy Frontend to Vercel

#### On Vercel (https://vercel.com):
1. Log in to Vercel and click **Add New...** → **Project**.
2. Import your GitHub repository.
3. Configure project settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click *Edit* and select `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. In **Environment Variables**, add:
   - `VITE_API_BASE_URL`: Paste your Render backend URL (e.g. `https://interviewiq-api.onrender.com` without a trailing slash).
5. Click **Deploy**.
6. Vercel will build and launch your live frontend (e.g. `https://interviewiq.vercel.app`).

> [!TIP]
> The included [`frontend/vercel.json`](file:///d:/development/AI_Driven_InterViewPlatfrom/frontend/vercel.json) automatically handles React Router client-side rewrites so refreshing `/interview/:id` or `/report/:id` will never throw a 404 error.

---

### Step 3: Connect Frontend URL to Backend CORS

In your Render dashboard:
1. Go to your backend service's **Environment** tab.
2. Update `ALLOWED_ORIGINS` to include your live Vercel URL (e.g. `https://interviewiq.vercel.app`).
3. Save changes.

---

## Option 2: Docker / Containerized Deployment (Any VPS / AWS EC2)

You can run the entire platform with Docker on any Linux VPS (Ubuntu, Debian, AWS EC2, DigitalOcean):

### 1. Prerequisites
- Docker & Docker Compose installed:
  ```bash
  sudo apt update && sudo apt install -y docker.io docker-compose-v2
  ```

### 2. Configure Environment
Ensure [`backend/.env`](file:///d:/development/AI_Driven_InterViewPlatfrom/backend/.env) is populated with your live credentials.

### 3. Build & Run
From the project root directory:
```bash
docker compose up --build -d
```

### 4. Verify Containers
```bash
docker compose ps
docker compose logs -f
```
- Frontend will be accessible at: `http://<your-server-ip>:5173`
- Backend API will be accessible at: `http://<your-server-ip>:8000/docs`

---

## Option 3: AWS Deployment (EC2 with Nginx Reverse Proxy & SSL)

If deploying to an Ubuntu EC2 instance:
1. Clone your repository:
   ```bash
   git clone https://github.com/your-username/AI_Driven_InterViewPlatfrom.git
   cd AI_Driven_InterViewPlatfrom
   ```
2. Build frontend:
   ```bash
   cd frontend && npm install && npm run build && cd ..
   ```
3. Set up Python virtual environment and Systemd service for backend:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
4. Create a systemd service `/etc/systemd/system/interviewiq.service`:
   ```ini
   [Unit]
   Description=InterviewIQ FastAPI Backend
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/AI_Driven_InterViewPlatfrom/backend
   EnvironmentFile=/home/ubuntu/AI_Driven_InterViewPlatfrom/backend/.env
   ExecStart=/home/ubuntu/AI_Driven_InterViewPlatfrom/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
5. Enable and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now interviewiq
   ```
6. Configure Nginx to serve `frontend/dist` on port 80 and proxy `/api` requests to `http://127.0.0.1:8000`.

---

## Summary of Environment Variables

### Backend (`backend/.env`)
| Variable | Description | Example |
| :--- | :--- | :--- |
| `GROQ_API_KEY` | Groq Cloud LPU key | `gsk_...` |
| `GROQ_MODEL` | Model ID | `openai/gpt-oss-20b` |
| `MONGODB_URI` | MongoDB connection string | `mongodb+srv://...` |
| `MONGODB_DB_NAME` | Database name | `interviewiq_db` |
| `ALLOWED_ORIGINS` | Comma-separated allowed frontend domains | `https://interviewiq.vercel.app,http://localhost:5173` |
| `LANGCHAIN_TRACING_V2` | Enable LangSmith | `true` |
| `LANGCHAIN_API_KEY` | LangSmith API Key | `lsv2_pt_...` |
| `LANGCHAIN_PROJECT` | LangSmith Project name | `InterviewIQ` |

### Frontend (`frontend/.env`)
| Variable | Description | Example |
| :--- | :--- | :--- |
| `VITE_API_BASE_URL` | Live backend API URL | `https://interviewiq-api.onrender.com` |
