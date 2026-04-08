# AI Personal Productivity Assistant 🚀

A production-ready Multi-Agent AI system built with Python, FastAPI, and Google Gemini.

## Features
- **Coordinator Agent** dynamically delegates sub-tasks to specialized agents.
- **Task Agent, Scheduler Agent, Notes Agent, Reminder Agent** with native MCP tool calling to an SQLite database.
- **FastAPI** backend providing native REST API access.
- **Vanilla HTML/JS** Frontend dashboard integrating conversational output with live database states.
- Clean JSON output generation.
- Deployable directly to **Google Cloud Run**.

## Requirements
- Python 3.10+
- A Google Gemini API Key (`GEMINI_API_KEY`)

---

## 💻 1. How to Run Locally

### Approach A: Native Python Setup

1. **Set your API Key**
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Server**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Access the Application**
   Open your browser and navigate to: [http://127.0.0.1:8000](http://127.0.0.1:8000)

### Approach B: Docker

1. **Build image**
   ```bash
   docker build -t productivity-agent .
   ```

2. **Run container**
   ```bash
   docker run -p 8080:8080 -e GEMINI_API_KEY="your_api_key" productivity-agent
   ```

---

## ☁️ 2. How to Deploy to Google Cloud Run

Google Cloud Run allows serverless execution of containerized applications.

### Option 1: Using Google Cloud SDK (CLI)

1. Authenticate with Google Cloud:
   ```bash
   gcloud auth login
   gcloud config set project [YOUR-PROJECT-ID]
   ```

2. Build and Submit your image to Google Container Registry (GCR):
   ```bash
   gcloud builds submit --tag gcr.io/[YOUR-PROJECT-ID]/productivity-agent
   ```

3. Deploy to Cloud Run:
   ```bash
   gcloud run deploy productivity-agent \
      --image gcr.io/[YOUR-PROJECT-ID]/productivity-agent \
      --platform managed \
      --region us-central1 \
      --allow-unauthenticated \
      --set-env-vars="GEMINI_API_KEY=your_gemini_api_key_here"
   ```

### Option 2: Using the Google Cloud Web Console
1. Go to **Google Cloud Console** -> **Cloud Run**.
2. Click **Create Service**.
3. Select "Continuously deploy new revisions from a source repository" (connect your GitHub repo with this codebase).
4. In "Advanced Settings" -> "Variables & Secrets", add `GEMINI_API_KEY` with your actual key.
5. Hit **Create**. Once deployed, you will get a public URL for your web app!
