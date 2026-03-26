
from flask import Flask, request, jsonify
import telebot
import json
import os
import re
from datetime import datetime
from telebot.types import Update

# ========== إعدادات البوت ==========
BOT_TOKEN = "8699825523:AAGNlTsUFTAi1-PAQZXlcAmKIhyVlAkKLpo"
ADMIN_ID = 5992411452

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ملف حفظ المنشورات
POSTS_FILE = "posts.json"

# ========== دوال حفظ وجلب المنشورات ==========
def load_posts():
    """جلب المنشورات من الملف"""
    try:
        if os.path.exists(POSTS_FILE):
            with open(POSTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return []

def save_posts(posts):
    """حفظ المنشورات في الملف"""
    try:
        with open(POSTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
    except:
        pass

def detect_platform(url):
    """تحديد المنصة من الرابط"""
    if 'youtube.com' in url or 'youtu.be' in url:
        return 'youtube'
    elif 'twitter.com' in url or 'x.com' in url:
        return 'twitter'
    elif 'tiktok.com' in url:
        return 'tiktok'
    elif 'instagram.com' in url:
        return 'instagram'
    elif 't.me' in url or 'telegram.me' in url:
        return 'telegram'
    else:
        return 'other'

def get_platform_emoji(platform):
    """أيقونة المنصة"""
    emojis = {
        'youtube': '📺',
        'twitter': '🐦',
        'tiktok': '📷',
        'instagram': '📸',
        'telegram': '💬',
        'other': '🔗'
    }
    return emojis.get(platform, '🔗')

def add_post(url, platform):
    """إضافة منشور جديد"""
    posts = load_posts()
    
    post_data = {
        'id': len(posts) + 1,
        'url': url,
        'platform': platform,
        'created_at': datetime.now().isoformat(),
        'title': get_title_from_url(url, platform)
    }
    
    posts.insert(0, post_data)
    save_posts(posts)
    return post_data

def get_title_from_url(url, platform):
    """استخراج عنوان بسيط من الرابط"""
    titles = {
        'youtube': '🎬 فيديو يوتيوب جديد',
        'twitter': '🐦 تغريدة جديدة',
        'tiktok': '📱 فيديو تيك توك',
        'instagram': '📸 منشور انستقرام',
        'telegram': '💬 منشور تليجرام',
        'other': '🔗 رابط جديد'
    }
    return titles.get(platform, '🔗 رابط جديد')

def delete_post_by_id(post_id):
    """حذف منشور حسب الرقم"""
    posts = load_posts()
    new_posts = [p for p in posts if p['id'] != post_id]
    
    if len(new_posts) == len(posts):
        return False
    
    save_posts(new_posts)
    return True

# ========== أوامر البوت ==========

@bot.message_handler(commands=['start'])
def start_command(message):
    """رسالة الترحيب"""
    bot.reply_to(message, """
🎯 *بوت إدارة المنشورات*

✨ *مرحباً بك!*

📝 *الأوامر المتاحة:*

• أرسل *رابط* مباشرة → إضافة منشور جديد
• `/lista` → عرض جميع المنشورات
• `/delete [رقم]` → حذف منشور (مثال: /delete 5)
• `/clear` → حذف جميع المنشورات
• `/help` → عرض هذه المساعدة

👑 *ملاحظة:* أنت الأدمن الوحيد الذي يمكنه إضافة وحذف المنشورات

🔗 *للمطورين:* 
• `/api` → تصدير البيانات بصيغة JSON
    """, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def help_command(message):
    """عرض المساعدة"""
    start_command(message)

@bot.message_handler(commands=['lista'])
def list_posts_command(message):
    """عرض جميع المنشورات"""
    # التحقق من أن المرسل هو الأدمن
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔ غير مصرح لك! هذا الأمر للأدمن فقط")
        return
    
    posts = load_posts()
    
    if not posts:
        bot.reply_to(message, "📭 *لا يوجد منشورات حالياً*\n\nأرسل رابطاً لإضافة منشور جديد", parse_mode='Markdown')
        return
    
    text = "📋 *قائمة المنشورات:*\n\n"
    for i, post in enumerate(posts[:30], 1):
        emoji = get_platform_emoji(post['platform'])
        title = post.get('title', 'منشور')[:35]
        created = post['created_at'][:16].replace('T', ' ')
        
        text += f"{i}. {emoji} *{title}*\n"
        text += f"   🆔 رقم: `{post['id']}` | 📅 {created}\n"
        text += f"   🔗 [الرابط]({post['url']})\n\n"
    
    # إذا كان هناك أكثر من 30 منشور
    if len(posts) > 30:
        text += f"\n*و {len(posts) - 30} منشورات أخرى...*"
    
    bot.reply_to(message, text, parse_mode='Markdown', disable_web_page_preview=True)

@bot.message_handler(commands=['delete'])
def delete_post_command(message):
    """حذف منشور حسب الرقم"""
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔ غير مصرح لك! هذا الأمر للأدمن فقط")
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ *طريقة الاستخدام:*\n`/delete 5`\n\n(5 هو رقم المنشور)", parse_mode='Markdown')
            return
        
        post_id = int(parts[1])
        
        # البحث عن المنشور للتأكد من وجوده
        posts = load_posts()
        post_exists = any(p['id'] == post_id for p in posts)
        
        if not post_exists:
            bot.reply_to(message, f"❌ *المنشور رقم {post_id} غير موجود*\n\nاستخدم `/lista` لرؤية المنشورات", parse_mode='Markdown')
            return
        
        # حذف المنشور
        success = delete_post_by_id(post_id)
        
        if success:
            bot.reply_to(message, f"✅ *تم حذف المنشور رقم {post_id} بنجاح*", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"❌ *فشل حذف المنشور رقم {post_id}*", parse_mode='Markdown')
            
    except ValueError:
        bot.reply_to(message, "❌ *خطأ:* الرقم غير صحيح\n\nمثال: `/delete 5`", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ *خطأ:* {str(e)}", parse_mode='Markdown')

@bot.message_handler(commands=['clear'])
def clear_all_command(message):
    """حذف جميع المنشورات"""
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔ غير مصرح لك! هذا الأمر للأدمن فقط")
        return
    
    posts = load_posts()
    count = len(posts)
    
    if count == 0:
        bot.reply_to(message, "📭 *لا يوجد منشورات لحذفها*", parse_mode='Markdown')
        return
    
    save_posts([])
    bot.reply_to(message, f"🗑️ *تم حذف جميع المنشورات* ({count} منشور)", parse_mode='Markdown')

@bot.message_handler(commands=['api'])
def api_command(message):
    """تصدير البيانات بصيغة JSON"""
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔ غير مصرح لك!")
        return
    
    posts = load_posts()
    data = {
        'posts': posts,
        'count': len(posts),
        'last_update': datetime.now().isoformat(),
        'admin_id': ADMIN_ID
    }
    
    # حفظ الملف مؤقتاً
    temp_file = "posts_export.json"
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    with open(temp_file, 'rb') as f:
        bot.send_document(
            message.chat.id, 
            f, 
            caption=f"📊 *بيانات المنشورات*\n\n📝 عدد المنشورات: {len(posts)}\n🕐 آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            parse_mode='Markdown'
        )
    
    # حذف الملف المؤقت
    os.remove(temp_file)

@bot.message_handler(func=lambda m: True)
def handle_url_message(message):
    """معالجة الروابط المرسلة"""
    # التحقق من أن المرسل هو الأدمن
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔ *غير مصرح لك!*\n\nأنت لست الأدمن، لا يمكنك إضافة منشورات", parse_mode='Markdown')
        return
    
    # استخراج الروابط من الرسالة
    urls = re.findall(r'(https?://[^\s]+)', message.text)
    
    if not urls:
        bot.reply_to(message, "❌ *لم أجد رابط في الرسالة!*\n\nأرسل رابط المنشور فقط", parse_mode='Markdown')
        return
    
    url = urls[0]
    
    # تحديد المنصة
    platform = detect_platform(url)
    emoji = get_platform_emoji(platform)
    
    # إضافة المنشور
    post = add_post(url, platform)
    
    # إرسال تأكيد
    bot.reply_to(message, f"""
✅ *تم إضافة المنشور بنجاح!*

{emoji} *{post['title']}*
🆔 رقم: `{post['id']}`
📅 الوقت: {post['created_at'][:16].replace('T', ' ')}
🔗 [اضغط للمشاهدة]({url})

📋 إجمالي المنشورات: {len(load_posts())}
    """, parse_mode='Markdown', disable_web_page_preview=True)

# ========== API Endpoints للتطبيق ==========

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    return '''
    <html>
        <head>
            <title>OSLN Bot - Post Manager</title>
            <style>
                body { font-family: Arial; text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
                h1 { font-size: 48px; }
                .status { background: rgba(255,255,255,0.2); padding: 20px; border-radius: 10px; margin: 20px auto; max-width: 500px; }
                a { color: #ffd700; }
            </style>
        </head>
        <body>
            <h1>🚀 OSLN Bot</h1>
            <div class="status">
                <h2>✅ البوت يعمل بنجاح</h2>
                <p>بوت إدارة المنشورات شغال 24/7</p>
                <p>📊 <a href="/posts">عرض المنشورات (API)</a></p>
            </div>
        </body>
    </html>
    '''

@app.route('/posts')
def get_posts():
    """API لجلب المنشورات للتطبيق"""
    posts = load_posts()
    return jsonify({
        'success': True,
        'count': len(posts),
        'posts': posts,
        'last_update': datetime.now().isoformat()
    })

@app.route('/posts/latest')
def get_latest_posts():
    """جلب أحدث 10 منشورات"""
    posts = load_posts()
    return jsonify({
        'success': True,
        'count': min(10, len(posts)),
        'posts': posts[:10]
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook لتلقي تحديثات تليجرام"""
    try:
        json_str = request.get_data().decode('UTF-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return 'OK', 200
    except Exception as e:
        print(f"Webhook error: {e}")
        return 'Error', 500

# ========== تشغيل البوت ==========
if __name__ == '__main__':
    print("🚀 OSLN Bot is starting...")
    print(f"🤖 Bot Token: {BOT_TOKEN[:10]}...")
    print(f"👑 Admin ID: {ADMIN_ID}")
    print(f"📁 Posts file: {POSTS_FILE}")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
