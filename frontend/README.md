# Document Q&A Assistant — Frontend

A separate React, TypeScript, Vite, and Tailwind CSS frontend for the existing FastAPI document Q&A backend.

## Run locally

1. Install Node.js 20.19+ or 22.12+ and npm.
2. From this directory, install the frontend dependencies:

   ```bash
   npm install
   ```

3. Copy `.env.example` to `.env` and set `VITE_API_BASE_URL` to the running FastAPI server. The example uses `http://127.0.0.1:8000`.
4. Start the frontend:

   ```bash
   npm run dev
   ```

The backend must be running separately and allow the frontend origin through CORS. API keys belong only in the backend environment; this frontend does not use or store Groq or Jina credentials.

## Production build

```bash
npm run build
npm run preview
```

Vite writes the static production site to `dist/`.

## Deploy to Vercel

1. Import this frontend project into Vercel. If the repository also contains the backend, set the Vercel **Root Directory** to `frontend`.
2. Set the Vercel environment variable `VITE_API_BASE_URL` to the deployed FastAPI API base URL, without a trailing slash.
3. Deploy with the default Vite settings. The build command is `npm run build` and the output directory is `dist`.
4. Configure the backend to allow the deployed Vercel origin through CORS. The backend is intentionally managed separately.
