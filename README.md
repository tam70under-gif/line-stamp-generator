# LINE Stamp Generator

A Streamlit web application to generate LINE-style stamps using Google Gemini 3 Pro (Imagen 3).

## Features
- Generate 8-40 stamps at once.
- Preserves character consistency locally (best effort).
- Export to ZIP.
- Mobile-friendly UI.

## Local Setup
1. **Install Git**: [Download Git](https://git-scm.com/downloads)
2. **Clone/Download** this repository.
3. **Run**:
   ```bash
   run_app.bat
   ```

## Deployment
### Streamlit Community Cloud
1. Push this code to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io).
3. Connect your GitHub account.
4. Select this repository.
5. Set `app.py` as the main file.
6. **Important**: Add your `GOOGLE_API_KEY` in Streamlit "Secrets" settings.

### Vercel
> [!WARNING]
> Streamlit apps rely on WebSockets, which Vercel Serverless Functions do not natively support. Deployment on Vercel may result in "Connection Error" or limited functionality. **Google Cloud Run or Streamlit Community Cloud represents the recommended deployment method.**

1. Install Vercel CLI.
2. Run `vercel`.

### Google Cloud Run
1. **Install Google Cloud CLI**: [Download SDK](https://cloud.google.com/sdk/docs/install).
2. **Authenticate**:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```
3. **Deploy from Source**:
   ```bash
   gcloud run deploy line-stamp-gen --source . --port 8501 --allow-unauthenticated
   ```
   (This automatically builds using the Dockerfile)
4. **Environment Variables**:
   Set `gemini_api_key` in the Cloud Run console or passed via `--set-env-vars`.
   *(Note: The app allows entering the key in the UI, which is safer for public demos)*
