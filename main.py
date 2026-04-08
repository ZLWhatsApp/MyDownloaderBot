import telebot
from telebot import types
from yt_dlp import YoutubeDL
import os
import re
import threading
from pathlib import Path

# ================== التوكن مكتوب مباشرة ==================
TOKEN = '8216426518:AAFdpWpZ8d3Jc2kTZXrxCW5mFvuQ9UPXcMI'
bot = telebot.TeleBot(TOKEN)

# ================== الإعدادات ==================
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

user_states = {}  # لتخزين نوع التحميل لكل مستخدم
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 ميجابايت

def clean_filename(filename: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def delete_file(path: Path):
    try:
        if path.exists():
            path.unlink()
    except Exception as e:
        print(f"خطأ في حذف الملف: {e}")

# ================== لوحة المفاتيح ==================
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("🎬 تحميل فيديو"),
        types.KeyboardButton("🎵 تحميل صوت"),
        types.KeyboardButton("📊 حالة النظام"),
        types.KeyboardButton("🛠️ الدعم"),
        types.KeyboardButton("❌ إلغاء")
    )
    return markup

# ================== أوامر البوت ==================
@bot.message_handler(commands=['start'])
def welcome_user(message):
    name = message.from_user.first_name
    msg = (
        f"👑 **مرحباً {name} في بوت التحميل الشامل**\n\n"
        "📌 **المنصات المدعومة:**\n"
        "✅ يوتيوب - تيك توك - انستغرام - فيسبوك - تويتر - لينكد إن - وغيرها\n\n"
        "🎯 **كيفية الاستخدام:**\n"
        "1️⃣ اختر نوع التحميل (فيديو أو صوت).\n"
        "2️⃣ أرسل الرابط.\n"
        "3️⃣ انتظر التحميل والرفع.\n\n"
        "⚡ **ملاحظة:** لتحميل فيديوهات يوتيوب، يجب وضع ملف `cookies.txt` في مجلد البوت (انظر شرح الإضافة)."
    )
    bot.send_message(message.chat.id, msg, reply_markup=get_main_keyboard(), parse_mode='Markdown')

@bot.message_handler(commands=['cancel'])
def cancel_action(message):
    chat_id = message.chat.id
    if chat_id in user_states:
        del user_states[chat_id]
        bot.send_message(chat_id, "❌ تم إلغاء العملية الحالية.")
    else:
        bot.send_message(chat_id, "⚠️ لا توجد عملية نشطة.")

# ================== معالجة الأزرار ==================
@bot.message_handler(func=lambda message: message.text in ["🎬 تحميل فيديو", "🎵 تحميل صوت", "📊 حالة النظام", "🛠️ الدعم", "❌ إلغاء"])
def handle_buttons(message):
    chat_id = message.chat.id
    text = message.text

    if text == "📊 حالة النظام":
        total_size = sum(f.stat().st_size for f in DOWNLOAD_DIR.glob('*') if f.is_file())
        bot.send_message(chat_id, f"✅ **جميع الأنظمة تعمل بكفاءة**\n📦 مساحة التخزين المستخدمة: {total_size / (1024**3):.2f} جيجابايت", parse_mode='Markdown')
    elif text == "🛠️ الدعم":
        bot.send_message(chat_id, "👨‍💻 **المطور:** @ZLWhatsApp\n📧 للاستفسارات، تواصل مع المطور.", parse_mode='Markdown')
    elif text == "❌ إلغاء":
        if chat_id in user_states:
            del user_states[chat_id]
            bot.send_message(chat_id, "❌ تم إلغاء العملية الحالية.")
        else:
            bot.send_message(chat_id, "⚠️ لا توجد عملية نشطة.")
    elif text == "🎬 تحميل فيديو":
        user_states[chat_id] = "video"
        bot.send_message(chat_id, "🎬 **أرسل رابط الفيديو الآن** (من أي منصة):\nيمكنك الضغط /cancel للإلغاء.", parse_mode='Markdown')
    elif text == "🎵 تحميل صوت":
        user_states[chat_id] = "audio"
        bot.send_message(chat_id, "🎵 **أرسل رابط المقطع لاستخراج الصوت:**", parse_mode='Markdown')

