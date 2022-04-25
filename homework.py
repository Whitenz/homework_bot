"""
Telegram-бот для работы с API сервиса Яндекс.Практикум.

Узнаёт статус вашей домашней работы с заданным интервалом и отправляет
 его в Ваш заданный Telegram-чат.
"""

import logging
import logging.config
import os
import sys
import time
from http import HTTPStatus
from typing import Dict, List

import requests
import telegram
from dotenv import load_dotenv

import exceptions
import settings

logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)

load_dotenv()
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


def send_message(bot: telegram.Bot, message: str) -> None:
    """Функция отправляет сообщение в заданный чат Telegram."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
    except telegram.error.Unauthorized:
        logger.error(
            'Сбой при отправке сообщения в чат Telegram: '
            'у бота недостаточно прав для отправки сообщения в заданный чат.'
        )
        raise
    except telegram.error.InvalidToken as error:
        logger.error(
            'Сбой при отправке сообщения в чат Telegram: '
            f'ошибка в токене Telegram-бота - "{error}".'
        )
        raise
    except telegram.error.NetworkError as error:
        logger.error(
            'Сбой при отправке сообщения в чат Telegram: '
            f'ошибка сетевого подключения - "{error}".'
        )
        raise

    logger.info(f'Бот отправил сообщение "{message}"')


def get_api_answer(current_timestamp: int) -> Dict:
    """Функция делает запрос к API Яндекс.Практикума."""
    params = {'from_date': current_timestamp}

    try:
        response = requests.get(
            url=settings.ENDPOINT,
            params=params,
            headers=HEADERS
        )
    except Exception as error:
        raise exceptions.GetAPIError(
            f'ошибка при запросе к API сервиса - {error}'
        )

    if response.status_code == HTTPStatus.OK:
        return response.json()
    else:
        raise exceptions.StatusCodeError(
            'ошибка при запросе к API сервиса - '
            f'код ответа API: {response.status_code}'
        )


def check_response(response: Dict) -> List:
    """Функция проверяет корректность ответа API."""
    if type(response) != dict:
        raise TypeError(
            'API не вернул нужный тип данных'
        )

    if not bool(response):
        raise exceptions.EmptyResponseError(
            'ответ API содержит пустой словарь'
        )

    homeworks = response.get('homeworks')
    if homeworks is None:
        raise KeyError(
            'ответ API не содержит ключ "homeworks"'
        )

    if type(homeworks) != list:
        raise TypeError(
            'переменная "homeworks" не является списком'
        )

    return homeworks


def parse_status(homework: Dict) -> str:
    """Функция извлекает информацию о домашней работе."""
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
        verdict = settings.HOMEWORK_STATUSES[homework_status]
    except KeyError as error:
        raise KeyError(
            f'ошибка при парсинге данных, недоступен ключ {error}'
        )
    return (
        f'Изменился статус проверки работы "{homework_name}". {verdict}'
    )


def check_tokens() -> bool:
    """Функция проверяет доступность необходимых переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical(
            'Отсутствуют необходимые переменные окружения. '
            'Работа программы завершена.'
        )
        sys.exit()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    status = None
    message = None

    while True:
        try:
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
            time.sleep(settings.RETRY_TIME)

        if status != new_status:
            status = new_status
            send_message(bot, status)
        else:
            logger.debug('Статус работы не изменился.')
        time.sleep(settings.RETRY_TIME)


if __name__ == '__main__':
    main()
