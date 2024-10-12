import logging
import sys
import hashlib

log = logging.getLogger("psv")

def bytes_hash(algo: str, data: str, encoding: str = "UTF-8"):
    h = hashlib.new(algo)
    h.update(data.encode(encoding))
    return h.hexdigest()
 
def openfiles(args: list[str] = []):
    if not args:  # empty list is same as stdin
        args = ["-"]
    for fn in args:
        if fn == "-":
            yield fn, sys.stdin
        else:
            with open(fn) as fh:
                yield fn, fh
