import telebot
from telebot import types
from yt_dlp import YoutubeDL
import os

# --- الإعدادات الفنية الفائقة ---
TOKEN = '8216426518:AAFdpWpZ8d3Jc2kTZXrxCW5mFvuQ9UPXcMI'
bot = telebot.TeleBot(TOKEN)

# --- واجهة المستخدم الاحترافية ---
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("🚀 تحميل فيديو"),
        types.KeyboardButton("🎵 تحميل صوت"),
        types.KeyboardButton("📊 حالة النظام"),
        types.KeyboardButton("🛠️ الدعم المباشر")
    )
    return markup

@bot.message_handler(commands=['start'])
def welcome_user(message):
    name = message.from_user.first_name
    msg = (
        f"👑 **مرحباً بك يا {name} في منصة التحميل المتقدمة**\n\n"
        "تم تحديث النظام ليتجاوز القيود البرمجية بأحدث التقنيات.\n"
        "كل ما عليك فعله هو إرسال الرابط وسأقوم بالباقي."
    )
    bot.send_message(message.chat.id, msg, reply_markup=get_main_keyboard(), parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_requests(message):
    chat_id = message.chat.id
    text = message.text

    if text == "📊 حالة النظام":
        bot.send_message(chat_id, "✅ جميع المحركات تعمل بكفاءة عالية.")
    elif text == "🛠️ الدعم المباشر":
        bot.send_message(chat_id, "👨‍💻 المطور: @ZLWhatsApp")
    elif text.startswith(('http://', 'https://')):
        start_download(message)

# --- محرك التحميل الذكي المتجاوز للقيود ---
def start_download(message):
    url = message.text
    chat_id = message.chat.id
    status = bot.reply_to(message, "⚙️ **جاري اختراق القيود ومعالجة الرابط..**")

    # إعدادات احترافية لمحاكاة متصفح حقيقي (تجاوز قيود يوتيوب)
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'outtmpl': f'downloads/{chat_id}_%(title)s.%(ext)s',
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            # محاولة جلب المعلومات أولاً
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            bot.edit_message_text("📤 **جاري رفع الملف الفائق..**", chat_id, status.message_id)
            with open(filename, 'rb') as video:
                bot.send_chat_action(chat_id, 'upload_video')
                bot.send_video(chat_id, video, caption=f"✨ **تم الإنجاز بنجاح!**\n🎬: {info.get('title')}", parse_mode='Markdown')
            
            os.remove(filename)
            bot.delete_message(chat_id, status.message_id)

    except Exception as e:
        error_msg = str(e)
        if "confirm your age" in error_msg:
            hint = "⚠️ هذا الفيديو يتطلب تسجيل دخول (مقيد بالفئة العمرية)، جرب فيديو آخر عام."
        else:
            hint = f"❌ خطأ تقني: `{error_msg[:100]}`"
        bot.edit_message_text(hint, chat_id, status.message_id, parse_mode='Markdown')

if __name__ == "__main__":
    bot.polling(none_stop=True)
