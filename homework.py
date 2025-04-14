import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telebot
from dotenv import load_dotenv
from telebot import TeleBot


load_dotenv()

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
    CHECK_TOKENS = ("PRACTICUM_TOKEN", "TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID")
    for token in CHECK_TOKENS:
        if not globals()[token]:
            text_critical_error = f'Отсутствуюет переменная окружения: {token}'
            logging.critical(text_critical_error)
            sys.exit(text_critical_error)
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """Отправляет сообщение в Telegram-чат."""
    try:
        logging.info('Начинаем отправку сообщения')
        bot.send_message(TELEGRAM_CHAT_ID, text=message)
        logging.debug('Удачная отправка сообщения в Telegram')
    except (requests.RequestException,
            telebot.apihelper.ApiException) as error:
        logging.error(f'Сбой при отправке сообщения в Telegram: {error}')


def get_api_answer(timestamp):
    """Отправляет запрос к единственному эндпоинту API-сервиса."""
    try:
        logging.info('Начинаем запрос API(ENDPOINT, HEADERS, payload)')
        payload = {'from_date': timestamp}
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        if response.status_code != HTTPStatus.OK:
            raise ValueError(
                'При отправке запроса к API вернулся код отличный от 200',
                response.reason
            )
        logging.info(
            'Успешное завершение запроса к API(ENDPOINT, HEADERS, payload)'
        )
        return response.json()
    except ConnectionError as error:
        logging.debug(
            f'Ошибка при запросе к API:(ENDPOINT, HEADERS, payload): {error}'
        )
    except requests.RequestException as error:
        logging.debug(
            f'Ошибка при запросе к API:(ENDPOINT, HEADERS, payload): {error}'
        )


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    logging.info('Начинаем проверку ответа API')
    if not isinstance(response, dict):
        raise TypeError(f'Тип ответа API {type(response)} ожидаем словарь')
    if ['homeworks'] in response.get('homeworks'):
        if not isinstance(response.get('homeworks'), list):
            raise TypeError(
                'Ожидаем список тип ответа API под ключом homeworks',
                {type(response.get('homeworks'))})
    if (['homeworks'] or (['current_date']) not in response.get()):
        logging.info('Успешная проверка ответа API')
        return response
    else:
        raise KeyError(
            'В ответе API отсутствуют ключи homeworks или current_date'
        )


def parse_status(homework):
    """Извлекает статус конкретной домашней работе."""
    logging.info('Начало проверки статуса работы')
    if 'homework_name' not in homework:
        raise KeyError('В ответе API отсутствуют ключ homework_name')
    if 'status' not in homework:
        raise KeyError('В ответе API отсутствуют ключ status')
    homework_status = homework.get('status')
    homework_name = homework.get('homework_name')
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError(f'В ответе API отсутствует статус {homework_status}')
    verdict = HOMEWORK_VERDICTS[homework_status]
    logging.info('Успешное окончание проверки статуса работы')
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
            homeworks = check_response(response)
            if homeworks['homeworks']:
                message = parse_status(homeworks['homeworks'][0])
            else:
                message = 'Отсутствуют новые статусы'
                logging.debug(message)
            send_message(bot, message)
            timestamp = response.get('current_date', int(time.time()))
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message, exc_info=True)
            if message != empty_message:
                send_message(bot, message)
                empty_message = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        format=(
            '%(lineno)d, %(funcName)s, %(asctime)s, %(levelname)s, %(message)s'
        ),
        level=logging.DEBUG,
        handlers=[
            logging.FileHandler('my_logger.log'),
            logging.StreamHandler(sys.stdout),
        ]
    )
    main()