# ================== استقبال الروابط ==================
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_urls(message):
    chat_id = message.chat.id
    url = message.text.strip()

    if not (url.startswith(('http://', 'https://'))):
        if chat_id in user_states:
            bot.send_message(chat_id, "⚠️ يرجى إرسال رابط صحيح يبدأ بـ http:// أو https://\nأو اضغط /cancel للإلغاء.")
        else:
            bot.send_message(chat_id, "🔘 اختر أولاً نوع التحميل من الأزرار.")
        return

    if chat_id not in user_states:
        bot.send_message(chat_id, "⚠️ يرجى اختيار نوع التحميل أولاً (فيديو أو صوت) من الأزرار.")
        return

    download_type = user_states[chat_id]
    del user_states[chat_id]

    threading.Thread(target=start_download, args=(message, url, download_type), daemon=True).start()

# ================== دالة التحميل الأساسية (مع دعم الكوكيز) ==================
def start_download(message, url, download_type):
    chat_id = message.chat.id
    status_msg = bot.reply_to(message, "⏳ **جاري تجهيز الرابط...**", parse_mode='Markdown')

    # إعدادات الكوكيز - إذا وجد ملف cookies.txt سيتم استخدامه
    cookies_file = "cookies.txt"
    cookies_option = {'cookiefile': cookies_file} if os.path.exists(cookies_file) else {}

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'extract_flat': False,
        'force_generic_extractor': False,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'http_headers': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
        },
        'outtmpl': str(DOWNLOAD_DIR / '%(id)s.%(ext)s'),
        **cookies_option,
    }

    if download_type == "audio":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
        send_func = bot.send_audio
        caption = "🎵 **تم استخراج الصوت بنجاح!**"
    else:
        ydl_opts.update({
            'format': 'best[height<=720]',
            'merge_output_format': 'mp4',
        })
        send_func = bot.send_video
        caption = "🎬 **تم تحميل الفيديو بنجاح!**"

    try:
        bot.edit_message_text("📥 **جاري التحميل...**", chat_id, status_msg.message_id, parse_mode='Markdown')
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                raise Exception("لم يتم العثور على محتوى.")

            filename = ydl.prepare_filename(info)
            if download_type == "audio":
                filename = Path(filename).with_suffix('.mp3')
            else:
                filename = Path(filename)

            if not filename.exists():
                file_id = info.get('id', 'unknown')
                possible = list(DOWNLOAD_DIR.glob(f"{file_id}.*"))
                if possible:
                    filename = possible[0]
                else:
                    raise Exception("الملف غير موجود.")

            file_size = filename.stat().st_size
            if file_size > MAX_FILE_SIZE:
                bot.edit_message_text(f"⚠️ الحجم {file_size/(1024**2):.1f} ميجابايت > 50 ميجابايت، لا يمكن الرفع.", chat_id, status_msg.message_id)
                delete_file(filename)
                return

            bot.edit_message_text("📤 **جاري الرفع...**", chat_id, status_msg.message_id, parse_mode='Markdown')
            with open(filename, 'rb') as f:
                send_func(chat_id, f, caption=f"{caption}\n🎬 {info.get('title', 'فيديو')[:100]}", parse_mode='Markdown', timeout=120)

            delete_file(filename)
            bot.delete_message(chat_id, status_msg.message_id)

    except Exception as e:
        error_str = str(e).lower()
        if "sign in" in error_str or "bot" in error_str:
            hint = "🍪 **مطلوب ملف كوكيز ليوتيوب.**\n\nقم بتحميل إضافة 'Get cookies.txt' لمتصفحك، وسجل الدخول إلى يوتيوب، ثم صدّر الكوكيز إلى ملف `cookies.txt` وضعه في مجلد البوت."
        elif "age" in error_str:
            hint = "🔞 هذا الفيديو مقيد عمرياً ولا يمكن تحميله."
        elif "private" in error_str:
            hint = "🔒 هذا المحتوى خاص أو محذوف."
        else:
            hint = f"⚠️ خطأ: {error_str[:150]}"
        bot.edit_message_text(hint, chat_id, status_msg.message_id, parse_mode='Markdown')
        for f in DOWNLOAD_DIR.glob(f"{chat_id}_*"):
            delete_file(f)

# ================== تشغيل البوت ==================
if __name__ == "__main__":
    print("🚀 البوت يعمل الآن...")
    bot.infinity_polling(timeout=60)
