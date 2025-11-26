# 🚀 Deploying Dr. HealBot to Render

This guide will help you deploy your medical chatbot application to Render.

## 📋 Prerequisites

1. A [Render account](https://render.com) (free tier available)
2. A [Groq API key](https://console.groq.com) for the AI chatbot
3. Your code pushed to a GitHub repository

## 🔧 Deployment Steps

### Option 1: Deploy via Render Dashboard (Recommended)

#### Step 1: Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit for Render deployment"
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

#### Step 2: Create Web Service on Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure the service:

   **Basic Settings:**
   - **Name**: `dr-healbot` (or your preferred name)
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Runtime**: `Docker`
   - **Instance Type**: `Free` (or paid for better performance)

   **Environment Variables:**
   Click **"Advanced"** and add:
   - Key: `GROQ_API_KEY`
   - Value: Your Groq API key

5. Click **"Create Web Service"**

#### Step 3: Wait for Deployment

Render will:
- Build your Docker image
- Install dependencies
- Download the Vosk model
- Deploy your application

This takes 5-10 minutes for the first deployment.

#### Step 4: Access Your App

Once deployed, you'll get a URL like:
```
https://dr-healbot.onrender.com
```

Your API will be available at:
- **Frontend**: `https://dr-healbot.onrender.com/`
- **API Docs**: `https://dr-healbot.onrender.com/docs`
- **Chat Endpoint**: `https://dr-healbot.onrender.com/chat`

---

### Option 2: Deploy via Render CLI

```bash
# Install Render CLI
npm install -g render-cli

# Login to Render
render login

# Deploy
render deploy
```

---

## 🔐 Environment Variables

Make sure to set these in Render Dashboard → Your Service → Environment:

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Your Groq API key for AI chat | ✅ Yes |

---

## 📁 File Structure

```
finalChatDoc/
├── backend.py              # FastAPI application
├── index.html              # Frontend interface
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker configuration
├── .dockerignore          # Files to exclude from Docker
├── .env.example           # Environment variables template
├── README_DEPLOY.md       # This file
├── data/                  # Created automatically
│   ├── chat_history/      # User chat histories
│   └── patient_data/      # Patient profiles
└── vosk-model-small-en-us-0.15/  # Downloaded during build
```

---

## 🧪 Testing Your Deployment

### Test the API:
```bash
# Health check
curl https://YOUR_APP.onrender.com/

# Test chat endpoint
curl -X POST https://YOUR_APP.onrender.com/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I have a headache",
    "user_id": "test_user_123",
    "language": "auto"
  }'
```

### Test the Frontend:
Open `https://YOUR_APP.onrender.com/` in your browser

---

## ⚠️ Important Notes

### Free Tier Limitations:
- **Spin down after 15 minutes of inactivity** (first request after spin down takes ~30 seconds)
- **750 hours/month** of runtime
- **Limited resources** (512 MB RAM)

### Upgrade for Production:
- **Starter Plan ($7/month)**: No spin down, more resources
- **Standard Plan ($25/month)**: Better performance, scaling

### Data Persistence:
- The `data/` folder stores chat history and patient data
- On free tier, this data is **ephemeral** (lost on redeploy)
- For persistent storage, upgrade to a paid plan or use external storage (S3, etc.)

---

## 🐛 Troubleshooting

### Build Fails:
- Check that all files are committed to GitHub
- Verify `requirements.txt` is present
- Check Render build logs for specific errors

### Application Crashes:
- Check `GROQ_API_KEY` is set correctly
- View logs in Render Dashboard → Your Service → Logs
- Ensure you're not exceeding free tier limits

### Slow Response:
- Free tier spins down after inactivity
- First request after spin down takes 30+ seconds
- Consider upgrading to paid plan

### Vosk Model Issues:
- Model downloads automatically during build
- If it fails, check Render build logs
- May need to increase build timeout

---

## 🔄 Updating Your App

```bash
# Make changes to your code
git add .
git commit -m "Update feature X"
git push origin main
```

Render will automatically detect the push and redeploy!

---

## 📊 Monitoring

Access logs and metrics:
1. Go to Render Dashboard
2. Select your service
3. Click **"Logs"** tab for real-time logs
4. Click **"Metrics"** tab for performance data

---

## 🆘 Support

- **Render Docs**: https://render.com/docs
- **Render Community**: https://community.render.com
- **Groq Docs**: https://console.groq.com/docs

---

## 🎉 Success!

Your Dr. HealBot is now live and accessible worldwide! 🌍

Share your deployment URL with users and start helping people with their health questions.

**Example URL**: `https://dr-healbot.onrender.com`
