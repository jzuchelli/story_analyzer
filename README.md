# Story Analyzer

Story Analyzer is a local web app for checking Azure DevOps-style user stories before work starts. It validates a story against rule-based readiness checks, runs Hugging Face zero-shot classification, and streams partial results back to the UI as validation work completes.

## Images

Add screenshots to `docs/images/` so readers can preview the app before running it locally.

Suggested screenshots:

- `docs/images/story-input.png` - Story entry form before validation
- `docs/images/validation-progress.png` - Floating progress indicator while AI validation is running
- `docs/images/validation-results.png` - Final score, readiness checks, suggestions, and Hugging Face classification

After adding screenshots, they will render here:

![Story input form](docs/images/story-input.png)

![Validation progress indicator](docs/images/validation-progress.png)

![Validation results](docs/images/validation-results.png)

![Story suggestions](docs/images/story-suggestions.png)

## Prerequisites

Before setting up the project, confirm that Git, Python, Node.js, npm, and uv are available.

### 1. Check Git

```bash
git --version
```

If this fails, install Git from https://git-scm.com/downloads.

### 2. Check Python

This project requires Python 3.10 or newer.

```bash
python --version
```

If that command fails, try:

```bash
python3 --version
```

If Python is missing or older than 3.10, install the latest Python 3 release from https://www.python.org/downloads/.

### 3. Check Node.js and npm

The UI uses Next.js, which is installed through npm. You do not need to install Next.js globally.

```bash
node --version
npm --version
```

If either command fails, install the current LTS version of Node.js from https://nodejs.org/.

### 4. Check uv

The backend dependencies are managed with uv.

```bash
uv --version
```

If uv is missing, install it:

```bash
python -m pip install uv
```

If your system uses `python3` instead of `python`, run:

```bash
python3 -m pip install uv
```

## Setup

Clone the repository and enter the project directory:

```bash
git clone <repo-url>
cd story_analyzer
```

Install the backend dependencies:

```bash
uv sync
```

Install the frontend dependencies:

```bash
cd frontend
npm install
cd ..
```

## Run the App

On macOS, Linux, WSL, or Git Bash, run:

```bash
./start.sh
```

The script starts:

- FastAPI API: `http://127.0.0.1:8000`
- Next.js UI: `http://127.0.0.1:3000`

It waits for the UI to become available and then opens the default browser. Press `Ctrl+C` in the terminal to stop both servers.

## Manual Run Commands

If you are on Windows without Bash, or if you prefer separate terminals, start the backend and frontend manually.

Terminal 1:

```bash
uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Terminal 2:

```bash
cd frontend
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Then open:

```text
http://127.0.0.1:3000
```

## First Run Notes

The first story validation that reaches Hugging Face classification may take longer because Transformers downloads the configured zero-shot model:

```text
facebook/bart-large-mnli
```

The default model can be changed with:

```bash
HUGGINGFACE_ZERO_SHOT_MODEL=<model-name> ./start.sh
```

For manual backend startup:

```bash
HUGGINGFACE_ZERO_SHOT_MODEL=<model-name> uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

## Verify the Backend

Once the API is running:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

Check Hugging Face backend availability:

```bash
curl http://127.0.0.1:8000/huggingface/status
```

The response should show `"available": true` and include at least one backend, such as `torch`.

## Troubleshooting

If `uv sync` fails because Python is too old, install Python 3.10 or newer and rerun `uv sync`.

If `npm install` fails, confirm `node --version` and `npm --version` work from the same terminal.

If port `8000` or `3000` is already in use, stop the existing process or run with different ports:

```bash
API_PORT=8010 UI_PORT=3010 ./start.sh
```

If the UI cannot reach the API, confirm the backend is running at `http://127.0.0.1:8000` and that `NEXT_PUBLIC_API_BASE_URL` points to the same URL when starting the frontend manually.

## Project Structure

```text
.
├── main.py                  # FastAPI app and validation endpoints
├── models.py                # Request and response models
├── validators/              # Rule and Hugging Face validators
├── scoring/                 # Readiness score calculation
├── frontend/                # Next.js UI
├── start.sh                 # Starts backend, frontend, and browser
├── pyproject.toml           # Python dependency metadata
└── uv.lock                  # Locked Python dependency versions
```
