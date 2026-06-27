# 🇩🇪 Instagram Reel German Transcriber Bot

Sends Instagram Reel links → Bot replies with German transcript (free, no API key needed!)

---

## 🛠️ Setup (one time)

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Install FFmpeg (required for audio processing)

**Windows:**
- Download from https://ffmpeg.org/download.html
- Add to PATH

**Mac:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

### 3. Create your Telegram Bot
1. Open Telegram → search **@BotFather**
2. Send `/newbot`
3. Follow steps → copy the **token** it gives you
4. Open `bot.py` → replace `YOUR_TELEGRAM_BOT_TOKEN` with your token

### 4. Run the bot
```bash
python bot.py
```

---

## 📱 How to use

1. Open Telegram → find your bot
2. Send any **public** Instagram Reel link
3. Bot replies with the **German transcript**
4. Paste transcript into Claude for translation + breakdown!

---

## ⚙️ Whisper Model sizes (in bot.py)

| Model | Speed | Accuracy |
|-------|-------|----------|
| tiny  | ⚡ Fast | OK |
| base  | Fast | Good (default) |
| small | Medium | Better |
| medium | Slow | Best free option |

Change `WHISPER_MODEL = "base"` to whichever you prefer.

---

## ⚠️ Notes
- Only works with **public** reels
- First run downloads the Whisper model (~150MB for base)
- Completely free, runs on your laptop
