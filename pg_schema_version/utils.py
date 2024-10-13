import sys
import logging
import hashlib

log = logging.getLogger("psv")

def bytes_hash(algo: str, data: str, encoding: str = "UTF-8") -> str:
    """Compute signature of data with a hash algorithm."""
    h = hashlib.new(algo)
    h.update(data.encode(encoding))
    return h.hexdigest()
 
def openfiles(args: list[str] = []):
    """Generate opened files from a list of file names."""
    for fn in args:
        if fn == "-":
            yield fn, sys.stdin
        else:
            with open(fn) as fh:
                yield fn, fh
