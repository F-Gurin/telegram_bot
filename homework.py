import requests
import os
import time
import logging, sys

from dotenv import load_dotenv
from telegram import Bot

# import telegram
# from telegram.ext import Updater


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


class ConnectionException(Exception):
    """Ошибка соединения с API-сервисом."""

    pass


logger = logging.getLogger(__name__)

handler = logging.StreamHandler(sys.stdout)

logging.basicConfig(
    level=logging.INFO,
    filename='main.log',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
)

logger.addHandler(handler)


def send_message(bot, message):
    """Функция отправки сообщения в чат."""
    try:
        logger.info('Сообщение отправлено')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as e:
        logger.error(f'Сообщение не отправлено {e}')
    return


def get_api_answer(current_timestamp):
    """Функция с запросом к API-сервису."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    homework_statuses = requests.get(
        ENDPOINT, headers=HEADERS, params=params)

    if homework_statuses.status_code != 200:
        raise ConnectionException('Ошибка соединения с API-сервисом')

    return homework_statuses.json()


def check_response(response):
    """Функция прверки API на корректность."""
    logger.debug('Проверка ответа API на корректность')
    if not isinstance(response, dict):
        message = 'Ответ API не словарь'
        raise TypeError(message)
    if len(response['homeworks']) <= 0:
        message = 'Домашняя работа не передана на проверку'
        raise IndexError(message)
    return response['homeworks'][0]


def parse_status(homework):
    """Функция извлечения статуса домашней работы."""
    try:
        homework_name = homework.get('homework_name')
    except KeyError as error:
        error_message = f'В словаре нет ключа homework_name {error}'
        logger.error(error_message)
    try:
        homework_status = homework['status']
    except KeyError as error:
        error_message = f'В словаре нет ключа status {error}'
        logger.error(error_message)
    if homework_status not in HOMEWORK_STATUSES:
        error_message = 'Получен неизвестный статус'
        logger.error(error_message)
        raise Exception(error_message)
    if homework_status == 'approved':
        verdict = HOMEWORK_STATUSES[homework_status]
    elif homework_status == 'rejected':
        verdict = HOMEWORK_STATUSES[homework_status]
    else:
        verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка переменных окружения."""
    if (PRACTICUM_TOKEN is None
            and TELEGRAM_TOKEN is None
            and TELEGRAM_CHAT_ID is None):
        print(PRACTICUM_TOKEN)
        return False
    else:
        return True


def main():
    """Основная логика работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)
    tokens = check_tokens()
    previous_status = ''
    old_message = ''
    # bot = telegram.Bot(token=TELEGRAM_TOKEN)
    # current_timestamp = int(time.time())
    try:
        if not tokens:
            raise Exception
    except Exception:
        message = 'Отсутствие обязательных переменных окружения'
        logger.critical(message)
        send_message(bot, message)

    while True:
        try:
            # current_timestamp = int(time.time())
            response = get_api_answer(1634860800)
            homework = check_response(response)
            status = parse_status(homework)
            if previous_status != status:
                send_message(bot, status)
                previous_status = status
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if old_message != message:
                send_message(bot, message)
                old_message = message
            time.sleep(RETRY_TIME)
        # else:
            # previous_status = status


if __name__ == '__main__':
    main()
