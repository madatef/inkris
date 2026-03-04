import logging
import sys

from app.core.context import request_id, user_id

class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id.get()
        record.user_id = user_id.get()
        return True

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored log levels"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Color the level name for console output
        if hasattr(self, 'use_color') and self.use_color:
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        
        return super().format(record)

logger = logging.getLogger("AppLogger")
logger.setLevel(logging.DEBUG)
format_string = '(%(asctime)s) [request_id=%(request_id)s user_id=%(user_id)s] %(levelname)s: %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'

# Console handler with colors
console_handler = logging.StreamHandler(sys.stdout)
console_formatter = ColoredFormatter(format_string, datefmt=date_format)
console_formatter.use_color = True
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)
logger.addFilter(RequestContextFilter())
