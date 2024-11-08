import csv
import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import requests_cache
from tqdm import tqdm

from collections import defaultdict

from configs import configure_argument_parser, configure_logging
from constants import (
    BASE_DIR, MAIN_DOC_URL, PEP_INDEX_URL, DOWNLOADS_DIR, get_downloads_dir
)
from outputs import control_output
from utils import find_tag, get_response

ARCHIVE_SAVED_MESSAGE = 'Архив был загружен и сохранён: {archive_path}'
FILE_SAVED_MESSAGE = 'Файл сохранён по пути: {archive_path}'
PARSING_STARTED_MESSAGE = 'Парсер запущен!'
ARGS_MESSAGE = 'Аргументы командной строки: {args}'
CACHE_CLEARED_MESSAGE = 'Кеш очищен.'
PARSING_FINISHED_MESSAGE = 'Парсер завершил работу.'
ERROR_MESSAGE = 'Ошибка при выполнении программы'


def get_soup(session, url, parser='lxml'):
    response = get_response(session, url)
    if response is None:
        return
    return BeautifulSoup(response.text, parser)


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    soup = get_soup(session, whats_new_url)
    if soup is None:
        return []
    main_section = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    sections = main_section.find_all('div', class_='toctree-wrapper compound')
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    errors = []
    for section in tqdm(sections):
        h2_tag = section.find('h2')
        if h2_tag is None:
            errors.append(f'Не найден тег h2 в секции: {section}')
            continue
        version_text = h2_tag.text.strip()
        link_tag = section.find('a')
        link = urljoin(whats_new_url, link_tag['href'])
        results.append((link, version_text, 'Неизвестный автор'))
    if errors:
        for error in errors:
            logging.warning(error)
    return results


def latest_versions(session):
    soup = get_soup(session, MAIN_DOC_URL, parser='html.parser')
    if soup is None:
        return []
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
    if soup is None:
        return
    pdf_a4_tag = soup.select_one(
        'div[role=\'main\'] table.docutils a[href$=\'pdf-a4.zip\']'
    )
    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(MAIN_DOC_URL, pdf_a4_link)
    filename = archive_url.split('/')[-1]
    DOWNLOADS_DIR = get_downloads_dir(base_dir=BASE_DIR)
    DOWNLOADS_DIR.mkdir(exist_ok=True)
    archive_path = DOWNLOADS_DIR / filename
    response = get_response(session, archive_url)
    if response is None:
        return
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(ARCHIVE_SAVED_MESSAGE.format(archive_path=archive_path))
    print(FILE_SAVED_MESSAGE.format(archive_path=archive_path))


def pep(session):
    soup = get_soup(session, PEP_INDEX_URL)
    if soup is None:
        return []
    pep_links = soup.select('#pep-content td a[href^=\'/dev/peps/pep-\']')
    results = defaultdict(int)
    inconsistencies = []
    failed_peps = []
    for link in tqdm(pep_links):
        pep_link = urljoin(PEP_INDEX_URL, link['href'])
        pep_soup = get_soup(session, pep_link)
        if pep_soup is None:
            failed_peps.append(pep_link)
            continue
        status_tag = find_tag(pep_soup, 'dt', string='Status')
        status = status_tag.find_next_sibling('dd').text.strip()
        results[status] += 1
        expected_status = link.parent.find_next_sibling('td').text.strip()
        if expected_status and expected_status != status:
            inconsistencies.append(
                f'Несовпадающие статусы:\n{pep_link}\n'
                f'Статус в карточке: {status}\n'
                f'Ожидаемый статус: {expected_status}\n'
            )
    if inconsistencies:
        logging.warning('\n'.join(inconsistencies))
    if failed_peps:
        logging.warning('Не удалось получить следующие страницы PEP:')
        for pep in failed_peps:
            logging.warning(pep)
    total = sum(results.values())
    results_data = [('Статус', 'Количество')] + list(results.items()) + [('Total', total)]
    return results_data


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
        logging.exception(ERROR_MESSAGE)
    else:
        logging.info(PARSING_FINISHED_MESSAGE)

if __name__ == '__main__':
    main()
