import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiohttp import web
import yt_dlp

# --- CONFIGURATION ---
TOKEN = os.getenv("BOT_TOKEN")  # We will set this in Render later
app = web.Application()

# --- BOT SETUP ---
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- DOWNLOADER LOGIC ---
def download_video(url):
    """Downloads video using yt-dlp and returns filename"""
    ydl_opts = {
        'format': 'mp4/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'max_filesize': 50 * 1024 * 1024,
        'quiet': True,
        'cookiefile': 'cookies.txt'  # <--- ADD THIS LINE
    }
    # ... rest of the code remains the same


    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# --- BOT HANDLERS ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.reply("👋 Hi! Send me an Instagram or YouTube link, and I'll download it for you.")

@dp.message(F.text.contains("http"))
async def handle_link(message: types.Message):
    status_msg = await message.reply("⏳ Downloading... Please wait.")
    
    try:
        url = message.text
        # Run the download in a separate thread to keep bot responsive
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(None, download_video, url)
        
        # Send video
        video_file = types.FSInputFile(file_path)
        await bot.send_video(chat_id=message.chat.id, video=video_file, caption="Here is your video! 🎥")
        
        # Cleanup
        os.remove(file_path)
        await bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")

# --- KEEP-ALIVE SERVER (For Free Hosting) ---
async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

# --- MAIN ---
async def main():
    # Start the dummy web server first
    await start_web_server()
    # Start the bot
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Create downloads folder if not exists
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    asyncio.run(main())
