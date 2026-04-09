import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, LabeledPrice
import sqlite3
import datetime
import threading
import time
import logging
import os
import json as _json
import hmac as _hmac
import hashlib
import random as _random
import urllib.parse as _urllib_parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler as _BaseHTTPHandler
from dotenv import load_dotenv

load_dotenv()

from logging.handlers import RotatingFileHandler

# --- Логирование ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        RotatingFileHandler('bot.log', maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- НАСТРОЙКИ ---
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN не задан в .env файле!")

WEB_APP_URL = os.getenv("WEB_APP_URL", "https://KeltSham.github.io/TarrotBot/").rstrip("/")
API_URL  = os.getenv("API_URL", "")          # публичный URL бота для Mini App, напр. http://1.2.3.4:8080
API_PORT = int(os.getenv("API_PORT", "8080")) # порт HTTP-сервера Mini App API
OLEG_USERNAME = "kelt_sham"                   # Telegram-username Олега для прямой оплаты

# Единые дневные лимиты (считаются по всем типам раскладов суммарно)
LIMIT_FREE    = 3   # бесплатных раскладов в день
LIMIT_PREMIUM = 10  # Premium раскладов в день

# Московская таймзона (UTC+3) — используется для сравнения дат подписок
MSK_TZ = datetime.timezone(datetime.timedelta(hours=3))

def now_msk() -> datetime.datetime:
    """Текущее время в московской таймзоне (UTC+3), naive (без tzinfo) для сравнения с БД."""
    return datetime.datetime.now(tz=MSK_TZ).replace(tzinfo=None)

_ADMIN_ID_STR = os.getenv("ADMIN_ID")
if not _ADMIN_ID_STR:
    raise ValueError("ADMIN_ID не задан в .env файле!")
try:
    ADMIN_ID = int(_ADMIN_ID_STR)
except ValueError:
    raise ValueError(f"ADMIN_ID должен быть числом, получено: '{_ADMIN_ID_STR}'")
# -----------------

bot = telebot.TeleBot(TOKEN)
logger.info("Бот инициализирован.")

# Инициализация Базы Данных SQLite
if not os.path.exists('data'):
    os.makedirs('data')
