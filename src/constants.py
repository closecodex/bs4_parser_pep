from pathlib import Path

BASE_DIR = Path(__file__).parent
RESULTS_DIR_NAME = 'results'
DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'

SAVE_MESSAGE = 'Файл с результатами был сохранён: {file_path}'

LOG_DIR_NAME = 'logs'
LOG_DIR = BASE_DIR / LOG_DIR_NAME
LOG_FILE_NAME = 'parser.log'
LOG_FILE_PATH = LOG_DIR / LOG_FILE_NAME


def get_downloads_dir(base_dir=None):
    if base_dir is None:
        base_dir = Path(__file__).parent
    return base_dir / 'downloads'


OUTPUT_FORMATS = ('pretty', 'file')
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
