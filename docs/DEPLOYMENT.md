# InsightIQ Deployment Guide

This guide explains how to deploy InsightIQ to free-tier infrastructure.

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Cloudflare     │     │  Render         │     │  Neon           │
│  Pages          │◄───►│  Web Service    │◄───►│  PostgreSQL     │
│  (Frontend)     │     │  (Backend)      │     │  (Database)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Cloudflare R2  │
                       │  (File Storage) │
                       └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  NVIDIA NIM API │
                       │  (AI/Analytics) │
                       └─────────────────┘
```

## Prerequisites

### Required Accounts

1. **GitHub** - Source code repository
2. **Cloudflare** - Pages (frontend) + R2 (file storage)
3. **Render** - Web service (backend)
4. **Neon** - PostgreSQL database
5. **NVIDIA Developer Program** - NIM API access

### Local Development Requirements

- Python 3.11+
- Node.js 20+
- Docker (optional, for local PostgreSQL)

---

## Step 1: Set Up Neon PostgreSQL Database

1. Create a Neon account at https://neon.tech
2. Create a new project named `insightiq`
3. Create a database named `insightiq`
4. Note the connection string (format: `postgresql://user:pass@host/dbname?sslmode=require`)

**Required Environment Variable:**
```
DATABASE_URL=postgresql://user:password@ep-xxx.us-east-1.aws.neon.tech/insightiq?sslmode=require
```

---

## Step 2: Set Up Cloudflare R2 Storage

1. Enable R2 in Cloudflare dashboard
2. Create a bucket named `insightiq-datasets`
3. Create an API token with R2 read/write permissions
4. Note the Account ID, Access Key ID, and Secret Access Key

**Optional (for public file access):**
- Set up a custom domain for R2 public access
- Configure CORS for the bucket

**Required Environment Variables:**
```
R2_ACCOUNT_ID=your-account-id
R2_ACCESS_KEY_ID=your-access-key
R2_SECRET_ACCESS_KEY=your-secret-key
R2_BUCKET_NAME=insightiq-datasets
R2_PUBLIC_URL=https://pub-xxx.r2.dev  # Optional, for public URLs
```

---

## Step 3: Set Up NVIDIA NIM API

1. Join NVIDIA Developer Program at https://developer.nvidia.com
2. Request access to NIM APIs
3. Create an API key at https://integrate.api.nvidia.com
4. Select model: `meta/llama-3.1-70b-instruct` (or your preferred model)

**Required Environment Variables:**
```
LLM_PROVIDER=nvidia-nim
LLM_API_KEY=your-nvidia-api-key
LLM_BASE_URL=https://integrate.api.nvidia.com/v1
LLM_MODEL=meta/llama-3.1-70b-instruct
```

---

## Step 4: Deploy Backend to Render

### Option A: Using render.yaml (Recommended)

1. Push your code to GitHub
2. In Render dashboard, click "New +" → "Blueprint"
3. Connect your GitHub repository
4. Render will detect `render.yaml` and configure the service

### Option B: Manual Setup

1. Create a new Web Service in Render
2. Connect your GitHub repository
3. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app.main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120`
   - **Environment**: Python 3.11

### Required Environment Variables (Backend)

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | JWT signing secret (generate with `openssl rand -hex 32`) | Yes |
| `DATABASE_URL` | Neon PostgreSQL connection string | Yes |
| `LLM_API_KEY` | NVIDIA NIM API key | Yes |
| `R2_ACCOUNT_ID` | Cloudflare R2 account ID | Yes |
| `R2_ACCESS_KEY_ID` | R2 access key | Yes |
| `R2_SECRET_ACCESS_KEY` | R2 secret key | Yes |
| `CORS_ORIGINS` | Frontend URL(s), e.g., `https://insightiq.pages.dev` | Yes |
| `DEBUG` | Set to `false` in production | No (default: false) |

---

## Step 5: Deploy Frontend to Cloudflare Pages

### Option A: Using Cloudflare Dashboard

