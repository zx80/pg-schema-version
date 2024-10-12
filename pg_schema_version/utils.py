import logging
import sys
import hashlib

log = logging.getLogger("psv")

def bytes_hash(algo: str, data: str):
    h = hashlib.new(algo)
    h.update(data.encode('UTF-8'))
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
