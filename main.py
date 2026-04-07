import telebot
from yt_dlp import YoutubeDL
import os

# وضعنا التوكن الذي أرسلته بين علامتي التنصيص بدقة
TOKEN = '8216426518:AAFdpWpZ8d3Jc2kTZXrxCW5mFvuQ9UPXcMI'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🚀 أهلاً بك عبد الحميد في بوت التحميل الشامل!\n\nأرسل لي أي رابط من يوتيوب أو فيسبوك وسأحمله لك.")

@bot.message_handler(func=lambda message: message.text.startswith('http'))
def download_video(message):
    url = message.text
    chat_id = message.chat.id
    msg = bot.reply_to(message, "⏳ جاري المعالجة...")

    ydl_opts = {
        'format': 'best',
        'outtmpl': 'video.mp4',
        'noplaylist': True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            with open('video.mp4', 'rb') as video:
                bot.send_video(chat_id, video, caption="✅ تم التحميل بنجاح")
            os.remove('video.mp4')
            bot.delete_message(chat_id, msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ خطأ: {str(e)}", chat_id, msg.message_id)

if __name__ == "__main__":
    bot.polling(none_stop=True)
