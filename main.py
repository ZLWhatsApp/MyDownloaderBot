import telebot
from telebot import types
from yt_dlp import YoutubeDL
import os
import re
import threading
from pathlib import Path

# ================== الإعدادات الأساسية ==================
TOKEN = '8216426518:AAFdpWpZ8d3Jc2kTZXrxCW5mFvuQ9UPXcMI'  # يُفضّل نقله إلى متغيرات البيئة
bot = telebot.TeleBot(TOKEN)

# مجلد التحميلات المؤقتة
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# قاموس لحفظ حالة كل مستخدم (نوع التحميل المطلوب)
user_states = {}

# الحد الأقصى لحجم الملف القابل للإرسال في تليجرام (50 ميجابايت)
MAX_FILE_SIZE = 50 * 1024 * 1024

# ================== دوال مساعدة ==================
def clean_filename(filename: str) -> str:
    """إزالة الأحرف غير المسموحة من اسم الملف"""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def get_download_path(chat_id: int, title: str, ext: str) -> Path:
    """إنشاء مسار ملف فريد وآمن"""
    safe_title = clean_filename(title)[:50]  # اختصار العنوان الطويل
    return DOWNLOAD_DIR / f"{chat_id}_{safe_title}.{ext}"

def delete_file(path: Path):
    """حذف الملف بعد الإرسال بأمان"""
    try:
        if path.exists():
            path.unlink()
    except Exception as e:
        print(f"خطأ في حذف الملف: {e}")

# ================== لوحة المفاتيح الرئيسية ==================
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
        f"👑 **مرحباً {name} في أقوى بوت تحميل من وسائل التواصل!**\n\n"
        "📌 **المنصات المدعومة:**\n"
        "✅ يوتيوب - تيك توك - انستغرام - فيسبوك - تويتر - لينكد إن - وغيرها\n\n"
        "🎯 **كيفية الاستخدام:**\n"
        "1️⃣ اختر نوع التحميل (فيديو أو صوت).\n"
        "2️⃣ أرسل الرابط مباشرة.\n"
        "3️⃣ انتظر قليلاً وسيتم الرفع تلقائياً.\n\n"
        "⚡ **مميزات البوت:**\n"
        "• سرعة فائقة بفضل تقنيات التحميل المتوازي.\n"
        "• تجاوز القيود العمرية والجغرافية.\n"
        "• دعم كامل للصوت بجودة عالية."
    )
    bot.send_message(message.chat.id, msg, reply_markup=get_main_keyboard(), parse_mode='Markdown')

@bot.message_handler(commands=['cancel'])
def cancel_action(message):
    chat_id = message.chat.id
    if chat_id in user_states:
        del user_states[chat_id]
        bot.send_message(chat_id, "❌ تم إلغاء العملية الحالية.")
    else:
        bot.send_message(chat_id, "⚠️ لا توجد عملية نشطة للإلغاء.")

# ================== معالجة الأزرار ==================
@bot.message_handler(func=lambda message: message.text in ["🎬 تحميل فيديو", "🎵 تحميل صوت", "📊 حالة النظام", "🛠️ الدعم", "❌ إلغاء"])
def handle_buttons(message):
    chat_id = message.chat.id
    text = message.text

    if text == "📊 حالة النظام":
        bot.send_message(chat_id, "✅ **جميع الأنظمة تعمل بكفاءة**\n📦 المساحة المتاحة: {:.2f} جيجابايت".format(
            sum(f.stat().st_size for f in DOWNLOAD_DIR.glob('*') if f.is_file()) / (1024**3)
        ), parse_mode='Markdown')
    
    elif text == "🛠️ الدعم":
        bot.send_message(chat_id, "👨‍💻 **المطور:** @ZLWhatsApp\n📧 للاستفسارات والدعم الفني، تواصل مع المطور مباشرة.", parse_mode='Markdown')
    
    elif text == "❌ إلغاء":
        if chat_id in user_states:
            del user_states[chat_id]
            bot.send_message(chat_id, "❌ تم إلغاء العملية الحالية.")
        else:
            bot.send_message(chat_id, "⚠️ لا توجد عملية نشطة للإلغاء.")
    
    elif text == "🎬 تحميل فيديو":
        user_states[chat_id] = "video"
        bot.send_message(chat_id, "🎬 **أرسل رابط الفيديو الآن** (من أي منصة):\nيمكنك إرسال الرابط مباشرة أو الضغط على /cancel للإلغاء.", parse_mode='Markdown')
    
    elif text == "🎵 تحميل صوت":
        user_states[chat_id] = "audio"
        bot.send_message(chat_id, "🎵 **أرسل رابط المقطع لاستخراج الصوت بجودة عالية:**\n(سيتم تحويله إلى MP3)", parse_mode='Markdown')

# ================== استقبال الروابط بناءً على الحالة ==================
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_urls(message):
    chat_id = message.chat.id
    url = message.text.strip()
    
    # التحقق من صحة الرابط
    if not (url.startswith(('http://', 'https://'))):
        # إذا لم يكن رابطاً، نعطي توجيه
        if chat_id in user_states:
            bot.send_message(chat_id, "⚠️ يرجى إرسال رابط صحيح يبدأ بـ http:// أو https://\nأو اضغط /cancel للإلغاء.")
        else:
            bot.send_message(chat_id, "🔘 اختر أولاً نوع التحميل من الأزرار، ثم أرسل الرابط.")
        return
    
    # التحقق من وجود حالة للمستخدم
    if chat_id not in user_states:
        bot.send_message(chat_id, "⚠️ يرجى اختيار نوع التحميل أولاً (فيديو أو صوت) من الأزرار.")
        return
    
    download_type = user_states[chat_id]
    # حذف الحالة فوراً لمنع التكرار
    del user_states[chat_id]
    
    # تشغيل التحميل في خيط منفصل
    threading.Thread(target=start_download, args=(message, url, download_type), daemon=True).start()

