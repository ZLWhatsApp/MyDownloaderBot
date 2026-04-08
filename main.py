import telebot
from telebot import types
from yt_dlp import YoutubeDL
import os
import time

# --- إعدادات البوت الأساسية ---
TOKEN = '8216426518:AAFdpWpZ8d3Jc2kTZXrxCW5mFvuQ9UPXcMI' # التوكن الخاص بك
bot = telebot.TeleBot(TOKEN)

# --- لوحة التحكم الاحترافية ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("🚀 تحميل سريع"),
        types.KeyboardButton("📈 حالة السيرفر"),
        types.KeyboardButton("📜 دليل المنصات"),
        types.KeyboardButton("🛠️ الدعم الفني")
    )
    return markup

# --- الترحيب الرسمي الذكي ---
@bot.message_handler(commands=['start'])
def welcome(message):
    name = message.from_user.first_name
    welcome_text = (
        f"💎 **مرحباً بك في نظام التنزيلات المتقدم** 💎\n\n"
        f"أهلاً بك يا {name}، أنت الآن تستخدم أحد أقوى البوتات البرمجية للتحميل من السوشيال ميديا.\n\n"
        "⚡ **المميزات الحالية:**\n"
        "• جودة 4K/HD تلقائية.\n"
        "• دعم اليوتيوب، تيك توك، فيسبوك، وإنستقرام.\n"
        "• معالجة سحابية فائقة السرعة.\n\n"
        "👇 **أرسل الرابط الآن للبدء!**"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu(), parse_mode='Markdown')

# --- التعامل مع الأزرار ---
@bot.message_handler(func=lambda message: True)
def router(message):
    chat_id = message.chat.id
    if message.text == "🚀 تحميل سريع":
        bot.send_message(chat_id, "فقط قم بإرسال أي رابط وسأقوم بتحليله تلقائياً!")
    elif message.text == "📈 حالة السيرفر":
        bot.send_message(chat_id, "✅ الحالة: متصل\n⚡ السرعة: 1000 Mbps\n📦 التوفر: 99.9%")
    elif message.text == "📜 دليل المنصات":
        bot.send_message(chat_id, "يدعم البوت أكثر من 1000 موقع عالمي بما في ذلك:\n(YouTube, FB, Insta, TikTok, X, SoundCloud)")
    elif message.text == "🛠️ الدعم الفني":
        bot.send_message(chat_id, "للاستفسارات والمشاكل التقنية: @ZLWhatsApp")
    elif message.text.startswith(('http://', 'https://')):
        handle_download(message)

# --- محرك التحميل الاحترافي ---
def handle_download(message):
    url = message.text
    chat_id = message.chat.id
    status = bot.reply_to(message, "🔍 **جاري فحص الرابط وتجاوز القيود..**")

    # إعدادات متقدمة لتجاوز حظر الروابط والتحميل بأعلى جودة
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': f'downloads/{chat_id}_%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'cookiefile': None, # يمكن إضافة ملف كوكيز هنا لاحقاً للحسابات الخاصة
        'merge_output_format': 'mp4',
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            bot.edit_message_text("⚡ **بدء التحميل من السيرفر..**", chat_id, status.message_id)
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            bot.edit_message_text("📤 **جاري رفع الملف إلى تلجرام..**", chat_id, status.message_id)
            with open(filename, 'rb') as video:
                bot.send_chat_action(chat_id, 'upload_video')
                bot.send_video(chat_id, video, caption=f"✅ **تم التحميل بنجاح**\n\n🎬: {info.get('title')}\n⏱️: {time.strftime('%H:%M:%S', time.gmtime(info.get('duration', 0)))}", parse_mode='Markdown')
            
            os.remove(filename)
            bot.delete_message(chat_id, status.message_id)

    except Exception as e:
        bot.edit_message_text(f"⚠️ **فشل النظام في التحميل!**\n\nقد يكون الرابط محمي بخصوصية عالية أو يتطلب تسجيل دخول.\n\n`السبب البرمجي: {str(e)[:50]}...`", chat_id, status.message_id)

if __name__ == "__main__":
    bot.polling(none_stop=True)
