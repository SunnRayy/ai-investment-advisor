
import sys

def log(msg, error=False):
    """Output log to stderr, not interfering with stdout JSON output"""
    dest = sys.stderr
    prefix = "[ERROR] " if error else "[INFO] "
    print(f"{prefix}{msg}", file=dest)
