import os

from common import HOST

# Configuration
CONFIG = {
    'freeswitch': {
        'host': '127.0.0.1',
        'port': 8021,
        'password': os.environ['FS_ESL_PASSWORD']
    },
    'api': {
        'base_url': f'{HOST}/api/v1/telephony/notify',
        'timeout': 5,
        'retry_attempts': 3,
        'retry_delay': 3
    }
}