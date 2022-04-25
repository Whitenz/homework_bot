"""Модуль содержит кастомные исключения."""


class GetAPIError(Exception):
    """Исключение поднимается при ошибочном GET-запросе к API."""

    pass


class StatusCodeError(Exception):
    """Исключение поднимается, если код статуса ответа от API не равен 200."""

    pass


class EmptyResponseError(Exception):
    """Исключение поднимается, если response содержит пустой словарь."""

    pass
