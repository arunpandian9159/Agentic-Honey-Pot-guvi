# Google Cloud Run Deployment Guide

Deploy the AI Honeypot to Google Cloud Run — a fully managed, serverless container platform.

## Why Cloud Run?

- **Free tier**: 2M requests/month, 360,000 GB-seconds of compute free
- **Pay-per-use**: Scales to zero when idle (no cost when not in use)
- **Docker-native**: Uses our optimized Dockerfile directly
- **Auto-scaling**: Handles traffic spikes automatically
- **HTTPS by default**: Free SSL/TLS certificates
- **Perfect for free trial**: Stays well within $300 free credit

## Prerequisites

1. **Google Cloud account** with free trial activated
2. **Google Cloud SDK (gcloud CLI)** installed locally
3. **Docker** installed (optional — Cloud Build can build for you)
4. **Environment variables** ready (see `.env.example`)

### Install gcloud CLI

```bash
# Windows (PowerShell)
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:TEMP\GoogleCloudSDKInstaller.exe")
& "$env:TEMP\GoogleCloudSDKInstaller.exe"

# macOS
brew install google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash
```

After installation:
```bash
gcloud init
gcloud auth login
```

---

## Deployment Steps

### Step 1: Create a Google Cloud Project

```bash
# Create a new project (or use existing)
gcloud projects create ai-honeypot-project --name="AI Honeypot"

# Set it as active project
gcloud config set project ai-honeypot-project

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

### Step 2: Set Your Region

```bash
# Use a region close to you (asia-south1 for India)
gcloud config set run/region asia-south1
```

Available regions: `us-central1`, `us-east1`, `europe-west1`, `asia-south1`, `asia-southeast1`, etc.

### Step 3: Deploy with a Single Command

This is the easiest method — Cloud Build builds the Docker image and deploys it:

```bash
gcloud run deploy ai-honeypot \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --min-instances 0 \
  --max-instances 3 \
  --set-env-vars "GROQ_API_KEY=your_groq_key_here" \
  --set-env-vars "API_SECRET_KEY=your_secret_key_min_32_chars" \
  --set-env-vars "GUVI_CALLBACK_URL=https://hackathon.guvi.in/api/updateHoneyPotFinalResult" \
  --set-env-vars "QDRANT_URL=https://your-cluster.qdrant.io" \
  --set-env-vars "QDRANT_API_KEY=your_qdrant_key" \
  --set-env-vars "ENVIRONMENT=production" \
  --set-env-vars "LOG_LEVEL=INFO" \
  --set-env-vars "DEBUG=false"
```

> **Note**: Replace the placeholder values with your actual API keys.

### Step 4: Get Your Service URL

After deployment completes, you'll see output like:
```
Service [ai-honeypot] revision [ai-honeypot-00001-abc] has been deployed
and is serving 100 percent of traffic.
Service URL: https://ai-honeypot-xxxxxxxxxx-el.a.run.app
```

Your API is now live at that URL!

---

## Alternative: Build and Deploy Separately

If you prefer more control:

### Build the Docker Image

```bash
# Option A: Build with Cloud Build (no local Docker needed)
gcloud builds submit --tag gcr.io/ai-honeypot-project/ai-honeypot

# Option B: Build locally and push
docker build -t gcr.io/ai-honeypot-project/ai-honeypot .
docker push gcr.io/ai-honeypot-project/ai-honeypot
```

### Deploy the Image

```bash
gcloud run deploy ai-honeypot \
  --image gcr.io/ai-honeypot-project/ai-honeypot \
  --region asia-south1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --min-instances 0 \
  --max-instances 3
```

### Set Environment Variables Separately

```bash
gcloud run services update ai-honeypot \
  --region asia-south1 \
  --set-env-vars "GROQ_API_KEY=your_key,API_SECRET_KEY=your_secret,QDRANT_URL=your_url,QDRANT_API_KEY=your_key"
```

---

## Using Secret Manager (Recommended for Production)

Instead of passing secrets as plain env vars, use Google Secret Manager:

```bash
# Enable Secret Manager API
gcloud services enable secretmanager.googleapis.com