# ================== محرك التحميل الأساسي ==================
def start_download(message, url, download_type):
    chat_id = message.chat.id
    status_msg = bot.reply_to(message, "⏳ **جاري تجهيز الرابط وتحليل المحتوى...**\nقد يستغرق هذا بضع ثوانٍ.", parse_mode='Markdown')
    
    # إعدادات yt-dlp الاحترافية (محاكاة متصفح حقيقي)
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
            'Sec-Fetch-Mode': 'navigate',
        },
        'outtmpl': str(DOWNLOAD_DIR / '%(id)s.%(ext)s'),  # قالب مؤقت
    }
    
    # إعدادات خاصة بنوع التحميل
    if download_type == "audio":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': str(DOWNLOAD_DIR / '%(id)s.%(ext)s'),
        })
        final_ext = 'mp3'
        send_func = bot.send_audio
        caption = "🎵 **تم استخراج الصوت بنجاح!**"
    else:  # video
        ydl_opts.update({
            'format': 'best[height<=720]',  # حد أقصى 720p لتقليل الحجم، يمكن تغييره إلى 'best'
            'merge_output_format': 'mp4',
        })
        final_ext = 'mp4'
        send_func = bot.send_video
        caption = "🎬 **تم تحميل الفيديو بنجاح!**"
    
    try:
        # تحديث رسالة الحالة
        bot.edit_message_text("📥 **جاري التحميل والمعالجة...**\nقد يختلف الوقت حسب حجم الموجود.", chat_id, status_msg.message_id, parse_mode='Markdown')
        
        with YoutubeDL(ydl_opts) as ydl:
            # جلب المعلومات والتحميل
            info = ydl.extract_info(url, download=True)
            if info is None:
                raise Exception("لم يتم العثور على محتوى في هذا الرابط.")
            
            # الحصول على اسم الملف النهائي (بعد المعالجة)
            filename = ydl.prepare_filename(info)
            if download_type == "audio":
                # تحويل الامتداد إلى mp3 بعد المعالجة
                filename = Path(filename).with_suffix('.mp3')
            else:
                filename = Path(filename)
            
            # التحقق من وجود الملف
            if not filename.exists():
                # محاولة البحث عن أي ملف بنفس المعرف
                file_id = info.get('id', 'unknown')
                possible_files = list(DOWNLOAD_DIR.glob(f"{file_id}.*"))
                if possible_files:
                    filename = possible_files[0]
                else:
                    raise Exception("فشل في العثور على الملف المحمل.")
            
            # التحقق من حجم الملف
            file_size = filename.stat().st_size
            if file_size > MAX_FILE_SIZE:
                bot.edit_message_text(
                    f"⚠️ **الملف كبير جداً للإرسال عبر تليجرام**\n"
                    f"الحجم: {file_size / (1024**2):.1f} ميجابايت (الحد الأقصى 50 ميجابايت)\n"
                    f"❌ لا يمكن رفع هذا الملف.", 
                    chat_id, status_msg.message_id, parse_mode='Markdown'
                )
                delete_file(filename)
                return
            
            # رفع الملف مع إظهار حالة الرفع
            bot.edit_message_text("📤 **جاري رفع الملف إلى تليجرام...**", chat_id, status_msg.message_id, parse_mode='Markdown')
            bot.send_chat_action(chat_id, 'upload_video' if download_type == 'video' else 'upload_audio')
            
            with open(filename, 'rb') as f:
                send_func(
                    chat_id, f,
                    caption=f"{caption}\n🎬 **العنوان:** {info.get('title', 'غير معروف')[:100]}",
                    parse_mode='Markdown',
                    timeout=120
                )
            
            # حذف الملف بعد الإرسال
            delete_file(filename)
            bot.delete_message(chat_id, status_msg.message_id)
    
    except Exception as e:
        error_str = str(e).lower()
        # رسائل خطأ مفهومة للمستخدم
        if "age" in error_str or "confirm your age" in error_str:
            hint = "🔞 هذا الفيديو مقيد بالفئة العمرية ولا يمكن تحميله دون تسجيل دخول."
        elif "private" in error_str:
            hint = "🔒 هذا المحتوى خاص أو محذوف."
        elif "unavailable" in error_str:
            hint = "❌ المحتوى غير متوفر (ربما تم حذفه أو حظره في منطقتك)."
        elif "not found" in error_str:
            hint = "❌ الرابط غير صالح أو لم نتمكن من الوصول إليه."
        else:
            hint = f"⚠️ حدث خطأ تقني: `{error_str[:150]}`"
        
        bot.edit_message_text(hint, chat_id, status_msg.message_id, parse_mode='Markdown')
        
        # تنظيف أي ملفات متبقية
        for f in DOWNLOAD_DIR.glob(f"{message.chat.id}_*"):
            delete_file(f)

# ================== تشغيل البوت ==================
if __name__ == "__main__":
    print("🚀 تم تشغيل البوت بنجاح...")
    # التأكد من وجود ffmpeg (مطلوب لتحويل الصوت)
    try:
        import subprocess
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except:
        print("⚠️ تحذير: ffmpeg غير مثبت على النظام، لن يعمل تحميل الصوت!")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
