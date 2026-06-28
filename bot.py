import os
import re
import base64
import subprocess
import tempfile
import asyncio
import yt_dlp
import whisper
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# === CONFIG ===
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base")  # tiny, base, small, medium
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG_DIR = os.path.join(SCRIPT_DIR, "ffmpeg", "bin")
COOKIES_PATH = os.path.join(SCRIPT_DIR, "cookies.txt")
if os.path.isdir(FFMPEG_DIR):
    os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")

model = None


def setup_instagram_cookies():
    """Load Instagram cookies from env or local file (needed on cloud servers)."""
    if os.path.isfile(COOKIES_PATH):
        return COOKIES_PATH

    raw = os.environ.get("INSTAGRAM_COOKIES", "")
    b64 = os.environ.get("INSTAGRAM_COOKIES_B64", "")
    if b64:
        raw = base64.b64decode(b64).decode("utf-8")
    if raw.strip():
        with open(COOKIES_PATH, "w", encoding="utf-8") as f:
            f.write(raw)
        return COOKIES_PATH
    return None


def clean_instagram_url(url):
    url = url.strip().split()[0]
    url = url.split("?")[0].rstrip("/") + "/"
    return url


def strip_ansi(text):
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def instagram_error_message(error_text):
    if "empty media response" in error_text or "login required" in error_text:
        return (
            "❌ Instagram blocked the download.\n\n"
            "This often happens on cloud servers (Railway). Try:\n"
            "1. Make sure the reel is public\n"
            "2. Add Instagram cookies in Railway Variables:\n"
            "   • Export cookies.txt while logged into Instagram\n"
            "   • Set INSTAGRAM_COOKIES_B64 to the base64 of that file\n"
            "3. Or run the bot locally on your PC instead\n\n"
            f"Details: {error_text[:200]}"
        )
    return f"❌ Error: {error_text}\n\nMake sure the reel is public!"


def build_ydl_opts(tmpdir):
    opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(tmpdir, "audio.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
        "noplaylist": True,
    }
    if os.path.isdir(FFMPEG_DIR):
        opts["ffmpeg_location"] = FFMPEG_DIR
    cookies = setup_instagram_cookies()
    if cookies:
        opts["cookiefile"] = cookies
    return opts

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    
    # Check if it's an Instagram link
    if "instagram.com" not in text:
        await update.message.reply_text("Send me an Instagram Reel link and I'll transcribe the German audio!")
        return

    await update.message.reply_text("⏳ Downloading reel... please wait")
    url = clean_instagram_url(text)

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = build_ydl_opts(tmpdir)

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Find the downloaded mp3
            mp3_files = [f for f in os.listdir(tmpdir) if f.endswith(".mp3")]
            if not mp3_files:
                await update.message.reply_text("❌ Could not download audio. The reel might be private.")
                return

            audio_file = os.path.join(tmpdir, mp3_files[0])

            await update.message.reply_text("🎙️ Transcribing German audio...")

            # Transcribe with Whisper (force German language)
            result = model.transcribe(audio_file, language="de", fp16=False)
            transcript = result["text"].strip()

            if not transcript:
                await update.message.reply_text("❌ No speech detected in the audio.")
                return

            # Send transcript
            await update.message.reply_text(
                f"📝 *German Transcript:*\n\n{transcript}",
                parse_mode="Markdown"
            )
            await update.message.reply_text(
                "✅ Done! Paste this into Claude to get translation + breakdown 🇩🇪"
            )

    except yt_dlp.utils.DownloadError as e:
        msg = strip_ansi(str(e))
        await update.message.reply_text(instagram_error_message(msg))
    except Exception as e:
        msg = strip_ansi(str(e))
        await update.message.reply_text(instagram_error_message(msg))

def main():
    print(f"TELEGRAM_TOKEN configured: {bool(TELEGRAM_TOKEN)}")
    print(f"Instagram cookies configured: {bool(setup_instagram_cookies())}")
    if not TELEGRAM_TOKEN:
        raise SystemExit(
            "TELEGRAM_TOKEN is missing. In Railway: open your SERVICE (not Project Settings) "
            "→ Variables → add TELEGRAM_TOKEN with your @BotFather token."
        )

    global model
    print("Loading Whisper model...")
    model = whisper.load_model(WHISPER_MODEL)
    print("Model loaded!")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is running... Send an Instagram Reel link on Telegram!")
    app.run_polling()

if __name__ == "__main__":
    main()
