# -*- coding: utf-8 -*-
"""Credential-safe execution helper for the Wave 4 runtime (wave4_odoo /
wave4_pg containers).

The database password is never placed in a subprocess argument list
(so it cannot appear in `ps aux`/`docker inspect`/host process-listing
output while a command runs) and never printed or written to a log
file. Instead:

  1. The password is read once from the wave4_pg container's own
     environment (`docker exec wave4_pg printenv POSTGRES_PASSWORD`,
     which is itself argument-free of the secret) into this Python
     process's memory.
  2. It is written into a `.pgpass` file INSIDE the wave4_odoo
     container by piping it over stdin to `docker exec -i` (a pipe,
     not an argument -- never visible in any process listing), with
     the file created at mode 0600 via `umask 077` before the write.
     libpq (which psycopg2/Odoo's db layer uses) reads this file
     automatically for password lookup; no --db_password flag and no
     PGPASSWORD environment variable are ever passed to `odoo`.
  3. The file is removed from the container when the process using it
     is done (`cleanup()` / the `with secure_pg_auth():` context
     manager below), and always via a `try/finally`.

Usage as a context manager:

    from wave4_pg_secure_exec import secure_pg_auth, run_odoo

    with secure_pg_auth():
        rc, log = run_odoo(["-d", "mydb", "--db_host=wave4_pg",
                             "--db_user=odoo", "-i", "kyc_management",
                             "--stop-after-init", "--no-http"])

Usage as a CLI (mirrors the older tools/_wave4_runner.py contract, for
drop-in use in shell one-liners):

    python tools/wave4_pg_secure_exec.py <log_path> -- <odoo args...>
    python tools/wave4_pg_secure_exec.py --stdin <script.py> <log_path> -- shell ...
"""
import contextlib
import subprocess
import sys

ODOO_CONTAINER = "wave4_odoo"
PG_CONTAINER = "wave4_pg"
PG_HOST = "wave4_pg"
PG_USER = "odoo"
PGPASS_PATH = "/var/lib/odoo/.pgpass"


def _get_pg_password():
    r = subprocess.run(
        ["docker", "exec", PG_CONTAINER, "printenv", "POSTGRES_PASSWORD"],
        capture_output=True, text=True,
    )
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError("could not fetch POSTGRES_PASSWORD: %s" % r.stderr)
    return r.stdout.strip()


def _write_pgpass(password):
    pgpass_line = "%s:*:*:%s:%s\n" % (PG_HOST, PG_USER, password)
    cmd = [
        "docker", "exec", "-i", ODOO_CONTAINER,
        "sh", "-c", "umask 077 && cat > %s" % PGPASS_PATH,
    ]
    r = subprocess.run(cmd, input=pgpass_line, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("could not write .pgpass in container: %s" % r.stderr)


def _remove_pgpass():
    subprocess.run(
        ["docker", "exec", ODOO_CONTAINER, "rm", "-f", PGPASS_PATH],
        capture_output=True, text=True,
    )


@contextlib.contextmanager
def secure_pg_auth():
    """Places a .pgpass file in wave4_odoo for the duration of the block,
    with the password never touching any subprocess argument list."""
    password = _get_pg_password()
    _write_pgpass(password)
    del password
    try:
        yield
    finally:
        _remove_pgpass()


def run_odoo(odoo_args, stdin_text=None):
    """Run `odoo <odoo_args>` inside wave4_odoo. Must be called within a
    `with secure_pg_auth():` block. Returns (returncode, combined_log_text).
    Never passes --db_password or PGPASSWORD -- relies on the .pgpass
    file placed by secure_pg_auth()."""
    cmd = ["docker", "exec"]
    if stdin_text is not None:
        cmd.append("-i")
    cmd += [ODOO_CONTAINER, "odoo", *odoo_args]
    proc = subprocess.run(cmd, capture_output=True, text=True, input=stdin_text)
    log = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    return proc.returncode, log


def run_psql(db, sql):
    """Run one SQL statement via psql inside wave4_pg and return
    (returncode, stdout). Uses trust-auth from inside the container
    network -- no password needed for this path (verified: `psql -U
    odoo` from inside wave4_pg does not prompt)."""
    cmd = ["docker", "exec", PG_CONTAINER, "psql", "-U", PG_USER, "-d", db,
           "-t", "-A", "-c", sql]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip()


def _cli_main():
    args = sys.argv[1:]
    if "--" not in args:
        print(__doc__, file=sys.stderr)
        return 2
    sep = args.index("--")
    stdin_file = None
    if args[0] == "--stdin":
        stdin_file = args[1]
        log_path = args[2]
    else:
        log_path = args[0]
    odoo_args = args[sep + 1:]

    stdin_text = None
    if stdin_file:
        with open(stdin_file, "r", encoding="utf-8") as fh:
            stdin_text = fh.read()

    with secure_pg_auth():
        rc, log = run_odoo(odoo_args, stdin_text=stdin_text)
    with open(log_path, "w", encoding="utf-8") as fh:
        fh.write(log)
    tail = "\n".join(log.splitlines()[-15:])
    print("exit=%s log=%s bytes=%s" % (rc, log_path, len(log)))
    print("--- tail ---")
    print(tail)
    return rc


if __name__ == "__main__":
    sys.exit(_cli_main())
