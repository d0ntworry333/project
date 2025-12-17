"""
Скрипт для получения информации о Telegram боте по токену из .env файла
"""
import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot

# Загружаем переменные из .env файла
load_dotenv()

# Получаем токен из переменной окружения
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')


async def get_bot_info():
    """Получает информацию о боте через Telegram Bot API"""
    if not BOT_TOKEN:
        print("❌ Ошибка: Токен бота не найден в файле .env!")
        print("Убедитесь, что в файле .env есть строка: TELEGRAM_BOT_TOKEN=your_token_here")
        return
    
    try:
        # Создаем экземпляр бота
        bot = Bot(token=BOT_TOKEN)
        
        # Получаем информацию о боте через метод getMe
        bot_info = await bot.get_me()
        
        # Выводим информацию
        print("=" * 50)
        print("Информация о боте:")
        print("=" * 50)
        print(f"Название бота: {bot_info.first_name}")
        if bot_info.last_name:
            print(f"Фамилия: {bot_info.last_name}")
        print(f"Username (адрес): @{bot_info.username}")
        print(f"ID бота: {bot_info.id}")
        print(f"Может присоединяться к группам: {bot_info.can_join_groups}")
        print(f"Может читать все сообщения в группах: {bot_info.can_read_all_group_messages}")
        print(f"Поддерживает inline-запросы: {bot_info.supports_inline_queries}")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Ошибка при получении информации о боте: {e}")
        print("Проверьте правильность токена в файле .env")


if __name__ == "__main__":
    asyncio.run(get_bot_info())

