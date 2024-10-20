import os
import sys
import re
import logging
import argparse
from .utils import log, bytes_hash, squote
from .psql import SCRIPT_HEADER, FILE_HEADER, FILE_FOOTER, SCRIPT_FOOTER

class ScriptError(BaseException):
    pass

class Script:
    """Hold an SQL script."""

    def __init__(self, filename: str, trust = False, hasher = "sha3_256", encoding = "UTF-8"):
        # read
        self._filename = filename
        if filename == "-":
            script = sys.stdin.read()
        else:
            with open(filename) as f:
                script = f.read()
        # checks
        if not re.match(r"\s*--\s*psv\s*:", script):
            raise ScriptError(f"script {filename} missing psv header: -- psv: …")
        m = re.match(r"\s*--\s*psv\s*:\s*(\w+)\s*([-+])\s*(\d+)(\s+(.*?)\s*)?$", script, re.M)
        if not m:
            raise ScriptError(f"script {filename} unexpected psv header")
        if re.search(r"^\s*\\", script, re.M):
            if trust:
                log.warning(f"script {filename} seems to contain a backslash command")
            else:
                raise ScriptError(f"script {filename} contains a backslash command")
        if re.search(r"^\s*(commit|rollback|savepoint)\b", script, re.I|re.M):
            if trust:
                log.warning(f"script {filename} seems to contain a transaction command")
            else:
                raise ScriptError(f"script {filename} contains a transaction command")
        # extract and store
        self._script = script
        self._name = m.group(1)
        self._forward = m.group(2) == "+"
        self._version = int(m.group(3))
        self._description = m.group(5)
        if not self._description:
            self._description = f"{self._name} {'forward' if self._forward else 'reverse'} {self._version}"
        self._signature = bytes_hash(hasher, script.encode(encoding))

    def __str__(self):
        """Generate psql script."""
        out = FILE_HEADER.format(
            file=self._filename, version=self._version,
            signature=self._signature, description=squote(self._description),
            filename=self._filename.split("/")[-1],
            forward=1 if self._forward else 0,
            operation="apply" if self._forward else "reverse",
        )
        out += self._script
        out += FILE_FOOTER
        return out

def check_versions(scripts: list[Script], partial=False):
    """Tell about version errors."""
    bads = set(filter(lambda s: s._version < 1, scripts))
    # version < 1
    if bads:
        raise ScriptError(f"unexpected non positive versions: {' '.join(str(v._version) for v in bads)}")
    versions = set(s._version for s in scripts)
    # repeated
    if len(versions) != len(scripts):
        seen, repeated = set(), set()
        for s in scripts:
            if s._version in seen:
                repeated.add(s._version)
            else:
                seen.add(s._version)
        msg = f"repeated versions: {' '.join(str(v) for v in sorted(repeated))}"
        if partial:
            log.warning(msg)
        else:
            raise ScriptError(msg)
    # missing
    latest = max(s._version for s in scripts)
    expected = set(range(1, latest+1))
    if len(versions) != len(expected):
        msg = f"missing versions: {' '.join(str(v) for v in sorted(expected - versions))}"
        if partial:
            log.warning(msg)
        else:
            raise ScriptError(msg)

def gen_psql_script(args):
    """Generate an idempotent psql script."""

    log.info(f"loading {len(args.sql)} scripts…")

    # load all scripts
    scripts = [Script(fn, args.trust_scripts, args.hash, args.encoding) for fn in args.sql]

    # check name consistency
    if not args.app and scripts:
        args.app = scripts[0]._name
    if args.app:
        log.info(f"considering scripts for application {args.app}")
        bad_names = [script for script in scripts if script._name != args.app]
        if bad_names:
            filenames = ", ".join(script._filename for script in scripts)
            raise ScriptError(f"inconsistent application name found in: {filenames}")

    # order and check versions
    forwards = sorted((s for s in scripts if s._forward), key=lambda s: s._version)
    if forwards:
        check_versions(forwards, args.partial)

    backwards = sorted((s for s in scripts if not s._forward), key=lambda s: s._version, reverse=True)
    if backwards:
        check_versions(backwards, args.partial)

    assert len(forwards) + len(backwards) == len(scripts)

    if backwards and len(forwards) != len(backwards):
        if args.partial:
            log.warning("asymmetrical steps")
        else:
            raise ScriptError("asymmetrical steps")

    # actual psql generation
    log.info("generating schema construction script for {args.app}")

    def output(s: str):
        print(s, file=args.out, end="")

    output(SCRIPT_HEADER.format(app=args.app, schema=squote(args.schema), table=squote(args.table)))
    for script in forwards + backwards:
        log.info(f"considering file {script._filename} for step {args.app} {script._version}")
        output(str(script))
    output(SCRIPT_FOOTER.format(app=args.app))

    log.info(f"generation for {args.app} done")

    return 0

def psv():
    """Actual Postgres schema version script."""

    logging.basicConfig(level=logging.WARN)

    ap = argparse.ArgumentParser(
            prog="pg-schema-version",
            description="Generate an idempotent psql script for Postgres schema versioning.",
            epilog="All software have bugs…")
    ap.add_argument("-d", "--debug", default=False, action="store_true",
                    help="set debug mode")
    ap.add_argument("-v", "--verbose", default=False, action="store_true",
                    help="set verbose mode")
    ap.add_argument("-a", "--app", type=str, default=None,
                    help="expected application name")
    ap.add_argument("-s", "--schema", type=str, default="public",
                    help="schema name for psv infra, default is 'public'")
    ap.add_argument("-t", "--table", type=str, default="psv_app_status",
                    help="table name for psv infra, default is 'psv_app_status'")
    ap.add_argument("-e", "--encoding", type=str, default="UTF-8",
                    help="sql file encoding, default is 'UTF-8'")
    ap.add_argument("-H", "--hash", type=str, default="sha3_256",
                    help="hashlib algorithm for step signature, default is 'sha3_256'")
    ap.add_argument("-o", "--out", type=str, default=sys.stdout,
                    help="output script, default on stdout")
    ap.add_argument("-p", "--partial", default=False, action="store_true",
                    help="allow partial scripts")
    ap.add_argument("-T", "--trust-scripts", default=False, action="store_true",
                    help="blindly trust provided scripts")
    ap.add_argument("sql", nargs="*",
                    help="sql data definition files")
    args = ap.parse_args()

    if args.debug:
        log.setLevel(logging.DEBUG)
    elif args.verbose:
        log.setLevel(logging.INFO)

    if isinstance(args.out, str):
        if os.path.exists(args.out):
            log.error(f"psv will not overwrite output file {args.out}, remove it first")
            return 3
        args.out = open(args.out, "w")

    try:
        return gen_psql_script(args)
    except ScriptError as e:
        log.error(str(e))
        if args.debug:
            raise
        return 4
