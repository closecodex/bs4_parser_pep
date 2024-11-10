from pathlib import Path

BASE_DIR = Path(__file__).parent
RESULTS_DIR_NAME = 'results'
DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'

SAVE_MESSAGE = 'Файл с результатами был сохранён: {file_path}'

LOG_DIR_NAME = 'logs'
LOG_DIR = BASE_DIR / LOG_DIR_NAME
LOG_FILE_NAME = 'parser.log'
LOG_FILE_PATH = LOG_DIR / LOG_FILE_NAME

DOWNLOADS_DIR_NAME = 'downloads'


def get_downloads_dir(base_dir=None):
    return base_dir / DOWNLOADS_DIR_NAME


OUTPUT_FORMAT_PRETTY = 'pretty'
OUTPUT_FORMAT_FILE = 'file'
OUTPUT_FORMAT_SILENT = 'silent'
OUTPUT_FORMAT_DEFAULT = None
LOG_FORMAT = '%(asctime)s - [%(levelname)s] - %(message)s'
DT_FORMAT = '%d.%m.%Y %H:%M:%S'

MAIN_DOC_URL = 'https://docs.python.org/3/'
PEP_INDEX_URL = 'https://peps.python.org/'

EXPECTED_STATUS = {
    'A': ('Active', 'Accepted'),
    'D': ('Deferred',),
    'F': ('Final',),
    'P': ('Provisional',),
    'R': ('Rejected',),
    'S': ('Superseded',),
    'W': ('Withdrawn',),
    '': ('Draft', 'Active'),
}
