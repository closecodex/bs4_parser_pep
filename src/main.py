import csv
import logging
import re
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from utils import get_response, find_tag
from configs import configure_argument_parser, configure_logging
from constants import BASE_DIR, MAIN_DOC_URL, PEP_INDEX_URL
from outputs import control_output


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return []

    soup = BeautifulSoup(response.text, 'lxml')
    main_section = find_tag(
        soup, 'section', attrs={'id': 'what-s-new-in-python'}
    )
    sections = main_section.find_all('div', class_='toctree-wrapper compound')

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    for section in tqdm(sections):
        h2_tag = section.find('h2')
        if h2_tag is None:
            logging.warning(
                f'Не удалось найти необходимый тег в секции: {section}'
            )
            continue
        version_text = h2_tag.text.strip()
        link_tag = section.find('a')
        link = urljoin(whats_new_url, link_tag['href'])
        results.append((link, version_text, 'Неизвестный автор'))

        logging.info(f'Парсинг нововведений для версии: {version_text}')

    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return

    soup = BeautifulSoup(response.text, 'html.parser')
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
                logging.info(
                    f'Найдена версия: {version_text} со статусом: {status}'
                )

    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = get_response(session, downloads_url)
    if response is None:
        return

    soup = BeautifulSoup(response.text, 'lxml')
    main_tag = find_tag(soup, 'div', {'role': 'main'})
    table_tag = find_tag(main_tag, 'table', {'class': 'docutils'})
    pdf_a4_tag = find_tag(table_tag, 'a', {'href': re.compile(r'.+pdf-a4\.zip$')})
    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(MAIN_DOC_URL, pdf_a4_link)

    filename = archive_url.split('/')[-1]
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename

    response = get_response(session, archive_url)
    if response is None:
        return

    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')
    print(f'Файл сохранён по пути: {archive_path}')


def pep(session):
    """Парсинг статусов PEP-документов."""

    response = get_response(session, PEP_INDEX_URL)
    if response is None:
        return

    soup = BeautifulSoup(response.text, 'lxml')
    pep_links = soup.select('#pep-content td a[href^="/dev/peps/pep-"]')

    results = {}
    inconsistencies = []

    for link in tqdm(pep_links):
        pep_link = urljoin(PEP_INDEX_URL, link['href'])
        pep_response = get_response(session, pep_link)
        if pep_response is None:
            continue

        pep_soup = BeautifulSoup(pep_response.text, 'lxml')
        status_tag = find_tag(pep_soup, 'dt', string='Status')
        status = status_tag.find_next_sibling('dd').string

        pep_number = link.text.strip()
        if status not in results:
            results[status] = 0
        results[status] += 1

        expected_status = link.parent.find_next_sibling('td').text.strip()
        if expected_status and expected_status != status:
            inconsistencies.append(
                f'Несовпадающие статусы:\n{pep_link}\n'
                f'Статус в карточке: {status}\n'
                f'Ожидаемый статус: {expected_status}\n'
            )

    results_path = BASE_DIR / 'results' / 'pep_statuses.csv'
    results_path.parent.mkdir(exist_ok=True)
    with open(results_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Статус', 'Количество'])
        total = 0
        for status, count in results.items():
            total += count
            writer.writerow([status, count])
        writer.writerow(['Total', total])

    if inconsistencies:
        logging.warning('\n'.join(inconsistencies))

    logging.info(f'Результаты парсинга сохранены в {results_path}')

MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')

    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки: {args}')

    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()
        logging.info('Кеш очищен.')

    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)

    if results is not None:
        control_output(results, args)

    logging.info('Парсер завершил работу.')

if __name__ == '__main__':
    main()
