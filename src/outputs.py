import csv
import datetime as dt
import logging

from prettytable import PrettyTable

from constants import (
    BASE_DIR, DATETIME_FORMAT, RESULTS_DIR_NAME, 
    SAVE_MESSAGE, OUTPUT_FORMAT_FILE, OUTPUT_FORMAT_PRETTY
)

def default_output(results, *args, **kwargs):
    for row in results:
        print(*row)


def pretty_output(results, *args, **kwargs):
    table = PrettyTable()
    table.field_names = results[0]
    table.align = 'l'
    table.add_rows(results[1:])
    print(table)


def file_output(results, cli_args):
    results_dir = BASE_DIR / RESULTS_DIR_NAME
    results_dir.mkdir(exist_ok=True)
    current_time = dt.datetime.now().strftime(DATETIME_FORMAT)
    file_name = f'{cli_args.mode}_{current_time}.csv'
    file_path = results_dir / file_name
    with open(file_path, 'w', encoding='utf-8') as file:
        csv.writer(file, dialect=csv.unix_dialect).writerows(results)
    logging.info(SAVE_MESSAGE.format(file_path=file_path))


OUTPUT_FUNCTIONS = {
    OUTPUT_FORMAT_PRETTY: pretty_output,
    OUTPUT_FORMAT_FILE: file_output,
}


def control_output(results, cli_args):
    OUTPUT_FUNCTIONS.get(cli_args.output, default_output)(results, cli_args) 
