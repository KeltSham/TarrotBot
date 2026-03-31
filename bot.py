import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, LabeledPrice
import sqlite3
import datetime
import threading
import time

# --- НАСТРОЙКИ ---
TOKEN = "REDACTED_TOKEN"
WEB_APP_URL = "https://KeltSham.github.io/TarrotBot/"
ADMIN_ID = 1491094235
# -----------------

bot = telebot.TeleBot(TOKEN)

# Инициализация Базы Данных SQLite
conn = sqlite3.connect('users.db', check_same_thread=False)
with conn:
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            trial_end_date TIMESTAMP,
            sub_end_date TIMESTAMP,
            push_enabled INTEGER DEFAULT 1
        )
    ''')
    try:
        conn.execute('ALTER TABLE users ADD COLUMN push_enabled INTEGER DEFAULT 1')
    except sqlite3.OperationalError:
        pass

def get_user(user_id):
    with conn:
        cursor = conn.cursor()
        cursor.execute('SELECT trial_end_date, sub_end_date, push_enabled FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()

def get_all_users():
    with conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, trial_end_date, sub_end_date, push_enabled FROM users')
        return cursor.fetchall()

def add_user(user_id):
    now = datetime.datetime.now()
    trial_end = now + datetime.timedelta(days=7) # 7 дней бесплатно
    with conn:
        conn.execute('INSERT INTO users (user_id, trial_end_date) VALUES (?, ?)', (user_id, trial_end.isoformat()))
    return trial_end

def update_subscription(user_id, days=30):
    user = get_user(user_id)
    now = datetime.datetime.now()
    
    current_sub_end = None
    if user and user[1]:
        try:
            current_sub_end = datetime.datetime.fromisoformat(user[1])
        except Exception:
            pass

    if current_sub_end and current_sub_end > now:
        new_end = current_sub_end + datetime.timedelta(days=days)
    else:
        new_end = now + datetime.timedelta(days=days)
        
    with conn:
        conn.execute('UPDATE users SET sub_end_date = ? WHERE user_id = ?', (new_end.isoformat(), user_id))
    return new_end

def has_access(user_id):
    user = get_user(user_id)
    if not user:
        return False, "Not registered", False
    
    now = datetime.datetime.now()
    trial_end = datetime.datetime.fromisoformat(user[0])
    
    sub_end = None
    if user[1]:
        sub_end = datetime.datetime.fromisoformat(user[1])
        
    if sub_end and sub_end > now:
        return True, f"Активная подписка (осталось {(sub_end - now).days} дней)", True
    if trial_end > now:
        return True, f"Пробный период (осталось {(trial_end - now).days} дней)", False
        
    return False, "Доступ закрыт", False

# --- АДМИН ПАНЕЛЬ ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return

    markup = InlineKeyboardMarkup(row_width=1)
    btn_users = InlineKeyboardButton("👥 Список пользователей", callback_data="admin_users")
    btn_grant = InlineKeyboardButton("🎁 Выдать платную версию", callback_data="admin_grant")
    markup.add(btn_users, btn_grant)
    
    bot.send_message(message.chat.id, "🛠 <b>Панель Администратора</b>\nВыберите действие:", reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def admin_callback(call):
    if call.from_user.id != ADMIN_ID:
        return
        
    if call.data == "admin_users":
        users = get_all_users()
        if not users:
            bot.send_message(call.message.chat.id, "В базе пока нет пользователей.")
            return
            
        text = "👥 <b>Список пользователей:</b>\n\n"
        for u in users:
            uid, trial, sub = u
            now = datetime.datetime.now()
            
            status = "❌ Истек"
            if sub and datetime.datetime.fromisoformat(sub) > now:
                status = f"✅ Платная подписка (до {sub[:10]})"
            elif trial and datetime.datetime.fromisoformat(trial) > now:
                status = f"⏳ Пробный (до {trial[:10]})"
                
            text += f"<code>{uid}</code> - {status}\n"
            
        bot.send_message(call.message.chat.id, text, parse_mode="HTML")
        
    elif call.data == "admin_grant":
        msg = bot.send_message(call.message.chat.id, "Отправьте мне <b>ID пользователя</b> (из списка выше) и <b>количество дней</b> доступа через пробел.\n\nПример: <code>1491094235 30</code>", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_grant)

def process_grant(message):
    if message.from_user.id != ADMIN_ID:
        return
        
    try:
        parts = message.text.split()
        target_id = int(parts[0])
        days = int(parts[1]) if len(parts) > 1 else 30
        
        # Проверяем есть ли такой юзер
        if not get_user(target_id):
            bot.send_message(message.chat.id, "❌ Пользователь не найден в базе данных. Он должен хотя бы раз нажать /start")
            return
            
        new_date = update_subscription(target_id, days=days)
        bot.send_message(message.chat.id, f"✅ Успех! Пользователю {target_id} выдан полный оплаченный доступ до {new_date.isoformat()[:10]}")
        
        # Оповещаем пользователя
        bot.send_message(target_id, f"🎉 Администратор активировал вам полную подписку на {days} дней!\n\n/start - обновить меню.")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Ошибка формата. Убедитесь что ввели ID и число дней, например:\n<code>1491094235 30</code>", parse_mode="HTML")

def send_invoice(chat_id):
    prices = [LabeledPrice(label='Подписка Таро (30 дней)', amount=250)]
    bot.send_invoice(
        chat_id,
        title='Продление доступа к Таро',
        description='Подписка на 30 дней для использования приватного Telegram Web App раскладов.',
        invoice_payload='tarot_sub_1_month',
        provider_token='',
        currency='XTR',
        prices=prices,
        start_parameter='tarot-sub',
        is_flexible=False
    )

@bot.callback_query_handler(func=lambda call: call.data == "buy_sub")
def buy_sub_callback(call):
    # Убираем "часики" загрузки на кнопке
    bot.answer_callback_query(call.id)
    send_invoice(call.message.chat.id)

# --- ОСНОВНАЯ ЛОГИКА ---
@bot.message_handler(commands=['buy', 'premium'])
def cmd_buy(message):
    user_id = message.from_user.id
    acc, _, is_paid = has_access(user_id)
    if is_paid:
        bot.send_message(user_id, "💎 У вас уже активна Premium подписка!")
    else:
        bot.send_message(user_id, "💳 Для покупки Premium доступа на 30 дней и разблокировки 'Расклада на 3 Карты', оплатите счет ниже Звездами Telegram:")
        send_invoice(user_id)

@bot.message_handler(commands=['help', 'info'])
def cmd_help(message):
    text = "🔮 <b>Официальный Бот Таролога Олега</b>\n\nЗдесь вы можете делать расклады карт Таро и получать послания от Вселенной.\n\n/start — Главное меню\n/buy — Купить Премиум (Расклад на 3 карты)\n/settings — Настройки уведомлений\n/help — Помощь\n\nПо вопросам личной глубокой консультации пишите разработчику-тарологу: <a href='https://t.me/kelt_sham'>@kelt_sham</a>"
    bot.send_message(message.chat.id, text, parse_mode="HTML", disable_web_page_preview=True)

@bot.message_handler(commands=['settings', 'push'])
def settings_msg(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    if not user:
        return
    
    current_push = user[2] if len(user) > 2 else 1
    new_state = 0 if current_push == 1 else 1
    
    with conn:
        conn.execute('UPDATE users SET push_enabled = ? WHERE user_id = ?', (new_state, user_id))
        
    state_str = "ВКЛЮЧЕНЫ 🔔" if new_state == 1 else "ВЫКЛЮЧЕНЫ 🔕"
    bot.send_message(user_id, f"Ежедневные напоминания и карта дня: {state_str}\n\nВы всегда можете переключить это командой /settings")

@bot.message_handler(commands=['start'])
def start_msg(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    if not user:
        add_user(user_id)
        text = "🔮 Добро пожаловать!\n\nВам предоставлен бесплатный пробный доступ на 7 дней к приватному Раскладу Таро.\n\nНажмите кнопку ниже, чтобы открыть карты:"
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("✨ Открыть Расклад", web_app=WebAppInfo(url=WEB_APP_URL)))
        markup.add(InlineKeyboardButton("🌟 Купить подписку", callback_data="buy_sub"))
        bot.send_message(user_id, text, reply_markup=markup)
        
        # Уведомляем админа о новеньком
        if user_id != ADMIN_ID:
            bot.send_message(ADMIN_ID, f"🔔 Новый пользователь!\nID: `{user_id}`\nИмя: {message.from_user.first_name}", parse_mode="Markdown")
        return

    access, status_info, is_paid = has_access(user_id)
    
    if access:
        url = f"{WEB_APP_URL}?premium=1" if is_paid else WEB_APP_URL
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("✨ Открыть Расклад", web_app=WebAppInfo(url=url)))
        
        if not is_paid:
             markup.add(InlineKeyboardButton("🌟 Купить / Продлить подписку", callback_data="buy_sub"))
        else:
             markup.add(InlineKeyboardButton("💎 Подписка Активна", callback_data="buy_sub"))
             
        # Add basic settings button context
        markup.add(InlineKeyboardButton("⚙️ Настройки Пушей", callback_data="toggle_settings"))
        
        bot.send_message(user_id, f"🔮 С возвращением!\n{status_info}\n\nНажмите кнопку ниже:", reply_markup=markup)
    else:
        bot.send_message(user_id, "⏳ Ваш бесплатный пробный период (или прошлая подписка) полностью завершен.\n\nПожалуйста, оплатите подписку (250 ⭐️ Звезд = ~500 рублей), чтобы продолжить использование бота.")
        send_invoice(user_id)

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    user_id = message.from_user.id
    update_subscription(user_id, days=30)
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("✨ Открыть Расклад", web_app=WebAppInfo(url=WEB_APP_URL)))
    
    bot.send_message(user_id, "🎉 Оплата Звездами успешно прошла! Огромное спасибо за подписку.\nВаш доступ продлен ровно на 30 дней.\n\nНажмите кнопку ниже, чтобы открыть карты:", reply_markup=markup)
    
    # Уведомляем админа о заработке
    bot.send_message(ADMIN_ID, f"💰 Ура! Пользователь `{user_id}` только что оплатил подписку 250 Звезд!", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "toggle_settings")
def toggle_set(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    user = get_user(user_id)
    if not user:
        return
    current_push = user[2] if len(user) > 2 else 1
    new_state = 0 if current_push == 1 else 1
    with conn:
        conn.execute('UPDATE users SET push_enabled = ? WHERE user_id = ?', (new_state, user_id))
    state_str = "ВКЛЮЧЕНЫ 🔔" if new_state == 1 else "ВЫКЛЮЧЕНЫ 🔕"
    bot.send_message(user_id, f"Ежедневные напоминания и карта дня: {state_str}\n\nВы всегда можете переключить это командой /settings")

def push_scheduler():
    while True:
        now = datetime.datetime.now()
        # Рассылка ровно в 10:00 утра
        if now.hour == 10 and now.minute == 0:
            users = get_all_users()
            for u in users:
                uid, trial, sub, push_enabled = u[0], u[1], u[2], u[3] if len(u) > 3 else 1
                if push_enabled == 1:
                    acc, _, is_p = has_access(uid)
                    if acc:
                        url = f"{WEB_APP_URL}?premium=1" if is_p else WEB_APP_URL
                        markup = InlineKeyboardMarkup()
                        markup.add(InlineKeyboardButton("🔮 Открыть Карту Дня", web_app=WebAppInfo(url=url)))
                        try:
                            bot.send_message(uid, "✨ Доброе утро! Карты говорят, у Вселенной есть послание для вас...\nЗаберите свою бесплатную Карту Дня!", reply_markup=markup)
                        except Exception:
                            pass
            time.sleep(60) # Спим 60 секунд, чтобы не отправить дважды в ту же минуту
        time.sleep(30) # Проверяем время каждые 30 секунд

threading.Thread(target=push_scheduler, daemon=True).start()

print("Бот успешно запущен (с меню команд, пушами и премиум 3-card)! Ожидаю сообщений от пользователей...")
if __name__ == '__main__':
    bot.set_my_commands([
        telebot.types.BotCommand("/start", "🔮 Запустить расклад"),
        telebot.types.BotCommand("/buy", "💎 Купить Premium доступ"),
        telebot.types.BotCommand("/settings", "⚙️ Настройки уведомлений"),
        telebot.types.BotCommand("/help", "❓ Помощь и связь с Олегом")
    ])
    bot.infinity_polling()
