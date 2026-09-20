import telebot
import os
import json
import subprocess
import time
import signal
import re
import sys
import shutil
import uuid
from threading import Lock
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# psutil kütüphanesi güvenli şekilde kontrol ediliyor
HAS_PSUTIL = False
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'psutil'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        import psutil
        HAS_PSUTIL = True
    except Exception:
        HAS_PSUTIL = False

# Buraya BotFather'dan aldığın YENİ Token değerini yazın
API_KEY = '8961710042:AAFyPg0OPrJPEU1ZKOLOroTFiJua-2RLmZg' 
ADMIN_ID = 8687183701
SCRIPT_FOLDER = 'user_scripts'
DATA_FILE = 'user_data.json'
SETTINGS_FILE = 'settings.json'
BANNED_FILE = 'banned_users.json'
USERS_FILE = 'all_users.json'

# Zorunlu Kanal Bilgileri
CHANNEL_ID = -1004472784027
CHANNEL_URL = 'https://t.me/YxceBerrxk'

bot = telebot.TeleBot(API_KEY)
os.makedirs(SCRIPT_FOLDER, exist_ok=True)

# Veri yapısı: { "user_id": { "script_id": { ... } } }
user_data = {}
cooldowns = {}
lock = Lock()
admin_states = {} 

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        user_data = json.load(f)

maintenance_mode = False
if os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, 'r') as f:
        maintenance_mode = json.load(f).get("maintenance", False)

banned_users = []
if os.path.exists(BANNED_FILE):
    with open(BANNED_FILE, 'r') as f:
        banned_users = json.load(f)

all_users = set()
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'r') as f:
        all_users = set(json.load(f))

def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(user_data, f)

def save_settings():
    with open(SETTINGS_FILE, 'w') as f:
        json.dump({"maintenance": maintenance_mode}, f)

def save_banned():
    with open(BANNED_FILE, 'w') as f:
        json.dump(banned_users, f)

def save_users():
    with open(USERS_FILE, 'w') as f:
        json.dump(list(all_users), f)

def add_user(user_id):
    if user_id not in all_users:
        all_users.add(user_id)
        save_users()

def stop_specific_script(user_id, script_id):
    str_uid = str(user_id)
    if str_uid in user_data and script_id in user_data[str_uid]:
        info = user_data[str_uid][script_id]
        if "pid" in info:
            try:
                if HAS_PSUTIL:
                    p = psutil.Process(info["pid"])
                    for proc in p.children(recursive=True):
                        proc.terminate()
                    p.terminate()
                else:
                    os.kill(info["pid"], signal.SIGTERM)
            except Exception:
                pass
        file_path = info.get("file")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        log_path = file_path + ".log" if file_path else ""
        if log_path and os.path.exists(log_path):
            try:
                os.remove(log_path)
            except Exception:
                pass
                
        del user_data[str_uid][script_id]
        if not user_data[str_uid]:
            del user_data[str_uid]
        save_data()

def stop_all_user_scripts(user_id):
    str_uid = str(user_id)
    if str_uid in user_data:
        script_ids = list(user_data[str_uid].keys())
        for sid in script_ids:
            stop_specific_script(user_id, sid)

def check_subscription(user_id):
    if user_id == ADMIN_ID:
        return True
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception:
        pass
    return False

def get_channel_markup():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 Kanalım", url=CHANNEL_URL))
    markup.add(InlineKeyboardButton("✅ Üye Oldum Kontrol Et", callback_data="check_sub"))
    return markup

def create_main_menu(is_admin=False):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📁 Bot Ekle", callback_data="add_file"),
        InlineKeyboardButton("📂 Botlarım / Yönet", callback_data="show_file")
    )
    markup.add(
        InlineKeyboardButton("📊 Liderlik Tablosu", callback_data="leaderboard"),
        InlineKeyboardButton("❓ SSS (Nasıl Kullanılır?)", callback_data="faq_menu")
    )
    markup.add(
        InlineKeyboardButton("🎫 Destek / Ticket", callback_data="create_ticket"),
        InlineKeyboardButton("👨‍💻 ADMİN", url="http://t.me/CxmeBackk")
    )
    if is_admin:
        markup.add(InlineKeyboardButton("⚙️ Admin Paneli", callback_data="admin_panel"))
    return markup

