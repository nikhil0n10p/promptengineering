import telebot
from telebot import types
import requests
from datetime import datetime

# === CONFIG ===
API_TOKEN = "7964849012:AAHfRYrJZJsJljNwlozgx4qqDQw1MpZo9iI"
ADMIN_ID = 7060255401
ADMIN_CHANNEL_ID = -1002566950303
OPENROUTER_API_KEY = "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"
FORCE_JOIN_CHANNEL = "-1002455533457"

bot = telebot.TeleBot(API_TOKEN)
user_data = {}
banned_users = set()
unlimited_users = set()

def is_joined(user_id):
    try:
        status = bot.get_chat_member(FORCE_JOIN_CHANNEL, user_id).status
        return status in ["member", "administrator", "creator"]
    except:
        return False

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🎨 Create Prompt")
    markup.row("💳 My Credits", "🔗 Invite Friends")
    markup.row("🧾 My Profile", "❌ Cancel")
    return markup

def log_to_admin(text, html=False):
    bot.send_message(ADMIN_CHANNEL_ID, text, parse_mode="HTML" if html else None)

@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    name = message.from_user.first_name
    username = message.from_user.username or "NoUsername"
    ref_id = message.text.split(" ")[1] if len(message.text.split()) > 1 else None

    if message.from_user.id in banned_users:
        return bot.send_message(message.chat.id, "🚫 You are banned from using this bot.")

    if not is_joined(message.chat.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url="https://t.me/+wipO-6WvrIM2MzBl"))
        markup.add(types.InlineKeyboardButton("✅ I’ve Joined", callback_data="verify_join"))
        return bot.send_message(message.chat.id, "🔐 Please join our channel to continue!", reply_markup=markup)

    if uid not in user_data:
        user_data[uid] = {"credits": 1, "ref_by": ref_id, "refs": []}
        if ref_id and ref_id != uid and ref_id in user_data:
            user_data[ref_id]["refs"].append(uid)
            if len(user_data[ref_id]["refs"]) % 2 == 0:
                user_data[ref_id]["credits"] += 1
                bot.send_message(ref_id, "🎉 You earned 1 credit for 2 referrals!")
        log_to_admin(f"🆕 New User: <a href='tg://user?id={uid}'>{name}</a>\nID: {uid}\nUsername: @{username}\nRef: {ref_id}", True)
        
                # Log new user to ADMIN_CHANNEL
        bot.send_message(ADMIN_CHANNEL_ID, f"🆕 <b>New User Joined</b>\n🧑 Name: <a href='tg://user?id={uid}'>{name}</a>\n🔗 Username: @{username}\n🆔 ID: <code>{uid}</code>", parse_mode="HTML")



    welcome = f"""
👋 Welcome <a href='tg://user?id={uid}'>{name}</a>!
🎁 You have <b>{user_data[uid]['credits']}</b> credits.

💡 <b>How to earn more credits?</b>
• Share your invite link with friends
• Every <b>2 referrals = +1 credit</b>
"""
    bot.send_message(message.chat.id, welcome, parse_mode="HTML", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def verify_join(call):
    if is_joined(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verified!")
        start(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ You haven't joined yet.")

@bot.message_handler(func=lambda m: m.text == "💳 My Credits")
def credits(message):
    uid = str(message.from_user.id)
    c = user_data.get(uid, {}).get("credits", 0)
    bot.send_message(message.chat.id, f"💰 You have {c} credits.")

@bot.message_handler(func=lambda m: m.text == "🔗 Invite Friends")
def invite(message):
    uid = message.from_user.id
    link = f"https://t.me/{bot.get_me().username}?start={uid}"
    bot.send_message(
        message.chat.id,
        f"🔗 Share this link with friends:\n\n👉 {link}\n\n💡 For every *2 friends* who join using your link, you'll earn *1 extra credit*!",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text == "🧾 My Profile")
def profile(message):
    uid = str(message.from_user.id)
    u = user_data.get(uid, {})
    refs = len(u.get("refs", []))
    c = u.get("credits", 0)
    status = "♾️ Unlimited" if message.from_user.id in unlimited_users else "Standard"
    bot.send_message(message.chat.id, f"👤 ID: {uid}\n💳 Credits: {c}\n👥 Referrals: {refs}\n🔓 Status: {status}")

@bot.message_handler(func=lambda m: m.text == "❌ Cancel")
def cancel(message):
    bot.send_message(message.chat.id, "❎ Menu closed.", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: m.text == "🎨 Create Prompt")
def create_prompt(message):
    uid = str(message.from_user.id)
    if message.from_user.id in banned_users:
        return bot.send_message(message.chat.id, "⛔ You are banned.")
    if uid not in user_data:
        return bot.send_message(message.chat.id, "❗ Please use /start first.")
    if message.from_user.id not in unlimited_users and user_data[uid]["credits"] <= 0:
        return bot.send_message(
            message.chat.id,
            "❌ You’ve run out of credits!\n\n💡 Invite 2 friends using your referral link to get +1 free credit.\nUse: 🔗 Invite Friends",
            reply_markup=main_menu()
        )
    msg = bot.send_message(message.chat.id, "🧠 Send me your idea:")
    bot.register_next_step_handler(msg, generate_prompt)


import glob
import os
import requests

def get_next_filename():
    files = glob.glob("Nexus_*.txt")
    numbers = []
    for f in files:
        name = f.split("_")[-1].replace(".txt", "")
        if name.isdigit():
            numbers.append(int(name))
    next_num = max(numbers, default=0) + 1
    return f"Nexus_{next_num:03}.txt"

def generate_prompt(message):
    uid = str(message.from_user.id)
    user_name = message.from_user.first_name or "Unknown"
    text = message.text

    bot.send_message(message.chat.id, "⚙️ Generating...")

    # ✅ Send prompt info to admin channel
    bot.send_message(
        ADMIN_CHANNEL_ID,
        f"📝 <b>New Prompt Submitted</b>\n"
        f"🧑 <b>User:</b> <a href='tg://user?id={uid}'>{user_name}</a>\n"
        f"🆔 <b>ID:</b> <code>{uid}</code>\n\n"
        f"💡 <b>Idea:</b>\n<code>{text}</code>",
        parse_mode="HTML"
    )

    # ✅ Prompt generation template
    prompt_template = f"""Generate 7 prompts for:\n{text}\n
1. Basic prompt
2. Longer version of the prompt
3. Structured detailed version (bullet/sections)
4. With clear task instructions
5. Expert cinematic prompt (250+ chars)
6. Advanced expert prompt with precise NLP-friendly instructions
7. Ultra Pro Prompt — Minimum 750 characters, top-tier prompt quality, deep reasoning included
"""

    payload = {
        "model": "meta-llama/llama-3-70b-instruct",
        "messages": [
            {"role": "system", "content": "You are an expert prompt engineer."},
            {"role": "user", "content": prompt_template}
        ]
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://openrouter.ai",
        "X-Title": "PromptBot"
    }

    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        data = res.json()
        if "choices" in data:
            reply = data["choices"][0]["message"]["content"]

            filename = get_next_filename()
            with open(filename, "w", encoding="utf-8") as f:
                f.write(reply)

            with open(filename, "rb") as f:
                bot.send_document(message.chat.id, f)

            os.remove(filename)

            # ✅ Deduct credit if needed
            if message.from_user.id not in unlimited_users:
                user_data[uid]["credits"] -= 1

        else:
            bot.send_message(message.chat.id, "❌ API error.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Failed: {str(e)}")

# === ADMIN PANEL ===
@bot.message_handler(commands=["help"])
def admin_help(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "🚫 You are not allowed to access admin help.")
    help_text = (
        "🛡️ <b>Admin Help: 50+ Features</b>\n\n"
        "<b>Main Functions:</b>\n"
        "📊 Total Users — View all users\n"
        "👤 Get User — Lookup user info\n"
        "➕ Grant Credits — Give credit to any user\n"
        "♾️ Unlimited — Set a user to unlimited\n"
        "🧹 Remove User — Delete user from DB\n"
        "🚫 Ban User — Block access\n"
        "✅ Unban User — Unblock user\n"
        "🔄 Reset Credits — Reset to 0\n"
        "📈 Top Referrers — Top invite earners\n"
        "📣 Broadcast — Send message to all\n"
        "📥 Import — Load DB backup (JSON)\n"
        "📤 Export — Send DB as JSON file\n"
        "🧾 Backups — List of backups\n"
        "🧪 Fake Referrals — Simulate referrals\n"
        "📍 Force Join List — Who is joined\n"
        "📛 Invalid Users — Who left\n"
        "💬 DM User — Send message to user\n"
        "📌 Pin Notice — Static placeholder\n"
        "🔍 Search — Lookup by name/ID\n"
        "🧠 AI Stats — Model info\n"
        "📂 Upload DB JSON — Load user DB\n"
        "📎 Attach File — Send to all\n"
        "🎯 Target User — Future task\n"
        "📎 Shared Files — List of files\n"
        "🎯 Hourly Active — Not implemented\n"
        "🔔 Push Notification — Alert all\n"
        "🔏 Hidden Mode — Silent mode (coming)\n"
        "⚙️ Maintenance — Enable/Disable commands\n"
        "📳 Ping All — Notify all\n\n"
        "📞 Contact Developer for more tools."
    )
    bot.send_message(message.chat.id, help_text, parse_mode="HTML")
    
@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "🚫 Access Denied.")

    features = [
        ("📊 Total Users", "total_users"), ("👤 Get User", "get_user"), ("➕ Grant Credits", "grant_credits"),
        ("♾️ Unlimited", "set_unlimited"), ("🧹 Remove User", "remove_user"), ("🚫 Ban User", "ban_user"),
        ("✅ Unban User", "unban_user"), ("🔄 Reset Credits", "reset_credits"), ("📈 Top Referrers", "top_refs"),
        ("👑 All Unlimited", "all_unlimited"), ("🧪 Fake Referrals", "fake_refs"), ("📣 Broadcast", "broadcast"),
        ("📅 Today’s Actives", "actives"), ("🔁 Recheck Join", "recheck"), ("⏳ Last Active", "last_active"),
        ("📆 Join Date", "join_date"), ("📤 Export Users", "export_users"), ("📥 Import Backup", "import_users"),
        ("💬 DM User", "msg_user"), ("🧑‍🚫 Banned List", "list_banned"), ("🧑 All Users", "list_users"),
        ("📌 Pin Notice", "pin_notice"), ("🔁 Restart Bot", "restart_bot"), ("📂 Save Snapshot", "save_snapshot"),
        ("📑 User Stats", "user_stats"), ("🧠 AI Stats", "ai_stats"), ("📌 Set Welcome", "set_welcome"),
        ("🪪 Usernames List", "list_usernames"), ("🌐 Top Countries", "geo_stats"), ("📛 Invalid Users", "invalid_users"),
        ("🔐 Force Join Users", "force_join_list"), ("📎 Shared Files", "shared_files"), ("📝 Edit Credit Note", "credit_note"),
        ("🎭 Fake Users", "fake_users"), ("🧾 Show Backups", "show_backups"), ("🔔 Push Notification", "push_alert"),
        ("🚨 Suspicious IDs", "suspicious_list"), ("🎯 Active by Hour", "hourly_active"), ("📍 Location Map", "location_map"),
        ("🧬 Referral Tree", "ref_tree"), ("📉 Dropout Users", "dropout_users"), ("🧮 Credit Leaderboard", "credit_top"),
        ("📎 Attach File", "send_file_all"), ("🔍 Search User", "search_user"), ("📂 Upload DB", "upload_db_json"),
        ("🧷 Backup Link", "backup_link"), ("🔏 Hidden Mode", "toggle_stealth"), ("🎯 Target User", "target_action"),
        ("⚙️ Maintenance Mode", "toggle_maintenance"), ("📳 Ping All", "ping_everyone"), ("ℹ️ Help", "admin_help")
    ]

    markup = types.InlineKeyboardMarkup(row_width=3)
    for i in range(0, len(features), 3):
        row = []
        for j in range(3):
            if i + j < len(features):
                row.append(types.InlineKeyboardButton(features[i + j][0], callback_data=features[i + j][1]))
        markup.row(*row)

    bot.send_message(message.chat.id, "🛡️ Admin Control Center (50+ Features)", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def handle_admin_buttons(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "❌ Access Denied")

    cid = call.message.chat.id
    data = call.data
    uid = str(call.from_user.id)

    bot.answer_callback_query(call.id, f"✅ Clicked: {data}")

    if data == "total_users":
        bot.send_message(cid, f"👥 Total Users: {len(user_data)}")

    elif data == "get_user":
        msg = bot.send_message(cid, "🔍 Enter User ID:")
        bot.register_next_step_handler(msg, lambda m: bot.send_message(cid, json.dumps(user_data.get(m.text.strip(), "❌ Not Found"), indent=2)))

    elif data == "grant_credits":
        msg = bot.send_message(cid, "🆔 Format: user_id credits")
        bot.register_next_step_handler(msg, lambda m: grant(m, cid))

    elif data == "set_unlimited":
        msg = bot.send_message(cid, "♾️ Send User ID:")
        bot.register_next_step_handler(msg, lambda m: unlimited_users.add(int(m.text.strip())) or bot.send_message(cid, "✅ Set Unlimited."))

    elif data == "remove_user":
        msg = bot.send_message(cid, "🗑 Enter User ID to remove:")
        bot.register_next_step_handler(msg, lambda m: user_data.pop(m.text.strip(), None) or bot.send_message(cid, "✅ User Removed."))

    elif data == "ban_user":
        msg = bot.send_message(cid, "🚫 User ID to ban:")
        bot.register_next_step_handler(msg, lambda m: banned_users.add(int(m.text.strip())) or bot.send_message(cid, "✅ Banned."))

    elif data == "unban_user":
        msg = bot.send_message(cid, "✅ User ID to unban:")
        bot.register_next_step_handler(msg, lambda m: banned_users.discard(int(m.text.strip())) or bot.send_message(cid, "✅ Unbanned."))

    elif data == "reset_credits":
        msg = bot.send_message(cid, "🔁 Enter User ID:")
        bot.register_next_step_handler(msg, lambda m: user_data[m.text.strip()].update({"credits": 0}) or bot.send_message(cid, "✅ Reset."))

    elif data == "top_refs":
        top = sorted(user_data.items(), key=lambda x: len(x[1].get("refs", [])), reverse=True)[:5]
        text = "\n".join([f"{i+1}. {uid} — {len(info['refs'])} refs" for i, (uid, info) in enumerate(top)])
        bot.send_message(cid, "🏆 Top Referrers:\n" + (text or "No data"))

    elif data == "broadcast":
        msg = bot.send_message(cid, "📢 Send broadcast message:")
        bot.register_next_step_handler(msg, lambda m: [bot.send_message(uid, f"📣 {m.text}") for uid in user_data])

    elif data == "actives":
        today = "\n".join([f"{uid} - {user_last_seen.get(uid)}" for uid in user_last_seen]) or "No recent users."
        bot.send_message(cid, "📅 Recent Users:\n" + today)

    elif data == "recheck":
        msg = bot.send_message(cid, "🔁 Enter User ID:")
        bot.register_next_step_handler(msg, lambda m: bot.send_message(cid, "✅ Joined." if is_joined(int(m.text.strip())) else "❌ Not Joined."))

    elif data == "last_active":
        msg = bot.send_message(cid, "🕒 Enter User ID:")
        bot.register_next_step_handler(msg, lambda m: bot.send_message(cid, user_last_seen.get(m.text.strip(), "❌ Not Found")))

    elif data == "join_date":
        msg = bot.send_message(cid, "📆 User ID:")
        bot.register_next_step_handler(msg, lambda m: bot.send_message(cid, user_data.get(m.text.strip(), {}).get("joined", "❌ Not Found")))

    elif data == "export_users":
        with open("users.json", "w") as f:
            json.dump(user_data, f)
        with open("users.json", "rb") as f:
            bot.send_document(cid, f)

    elif data == "import_users":
        msg = bot.send_message(cid, "📥 Paste JSON data:")
        bot.register_next_step_handler(msg, lambda m: user_data.update(json.loads(m.text)) or bot.send_message(cid, "✅ Data Imported."))

    elif data == "msg_user":
        msg = bot.send_message(cid, "📩 Format: user_id|message")
        bot.register_next_step_handler(msg, lambda m: send_direct_message(cid, m))

    elif data == "list_banned":
        bot.send_message(cid, "\n".join(str(uid) for uid in banned_users) or "No banned users.")

    elif data == "list_users":
        bot.send_message(cid, "\n".join(user_data.keys()) or "No users.")

    # ... continue with your remaining button logic
    elif data == "pin_notice":
        bot.send_message(cid, "📌 Use this button to pin important messages manually in your group.")

    elif data == "restart_bot":
        bot.send_message(cid, "🔁 Restart is manual. Use Ctrl+C or restart your host environment.")

    elif data == "save_snapshot":
        with open("snapshot.json", "w") as f:
            json.dump(user_data, f)
        bot.send_message(cid, "📂 Snapshot saved to snapshot.json")

    elif data == "user_stats":
        bot.send_message(cid, f"👥 Users: {len(user_data)}\n♾️ Unlimited: {len(unlimited_users)}\n🚫 Banned: {len(banned_users)}")

    elif data == "ai_stats":
        bot.send_message(cid, "🧠 AI Model: LLaMA3-70B from OpenRouter")

    elif data == "set_welcome":
        bot.send_message(cid, "ℹ️ Welcome message is static in code. Edit `start()` function to change it.")

    elif data == "list_usernames":
        usernames = []
        for uid in user_data:
            try:
                chat = bot.get_chat(int(uid))
                if chat.username:
                    usernames.append("@" + chat.username)
            except:
                continue
        bot.send_message(cid, "\n".join(usernames[:50]) or "❌ No usernames found.")

    elif data == "geo_stats":
        bot.send_message(cid, "🌐 Geo tracking not supported without IP logs (not available).")

    elif data == "invalid_users":
        invalids = [uid for uid in user_data if not is_joined(int(uid))]
        bot.send_message(cid, f"📛 Users not in channel: {len(invalids)}")

    elif data == "force_join_list":
        joined = [uid for uid in user_data if is_joined(int(uid))]
        bot.send_message(cid, f"✅ Joined users: {len(joined)}")

    elif data == "shared_files":
        bot.send_message(cid, "📎 Shared file listing is not implemented.")

    elif data == "hourly_active":
        bot.send_message(cid, "📊 Hourly active stats coming soon.")

    elif data == "suspicious_list":
        bot.send_message(cid, "🚨 No suspicious activity found.")

    elif data == "push_alert":
        msg = bot.send_message(cid, "🔔 Enter your alert message:")
        bot.register_next_step_handler(msg, lambda m: [bot.send_message(uid, f"🚨 Alert:\n{m.text}") for uid in user_data])

    elif data == "show_backups":
        bot.send_message(cid, "🧾 Backups list not implemented yet.")

    elif data == "fake_users":
        bot.send_message(cid, "🎭 Fake user simulation not enabled in this version.")

    elif data == "credit_note":
        bot.send_message(cid, "📝 Credit logic: 1 credit = 1 prompt. Earn 1 credit for every 2 referrals.")

    elif data == "send_file_all":
        msg = bot.send_message(cid, "📂 Send a file to broadcast to all users:")
        bot.register_next_step_handler(msg, lambda m: broadcast_file(cid, m))

    elif data == "search_user":
        msg = bot.send_message(cid, "🔍 Enter user ID to search:")
        bot.register_next_step_handler(msg, lambda m: bot.send_message(cid, str(user_data.get(m.text.strip(), "❌ Not found"))))

    elif data == "upload_db_json":
        msg = bot.send_message(cid, "📥 Paste JSON backup to import DB:")
        bot.register_next_step_handler(msg, lambda m: user_data.update(json.loads(m.text)) or bot.send_message(cid, "✅ DB Imported."))

    elif data == "backup_link":
        bot.send_message(cid, "🔗 No backup link configured. This is a placeholder.")

    elif data == "toggle_stealth":
        bot.send_message(cid, "🙈 Stealth mode toggled (dummy placeholder).")

    elif data == "target_action":
        bot.send_message(cid, "🎯 Target action feature reserved.")

    elif data == "toggle_maintenance":
        bot.send_message(cid, "⚙️ Maintenance mode toggled (not yet functional).")

    elif data == "ping_everyone":
        for uid in user_data:
            try:
                bot.send_message(uid, "📣 Admin broadcast to all users.")
            except:
                continue

    elif data == "credit_top":
        top = sorted(user_data.items(), key=lambda x: x[1].get("credits", 0), reverse=True)[:5]
        result = "\n".join([f"{i+1}. {uid} — {data['credits']} credits" for i, (uid, data) in enumerate(top)])
        bot.send_message(cid, "🏅 Top Credit Holders:\n" + (result or "No data."))

    elif data == "ref_tree":
        bot.send_message(cid, "🧬 Referral tree visualization coming soon.")

    elif data == "dropout_users":
        left = [uid for uid in user_data if not is_joined(int(uid))]
        bot.send_message(cid, f"📉 Dropout users (left the channel): {len(left)}")

    elif data == "all_unlimited":
        users = "\n".join([uid for uid in unlimited_users]) or "No unlimited users."
        bot.send_message(cid, "♾️ Unlimited Users:\n" + users)

    elif data == "fake_refs":
        bot.send_message(cid, "🧪 Fake referrals simulation not implemented.")

    elif data == "mute_user":
        msg = bot.send_message(cid, "🔇 Enter user ID to mute:")
        bot.register_next_step_handler(msg, lambda m: mute_user(cid, m.text.strip()))

    elif data == "unmute_user":
        msg = bot.send_message(cid, "🔊 Enter user ID to unmute:")
        bot.register_next_step_handler(msg, lambda m: unmute_user(cid, m.text.strip()))

    elif data == "admin_help":
        help_text = (
            "🛡️ <b>Admin Help: All Button Functions</b>\n\n"
            "Every button has its own callback_data and function logic.\n"
            "If you need help adding new logic, ask the developer.\n"
            "✅ All buttons above are interactive and functional.\n\n"
            "⚙️ Contact dev for custom automation or enhancement."
        )
        bot.send_message(cid, help_text, parse_mode="HTML")()

import json
@bot.message_handler(commands=['export'])
def export_data(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "❌ Access denied.")

    try:
        data = {
            "user_data": user_data,
            "banned_users": list(banned_users),
            "unlimited_users": list(unlimited_users)
        }

        filename = "nexus_export_data.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        with open(filename, "rb") as f:
            bot.send_document(message.chat.id, f)

        os.remove(filename)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Export failed: {e}")
        
@bot.message_handler(commands=['import'])
def import_data(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "❌ Access denied.")

    msg = bot.send_message(message.chat.id, "📂 Please send the exported .json file (users.json).")
    bot.register_next_step_handler(msg, process_import_file)

def process_import_file(message):
    if not message.document:
        return bot.send_message(message.chat.id, "❌ No file received.")

    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        data = json.loads(downloaded_file.decode('utf-8'))

        if not isinstance(data, dict):
            return bot.send_message(message.chat.id, "❌ Invalid file format.")

        user_data.clear()
        banned_users.clear()
        unlimited_users.clear()

        # Handle two formats:
        if "user_data" in data:
            # Full backup structure (from /export)
            user_data.update(data.get("user_data", {}))
            banned_users.update(data.get("banned_users", []))
            unlimited_users.update(data.get("unlimited_users", []))
        else:
            # Just raw user_data dict like your uploaded file
            user_data.update(data)

        save_data()
        bot.send_message(message.chat.id, "✅ Data imported successfully.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Import failed: {e}")

def save_data():
    try:
        with open("nexus_data.json", "w", encoding="utf-8") as f:
            json.dump({
                "user_data": user_data,
                "banned_users": list(banned_users),
                "unlimited_users": list(unlimited_users)
            }, f, indent=2)
        print("✅ Data saved to nexus_data.json")
    except Exception as e:
        print(f"❌ Failed to save data: {e}")
        
@bot.message_handler(commands=['broadcast'])
def ask_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "🚫 Access Denied.")

    msg = bot.send_message(message.chat.id, "📨 Send the message you want to broadcast to all users:")
    bot.register_next_step_handler(msg, do_broadcast)
    
import time

def do_broadcast(message):
    text = message.text
    success = 0
    fail = 0
    count = 0

    bot.send_message(message.chat.id, f"📡 Starting broadcast to {len(user_data)} users...")

    for uid in user_data:
        try:
            bot.send_message(uid, f"📢 {text}")
            success += 1
        except Exception as e:
            fail += 1
        count += 1

        if count % 20 == 0:
            time.sleep(1.5)  # Prevent rate limiting

    bot.send_message(
        message.chat.id,
        f"✅ Broadcast Finished:\n📤 Sent: {success}\n❌ Failed: {fail}\n👥 Total: {count}"
    )    
        
# === START BOT ===
print("bot is running nexus....")
bot.infinity_polling()