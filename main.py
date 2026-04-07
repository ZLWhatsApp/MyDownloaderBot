import telebot
from telebot import types
from yt_dlp import YoutubeDL
import os

# توكن البوت الخاص بك
TOKEN = '8216426518:AAFdpWpZ8d3Jc2kTZXrxCW5mFvuQ9UPXcMI'
bot = telebot.TeleBot(TOKEN)

# --- أزرار القائمة الرئيسية ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("📖 كيفية الاستخدام")
    btn2 = types.KeyboardButton("🌐 المنصات المدعومة")
    btn3 = types.KeyboardButton("🆘 الدعم الفني")
    markup.add(btn1, btn2, btn3)
    return markup

# --- رسالة الترحيب الرسمية ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # استخدام اسم المستخدم الحقيقي بدل الاسم الثابت
    user_name = message.from_user.first_name
    welcome_text = (
        f"🙋‍♂️ **أهلاً بك يا {user_name} في بوت التنزيلات العالمي**\n\n"
        "أنا بوت احترافي مصمم لخدمتك في تحميل الفيديوهات والملفات من مختلف المنصات.\n\n"
        "👇 **أرسل رابط الفيديو الآن وسأبدأ بالتحميل فوراً!**"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu(), parse_mode='Markdown')

# --- معالجة الأزرار والروابط ---
@bot.message_handler(func=lambda message: True)
def handle_all(message):
    chat_id = message.chat.id
    
    if message.text == "📖 كيفية الاستخدام":
        guide = "💡 **ببساطة:** انسخ رابط أي فيديو (يوتيوب، فيسبوك، تيك توك، إلخ) وأرسله هنا مباشرة، وسأقوم بإرسال الفيديو لك كملف."
        bot.send_message(chat_id, guide, parse_mode='Markdown')
        
    elif message.text == "🌐 المنصات المدعومة":
        platforms = "✅ **ندعم حالياً:**\n• YouTube & Shorts\n• Facebook\n• Instagram\n• TikTok\n• X (Twitter)\n• والعديد غيرها..."
        bot.send_message(chat_id, platforms, parse_mode='Markdown')

    elif message.text == "🆘 الدعم الفني":
        bot.send_message(chat_id, "👨‍💻 للمساعدة تواصل مع المطور: @ZLWhatsApp")

    # إذا أرسل المستخدم رابطاً
    elif message.text.startswith(('http://', 'https://')):
        process_download(message)

def process_download(message):
    url = message.text
    chat_id = message.chat.id
    status_msg = bot.reply_to(message, "⏳ **جاري معالجة الرابط، يرجى الانتظار...**")

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
                bot.send_video(chat_id, video, caption=f"✅ **تم التحميل بنجاح**\n🎬: {info.get('title', 'فيديو')}", parse_mode='Markdown')
            
            os.remove(filename)
            bot.delete_message(chat_id, status_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ **عذراً، حدث خطأ!**\nتأكد أن الرابط عام (Public) وليس من حساب خاص.", chat_id, status_msg.message_id)

if __name__ == "__main__":
    bot.polling(none_stop=True)
