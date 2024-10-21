import logging
import hashlib

log = logging.getLogger("psv")

class ScriptError(BaseException):
    """PSV Script Errors."""

    def __init__(self, status: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status = status

def bytes_hash(algo: str, data: bytes) -> str:
    """Compute signature of data with a hashlib algorithm."""
    h = hashlib.new(algo)
    h.update(data)
    return h.hexdigest()

def squote(s: str):
    """Simple quote escaping for psql."""
    return "'" + s.replace("'", "''") + "'"
