import os
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
if os.path.isdir(FFMPEG_DIR):
    os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")

# Load Whisper model once
print("Loading Whisper model...")
model = whisper.load_model(WHISPER_MODEL)
print("Model loaded!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    
    # Check if it's an Instagram link
    if "instagram.com" not in text:
        await update.message.reply_text("Send me an Instagram Reel link and I'll transcribe the German audio!")
        return

    await update.message.reply_text("⏳ Downloading reel... please wait")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = os.path.join(tmpdir, "audio.mp3")

            # Download audio from Instagram reel using yt-dlp
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(tmpdir, "audio.%(ext)s"),
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                "quiet": True,
            }
            if os.path.isdir(FFMPEG_DIR):
                ydl_opts["ffmpeg_location"] = FFMPEG_DIR

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([text.strip()])

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

    except FileNotFoundError as e:
        await update.message.reply_text(
            f"❌ FFmpeg not found: {e}\n\nRestart the bot after setup."
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}\n\nMake sure the reel is public!")

def main():
    if not TELEGRAM_TOKEN:
        raise SystemExit("Set TELEGRAM_TOKEN environment variable.")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is running... Send an Instagram Reel link on Telegram!")
    app.run_polling()

if __name__ == "__main__":
    main()
