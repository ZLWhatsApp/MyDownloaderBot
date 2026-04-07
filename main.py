import telebot
from yt_dlp import YoutubeDL
import os

# ضع التوكن الخاص بك هنا بين العلامتين
TOKEN = '8216426518:AAFdpWpZ8d3Jc2kTZXrxCW5mFvuQ9UPXcMI'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً بك! أرسل لي رابط فيديو من فيسبوك أو يوتيوب أو تيك توك وسأقوم بتحميله لك.")

@bot.message_handler(func=lambda message: message.text.startswith('http'))
def download_video(message):
    url = message.text
    chat_id = message.chat.id
    bot.send_message(chat_id, "⏳ جاري التحميل... انتظر قليلاً")

    ydl_opts = {
        'format': 'best',
        'outtmpl': 'video.mp4',
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            with open('video.mp4', 'rb') as video:
                bot.send_video(chat_id, video)
            os.remove('video.mp4') # حذف الفيديو من السيرفر بعد إرساله
    except Exception as e:
        bot.send_message(chat_id, f"حدث خطأ: {e}")

bot.polling()
