class PageLoadError(Exception):
    """Вызывается, когда выходит ошибка при загрузке страницы."""


class ParserFindTagException(Exception):
    """Вызывается, когда парсер не может найти тег."""
