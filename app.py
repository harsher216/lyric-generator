import tempfile
from pathlib import Path

import streamlit as st
import yt_dlp
from openai import OpenAI


st.set_page_config(page_title="Lyric Generator", page_icon="🎵")
st.title("Lyric Generator")
st.caption("YouTube link → transcript → new lyrics in that style")


def safe_err(e: Exception, secret: str) -> str:
    msg = str(e)
    if secret:
        msg = msg.replace(secret, "[REDACTED]")
    return msg

with st.sidebar:
    api_key = st.text_input(
        "OpenAI API key",
        type="password",
        help="Bring your own key. Stored only in this session.",
    )
    st.markdown("[Get a key](https://platform.openai.com/api-keys)")
    st.caption(
        "🔒 Key held in session memory only. Sent over HTTPS to OpenAI. "
        "Never stored to disk, never logged. Cleared on tab close."
    )

tab_url, tab_upload = st.tabs(["YouTube URL", "Upload audio file"])
with tab_url:
    url = st.text_input("YouTube URL", placeholder="https://youtube.com/watch?v=...")
    st.caption("⚠️ YouTube often blocks cloud servers. If it fails, use the Upload tab.")
    transcribe_btn = st.button("Transcribe URL", type="primary", disabled=not (url and api_key))
with tab_upload:
    uploaded = st.file_uploader("Audio file (mp3/m4a/wav, ≤25 MB)", type=["mp3", "m4a", "wav", "mp4"])
    upload_btn = st.button("Transcribe file", type="primary", disabled=not (uploaded and api_key))


def download_audio(url: str, out_dir: Path) -> Path:
    opts = {
        "format": "bestaudio/best",
        "outtmpl": str(out_dir / "%(id)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return out_dir / f"{info['id']}.mp3", info.get("title", "untitled")


def transcribe(client: OpenAI, mp3_path: Path) -> str:
    with open(mp3_path, "rb") as f:
        resp = client.audio.transcriptions.create(
            model="gpt-4o-transcribe",
            file=f,
        )
    return resp.text


def generate_lyrics(client: OpenAI, transcript: str, style_hint: str) -> str:
    prompt = (
        "You are a songwriter. Below is a transcript of a song. "
        "Write ORIGINAL new lyrics inspired by its style, mood, rhyme scheme, "
        "and themes. Do not reproduce the original lyrics.\n\n"
        f"Extra direction from user: {style_hint or '(none)'}\n\n"
        f"Original transcript:\n{transcript}\n\n"
        "New original lyrics:"
    )
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


if transcribe_btn:
    try:
        client = OpenAI(api_key=api_key)
        with st.status("Downloading audio...", expanded=False) as status:
            with tempfile.TemporaryDirectory() as tmp:
                mp3, title = download_audio(url, Path(tmp))
                status.update(label="Transcribing...")
                text = transcribe(client, mp3)
        st.session_state["transcript"] = text
        st.session_state["title"] = title
        st.success(f"Done: {title}")
    except Exception as e:
        st.error(f"Failed: {safe_err(e, api_key)}")

if upload_btn:
    try:
        client = OpenAI(api_key=api_key)
        with st.status("Transcribing uploaded file...", expanded=False):
            with tempfile.TemporaryDirectory() as tmp:
                ext = Path(uploaded.name).suffix or ".mp3"
                path = Path(tmp) / f"upload{ext}"
                path.write_bytes(uploaded.getvalue())
                text = transcribe(client, path)
        st.session_state["transcript"] = text
        st.session_state["title"] = uploaded.name
        st.success(f"Done: {uploaded.name}")
    except Exception as e:
        st.error(f"Failed: {safe_err(e, api_key)}")

if "transcript" in st.session_state:
    st.subheader(f"Transcript — {st.session_state.get('title', '')}")
    st.text_area("transcript", st.session_state["transcript"], height=200, label_visibility="collapsed")
    st.download_button(
        "Download .txt",
        st.session_state["transcript"],
        file_name="transcript.txt",
    )

    st.divider()
    st.subheader("Generate new lyrics in this style")
    style_hint = st.text_input("Optional direction", placeholder="e.g. sadder, about space, shorter")
    if st.button("Generate lyrics", disabled=not api_key):
        try:
            client = OpenAI(api_key=api_key)
            with st.spinner("Writing..."):
                lyrics = generate_lyrics(client, st.session_state["transcript"], style_hint)
            st.session_state["lyrics"] = lyrics
        except Exception as e:
            st.error(f"Failed: {safe_err(e, api_key)}")

if "lyrics" in st.session_state:
    st.text_area("Generated lyrics", st.session_state["lyrics"], height=300)
    st.download_button(
        "Download lyrics .txt",
        st.session_state["lyrics"],
        file_name="new_lyrics.txt",
    )
