"""Настройки для работы бота."""

RETRY_TIME = 600
HOSTNAME = 'https://practicum.yandex.ru/'
API_HOMEWORK = 'api/user_api/homework_statuses/'
ENDPOINT = HOSTNAME + API_HOMEWORK

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