# Create secrets
echo -n "your_groq_key" | gcloud secrets create GROQ_API_KEY --data-file=-
echo -n "your_secret_key" | gcloud secrets create API_SECRET_KEY --data-file=-
echo -n "your_qdrant_url" | gcloud secrets create QDRANT_URL --data-file=-
echo -n "your_qdrant_key" | gcloud secrets create QDRANT_API_KEY --data-file=-

# Deploy with secrets
gcloud run deploy ai-honeypot \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --set-secrets "GROQ_API_KEY=GROQ_API_KEY:latest" \
  --set-secrets "API_SECRET_KEY=API_SECRET_KEY:latest" \
  --set-secrets "QDRANT_URL=QDRANT_URL:latest" \
  --set-secrets "QDRANT_API_KEY=QDRANT_API_KEY:latest"
```

---

## Configuration Recommendations

### Memory & CPU

| Setting | Recommended | Why |
|---------|-------------|-----|
| Memory | 1Gi | fastembed model needs ~500MB |
| CPU | 1 | Sufficient for inference |
| Min instances | 0 | Scale to zero when idle (saves cost) |
| Max instances | 3 | Prevent runaway costs on free trial |
| Timeout | 300s | Allow time for first request (lazy RAG init) |
| Concurrency | 80 (default) | FastAPI handles concurrent requests well |

### Cost Estimation (Free Trial)

With the free tier + $300 credit:
- **Idle**: $0/month (scales to zero)
- **Light usage** (100 req/day): ~$0-2/month
- **Moderate usage** (1000 req/day): ~$5-15/month
- **Free tier covers**: First 2M requests/month

---

## Verify Deployment

### Test the API

```bash
# Replace with your actual Cloud Run URL
export SERVICE_URL="https://ai-honeypot-xxxxxxxxxx-el.a.run.app"

# Health check - visit the dashboard
curl $SERVICE_URL

# Test the chat API
curl -X POST "$SERVICE_URL/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, your account has been compromised!", "session_id": "test-123"}'
```

### Check Logs

```bash
# Stream logs in real-time
gcloud run services logs read ai-honeypot --region asia-south1 --limit 50

# Or use Cloud Console
# https://console.cloud.google.com/run/detail/asia-south1/ai-honeypot/logs
```

### Monitor Performance

```bash
# View service details
gcloud run services describe ai-honeypot --region asia-south1

# View revisions
gcloud run revisions list --service ai-honeypot --region asia-south1
```

---

## Update Deployment

When you make code changes:

```bash
# Redeploy (rebuilds and deploys)
gcloud run deploy ai-honeypot --source . --region asia-south1
```

Cloud Build uses Docker layer caching, so subsequent deploys are much faster since only changed layers are rebuilt.

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "Container failed to start" | Check logs: `gcloud run services logs read ai-honeypot` |
| "Memory limit exceeded" | Increase to `--memory 2Gi` |
| "Request timeout" | Increase `--timeout 600` for first request |
| "Permission denied" | Run `gcloud auth login` and check project |
| "Port mismatch" | Ensure Dockerfile uses `$PORT` env var |
| "Cold start slow" | Set `--min-instances 1` (costs more but no cold start) |

### First Request is Slow

The first request triggers lazy RAG initialization. This is expected:
- First request: 5-15 seconds (RAG + Qdrant connection)
- Subsequent requests: <1 second

To eliminate cold starts (costs more):
```bash
gcloud run services update ai-honeypot \
  --region asia-south1 \
  --min-instances 1
```

---

## Cleanup

To avoid charges after testing:

```bash
# Delete the Cloud Run service
gcloud run services delete ai-honeypot --region asia-south1

# Delete the container image
gcloud container images delete gcr.io/ai-honeypot-project/ai-honeypot

# Or delete the entire project
gcloud projects delete ai-honeypot-project
```

---

## Quick Reference

```bash
# One-command deploy
gcloud run deploy ai-honeypot --source . --region asia-south1 --allow-unauthenticated --memory 1Gi

# View logs
gcloud run services logs read ai-honeypot --region asia-south1

# Update env vars
gcloud run services update ai-honeypot --set-env-vars "KEY=value"

# Delete service
gcloud run services delete ai-honeypot --region asia-south1
```
