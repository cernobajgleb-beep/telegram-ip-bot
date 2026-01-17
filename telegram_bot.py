# Telegram IP Bot v2.0
# Этот бот показывает информацию об IP-адресах
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем токен
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TELEGRAM_TOKEN:
    raise ValueError("Пожалуйста, установите TELEGRAM_TOKEN в файле .env")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = """
👋 Привет! Я бот для получения информации об IP-адресах.

📍 Отправьте мне IP-адрес, и я покажу информацию о нем.

Примеры использования:
• Просто отправьте IP-адрес: `8.8.8.8`
• Или используйте команду: `/ip 8.8.8.8`

📍 Если не указать IP, проверю ваш текущий адрес.
    """
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📋 Доступные команды:

/start - Начать работу с ботом
/help - Показать это сообщение
/ip [адрес] - Получить информацию об IP-адресе

📌 Просто отправьте IP-адрес сообщением для получения информации.

Примеры:
`8.8.8.8` - информация об адресе Google DNS
`/ip 1.1.1.1` - информация об адресе Cloudflare
    """
    await update.message.reply_text(help_text)

def get_ip_info(ip_address):
    """Функция для получения информации об IP"""
    try:
        if not ip_address or ip_address == '':
            # Получаем внешний IP пользователя
            response = requests.get('https://api.ipify.org?format=json', timeout=10)
            ip_address = response.json()['ip']
        
        # Используем ipapi.co
        response = requests.get(f'https://ipapi.co/{ip_address}/json/', timeout=10)
        data = response.json()
        
        if 'error' not in data:
            info = f"""
📍 *Информация об IP-адресе:*

• 🆔 *IP:* `{data.get('ip', 'N/A')}`
• 🏳️ *Страна:* {data.get('country_name', 'N/A')}
• 📍 *Регион:* {data.get('region', 'N/A')}
• 🏙️ *Город:* {data.get('city', 'N/A')}
• 📡 *Провайдер:* {data.get('org', 'N/A')}
• 🌐 *Организация:* {data.get('org', 'N/A')}
• 📍 *Координаты:* {data.get('latitude', 'N/A')}, {data.get('longitude', 'N/A')}
• 🕐 *Часовой пояс:* {data.get('timezone', 'N/A')}
            """
            return info
        else:
            return f"❌ Ошибка: Не удалось получить информацию об IP {ip_address}"
            
    except requests.exceptions.ConnectionError:
        return "❌ Ошибка соединения. Пожалуйста, проверьте подключение к интернету."
    except requests.exceptions.Timeout:
        return "⏰ Таймаут запроса. Сервер не ответил вовремя."
    except Exception as e:
        logger.error(f"Error getting IP info: {e}")
        return f"⚠️ Произошла ошибка: {str(e)}"

async def ip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /ip"""
    # Если IP передан как аргумент команды
    if context.args:
        ip_address = context.args[0]
        await update.message.reply_text("🔄 Получаю информацию...")
        result = get_ip_info(ip_address)
        await update.message.reply_text(result, parse_mode='Markdown')
    else:
        # Если IP не указан, показываем информацию о текущем IP пользователя
        await update.message.reply_text("🔍 Определяю ваш IP-адрес...")
        result = get_ip_info('')
        await update.message.reply_text(result, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_message = update.message.text.strip()
    
    # Проверяем, похоже ли сообщение на IP-адрес
    if is_valid_ip(user_message):
        await update.message.reply_text("🔄 Получаю информацию...")
        result = get_ip_info(user_message)
        await update.message.reply_text(result, parse_mode='Markdown')
    else:
        # Если это не IP, предлагаем помощь
        await update.message.reply_text(
            "🤔 Это не похоже на IP-адрес.\n\n"
            "📌 Отправьте IP-адрес в формате: `8.8.8.8`\n"
            "📌 Или используйте команду: `/ip 8.8.8.8`",
            parse_mode='Markdown'
        )

def is_valid_ip(ip):
    """Проверяет, является ли строка валидным IP-адресом"""
    import re
    # Паттерн для IPv4
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    
    if re.match(ipv4_pattern, ip):
        parts = ip.split('.')
        if all(0 <= int(part) <= 255 for part in parts):
            return True
    return False

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.message:
        await update.message.reply_text(
            "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
        )

def main():
    """Основная функция запуска бота"""
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ip", ip_command))
    
    # Регистрируем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Регистрируем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    print("🤖 Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
