"""
Telegram-бот для работы с API сервиса Яндекс.Практикум.

Узнаёт статус вашей домашней работы с заданным интервалом и отправляет
 его в Ваш заданный Telegram-чат.
"""

import logging
import os
import sys
import time
from http import HTTPStatus
from typing import Dict, List

import requests
from dotenv import load_dotenv
from telegram import Bot

import exceptions

logger = logging.getLogger(__name__)
logger_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(logger_handler)
logger.setLevel(logging.DEBUG)
logger_handler.setFormatter(
    logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s'
    )
)


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


def send_message(bot: Bot, message: str) -> None:
    """Функция отправляет сообщение в заданный чат Telegram."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
    except Exception as error:
        logger.error(f'Сбой при отправке сообщения в чат Telegram: {error}')
    else:
        logger.info(f'Бот отправил сообщение "{message}"')


def get_api_answer(current_timestamp: int) -> Dict:
    """Функция делает запрос к API Яндекс.Практикума."""
    params = {'from_date': current_timestamp}

    try:
        response = requests.get(url=ENDPOINT,
                                params=params,
                                headers=HEADERS
                                )
    except Exception as error:
        raise exceptions.GetAPIError(
            f'ошибка при запросе к API сервиса - {error}'
        )
    else:
        if response.status_code == HTTPStatus.OK:
            return response.json()
        else:
            raise exceptions.StatusCodeError(
                'ошибка при запросе к API сервиса - '
                f'код ответа API: {response.status_code}'
            )


def check_response(response: Dict) -> List:
    """Функция проверяет корректность ответа API."""
    if not isinstance(response, (dict, list)):
        raise exceptions.ResponseNotDictError(
            'API не вернул нужный тип данных'
        )

    if not bool(response):
        raise exceptions.EmptyResponseError(
            'ответ API содержит пустой словарь'
        )

    try:
        homeworks = response['homeworks']
    except KeyError as error:
        raise KeyError(
            f'ответ API не содержит ключ {error}'
        )

    if not isinstance(homeworks, list):
        raise exceptions.HomeworkIsNotListError(
            'переменная "homework" не является списком'
        )

    return homeworks


def parse_status(homework: Dict) -> str:
    """Функция извлекает информацию о домашней работе."""
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
        verdict = HOMEWORK_STATUSES[homework_status]
    except KeyError as error:
        raise KeyError(
            f'ошибка при парсинге данных, недоступен ключ {error}'
        )
    else:
        return (
            f'Изменился статус проверки работы "{homework_name}". {verdict}'
        )


def check_tokens() -> bool:
    """Функция проверяет доступность необходимых переменных окружения."""
    env_vars = {'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
                'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
                'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
                }
    for k, v in env_vars.items():
        if v is None:
            logger.critical(
                f'Отсуствует необходимая переменная окружения: "{k}".'
            )
            return False

    return True


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Работа программы завершена.')
        sys.exit()

    bot = Bot(token=TELEGRAM_TOKEN)
    status = None
    message = None

    while True:
        try:
            current_timestamp = int(time.time())
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if len(homeworks):
                new_status = parse_status(homeworks[0])
            else:
                new_status = 'За данный период времени нет сведений.'
        except Exception as error:
            new_message = f'Сбой в работе программы: {error}.'
            logger.error(new_message)
            if message != new_message:
                message = new_message
                send_message(bot, message)

            time.sleep(RETRY_TIME)
        else:
            if status != new_status:
                status = new_status
                send_message(bot, status)
            else:
                logger.debug('Статус работы не изменился.')

            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