def create_admin_menu():
    markup = InlineKeyboardMarkup()
    status_text = "🟢 Bakım Modu: Kapalı" if not maintenance_mode else "🔴 Bakım Modu: Açık"
    markup.add(InlineKeyboardButton(status_text, callback_data="toggle_maintenance"))
    markup.add(
        InlineKeyboardButton("👥 Kullanıcı Listesi", callback_data="admin_users"),
        InlineKeyboardButton("⚡ Aktiflik & Performans", callback_data="admin_active")
    )
    markup.add(
        InlineKeyboardButton("🚫 Kullanıcı Banla", callback_data="admin_ban"),
        InlineKeyboardButton("✅ Ban Kaldır", callback_data="admin_unban")
    )
    markup.add(
        InlineKeyboardButton("📢 Toplu Duyuru Yap", callback_data="admin_broadcast")
    )
    markup.add(InlineKeyboardButton("🔙 Ana Menüye Dön", callback_data="back_to_main"))
    return markup

BUILT_IN_MODULES = {
    'os', 'sys', 'json', 'time', 'signal', 'threading', 'subprocess', 
    'math', 'random', 'datetime', 're', 'collections', 'itertools', 
    'functools', 'pathlib', 'urllib', 'http', 'socket', 'asyncio', 'logging', 'atexit', 'shutil', 'psutil', 'uuid'
}

PACKAGE_MAPPING = {
    'telegram': 'python-telegram-bot'
}