1. Go to Cloudflare Pages
2. Click "Create a project" → "Connect to Git"
3. Select your GitHub repository
4. Configure:
   - **Build command**: `npm run build`
   - **Build output directory**: `dist`
   - **Root directory**: `frontend`

### Option B: Using Wrangler CLI

```bash
cd frontend
npm run build
npx wrangler pages deploy dist --project-name=insightiq-frontend
```

### Required Environment Variables (Frontend)

| Variable | Description | Required |
|----------|-------------|----------|
| `VITE_API_BASE_URL` | Backend API URL, e.g., `https://insightiq-backend.onrender.com/api` | Yes |

---

## Step 6: Configure CORS and Security

### Backend CORS Configuration

Update `CORS_ORIGINS` in backend environment:
```
CORS_ORIGINS=https://insightiq.pages.dev,https://*.insightiq.pages.dev
```

### Frontend API URL

Set in Cloudflare Pages environment variables:
```
VITE_API_BASE_URL=https://insightiq-backend.onrender.com/api
```

---

## Step 7: Database Migrations

Run migrations after deploying the backend:

```bash
# On Render, use the shell tab:
cd backend
alembic upgrade head
```

Or run locally with production DATABASE_URL:
```bash
DATABASE_URL=postgresql://... alembic upgrade head
```

---

## Step 8: Verify Deployment

1. **Backend Health Check**: `https://insightiq-backend.onrender.com/health`
2. **Backend Readiness**: `https://insightiq-backend.onrender.com/ready`
3. **Frontend**: `https://insightiq.pages.dev`
4. **API Docs** (if DEBUG=true): `https://insightiq-backend.onrender.com/docs`

---

## Free Tier Limits & Optimization

| Service | Free Tier Limits | Optimization |
|---------|------------------|--------------|
| Render | 512 MB RAM, sleeps after 15 min inactivity | Single worker, connection pooling |
| Neon | 0.5 GB storage, 3 GB compute hrs/month | Connection pooling, query optimization |
| Cloudflare Pages | Unlimited bandwidth, 500 builds/month | Static generation |
| Cloudflare R2 | 10 GB storage, 1M Class A ops/month | Lifecycle rules for old files |
| NVIDIA NIM | Rate limited by API tier | Request caching, rate limiting |

### Application-Level Limits (Configured)

- Max file upload: 100 MB
- Max dataset rows: 100,000
- Max concurrent analytics: 3
- NVIDIA rate limit: 60 requests/minute
- File retention: 7 days (configurable)

---

## Troubleshooting

### Render Cold Starts
- First request after 15 min inactivity takes 10-30 seconds
- Solution: Use health check endpoint to keep warm, or accept delay

### Database Connection Failures
- Check `DATABASE_URL` format
- Ensure Neon allows connections from Render IPs
- Verify SSL mode: `?sslmode=require`

### CORS Errors
- Verify `CORS_ORIGINS` includes exact frontend URL
- Check for trailing slashes
- Ensure credentials are allowed

### NVIDIA API Failures
- Check API key validity
- Monitor rate limits (60 req/min default)
- Handle 429 responses gracefully

### File Upload Errors
- Check R2 credentials
- Verify bucket exists and permissions
- Check file size limits (100 MB default)

---

## Monitoring & Maintenance

### Health Checks
- `/health` - Basic liveness
- `/ready` - Readiness with DB check

### Logs
- Render: View logs in dashboard
- Structured JSON logging enabled

### Cleanup
- Automatic hourly cleanup of old files
- Manual: `cleanup_service.run_all_cleanups()`

---

## Rollback Procedure

1. **Backend**: Render supports rollback via dashboard
2. **Frontend**: Cloudflare Pages keeps deployment history
2. **Database**: Use Alembic downgrade: `alembic downgrade -1`

---

## Cost Monitoring

Set up budget alerts:
- Render: Free tier monitoring
- Neon: Storage and compute alerts
- Cloudflare: R2 usage alerts
- NVIDIA: API usage monitoring