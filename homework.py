import logging
import sys
import os
import requests
import time

from telebot import TeleBot
from dotenv import load_dotenv
from http import HTTPStatus


load_dotenv()

logging.basicConfig(
    format='%(lineno)s, %(asctime)s, %(levelname)s, %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)

PRACTICUM_TOKEN = os.getenv('TOKEN_PRACTICUM')
TELEGRAM_TOKEN = os.getenv('TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Возвращает переменные окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """Отправляет сообщение в Telegram-чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, text=message)
        logging.debug('Удачная отправка сообщения в Telegram')
    except Exception as error:
        logging.error(f'Сбой при отправке сообщения в Telegram: {error}')


def get_api_answer(timestamp):
    """Отправляет запрос к единственному эндпоинту API-сервиса."""
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=timestamp)
        if response.status_code != HTTPStatus.OK:
            raise ValueError(
                'При отправке запроса к API вернулся код отличный от 200'
            )
        return response.json()
    except requests.RequestException as error:
        logging.error(f'Ошибка при запросе к API: {error}')


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('Тип ответа API отличный от словаря')
    elif not isinstance(response.get('homeworks'), list):
        raise TypeError(
            'Тип ответа API под ключом homeworks отличный от списка'
        )
    if response.get('homeworks') or response.get('current_date') is not None:
        return response
    else:
        raise KeyError(
            'В ответе API отсутствуют ключи homeworks или current_date'
        )


def parse_status(homework):
    """Извлекает статус конкретной домашней работе."""
    if 'homework_name' not in homework:
        raise KeyError('В ответе API отсутствуют ключ homework_name')
    homework_status = homework.get('status')
    homework_name = homework.get('homework_name')
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError('В ответе API отсутствует статус')
    homework_verdicts = dict.items(HOMEWORK_VERDICTS)
    for status, verdict in homework_verdicts:
        if status == homework_status:
            return (
                f'Изменился статус проверки работы "{homework_name}".{verdict}'
            )


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        text_critical_error = 'Отсутствуют обязательные переменные окружения'
        logging.critical(text_critical_error)
        sys.exit(text_critical_error)
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    empty_message = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            timestamp = response.get('current_date', int(time.time()))
            homeworks = check_response(response)
            if homeworks['homeworks']:
                message = parse_status(homeworks['homeworks'][0])
            else:
                message = 'Отсутствуют новые статусы'
            if message != empty_message:
                send_message(bot, message)
                empty_message = message
            else:
                logging.debug(message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message, exc_info=True)
            if message != empty_message:
                send_message(bot, message)
                empty_message = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