def install_requirements(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        imports = re.findall(r'^(?:\s*)?(?:import|from)\s+([a-zA-Z0-9_]+)', content, re.MULTILINE)
        
        for module in set(imports):
            if module not in BUILT_IN_MODULES:
                pip_package = PACKAGE_MAPPING.get(module, module)
                if module == 'telegram':
                    subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', 'telegram', 'python-telegram-bot'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', pip_package], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        print(f"Kütüphane yüklenirken hata oluştu: {e}")

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    add_user(user_id)

    if user_id in banned_users:
        bot.send_message(user_id, "❌ Botu kullanmanız admin tarafından engellenmiştir.")
        return

    if maintenance_mode and user_id != ADMIN_ID:
        bot.send_message(user_id, "🛠️ Bot şu anda bakımdadır. Lütfen daha sonra tekrar deneyin.")
        return
    
    if not check_subscription(user_id):
        bot.send_message(
            user_id,
            "⚠️ Botu kullanabilmek için öncelikle **Kanalım** adlı kanalımıza abone olmanız gerekmektedir.\n\nAbone olduktan sonra aşağıdaki **Üye Oldum Kontrol Et** butonuna basın.",
            reply_markup=get_channel_markup(),
            parse_mode="Markdown"
        )
        return

    is_admin = (user_id == ADMIN_ID)
    bot.send_message(
        user_id, 
        "🤖 **VDS Çoklu Bot Paneline Hoş Geldiniz!**\n\nBu sistem üzerinden aynı anda **birden fazla Python botu** çalıştırabilirsiniz. Aşağıdaki menüyü kullanabilirsiniz:", 
        reply_markup=create_main_menu(is_admin), 
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['admin'])
def handle_admin_command(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        return
    bot.send_message(user_id, "⚙️ **Admin Paneline Hoş Geldiniz**", reply_markup=create_admin_menu(), parse_mode="Markdown")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    user_id = message.from_user.id
    add_user(user_id)

    if user_id in banned_users:
        bot.reply_to(message, "❌ Botu kullanmanız engellenmiştir.")
        return

    if maintenance_mode and user_id != ADMIN_ID:
        bot.reply_to(message, "🛠️ Bot şu anda bakım modundadır.")
        return
    
    if not check_subscription(user_id):
        bot.reply_to(message, "⚠️ Lütfen önce zorunlu kanalımıza abone olun!", reply_markup=get_channel_markup())
        return

    now = time.time()
    if user_id in cooldowns and now - cooldowns[user_id] < 5:
        bot.reply_to(message, "Lütfen yeni bir dosya yüklemeden önce 5 saniye bekleyin...")
        return
    cooldowns[user_id] = now

    doc = message.document
    if not doc.file_name.endswith('.py'):
        bot.reply_to(message, "❌ Sadece .py uzantılı Python dosyalarını kabul ediyorum.")
        return

    script_id = str(uuid.uuid4())[:8]
    with lock:
        file_info = bot.get_file(doc.file_id)
        downloaded = bot.download_file(file_info.file_path)

        local_path = os.path.join(SCRIPT_FOLDER, f"{user_id}_{script_id}_{doc.file_name}")
        with open(local_path, 'wb') as f:
            f.write(downloaded)

        bot.reply_to(message, "🔄 Gerekli kütüphaneler kontrol ediliyor ve yükleniyor...")
        install_requirements(local_path)

        try:
            log_path = local_path + ".log"
            with open(log_path, "w") as log_file:
                proc = subprocess.Popen(
                    [sys.executable, local_path],
                    stdout=log_file,
                    stderr=log_file,
                    text=True
                )
            
            time.sleep(2)
            if proc.poll() is not None:
                with open(log_path, "r") as log_file:
                    err_output = log_file.read()
                bot.reply_to(message, f"❌ Bot hemen kapandı! Hata detayı:\n{err_output[:500]}")
                if os.path.exists(local_path):
                    os.remove(local_path)
                return

            str_uid = str(user_id)
            if str_uid not in user_data:
                user_data[str_uid] = {}

            user_data[str_uid][script_id] = {
                "file": local_path,
                "file_name": doc.file_name,
                "pid": proc.pid,
                "time": int(time.time())
            }
            save_data()
            bot.reply_to(message, f"✅ Bot başarıyla yüklendi ve arka planda çalıştırıldı!\n\n📌 **Dosya:** {doc.file_name}\n🆔 **PID:** {proc.pid}\n🔑 **Script ID:** `{script_id}`", parse_mode="Markdown")
        except Exception as e:
            bot.reply_to(message, f"❌ Hata oluştu: {e}")
            if os.path.exists(local_path):
                os.remove(local_path)

@bot.message_handler(func=lambda m: True)
def handle_all_text_inputs(message):
    user_id = message.from_user.id
    text = message.text.strip() if message.text else ""
    state = admin_states.get(user_id)

    if user_id == ADMIN_ID and message.reply_to_message:
        replied_text = message.reply_to_message.text or message.reply_to_message.caption or ""
        match = re.search(r"Kullanıcı ID:\s*`?(\d+)`?", replied_text)
        if match:
            target_user_id = int(match.group(1))
            try:
                bot.send_message(target_user_id, f"💬 **Yetkiliden Destek Yanıtı:**\n\n{text}")
                bot.reply_to(message, f"✅ Yanıt `{target_user_id}` ID'li kullanıcıya iletildi.", parse_mode="Markdown")
            except Exception as e:
                bot.reply_to(message, f"❌ Kullanıcıya mesaj gönderilemedi: {e}")
            return

    if user_id == ADMIN_ID and state and state.startswith("reply_ticket_"):
        target_user_id = int(state.split("_")[2])
        try:
            bot.send_message(target_user_id, f"💬 **Yetkiliden Destek Yanıtı:**\n\n{text}")
            bot.reply_to(message, f"✅ Yanıt `{target_user_id}` ID'li kullanıcıya iletildi.", parse_mode="Markdown")
        except Exception as e:
            bot.reply_to(message, f"❌ Kullanıcıya mesaj gönderilemedi: {e}")
        del admin_states[user_id]
        return

    if user_id == ADMIN_ID and state == "ban":
        try:
            target_id = int(text)
            if target_id == ADMIN_ID:
                bot.reply_to(message, "⚠️ Kendinizi banlayamazsınız!")
            elif target_id in banned_users:
                bot.reply_to(message, "ℹ️ Bu kullanıcı zaten banlı.")
            else:
                banned_users.append(target_id)
                save_banned()
                stop_all_user_scripts(target_id)
                bot.reply_to(message, f"✅ `{target_id}` ID'li kullanıcı banlandı ve tüm botları durduruldu.", parse_mode="Markdown")
        except ValueError:
            bot.reply_to(message, "❌ Geçersiz ID formatı.")
        del admin_states[user_id]

    elif user_id == ADMIN_ID and state == "unban":
        try:
            target_id = int(text)
            if target_id in banned_users:
                banned_users.remove(target_id)
                save_banned()
                bot.reply_to(message, f"✅ `{target_id}` ID'li kullanıcının banı kaldırıldı.", parse_mode="Markdown")
            else:
                bot.reply_to(message, "ℹ️ Bu kullanıcı ban listesinde değil.")
        except ValueError:
            bot.reply_to(message, "❌ Geçersiz ID formatı.")
        del admin_states[user_id]

    elif user_id == ADMIN_ID and state == "broadcast":
        del admin_states[user_id]
        success, fail = 0, 0
        bot.reply_to(message, "📢 Toplu duyuru gönderiliyor...")
        for uid in all_users:
            try:
                bot.send_message(uid, f"📢 **Yönetici Duyurusu:**\n\n{text}", parse_mode="Markdown")
                success += 1
            except Exception:
                fail += 1
        bot.send_message(ADMIN_ID, f"📊 **Duyuru Tamamlandı!**\n\n✅ Başarılı: {success}\n❌ Başarısız: {fail}")

    elif state == "ticket":
        ticket_markup = InlineKeyboardMarkup()
        ticket_markup.add(InlineKeyboardButton("💬 Yanıtla", callback_data=f"reply_to_{user_id}"))
        ticket_msg = f"🎫 **Yeni Destek Mesajı (Ticket)**\n\n👤 **Kullanıcı ID:** `{user_id}`\n💬 **Mesaj:**\n{text}"
        try:
            bot.send_message(ADMIN_ID, ticket_msg, reply_markup=ticket_markup, parse_mode="Markdown")
            bot.reply_to(message, "✅ Destek mesajınız admine iletildi!")
        except Exception:
            bot.reply_to(message, "❌ Mesaj gönderilemedi.")
        del admin_states[user_id]

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    data = call.data

    if data.startswith("reply_to_"):
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Yetkiniz yok!", show_alert=True)
            return
        target_uid = data.split("_")[2]
        admin_states[user_id] = f"reply_ticket_{target_uid}"
        bot.answer_callback_query(call.id)
        bot.send_message(user_id, f"✍️ `{target_uid}` ID'li kullanıcıya yanıtınızı yazın:", parse_mode="Markdown")
        return

    if data == "check_sub":
        if check_subscription(user_id):
            bot.answer_callback_query(call.id, "✅ Onaylandı!", show_alert=True)
            is_admin = (user_id == ADMIN_ID)
            bot.send_message(user_id, "🤖 **VDS Çoklu Bot Paneline Hoş Geldiniz!**", reply_markup=create_main_menu(is_admin), parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, "❌ Henüz kanala abone değilsiniz!", show_alert=True)
        return

    if data == "faq_menu":
        faq_text = (
            "❓ **Sık Sorulan Sorular**\n\n"
            "**S: Birden fazla bot çalıştırabilir miyim?**\n"
            "C: Evet! İstediğiniz kadar `.py` uzantılı dosya yükleyerek aynı anda birden fazla botu aktif tutabilirsiniz.\n\n"
            "**S: Botlarımı nasıl yönetebilirim?**\n"
            "C: '📂 Botlarım / Yönet' butonuna basarak çalışan tüm botlarınızı listeleyebilir, dilediğinizi durdurabilirsiniz."
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Ana Menüye Dön", callback_data="back_to_main_user"))
        bot.edit_message_text(faq_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        return

    if data == "leaderboard":
        total_users_count = len(all_users)
        active_bots_count = sum(len(bots) for bots in user_data.values())
        lb_text = (
            "📊 **İstatistik Tablosu**\n\n"
            f"👥 **Toplam Kullanıcı:** `{total_users_count}`\n"
            f"⚡ **Aktif Çalışan Bot Sayısı:** `{active_bots_count}`"
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Ana Menüye Dön", callback_data="back_to_main_user"))
        bot.edit_message_text(lb_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        return

    if data == "create_ticket":
        admin_states[user_id] = "ticket"
        bot.answer_callback_query(call.id)
        bot.send_message(user_id, "🎫 **Destek Talebi**\n\nMesajınızı tek mesaj halinde yazıp gönderin:")
        return

    if data == "back_to_main_user":
        is_admin = (user_id == ADMIN_ID)
        bot.edit_message_text("🤖 **VDS Çoklu Bot Paneline Hoş Geldiniz!**", call.message.chat.id, call.message.message_id, reply_markup=create_main_menu(is_admin), parse_mode="Markdown")
        return

    # Tekil Bot Yönetimi (Durdurma / Silme)
    if data.startswith("stop_bot_"):
        script_id = data.split("_")[2]
        stop_specific_script(user_id, script_id)
        bot.answer_callback_query(call.id, "🗑️ Bot durduruldu ve silindi!", show_alert=True)
        
        # Listeyi güncelle
        user_scripts = user_data.get(str(user_id), {})
        if not user_scripts:
            bot.edit_message_text("ℹ️ Şu anda aktif çalışan bir botunuz bulunmuyor.", call.message.chat.id, call.message.message_id, reply_markup=create_main_menu(user_id == ADMIN_ID))
        else:
            markup = InlineKeyboardMarkup()
            text = "📂 **Aktif Botlarınız:**\n\n"
            for sid, info in user_scripts.items():
                text += f"📌 `{info['file_name']}` (PID: {info['pid']})\n"
                markup.add(InlineKeyboardButton(f"🗑️ Durdur: {info['file_name']}", callback_data=f"stop_bot_{sid}"))
            markup.add(InlineKeyboardButton("🔙 Ana Menü", callback_data="back_to_main_user"))
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        return

    # Admin Paneli İşlemleri
    if data.startswith("admin_") or data == "toggle_maintenance" or data == "back_to_main":
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Yetkiniz yok!", show_alert=True)
            return

        if data == "admin_panel":
            bot.edit_message_text("⚙️ **Admin Paneli**", call.message.chat.id, call.message.message_id, reply_markup=create_admin_menu(), parse_mode="Markdown")
        
        elif data == "toggle_maintenance":
            global maintenance_mode
            maintenance_mode = not maintenance_mode
            save_settings()
            status = "açıldı 🔴" if maintenance_mode else "kapatıldı 🟢"
            bot.answer_callback_query(call.id, f"Bakım modu {status}", show_alert=True)
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=create_admin_menu())

        elif data == "admin_users":
            total = len(all_users)
            text = f"👥 **Kayıtlı Toplam Kullanıcı:** `{total}`\n"
            bot.answer_callback_query(call.id)
            bot.send_message(user_id, text, parse_mode="Markdown")

        elif data == "admin_active":
            total_active = sum(len(bots) for bots in user_data.values())
            text = f"⚡ **Tüm Aktif Çalışan Botlar ({total_active}):**\n\n"
            for uid, bots in user_data.items():
                for sid, info in bots.items():
                    cpu_usage, memory_usage = "N/A", "N/A"
                    if HAS_PSUTIL:
                        try:
                            p = psutil.Process(info['pid'])
                            cpu_usage = f"{p.cpu_percent(interval=0.1):.1f}"
                            memory_usage = f"{p.memory_percent():.1f}"
                        except Exception:
                            pass
                    text += f"👤 User: `{uid}` | Bot: `{info['file_name']}`\n⚙️ PID: `{info['pid']}` | CPU: %`{cpu_usage}` RAM: %`{memory_usage}`\n------------------\n"
            if total_active == 0:
                text = "ℹ️ Aktif bot bulunmuyor."
            bot.answer_callback_query(call.id)
            bot.send_message(user_id, text, parse_mode="Markdown")

        elif data == "admin_ban":
            admin_states[user_id] = "ban"
            bot.answer_callback_query(call.id)
            bot.send_message(user_id, "🚫 Banlanacak kullanıcının **Telegram ID** değerini yazın:")

        elif data == "admin_unban":
            admin_states[user_id] = "unban"
            bot.answer_callback_query(call.id)
            bot.send_message(user_id, f"✅ Banı kaldırılacak ID'yi yazın:\nBanlılar: {banned_users}")

        elif data == "admin_broadcast":
            admin_states[user_id] = "broadcast"
            bot.answer_callback_query(call.id)
            bot.send_message(user_id, "📢 Duyuru mesajını yazın:")

        elif data == "back_to_main":
            bot.edit_message_text("🤖 **VDS Çoklu Bot Paneline Hoş Geldiniz!**", call.message.chat.id, call.message.message_id, reply_markup=create_main_menu(True), parse_mode="Markdown")
        return

    if user_id in banned_users:
        bot.answer_callback_query(call.id, "❌ Engellendiniz.", show_alert=True)
        return

    if maintenance_mode and user_id != ADMIN_ID:
        bot.answer_callback_query(call.id, "🛠️ Bakım modu aktif!", show_alert=True)
        return

    if not check_subscription(user_id):
        bot.answer_callback_query(call.id, "⚠️ Kanala abone olmalısınız!", show_alert=True)
        return

    if data == "add_file":
        bot.send_message(user_id, "📤 Çalıştırmak istediğiniz yeni `.py` dosyanızı buraya gönderin. (İstediğiniz kadar ekleyebilirsiniz)")
    elif data == "show_file":
        user_scripts = user_data.get(str(user_id), {})
        if not user_scripts:
            bot.send_message(user_id, "ℹ️ Şu anda aktif çalışan bir botunuz bulunmuyor.")
        else:
            markup = InlineKeyboardMarkup()
            text = "📂 **Aktif Botlarınız ve Yönetim Paneli:**\n\n"
            for sid, info in user_scripts.items():
                running_time = time.strftime('%H:%M:%S', time.localtime(info['time']))
                text += f"📌 **{info['file_name']}**\n   ⚙️ PID: `{info['pid']}` | ⏱️ `{running_time}`\n\n"
                markup.add(InlineKeyboardButton(f"🗑️ Durdur / Sil: {info['file_name']}", callback_data=f"stop_bot_{sid}"))
            markup.add(InlineKeyboardButton("🔙 Ana Menü", callback_data="back_to_main_user"))
            bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

import atexit
atexit.register(lambda: [stop_all_user_scripts(int(uid)) for uid in list(user_data.keys())])

print("VDS Çoklu Bot Paneli aktif ve çalışıyor.")

# Çakışmaları ve webhooks kalıntılarını temizle
try:
    bot.remove_webhook()
    time.sleep(1)
except Exception:
    pass

# Çakışma ve 409 hatalarını ele alan güvenli sonsuz döngü
while True:
    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        print(f"Hata yakalandı: {e}. 10 saniye sonra yeniden denenecek...")
        time.sleep(10)