conn = sqlite3.connect('data/users.db', check_same_thread=False)
conn.execute('PRAGMA journal_mode=WAL')  # Безопасная работа с несколькими потоками
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
    try:
        conn.execute('ALTER TABLE users ADD COLUMN daily_count INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute('ALTER TABLE users ADD COLUMN last_reset_date TEXT DEFAULT ""')
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute('ALTER TABLE users ADD COLUMN referred_by INTEGER DEFAULT NULL')
    except sqlite3.OperationalError:
        pass
    try:
        # JS getTimezoneOffset(): UTC+3 → -180, UTC-5 → 300
        conn.execute('ALTER TABLE users ADD COLUMN timezone_offset INTEGER DEFAULT NULL')
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute('ALTER TABLE users ADD COLUMN last_push_date TEXT DEFAULT NULL')
    except sqlite3.OperationalError:
        pass
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usage_log (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            date         TEXT    NOT NULL,
            service_type TEXT    NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS readings_history (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            card_name    TEXT    NOT NULL,
            meaning_text TEXT    NOT NULL,
            mode         TEXT    NOT NULL DEFAULT 'question',
            created_at   TEXT    NOT NULL
        )
    ''')

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

def get_stats():
    """Возвращает (total, paid, trial, expired, push_on)."""
    users = get_all_users()
    now = datetime.datetime.now()
    paid = trial = push_on = 0
    for u in users:
        uid, trial_end, sub_end, push = u[0], u[1], u[2], (u[3] if len(u) > 3 else 1)
        try:
            if sub_end and datetime.datetime.fromisoformat(sub_end) > now:
                paid += 1
            elif trial_end and datetime.datetime.fromisoformat(trial_end) > now:
                trial += 1
        except Exception:
            pass
        if push == 1:
            push_on += 1
    expired = len(users) - paid - trial
    return len(users), paid, trial, expired, push_on

def get_moon_phase():
    """Возвращает (emoji, название, контекст) текущей лунной фазы."""
    known_new = datetime.datetime(2000, 1, 6, 18, 14)   # известное новолуние
    # Используем время МСК для синхронизации с пользователями
    days  = (now_msk() - known_new).total_seconds() / 86400.0
    frac  = (days % 29.53058867) / 29.53058867
    # Центрируем фазы вокруг астрономических точек (±0.017 цикла ≈ ±0.5 суток)
    T = 0.017
    if   frac < T or frac > 1 - T:    idx = 0  # новолуние
    elif frac < 0.25 - T:              idx = 1  # растущий серп
    elif frac < 0.25 + T:              idx = 2  # первая четверть
    elif frac < 0.5  - T:              idx = 3  # прибывающая
    elif frac < 0.5  + T:              idx = 4  # полнолуние
    elif frac < 0.75 - T:              idx = 5  # убывающая
    elif frac < 0.75 + T:              idx = 6  # последняя четверть
    else:                              idx = 7  # тёмная луна
    phases = [
        ("🌑", "Новолуние",          "новолуние — лучшее время задавать намерения"),
        ("🌒", "Растущий серп",      "растущая луна — энергия набирает силу"),
        ("🌓", "Первая четверть",    "первая четверть — действуй решительно"),
        ("🌔", "Прибывающая луна",   "прибывающая луна — желания усиливаются"),
        ("🌕", "Полнолуние",         "полнолуние — пик энергии, эмоции обострены"),
        ("🌖", "Убывающая луна",     "убывающая луна — самое время завершать дела"),
        ("🌗", "Последняя четверть", "убывающая луна — подводи итоги и отпускай"),
        ("🌘", "Тёмная луна",        "тёмная луна — береги силы, время тишины"),
    ]
    return phases[idx]

def get_today_stats():
    """Возвращает (dau, service_counts_dict) за сегодня из usage_log."""
    today = now_msk().strftime('%Y-%m-%d')
    with conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(DISTINCT user_id) FROM usage_log WHERE date = ?', (today,))
        dau = cursor.fetchone()[0]
        cursor.execute('SELECT service_type, COUNT(*) FROM usage_log WHERE date = ? GROUP BY service_type', (today,))
        rows = cursor.fetchall()
    return dau, {r[0]: r[1] for r in rows}

def get_weekly_stats():
    """Собирает статистику по дням за последнюю неделю."""
    lines = ["📈 <b>Динамика за 7 дней:</b>"]
    for i in range(7):
        d_dt = now_msk() - datetime.timedelta(days=i)
        d_str = d_dt.strftime('%Y-%m-%d')
        label = d_dt.strftime('%d.%m')
        with conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(DISTINCT user_id) FROM usage_log WHERE date = ?', (d_str,))
            dau = (cursor.fetchone() or [0])[0]
            cursor.execute('SELECT COUNT(*) FROM usage_log WHERE date = ?', (d_str,))
            total = (cursor.fetchone() or [0])[0]
        lines.append(f"📅 {label}: 👥 <b>{dau}</b> | 🔢 <b>{total}</b>")
    return "\n".join(lines)

def get_user_local_date(user_id) -> str:
    """
    Возвращает локальную дату пользователя (YYYY-MM-DD) на основе его
    timezone_offset, хранящегося в БД.  Расчёт ведётся по серверному UTC —
    клиентскому времени не доверяем, перемотка стрелок не поможет.

    JS getTimezoneOffset() возвращает: UTC+3 → -180, UTC-5 → 300.
    Формула: local_time = UTC - offset_minutes.
    """
    cursor = conn.cursor()
    cursor.execute('SELECT timezone_offset FROM users WHERE user_id=?', (user_id,))
    row = cursor.fetchone()
    tz_offset = row[0] if (row and row[0] is not None) else -180  # MSK по умолчанию
    user_local = datetime.datetime.utcnow() - datetime.timedelta(minutes=tz_offset)
    return user_local.strftime('%Y-%m-%d')

def update_timezone_offset(user_id, tz_offset: int):
    """Сохраняет/обновляет timezone_offset пользователя (из JS getTimezoneOffset)."""
    with conn:
        conn.execute('UPDATE users SET timezone_offset=? WHERE user_id=?', (tz_offset, user_id))

def get_daily_count(user_id) -> int:
    """
    Суммарное количество раскладов пользователя за его локальный сегодняшний день.
    Единый счётчик — тип расклада не важен.
    """
    today = get_user_local_date(user_id)
    with conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT COUNT(*) FROM usage_log WHERE user_id=? AND date=?',
            (user_id, today)
        )
        return cursor.fetchone()[0]

def get_user_streak(user_id) -> int:
    """
    Количество последовательных дней подряд, когда пользователь делал хотя бы
    один расклад. Считается по usage_log, начиная с сегодняшней локальной даты.
    """
    today = get_user_local_date(user_id)
    today_dt = datetime.datetime.strptime(today, '%Y-%m-%d')
    with conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT DISTINCT date FROM usage_log WHERE user_id=? ORDER BY date DESC',
            (user_id,)
        )
        dates = [row[0] for row in cursor.fetchall()]
    if not dates:
        return 0
    streak = 0
    check = today_dt
    for d in dates:
        try:
            d_dt = datetime.datetime.strptime(d, '%Y-%m-%d')
        except ValueError:
            continue
        if d_dt == check:
            streak += 1
            check -= datetime.timedelta(days=1)
        elif d_dt < check:
            break
    return streak

def _get_daily_limit(is_paid: bool, user_id: int = None) -> int:
    """
    Дневной лимит: 10 для Premium, 3 для бесплатных.
    Бонус +1 карта для бесплатных пользователей со стриком ≥ 5 дней.
    """
    base = LIMIT_PREMIUM if is_paid else LIMIT_FREE
    if not is_paid and user_id is not None:
        try:
            if get_user_streak(user_id) >= 5:
                base += 1
        except Exception:
            pass
    return base

def check_and_increment_limit(user_id, service_type, tz_offset: int = None):
    """
    Единая проверка суммарного дневного лимита (независимо от типа расклада).
    Если передан tz_offset — обновляет его в БД перед проверкой.
    Возвращает True если расклад разрешён.
    """
    if not get_user(user_id):
        return False

    if tz_offset is not None:
        update_timezone_offset(user_id, tz_offset)

    _, _, is_paid = has_access(user_id)
    limit   = _get_daily_limit(is_paid, user_id)
    current = get_daily_count(user_id)

    if current >= limit:
        return False

    today = get_user_local_date(user_id)
    with conn:
        conn.execute(
            'INSERT INTO usage_log (user_id, date, service_type) VALUES (?, ?, ?)',
            (user_id, today, service_type)
        )
    return True

def validate_init_data(init_data_str):
    """Проверяет подпись Telegram WebApp initData. Возвращает user_id или None."""
    if not init_data_str:
        return None
    try:
        parsed = dict(_urllib_parse.parse_qsl(init_data_str, keep_blank_values=True))
        hash_val = parsed.pop('hash', '')
        data_check = '\n'.join(f'{k}={v}' for k, v in sorted(parsed.items()))
        secret = _hmac.new(b'WebAppData', TOKEN.encode(), hashlib.sha256).digest()
        computed = _hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
        if not _hmac.compare_digest(computed, hash_val):
            return None
        return _json.loads(parsed.get('user', '{}')).get('id')
    except Exception as e:
        logger.error(f"validate_init_data: {e}")
        return None

def _build_webapp_url(is_premium: bool) -> str:
    """Формирует URL мини-приложения с нужными параметрами."""
    url = f"{WEB_APP_URL}?v=6"
    if is_premium:
        url += "&premium=1"
    if API_URL:
        url += "&api=" + _urllib_parse.quote(API_URL, safe='')
    return url

def add_user(user_id, referred_by=None):
    now = datetime.datetime.now()
    bonus = 3 if referred_by else 0          # реферал даёт +3 дня к стандартным 7
    trial_end = now + datetime.timedelta(days=7 + bonus)
    with conn:
        conn.execute(
            'INSERT INTO users (user_id, trial_end_date, referred_by) VALUES (?, ?, ?)',
            (user_id, trial_end.isoformat(), referred_by)
        )
    return trial_end

def extend_trial(user_id, days):
    """Продлевает пробный доступ на N дней (от текущего конца или от сейчас, если уже истёк)."""
    user = get_user(user_id)
    if not user:
        return None
    now = datetime.datetime.now()
    try:
        current_end = datetime.datetime.fromisoformat(user[0])
    except Exception:
        current_end = now
    new_end = max(current_end, now) + datetime.timedelta(days=days)
    with conn:
        conn.execute('UPDATE users SET trial_end_date = ? WHERE user_id = ?',
                     (new_end.isoformat(), user_id))
    return new_end

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

    now = now_msk()
    trial_end = datetime.datetime.fromisoformat(user[0])

    sub_end = None
    if user[1]:
        sub_end = datetime.datetime.fromisoformat(user[1])

    if sub_end and sub_end > now:
        return True, f"Активная подписка (осталось {(sub_end - now).days} дней)", True
    if trial_end > now:
        return True, f"Пробный Премиум-доступ (осталось {(trial_end - now).days} дней)", True

    return True, f"У вас Базовый тариф ({LIMIT_FREE} расклада в день)", False

# --- АДМИН ПАНЕЛЬ ---
USERS_PER_PAGE = 15

def _admin_menu_markup():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🎁 Выдать доступ", callback_data="admin_grant"),
               InlineKeyboardButton("❌ Забрать Premium", callback_data="admin_revoke"))
    markup.row(InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
               InlineKeyboardButton("📅 За неделю", callback_data="admin_weekly"))
    markup.row(InlineKeyboardButton("📢 Рассылка всем", callback_data="admin_broadcast"))
    markup.add(InlineKeyboardButton("📈 Список юзеров", callback_data="admin_users_0"))
    return markup

def _build_users_page(users, page):
    now = datetime.datetime.now()
    total = len(users)
    total_pages = max(1, (total + USERS_PER_PAGE - 1) // USERS_PER_PAGE)
    chunk = users[page * USERS_PER_PAGE : (page + 1) * USERS_PER_PAGE]

    lines = [f"👥 <b>Пользователи</b> — стр. {page+1}/{total_pages} (всего {total}):\n"]
    for u in chunk:
        uid, trial_end, sub_end, push = u[0], u[1], u[2], (u[3] if len(u) > 3 else 1)
        push_icon = "🔔" if push == 1 else "🔕"
        status = "❌ истёк"
        try:
            if sub_end and datetime.datetime.fromisoformat(sub_end) > now:
                d = (datetime.datetime.fromisoformat(sub_end) - now).days
                status = f"💎 суб. {d}д"
            elif trial_end and datetime.datetime.fromisoformat(trial_end) > now:
                d = (datetime.datetime.fromisoformat(trial_end) - now).days
                status = f"⏳ триал {d}д"
        except Exception:
            status = "⚠️ ошибка"
        lines.append(f"{push_icon} <code>{uid}</code> — {status}")

    markup = InlineKeyboardMarkup(row_width=2)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Назад", callback_data=f"admin_users_{page-1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("Вперёд ▶️", callback_data=f"admin_users_{page+1}"))
    if nav:
        markup.add(*nav)
    markup.add(InlineKeyboardButton("🏠 Меню", callback_data="admin_menu"))
    return "\n".join(lines), markup

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, "🛠 <b>Панель Администратора</b>\nВыберите действие:",
                     reply_markup=_admin_menu_markup(), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def admin_callback(call):
    bot.answer_callback_query(call.id)
    if call.from_user.id != ADMIN_ID:
        return

    data = call.data

    if data == "admin_menu":
        bot.edit_message_text("🛠 <b>Панель Администратора</b>\nВыберите действие:",
                              call.message.chat.id, call.message.message_id,
                              reply_markup=_admin_menu_markup(), parse_mode="HTML")

    elif data == "admin_stats":
        total, paid, trial, expired, push_on = get_stats()
        dau, svc = get_today_stats()
        q_cnt = svc.get('question', 0)
        d_cnt = svc.get('daily',    0)
        t_cnt = svc.get('three',    0)
        total_today = q_cnt + d_cnt + t_cnt
        services = [('❓ Вопрос', q_cnt), ('🃏 Карта дня', d_cnt), ('💎 3 карты', t_cnt)]
        top = max(services, key=lambda x: x[1])
        popular = f"{top[0]} ({top[1]})" if total_today > 0 else "нет данных"
        today_label = now_msk().strftime('%d.%m')
        text = (
            "📊 <b>Статистика бота</b>\n\n"
            f"👥 Всего пользователей: <b>{total}</b>\n"
            f"💎 Активная подписка:   <b>{paid}</b>\n"
            f"⏳ На триале:           <b>{trial}</b>\n"
            f"❌ Истёк доступ:        <b>{expired}</b>\n"
            f"🔔 Push включён:        <b>{push_on}</b>\n\n"
            f"📅 <b>Сегодня ({today_label})</b>\n"
            f"👁 Активных юзеров: <b>{dau}</b>   🔢 Раскладов: <b>{total_today}</b>\n"
            f"❓ Вопросов: <b>{q_cnt}</b>  🃏 Карт дня: <b>{d_cnt}</b>  💎 3 карт: <b>{t_cnt}</b>\n"
            f"🏆 Самое популярное: <b>{popular}</b>"
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏠 Меню", callback_data="admin_menu"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                              reply_markup=markup, parse_mode="HTML")

    elif data == "admin_weekly":
        text = get_weekly_stats()
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏠 Меню", callback_data="admin_menu"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                              reply_markup=markup, parse_mode="HTML")

    elif data == "admin_broadcast":
        msg = bot.send_message(call.message.chat.id, "📢 <b>Режим рассылки</b>\nВведите текст, который увидят ВСЕ пользователи:", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_broadcast)

    elif data.startswith("admin_users_"):
        page = int(data.split("_")[-1])
        users = get_all_users()
        if not users:
            bot.send_message(call.message.chat.id, "В базе пока нет пользователей.")
            return
        text, markup = _build_users_page(users, page)
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                                  reply_markup=markup, parse_mode="HTML")
        except Exception:
            bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

    elif data == "admin_grant":
        msg = bot.send_message(call.message.chat.id,
            "Отправьте <b>ID пользователя</b> и <b>количество дней</b> через пробел.\n\n"
            "Пример: <code>1491094235 30</code>", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_grant)

    elif data == "admin_revoke":
        msg = bot.send_message(call.message.chat.id,
            "Отправьте <b>ID пользователя</b>, у которого нужно забрать Premium.\n\n"
            "Пример: <code>1093226470</code>", parse_mode="HTML")
        bot.register_next_step_handler(msg, process_revoke)

def process_broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    text = message.text
    if not text or text.lower() in ['отмена', 'cancel', '/start']:
        bot.send_message(message.chat.id, "❌ Рассылка отменена.")
        return
    with conn:
        users = conn.execute('SELECT user_id FROM users').fetchall()
    bot.send_message(message.chat.id, f"🚀 Начинаю рассылку на {len(users)} пользователей...")
    count, blocked = 0, 0
    for u in users:
        uid = u[0]
        try:
            bot.send_message(uid, text)
            count += 1
            time.sleep(0.04)
        except telebot.apihelper.ApiTelegramException as e:
            if 'bot was blocked' in str(e):
                blocked += 1
                with conn: conn.execute('UPDATE users SET push_enabled=0 WHERE user_id=?', (uid,))
        except: pass
    bot.send_message(message.chat.id, f"✅ Рассылка завершена!\n\n📥 Доставлено: <b>{count}</b>\n🚫 Блоков: <b>{blocked}</b>", parse_mode="HTML")

def process_revoke(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        target_id = int(message.text.strip())
        if not get_user(target_id):
            bot.send_message(message.chat.id, "❌ Пользователь не найден в базе.")
            return
        with conn:
            conn.execute('UPDATE users SET sub_end_date = NULL WHERE user_id = ?', (target_id,))
        bot.send_message(message.chat.id, f"✅ Premium у пользователя {target_id} отозван.")
        try:
            bot.send_message(target_id, "⚠️ Ваша Premium-подписка была деактивирована администратором.\n\n/start — обновить меню.")
        except Exception:
            pass
    except Exception as e:
        logger.error(f"process_revoke error: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка. Отправьте только ID пользователя, например:\n<code>1093226470</code>", parse_mode="HTML")

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
        logger.error(f"process_grant error: {e}")
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

def _send_payment_options(chat_id):
    """Отправляет оффер Premium с преимуществами и двумя способами оплаты."""
    text = (
        "💎 <b>Premium Таро — 30 дней</b>\n\n"
        "<b>Что вы получаете:</b>\n"
        "⚡️ 10 раскладов в день вместо 3\n"
        "🃏 Доступ к раскладу «3 Карты» (Прошлое · Настоящее · Будущее)\n"
        "📜 История всех ваших раскладов — перечитывайте когда угодно\n"
        "💬 Прямая связь с мастером для вопросов и оплаты\n\n"
        "<b>Выберите удобный способ оплаты:</b>\n\n"
        "⭐ <b>Telegram Stars</b> — мгновенно, через Apple/Google Pay.\n"
        "💬 <b>Написать Олегу</b> — оплата с карты или другим способом, "
        "Олег поможет с активацией."
    )
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("⭐ Оплатить Звёздами (250 ★)", callback_data="buy_stars"),
        InlineKeyboardButton(
            "💬 Написать Олегу напрямую",
            url=f"https://t.me/{OLEG_USERNAME}?text=%D0%97%D0%B4%D1%80%D0%B0%D0%B2%D1%81%D1%82%D0%B2%D1%83%D0%B9%D1%82%D0%B5%2C+%D1%85%D0%BE%D1%87%D1%83+%D0%BF%D1%80%D0%B8%D0%BE%D0%B1%D1%80%D0%B5%D1%81%D1%82%D0%B8+Premium+%D0%B2+%D0%B1%D0%BE%D1%82%D0%B5+%D0%A2%D0%B0%D1%80%D0%BE"
        )
    )
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "buy_sub")
def buy_sub_callback(call):
    bot.answer_callback_query(call.id)
    _send_payment_options(call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "buy_stars")
def buy_stars_callback(call):
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
        _send_payment_options(user_id)

@bot.message_handler(commands=['history'])
def cmd_history(message):
    user_id = message.from_user.id
    _, _, is_paid = has_access(user_id)
    if not is_paid:
        bot.send_message(
            user_id,
            "📜 <b>История раскладов</b> доступна только Premium пользователям.\n\n"
            "Откройте подписку, чтобы сохранять и перечитывать все свои расклады в любое время!",
            parse_mode="HTML"
        )
        _send_payment_options(user_id)
        return
    with conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT card_name, mode, created_at FROM readings_history '
            'WHERE user_id=? ORDER BY id DESC LIMIT 10',
            (user_id,)
        )
        rows = cur.fetchall()
    if not rows:
        bot.send_message(
            user_id,
            "📜 У вас пока нет сохранённых раскладов.\n"
            "Сделайте расклад в приложении — и он появится здесь!",
            parse_mode="HTML"
        )
        return
    mode_names = {'daily': 'Карта дня', 'question': 'Вопрос', 'three': '3 карты'}
    lines = ["📜 <b>Ваши последние расклады:</b>\n"]
    for r in rows:
        mode_label = mode_names.get(r[1], r[1])
        date_str   = r[2][:10]
        lines.append(f"🃏 {r[0]} — {mode_label} ({date_str})")
    bot.send_message(user_id, '\n'.join(lines), parse_mode="HTML")

@bot.message_handler(commands=['help', 'info'])
def cmd_help(message):
    text = (
        "🔮 <b>Тайны Вселенной — Ваш Карманный Таролог</b>\n\n"
        "Этот бот — ваш надежный проводник в мир подсознания и энергетики. С его помощью вы сможете:\n"
        "▫️ Вытягивать <b>Карту Дня</b>, чтобы узнать, какие энергии будут сопутствовать вам сегодня.\n"
        "▫️ Задавать картам <b>сокровенные вопросы</b> и получать мудрые, глубокие интерпретации.\n"
        "▫️ Использовать мощный <b>Расклад на 3 Карты</b> (Прошлое, Настоящее, Будущее), чтобы увидеть всю картину целиком.\n\n"
        "<i>По вопросам личной глубокой консультации пишите живому тарологу:</i> <a href='https://t.me/kelt_sham'>@kelt_sham</a>"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML", disable_web_page_preview=True)
@bot.message_handler(commands=['settings', 'push'])
def settings_msg(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    if not user:
        return

    current_push = user[2] if len(user) > 2 else 1
    state_str = "ВКЛЮЧЕНЫ 🔔" if current_push == 1 else "ВЫКЛЮЧЕНЫ 🔕"
    toggle_label = "🔕 Выключить уведомления" if current_push == 1 else "🔔 Включить уведомления"

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(toggle_label, callback_data="toggle_settings"))

    bot.send_message(
        user_id,
        f"⚙️ <b>Настройки уведомлений</b>\n\nЕжедневная карта дня и напоминания сейчас: <b>{state_str}</b>",
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.message_handler(commands=['profile', 'status'])
def cmd_profile(message):
    user_id = message.from_user.id
    acc, status_info, is_paid = has_access(user_id)
    text = f"👤 <b>Ваш Профиль</b>\nID: <code>{user_id}</code>\n\nТекущий статус: <b>{status_info}</b>\n\n"
    if is_paid:
        text += "✅ Наслаждайтесь безлимитными картами и 'Раскладом на 3 Карты'."
    else:
        text += "⚠️ У вас базовый тариф (3 карты в день). Купите Premium, чтобы снять лимиты!"

    try:
        bot_username = bot.get_me().username
        ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    except Exception:
        ref_link = f"(ошибка получения ссылки, попробуйте позже)"

    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users WHERE referred_by = ?', (user_id,))
    count = cursor.fetchone()[0]

    text += (
        f"\n\n🔗 <b>Ваша реферальная ссылка:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        f"Поделитесь с друзьями:\n"
        f"• Друг получит <b>+3 дня</b> Premium-доступа\n"
        f"• Вы получите <b>+3 дня</b> за каждого приглашённого\n\n"
        f"👥 Приглашено друзей: <b>{count}</b>"
    )
    
    markup = InlineKeyboardMarkup()
    if not is_paid:
        markup.add(InlineKeyboardButton("🌟 Купить Premium", callback_data="buy_sub"))
        
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)


@bot.message_handler(commands=['start'])
def start_msg(message):
    user_id = message.from_user.id

    # Парсим реферальный payload: /start ref_12345
    parts = message.text.split(maxsplit=1)
    ref_id = None
    if len(parts) > 1 and parts[1].startswith('ref_'):
        try:
            candidate = int(parts[1][4:])
            if candidate != user_id:   # нельзя приглашать самого себя
                ref_id = candidate
        except ValueError:
            pass

    user = get_user(user_id)

    if not user:
        add_user(user_id, referred_by=ref_id)

        if ref_id:
            ref_bonus_text = "🎁 Вас пригласил друг — вам начислено <b>+3 дня</b> к пробному доступу!\n\n"
            # Награждаем реферера
            referrer_exists = get_user(ref_id)
            if referrer_exists:
                extend_trial(ref_id, 3)
                try:
                    bot.send_message(ref_id,
                        f"🎉 По вашей реферальной ссылке пришёл новый пользователь!\n"
                        f"Вам начислено <b>+3 дня</b> к пробному доступу. Так держать! 🚀",
                        parse_mode="HTML")
                except Exception:
                    pass
        else:
            ref_bonus_text = ""

        text = (
            f"🔮 <b>Добро пожаловать в Тайны Вселенной!</b>\n\n"
            f"Этот бот — ваш личный карманный таролог. С его помощью вы сможете вытянуть Карту Дня или задать картам самый сокровенный вопрос и получить мудрый и глубокий ответ.\n\n"
            f"{ref_bonus_text}"
            f"🔥 Вам уже предоставлен <b>бесплатный пробный доступ на 7 дней</b> к приватному Раскладу Таро!\n\n"
            f"👇 Нажмите кнопку ниже, чтобы открыть карты:"
        )
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("✨ Сделать Расклад", web_app=WebAppInfo(url=_build_webapp_url(True))))
        markup.add(InlineKeyboardButton("🌟 Premium Доступ", callback_data="buy_sub"))
        bot.send_message(user_id, text, reply_markup=markup, parse_mode="HTML")

        # Уведомляем админа о новеньком
        if user_id != ADMIN_ID:
            ref_note = f" (от ref {ref_id})" if ref_id else ""
            bot.send_message(ADMIN_ID,
                f"🔔 Новый пользователь{ref_note}!\nID: <code>{user_id}</code>\nИмя: {message.from_user.first_name}",
                parse_mode="HTML")
        return

    access, status_info, is_paid = has_access(user_id)

    if access:
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("✨ Сделать Расклад", web_app=WebAppInfo(url=_build_webapp_url(is_paid))))

        bot.send_message(user_id, f"🔮 {status_info}", reply_markup=markup, parse_mode="HTML")
    else:
        logger.warning(f"start_msg: has_access вернул False для зарегистрированного user_id={user_id}")
        bot.send_message(user_id, "🔮 Добро пожаловать! Нажмите /start ещё раз, чтобы открыть меню.")

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    user_id = message.from_user.id
    update_subscription(user_id, days=30)
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("✨ Открыть Расклад", web_app=WebAppInfo(url=_build_webapp_url(True))))

    bot.send_message(user_id, "🎉 Оплата Звездами успешно прошла! Огромное спасибо за подписку.\nВаш доступ продлен ровно на 30 дней.\n\nНажмите кнопку ниже, чтобы открыть карты:", reply_markup=markup)
    
    # Уведомляем админа о заработке
    bot.send_message(ADMIN_ID, f"💰 Ура! Пользователь <code>{user_id}</code> только что оплатил подписку 250 Звезд!", parse_mode="HTML")

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
    toggle_label = "🔕 Выключить уведомления" if new_state == 1 else "🔔 Включить уведомления"
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(toggle_label, callback_data="toggle_settings"))
    bot.send_message(
        user_id,
        f"✅ Готово! Ежедневная карта дня и напоминания: <b>{state_str}</b>",
        parse_mode="HTML",
        reply_markup=markup
    )

_push_sent_dates: set = set()  # Защита от двойной рассылки при перезапуске в 10:00

def push_scheduler():
    """Фоновая задача: пуши в 10:00 (по местному), 12:00 (истечение) и 19:00 (стрик)."""
    while True:
        try:
            now_utc = datetime.datetime.utcnow()
            now_msk_dt = now_msk()
            today_str = now_utc.strftime('%Y-%m-%d')
            today_msk = now_msk_dt.strftime('%Y-%m-%d')

            # --- 1. Утренние пуши (по МЕСТНОМУ времени 10:00) ---
            with conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id, timezone_offset 
                    FROM users 
                    WHERE push_enabled = 1 AND (last_push_date IS NULL OR last_push_date != ?)
                ''', (today_str,))
                users_morning = cursor.fetchall()

            if users_morning:
                moon_emoji, moon_name, moon_ctx = get_moon_phase()
                push_variants = [
                    f"✨ <b>Доброе утро!</b>\n\n{moon_emoji} Сейчас {moon_ctx}.\n\nКарты готовы открыть послание Вселенной специально для вас — заберите Карту Дня!",
                    f"🔮 Новый день — новое послание.\n\n{moon_emoji} <b>{moon_name}</b> усиливает энергию расклада.\n\nУзнайте, что карты говорят о сегодняшнем дне!",
                    f"🌅 <b>Утренний расклад ждёт вас!</b>\n\n{moon_emoji} {moon_ctx.capitalize()}.\n\nОдин взгляд на карту — и день пройдёт осознаннее. Заглядывайте! 🃏",
                    f"🌙 <b>Вселенная шепчет что-то важное...</b>\n\n{moon_emoji} {moon_ctx.capitalize()}.\n\nОткройте Карту Дня — карты уже выбрали послание именно для вас.",
                    f"🃏 <b>Ваша карта дня несёт предупреждение.</b>\n\nУзнайте, в чём оно заключается — прежде чем день войдёт в полную силу.",
                    f"🌌 <b>Сегодня энергия особенная.</b>\n\n{moon_emoji} {moon_ctx.capitalize()}.\n\nКарты ждут, чтобы рассказать вам то, о чём вы ещё не догадываетесь.",
                    f"🔮 <b>Один вопрос к Вселенной — один ответ.</b>\n\nЧто беспокоит вас прямо сейчас? Карты уже знают.",
                    f"⚡️ <b>Утро задаёт тон всему дню.</b>\n\nВытяните карту прямо сейчас — и вы будете готовы к тому, что ждёт впереди."
                ]
                for uid, tz_offset in users_morning:
                    offset = tz_offset if tz_offset is not None else -180
                    user_local = now_utc - datetime.timedelta(minutes=offset)
                    if user_local.hour == 10:
                        acc, _, is_p = has_access(uid)
                        if acc:
                            markup = InlineKeyboardMarkup()
                            markup.add(InlineKeyboardButton("🔮 Открыть Карту Дня", web_app=WebAppInfo(url=_build_webapp_url(is_p))))
                            try:
                                bot.send_message(uid, _random.choice(push_variants), reply_markup=markup, parse_mode="HTML")
                                with conn:
                                    conn.execute('UPDATE users SET last_push_date = ? WHERE user_id = ?', (today_str, uid))
                            except telebot.apihelper.ApiTelegramException as e:
                                if 'bot was blocked' in str(e):
                                    with conn: conn.execute('UPDATE users SET push_enabled=0 WHERE user_id=?', (uid,))
                            except Exception: pass
                            time.sleep(0.05)

            # --- 2. Стрик-пуш (19:00 по МСК) ---
            streak_key = today_msk + '_streak'
            if now_msk_dt.hour == 19 and now_msk_dt.minute < 15 and streak_key not in _push_sent_dates:
                _push_sent_dates.add(streak_key)
                users = get_all_users()
                for u in users:
                    uid = u[0]
                    push_on = u[3] if len(u) > 3 else 1
                    if push_on != 1: continue
                    acc, _, is_p = has_access(uid)
                    if not acc or is_p: continue
                    try:
                        streak = get_user_streak(uid)
                        if streak >= 5:
                            markup = InlineKeyboardMarkup()
                            markup.add(InlineKeyboardButton("🔮 Открыть Расклад", web_app=WebAppInfo(url=_build_webapp_url(False))))
                            bot.send_message(uid, f"🔥 <b>Вы гадаете {streak} дней подряд!</b>\n\n✨ Бонус: сегодня вам доступно <b>{LIMIT_FREE + 1} раскладов</b>!", reply_markup=markup, parse_mode="HTML")
                            time.sleep(0.05)
                    except: pass

            # --- 3. Истечение (12:00 по МСК) ---
            expiry_key = today_msk + '_expiry'
            if now_msk_dt.hour == 12 and now_msk_dt.minute < 15 and expiry_key not in _push_sent_dates:
                _push_sent_dates.add(expiry_key)
                users = get_all_users()
                warn_f = now_msk_dt + datetime.timedelta(days=2, hours=23)
                warn_t = now_msk_dt + datetime.timedelta(days=3, hours=1)
                for u in users:
                    uid, _, sub_end = u[0], u[1], u[2]
                    if not sub_end: continue
                    try:
                        sub_dt = datetime.datetime.fromisoformat(sub_end)
                        if warn_f <= sub_dt <= warn_t:
                            markup = InlineKeyboardMarkup()
                            markup.add(InlineKeyboardButton("🌟 Продлить подписку", callback_data="buy_sub"))
                            bot.send_message(uid, "⏰ <b>Ваша подписка истекает через 3 дня!</b>\n\nПродлите её, чтобы сохранить доступ к полным раскладам.", reply_markup=markup, parse_mode="HTML")
                            time.sleep(0.05)
                    except: pass

            # Очистка старых ключей раз в сутки
            if now_msk_dt.hour == 3: _push_sent_dates.clear()

        except Exception as e:
            logger.error(f"Push loop error: {e}")
        
        time.sleep(600) # Проверка раз в 10 минут

# ──────────────────────────────────────────────
# HTTP API для Mini App (лимиты и логирование)
# ──────────────────────────────────────────────
class _MiniAppHandler(_BaseHTTPHandler):
    def _cors(self):
        self.send_header('Access-Control-Allow-Origin',  '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        parsed_path = _urllib_parse.urlparse(self.path).path

        # GET /api/status?initData=...&tz_offset=...
        # → { is_paid, count, limit, limit_reached }
        if parsed_path == '/api/status':
            qs     = _urllib_parse.urlparse(self.path).query
            params = dict(_urllib_parse.parse_qsl(qs))
            uid    = validate_init_data(params.get('initData', ''))
            if not uid:
                body = _json.dumps({'error': 'invalid'}).encode()
                self.send_response(403)
            else:
                try:
                    tz = int(params.get('tz_offset', ''))
                    update_timezone_offset(uid, tz)
                except (ValueError, TypeError):
                    pass
                _, _, is_paid = has_access(uid)
                count = get_daily_count(uid)
                limit = _get_daily_limit(is_paid, uid)
                body  = _json.dumps({
                    'is_paid':       is_paid,
                    'count':         count,
                    'limit':         limit,
                    'limit_reached': count >= limit,
                }).encode()
                self.send_response(200)

        # GET /api/history?initData=...
        # → { history: [{card, meaning, mode, date}, ...] }  (только Premium)
        elif parsed_path == '/api/history':
            qs     = _urllib_parse.urlparse(self.path).query
            params = dict(_urllib_parse.parse_qsl(qs))
            uid    = validate_init_data(params.get('initData', ''))
            if not uid:
                body = _json.dumps({'error': 'invalid'}).encode()
                self.send_response(403)
            else:
                _, _, is_paid = has_access(uid)
                if not is_paid:
                    body = _json.dumps({'error': 'premium_only'}).encode()
                    self.send_response(403)
                else:
                    with conn:
                        cur = conn.cursor()
                        cur.execute(
                            'SELECT card_name, meaning_text, mode, created_at '
                            'FROM readings_history WHERE user_id=? ORDER BY id DESC LIMIT 30',
                            (uid,)
                        )
                        rows = cur.fetchall()
                    history = [
                        {'card': r[0], 'meaning': r[1], 'mode': r[2], 'date': r[3][:10]}
                        for r in rows
                    ]
                    body = _json.dumps({'history': history}).encode()
                    self.send_response(200)

        else:
            body = b'Not Found'
            self.send_response(404)

        self.send_header('Content-Type', 'application/json')
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        parsed_path = _urllib_parse.urlparse(self.path).path
        length = int(self.headers.get('Content-Length', 0))
        try:
            data = _json.loads(self.rfile.read(length).decode())
        except Exception:
            data = {}

        # POST /api/use  body: { initData, serviceType, tz_offset }
        # → { allowed, count, limit }
        if parsed_path == '/api/use':
            uid = validate_init_data(data.get('initData', ''))
            if not uid:
                body = _json.dumps({'allowed': False, 'error': 'invalid_init_data'}).encode()
                self.send_response(403)
            else:
                svc       = data.get('serviceType', 'question')
                tz_offset = data.get('tz_offset')
                try:
                    tz_offset = int(tz_offset) if tz_offset is not None else None
                except (ValueError, TypeError):
                    tz_offset = None
                allowed = check_and_increment_limit(uid, svc, tz_offset)
                _, _, is_paid = has_access(uid)
                body = _json.dumps({
                    'allowed': allowed,
                    'count':   get_daily_count(uid),
                    'limit':   _get_daily_limit(is_paid, uid),
                }).encode()
                self.send_response(200)

        # POST /api/save_reading  body: { initData, cardName, meaning, mode }
        # → { ok: true }  (только для Premium; для free — тоже ok, но не сохраняем)
        elif parsed_path == '/api/save_reading':
            uid = validate_init_data(data.get('initData', ''))
            if not uid:
                body = _json.dumps({'ok': False, 'error': 'invalid_init_data'}).encode()
                self.send_response(403)
            else:
                _, _, is_paid = has_access(uid)
                if is_paid:
                    card_name = str(data.get('cardName', ''))[:100]
                    meaning   = str(data.get('meaning', ''))[:2000]
                    mode      = str(data.get('mode', 'question'))[:20]
                    now_str   = datetime.datetime.utcnow().isoformat()
                    with conn:
                        conn.execute(
                            'INSERT INTO readings_history (user_id, card_name, meaning_text, mode, created_at) '
                            'VALUES (?, ?, ?, ?, ?)',
                            (uid, card_name, meaning, mode, now_str)
                        )
                body = _json.dumps({'ok': True}).encode()
                self.send_response(200)

        else:
            body = b'Not Found'
            self.send_response(404)

        self.send_header('Content-Type', 'application/json')
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass  # тишина в логах

def _start_api_server():
    server = ThreadingHTTPServer(('0.0.0.0', API_PORT), _MiniAppHandler)
    logger.info(f"Mini App API запущен на порту {API_PORT}")
    server.serve_forever()

if __name__ == '__main__':
    threading.Thread(target=_start_api_server, daemon=True).start()
    threading.Thread(target=push_scheduler, daemon=True).start()

    logger.info("Бот успешно запущен (с меню команд, пушами и премиум 3-card)! Ожидаю сообщений от пользователей...")
    bot.set_my_commands([
        telebot.types.BotCommand("/start", "🔮 Открыть Расклад"),
        telebot.types.BotCommand("/profile", "👤 Профиль и Рефералы"),
        telebot.types.BotCommand("/buy", "💎 Premium Доступ"),
        telebot.types.BotCommand("/settings", "⚙️ Настройки Уведомлений")
    ])
    bot.infinity_polling()
