# Lyric Generator

Paste a YouTube link, get the transcript, generate new original lyrics in the same style. Bring your own OpenAI API key.

## Run locally

Requires `ffmpeg` on PATH.

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501, paste your OpenAI key in the sidebar, paste a YouTube URL.

## Deploy (Streamlit Community Cloud, free)

1. Push this folder to a public GitHub repo.
2. Go to https://share.streamlit.io, "New app", point at your repo and `app.py`.
3. `packages.txt` auto-installs `ffmpeg` in the container.
4. Share the URL. Each user enters their own API key — no billing for you.

## Notes

- Downloads audio to a temp dir, deletes after transcription.
- `gpt-4o-transcribe` has a 25 MB upload limit (~20 min of audio). Long videos will fail until chunking is added.
- Generates **new original lyrics** inspired by style/mood — does not reproduce the original.
