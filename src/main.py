import logging
from collections import defaultdict
from urllib.parse import urljoin

import requests_cache
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import (
    BASE_DIR, MAIN_DOC_URL, PEP_INDEX_URL, get_downloads_dir
)
from outputs import control_output
from src.exceptions import PageLoadError
from utils import find_tag, get_response, get_soup

ARCHIVE_SAVED_MESSAGE = 'Архив был загружен и сохранён: {archive_path}'
FILE_SAVED_MESSAGE = 'Файл сохранён по пути: {archive_path}'
PARSING_STARTED_MESSAGE = 'Парсер запущен!'
ARGS_MESSAGE = 'Аргументы командной строки: {args}'
CACHE_CLEARED_MESSAGE = 'Кеш очищен.'
PARSING_FINISHED_MESSAGE = 'Парсер завершил работу.'
ERROR_MESSAGE = 'Ошибка при выполнении программы'
ERROR_H2_NOT_FOUND = 'Не найден тег h2 в секции: {}'
ERROR_PEP_LOAD_FAILED = 'Не удалось загрузить страницу {}: {}'
ERROR_PAGE_LOAD_FAILED = 'Не удалось загрузить страницу {}: {}'
ERROR_STATUS_NOT_FOUND = 'Не удалось найти статус на странице {}'
DEFAULT_AUTHOR = 'Неизвестный автор'
INCONSISTENCY_MESSAGE = (
    'Несовпадающие статусы:\n{pep_link}\n'
    'Статус в карточке: {status}\n'
    'Ожидаемый статус: {expected_status}'
)
FAILED_PEPS_MESSAGE = 'Не удалось получить следующие страницы PEP:'


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    soup = get_soup(session, whats_new_url)
    main_section = find_tag(
        soup, 'section', attrs={'id': 'what-s-new-in-python'}
    )
    sections = main_section.find_all('div', class_='toctree-wrapper compound')
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    errors = []
    for section in tqdm(sections):
        h2_tag = section.find('h2')
        if h2_tag is None:
            errors.append(ERROR_H2_NOT_FOUND.format(section))
            continue
        version_text = h2_tag.text.strip()
        link_tag = section.find('a')
        link = urljoin(whats_new_url, link_tag['href'])
        try:
            new_page_soup = get_soup(session, link)
        except ConnectionError as e:
            errors.append(ERROR_PAGE_LOAD_FAILED.format(link, e))
            continue

        author_tag = new_page_soup.find('p', class_='author')
        author_text = (
            author_tag.text.strip()
            if author_tag else DEFAULT_AUTHOR
        )
        results.append((link, version_text, author_text))
    if errors:
        logging.warning('\n'.join(errors))

    return results


def latest_versions(session):
    soup = get_soup(session, MAIN_DOC_URL, parser='html.parser')
    sidebar = find_tag(soup, 'div', {'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            for a_tag in a_tags:
                href = urljoin(MAIN_DOC_URL, a_tag['href'])
                version_text = a_tag.text
                status = 'EOL'
                if 'in development' in version_text.lower():
                    status = 'in development'
                elif 'stable' in version_text.lower():
                    status = 'stable'
                elif 'security-fixes' in version_text.lower():
                    status = 'security-fixes'
                elif 'pre-release' in version_text.lower():
                    status = 'pre-release'
                results.append((href, version_text, status))
    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    soup = get_soup(session, downloads_url)
    pdf_a4_tag = soup.select_one(
        'div[role="main"] table.docutils a[href$="pdf-a4.zip"]'
    )
    archive_url = urljoin(MAIN_DOC_URL, pdf_a4_tag['href'])
    filename = archive_url.split('/')[-1]
    DOWNLOADS_DIR = get_downloads_dir(base_dir=BASE_DIR)
    DOWNLOADS_DIR.mkdir(exist_ok=True)
    archive_path = DOWNLOADS_DIR / filename
    response = get_response(session, archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(ARCHIVE_SAVED_MESSAGE.format(archive_path=archive_path))


def pep(session):
    soup = get_soup(session, PEP_INDEX_URL)
    pep_links = soup.select('#pep-content td a[href^=\'/dev/peps/pep-\']')
    results = defaultdict(int)
    inconsistencies = []
    failed_peps = []

    for link in tqdm(pep_links):
        pep_link = urljoin(PEP_INDEX_URL, link['href'])
        process_pep_link(
            session, pep_link, link, results,
            inconsistencies, failed_peps
        )

    list(map(logging.warning, inconsistencies))
    if failed_peps:
        logging.warning(FAILED_PEPS_MESSAGE)
        list(map(logging.warning, failed_peps))

    return [
        ('Статус', 'Количество'),
        *results.items(),
        ('Total', sum(results.values())),
    ]


def process_pep_link(
    session, pep_link, link, results,
    inconsistencies, failed_peps
):
    try:
        pep_soup = get_soup(session, pep_link)
    except PageLoadError as e:
        failed_peps.append(ERROR_PEP_LOAD_FAILED.format(pep_link, e))
        return

    status_tag = find_tag(pep_soup, 'dt', string='Status')
    if status_tag is None:
        failed_peps.append(ERROR_STATUS_NOT_FOUND.format(pep_link))
        return

    status = status_tag.find_next_sibling('dd').text.strip()
    results[status] += 1

    expected_status = link.parent.find_next_sibling('td').text.strip()
    if expected_status and expected_status != status:
        inconsistencies.append(
            INCONSISTENCY_MESSAGE.format(
                pep_link=pep_link,
                status=status,
                expected_status=expected_status
            )
        )


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info(PARSING_STARTED_MESSAGE)
    try:
        arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
        args = arg_parser.parse_args()
        logging.info(ARGS_MESSAGE.format(args=args))

        session = requests_cache.CachedSession()
        if args.clear_cache:
            session.cache.clear()
            logging.info(CACHE_CLEARED_MESSAGE)

        parser_mode = args.mode
        results = MODE_TO_FUNCTION[parser_mode](session)

        if results:
            control_output(results, args)
    except Exception as e:
        logging.exception(ERROR_MESSAGE.format(error=str(e)))
    logging.info(PARSING_FINISHED_MESSAGE)


if __name__ == '__main__':
    main()
