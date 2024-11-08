from requests import RequestException

from exceptions import ParserFindTagException

ERROR_LOAD_PAGE = 'Возникла ошибка при загрузке страницы {}'
ERROR_TAG_NOT_FOUND = 'Не найден тег {} {}'


def get_response(session, url, encoding='utf-8'):
    try:
        response = session.get(url)
        response.encoding = encoding
        return response
    except RequestException as e:
        raise RequestException(ERROR_LOAD_PAGE.format(url)) from e


def find_tag(soup, tag, attrs=None):
    if attrs is None:
        attrs_message = 'None'
        attrs = {}
    else:
        attrs_message = f'с атрибутами {attrs}'

    searched_tag = soup.find(tag, attrs=attrs)
    if searched_tag is None:
        raise ParserFindTagException(
            ERROR_TAG_NOT_FOUND.format(tag, attrs_message)
        )
    return searched_tag
