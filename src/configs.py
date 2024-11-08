import argparse
import logging
import sys
from logging.handlers import RotatingFileHandler

from constants import (
    LOG_FORMAT, DT_FORMAT,
    LOG_DIR, LOG_FILE_PATH, OUTPUT_FORMATS
)


def configure_argument_parser(available_modes):
    parser = argparse.ArgumentParser(description='Парсер документации Python')
    parser.add_argument(
        'mode',
        choices=available_modes,
        help='Режимы работы парсера'
    )
    parser.add_argument(
        '-c',
        '--clear-cache',
        action='store_true',
        help='Очистка кеша'
    )
    parser.add_argument(
        '-o',
        '--output',
        choices=OUTPUT_FORMATS,
        help='Дополнительные способы вывода данных'
    )
    return parser


def configure_logging():
    log_dir = LOG_DIR
    log_dir.mkdir(exist_ok=True)

    rotating_handler = RotatingFileHandler(
        LOG_FILE_PATH, maxBytes=10 ** 6, backupCount=5
    )
    logging.basicConfig(
        datefmt=DT_FORMAT,
        format=LOG_FORMAT,
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_FILE_PATH, mode='w', encoding='utf-8'),
            rotating_handler
        ]
    )
