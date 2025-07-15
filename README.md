###Данный проект - Telegram-бот для отслеживания статуса моей домашней работы.
Что делает бот: раз в 10 минут опрашивает API сервис и проверяет статус моей домашней работы, при обновлении статуса анализирует ответ API и отправляет мне уведомление в Telegram, логирует свою работу и отправляет мне уведомление в Telegram в случае возникновения важных проблем.

###Технологии:
Python
pyTelegramBotAPI

###Шаги запуска игры:
Клонируйте репозиторий: git clone git@github.com:Tleuberdina/homework-bot.git
cd homework-bot
разверните и активируйте виртуальное окружение
Команда для Windows:
python -m venv venv source venv/Scripts/activate

Команда для Linux и macOS:
python3 -m venv venv source venv/bin/activate
Установите зависимости проекта: pip install -r requirements.txt
запуск бота: python homework.py
