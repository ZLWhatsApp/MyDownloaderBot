import telebot
from telebot import types
from yt_dlp import YoutubeDL
import os

# التوكن الخاص بك
TOKEN = '8216426518:AAFdpWpZ8d3Jc2kTZXrxCW5mFvuQ9UPXcMI'
bot = telebot.TeleBot(TOKEN)

# --- دالة إنشاء الأزرار الرئيسية ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("🔗 كيفية التحميل؟")
    btn2 = types.KeyboardButton("📊 المنصات المدعومة")
    btn3 = types.KeyboardButton("👨‍💻 الدعم الفني")
    markup.add(btn1, btn2, btn3)
    return markup

# --- استقبال أمر البداية /start ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name  # هنا يأخذ اسم المستخدم الحقيقي
    welcome_text = (
        f"🌟 **أهلاً بك يا {user_name} في بوت التحميل الذكي**\n\n"
        "أنا هنا لمساعدتك في تحميل الفيديوهات من مختلف منصات التواصل الاجتماعي بأعلى جودة ممكنة.\n\n"
        "👇 **كل ما عليك هو إرسال رابط الفيديو مباشرة هنا.**"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu(), parse_mode='Markdown')

# --- معالجة الأزرار والقوائم ---
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    chat_id = message.chat.id
    
    if message.text == "🔗 كيفية التحميل؟":
        guide = (
            "💡 **طريقة الاستخدام بسيطة جداً:**\n\n"
            "1️⃣ اذهب للمنصة (يوتيوب، فيسبوك، إلخ..).\n"
            "2️⃣ قم بنسخ رابط الفيديو (Share -> Copy Link).\n"
            "3️⃣ قم بلصق الرابط هنا في البوت.\n"
            "4️⃣ انتظر ثواني وسيصلك الفيديو جاهزاً."
        )
        bot.send_message(chat_id, guide, parse_mode='Markdown')

    elif message.text == "📊 المنصات المدعومة":
        platforms = (
            "✅ **يدعم البوت التحميل من:**\n"
            "• YouTube (Shorts & Videos)\n"
            "• Facebook & Instagram\n"
            "• TikTok (بدون علامة مائية)\n"
            "• X (Twitter سابقاً)\n"
            "• والعديد من المواقع الأخرى..."
        )
        bot.send_message(chat_id, platforms, parse_mode='Markdown')

    elif message.text == "👨‍💻 الدعم الفني":
        bot.send_message(chat_id, "👤 للتواصل مع المطور أو الإبلاغ عن مشكلة: \n\n @حسابك_هنا")

    # --- معالجة الروابط (التحميل الفعلي) ---
    elif message.text.startswith(('http://', 'https://')):
        process_download(message)

# --- دالة التحميل الاحترافية ---
def process_download(message):
    url = message.text
    chat_id = message.chat.id
    status_msg = bot.reply_to(message, "⏳ **جاري فحص الرابط واستخراج الفيديو..**")

    ydl_opts = {
        'format': 'best',
        'outtmpl': f'downloads/{chat_id}_video.%(ext)s',
        'noplaylist': True,
        'quiet': True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            with open(filename, 'rb') as video:
                bot.send_chat_action(chat_id, 'upload_video')
                bot.send_video(
                    chat_id, 
                    video, 
                    caption=f"✅ **تم التحميل بنجاح**\n\n🎬: {info.get('title', 'Video')}",
                    parse_mode='Markdown'
                )
            
            os.remove(filename)
            bot.delete_message(chat_id, status_msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ **عذراً، حدث خطأ!**\nتأكد أن الرابط عام وصحيح.\n\nالمشكلة: `رابط غير مدعوم أو محمي`", chat_id, status_msg.message_id)

if __name__ == "__main__":
    bot.polling(none_stop=True)
