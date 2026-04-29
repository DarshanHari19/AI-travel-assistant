# 🚀 Quick Deployment Checklist

Follow these steps in order for fastest deployment:

## ☑️ Pre-Deployment (5 min)

- [ ] Commit and push all changes to GitHub
  ```bash
  git add .
  git commit -m "Prepare for production deployment"
  git push origin main
  ```

- [ ] Create accounts (if not already):
  - [ ] [Neon](https://neon.tech) (PostgreSQL)
  - [ ] [Upstash](https://upstash.com) (Redis)
  - [ ] [Railway](https://railway.app) (Backend)
  - [ ] [Vercel](https://vercel.com) (Frontend)

---

## 1️⃣ Database - Neon (5 min)

1. Login to [Neon Console](https://console.neon.tech)
2. Create new project: `travel-assistant`
3. Region: Choose closest (e.g., `US East Ohio`)
4. Copy connection string from dashboard
5. **Save**: `postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require`

✅ **Test**: Click "SQL Editor" in Neon, run `SELECT 1;`

---

## 2️⃣ Cache - Upstash Redis (5 min)

1. Login to [Upstash Console](https://console.upstash.com)
2. Create database: `travel-assistant-cache`
3. Type: `Regional`, Region: Same as Neon
4. Copy Redis URL
5. **Save**: `redis://default:token@xxx.upstash.io:6379`

✅ **Test**: Click "CLI" in dashboard, run `PING` → should return `PONG`

---

## 3️⃣ Backend - Railway (10 min)

### Deploy

1. Login to [Railway Dashboard](https://railway.app)
2. New Project → Deploy from GitHub
3. Select repository: `AIBuilderChallenge-InMarket-`
4. Wait for initial build (may fail - that's ok, we need env vars)

### Configure Environment Variables

In Railway project → **Variables** tab, add:

```bash
# Copy these from your local .env file:
OPENAI_API_KEY=sk-proj-...
OPENWEATHER_API_KEY=044a...
AERODATABOX_API_KEY=534007...
OPENAI_MODEL=gpt-4o

# Paste from Neon:
POSTGRES_URI=postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require
POSTGRES_POOL_SIZE=10
POSTGRES_MAX_OVERFLOW=20

# Paste from Upstash:
REDIS_URL=redis://default:token@xxx.upstash.io:6379

# Server config:
PORT=8000
HOST=0.0.0.0
LOG_LEVEL=INFO
ENABLE_CORS=true
ALLOWED_ORIGINS=http://localhost:3000
```

Click **"Redeploy"** after adding variables.

### Get Backend URL

1. Settings → Generate Domain
2. Copy URL: `https://your-app.railway.app`
3. **Save this** for Vercel configuration

✅ **Test**: 
```bash
curl https://your-app.railway.app/health
```
Should return: `{"status": "healthy", ...}`

---

## 4️⃣ Frontend - Vercel (10 min)

### Update Environment File

Edit `frontend/.env.production`:
```bash
VITE_API_URL=https://your-app.railway.app
```

### Deploy

**Option A - Dashboard:**
1. Login to [Vercel Dashboard](https://vercel.com)
2. Add New Project → Import from GitHub
3. Select repository
4. Configure:
   - Root Directory: `frontend`
   - Framework: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`
5. Add Environment Variable:
   - Name: `VITE_API_URL`
   - Value: `https://your-app.railway.app`
6. Deploy

**Option B - CLI (faster):**
```bash
npm install -g vercel
cd frontend
vercel --prod
```

### Get Frontend URL

After deploy: `https://your-app-xxx.vercel.app`

✅ **Test**: Visit URL in browser, try a chat message

---

## 5️⃣ Connect Frontend ↔ Backend (5 min)

### Update CORS in Railway

Go back to Railway → Variables → Update:
```bash
ALLOWED_ORIGINS=https://your-app-xxx.vercel.app,http://localhost:3000
```

Click **"Redeploy"**

✅ **Test Full Stack**:
1. Visit frontend URL
2. Send message: "What's the weather in London?"
3. Should get AI response with weather data

---

## 🎯 Final Verification

Test all features work in production:

- [ ] Weather queries: "What's the weather in Tokyo?"
- [ ] Multi-city: "Compare London and New York weather"
- [ ] Airport intelligence: "JFK terminal 4 to 5 transfer time?"
- [ ] Flight status: "Check flight AA100"
- [ ] Redis caching: Query same city twice (2nd should be faster)
- [ ] Conversation persistence: Refresh page, messages should persist

---

## 📝 Record Your URLs

**Save these for your resume:**

- Frontend: `https://_____________________.vercel.app`
- Backend: `https://_____________________.railway.app`
- GitHub: `https://github.com/___________________`

---

## 🎓 Resume Bullet Point Template

Copy this to your resume after deployment:

> **AI-Powered Travel Assistant** | [Live Demo](https://your-app.vercel.app) | [GitHub](https://github.com/your-repo)
> - Deployed production full-stack application using Vercel (React/Vite), Railway (FastAPI), Neon (PostgreSQL), and Upstash (Redis)
> - Implemented serverless architecture with auto-scaling database and cache layer
> - Achieved 70% API cost reduction through Redis caching strategy (30min weather TTL, 5min flight TTL)
> - Built RAG system with FAISS for airport-specific intelligence using OpenAI embeddings
> - Configured CI/CD pipeline with automatic deployments from GitHub
> - **Stack**: React, FastAPI, PostgreSQL, Redis, GPT-4o, LangGraph, Docker

---

## 🐛 Troubleshooting

### Railway build fails
- Check logs in Railway dashboard
- Verify all environment variables are set
- Ensure `railway.toml` and `Procfile` exist in root

### Frontend can't connect to backend
- Check `VITE_API_URL` in Vercel environment variables
- Verify CORS includes your Vercel URL
- Check browser console for errors

### Database errors
- Verify connection string includes `?sslmode=require`
- Check Neon dashboard - project should be "Active"
- Test connection: `psql "your-connection-string"`

### Redis not working
- Verify Redis URL format is correct
- Check Upstash dashboard - database should be "Active"
- Backend logs should show "Redis connected"

---

## ⏱️ Total Time: ~30-40 minutes

**You'll have:**
- ✅ Live application accessible worldwide
- ✅ Auto-deploys from GitHub
- ✅ Professional URLs for resume
- ✅ Production experience with modern cloud services
- ✅ Portfolio project that impresses recruiters

**Ready? Start with Step 1: Neon Database** 🚀
