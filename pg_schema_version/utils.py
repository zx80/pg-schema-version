import sys
import logging
import hashlib

log = logging.getLogger("psv")

def bytes_hash(algo: str, data: bytes) -> str:
    """Compute signature of data with a hashlib algorithm."""
    h = hashlib.new(algo)
    h.update(data)
    return h.hexdigest()
 
def openfiles(args: list[str] = []):
    """Generate opened files from a list of file names."""
    for fn in args:
        if fn == "-":
            yield fn, sys.stdin
        else:
            with open(fn) as fh:
                yield fn, fh
