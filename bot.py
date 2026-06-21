import os
import sys
import re
from telebot import TeleBot
from groq import Groq

# قراءة البيئة ديناميكياً لتجاوز حماية GitHub والعمل على السيرفر السحابي بأمان
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not TELEGRAM_BOT_TOKEN or not GROQ_API_KEY:
    print("❌ Error: Missing Environment Variables (TELEGRAM_BOT_TOKEN or GROQ_API_KEY)")
    sys.exit(1)

bot = TeleBot(TELEGRAM_BOT_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)
MODEL_NAME = "llama-3.1-8b-instant"

def compress_logs(raw_text):
    timestamp_pattern = re.compile(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
    hex_id_pattern = re.compile(r'0x[0-9a-fA-F]+|\b[0-9a-f]{8}-[0-9a-f]{4}-.+?\b')
    lines = raw_text.strip().split('\n')
    compressed_buckets = {}
    for line in lines:
        if not line: continue
        cleaned = timestamp_pattern.sub('[TIMESTAMP]', line)
        cleaned = hex_id_pattern.sub('[HEX_ID]', cleaned)
        cleaned = cleaned.strip()
        compressed_buckets[cleaned] = compressed_buckets.get(cleaned, 0) + 1
    optimized = []
    for template, count in compressed_buckets.items():
        if count > 1:
            optimized.append(f"{template} (Repeated {count} times)")
        else:
            optimized.append(template)
    return "\n".join(optimized)

def analyze_with_groq(raw_data):
    compressed_data = compress_logs(raw_data)
    system_prompt = (
        "You are an expert security and systems analyst. You will receive compressed logs. "
        "The notation '(Repeated X times)' means the event occurred multiple times consecutively. "
        "Analyze the data and provide a brief, actionable summary. Respond in Arabic."
    )
    completion = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Data to analyze:\n\n{compressed_data}"}
        ],
        model=MODEL_NAME,
        temperature=0.2
    )
    return completion.choices[0].message.content

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "⚡ *مرحباً بك في بوت Headroom-Groq!* 📉\n\n"
        "أنا بوت أمني ذكي مدعوم بأتمتة تصفية البيانات وسحابة Groq.\n\n"
        "📥 *كيفية الاستخدام:*\n"
        "قم بإرسال ملف سجلات (`.txt` أو `.log`) أو انسخ النص مباشرة هنا، وسأقوم بضغطه وتحليله أمنياً بلمح البصر!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    try:
        status_msg = bot.reply_to(message, "📥 جاري تحميل الملف ومعالجته دلالياً...")
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        raw_data = downloaded_file.decode('utf-8')
        bot.edit_message_text("📉 تم ضغط السياق بنجاح. جاري الاستعلام من Groq API...", message.chat.id, status_msg.message_id)
        analysis = analyze_with_groq(raw_data)
        response = (
            f"📊 *تقرير التحليل الأمني المطور*\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"{analysis}\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📉 تم توفير حجم البيانات بذكاء قبل الإرسال البرمجي."
        )
        bot.edit_message_text(response, message.chat.id, status_msg.message_id, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء المعالجة: {str(e)}")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    try:
        status_msg = bot.reply_to(message, "⚡ جاري تحليل النص المرسل...")
        analysis = analyze_with_groq(message.text)
        response = (
            f"📊 *تحليل أمني فوري:*\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"{analysis}"
        )
        bot.edit_message_text(response, message.chat.id, status_msg.message_id, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {str(e)}")

if __name__ == "__main__":
    print("🚀 Cloud Production Bot Engine Started...")
    bot.infinity_polling()
