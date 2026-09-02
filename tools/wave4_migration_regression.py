# -*- coding: utf-8 -*-
"""Wave 4 existing-database migration-safety regression suite.

Builds a pre-migration snapshot of kyc_management/aml_compliance at
the last commit before the _sql_constraints -> models.Constraint /
groups_id -> group_ids fix (default: bcefd39, the parent of f4f4a71),
installs it into disposable databases, seeds clean and deliberately
conflicting ("dirty") representative data, then upgrades each to the
current working tree's code and asserts the fail-closed migration
guard (kyc_management/migrations/19.0.1.0.2/,
aml_compliance/migrations/19.0.1.0.1/) behaves correctly:

  * clean data upgrades successfully, all required constraints attach,
    historical data survives, KYC officer routing works against the
    migrated data, and a second update is idempotent.
  * dirty data is BLOCKED (non-zero exit), no records are modified,
    the module version does not advance, and no partial constraint
    state is left behind.
  * once the dirty data is corrected (simulating an approved
    remediation, applied directly to the fixture -- this script never
    remediates production data), the retry succeeds and all
    constraints attach.

Requires the wave4_odoo / wave4_pg containers (see
docs/WAVE_4_INSTALL_REGRESSION_RESULT.md for how they are provisioned)
and must be run with the repository as the container's bind-mounted
addons path. Uses tools/wave4_pg_secure_exec.py for all database
authentication -- the password never appears in any subprocess
argument list.

Usage:
    python tools/wave4_migration_regression.py [--pre-migration-rev bcefd39]
                                                [--keep-databases]

Exit code is 0 only if every assertion in this file passes.
"""
import argparse
import re
import subprocess
import sys
import tempfile
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wave4_pg_secure_exec import secure_pg_auth, run_odoo, run_psql  # noqa: E402

DEFAULT_PREMIGRATION_REV = "bcefd39"
SNAPSHOT_ADDONS_PATH = "/mnt/extra-addons/.wave4_regression_snapshot,/mnt/extra-addons"
CURRENT_ADDONS_PATH = None  # None => use the container's default (current tree)

DB_PREFIX = "wave4_migreg"

KYC_REQUIRED_CONSTRAINTS = ["kyc_application_kyc_id_unique"]
AML_REQUIRED_CONSTRAINTS = [
    "aml_fatf_jurisdiction_country_uniq",
    "aml_risk_factor_code_uniq",
    "aml_risk_factor_weight_positive",
    "aml_sanctions_list_name_source_uniq",
]

SEED_KYC_CLEAN = """
approver_group = env.ref('kyc_management.group_kyc_approver')
officer = env['res.users'].create({
    'name': 'Wave4 Regression Officer',
    'login': 'wave4_migreg_officer@example.com',
    'email': 'wave4_migreg_officer@example.com',
    'group_ids': [(4, approver_group.id)],
})
partner = env['res.partner'].create({'name': 'Wave4 Migreg Clean Partner', 'email': 'wave4migregclean@example.com'})
app = env['kyc.application'].create({
    'kyc_id': 'KYC-MIGREG-CLEAN-001', 'partner_id': partner.id,
    'email': 'wave4migregclean@example.com', 'phone': '+971500000101',
    'first_name': 'Wave4MigregClean', 'last_name': 'Tester',
})
env.cr.commit()
print("SEED_OK app=%s officer=%s" % (app.id, officer.id))
"""

SEED_KYC_DIRTY = """
p1 = env['res.partner'].create({'name': 'Wave4 Migreg Dirty A', 'email': 'wave4migregdirtyA@example.com'})
p2 = env['res.partner'].create({'name': 'Wave4 Migreg Dirty B', 'email': 'wave4migregdirtyB@example.com'})
a1 = env['kyc.application'].create({
    'kyc_id': 'KYC-MIGREG-DUP-001', 'partner_id': p1.id,
    'email': 'wave4migregdirtyA@example.com', 'phone': '+971500000102',
    'first_name': 'Wave4MigregDirtyA', 'last_name': 'Tester',
})
a2 = env['kyc.application'].create({
    'kyc_id': 'KYC-MIGREG-DUP-001', 'partner_id': p2.id,
    'email': 'wave4migregdirtyB@example.com', 'phone': '+971500000103',
    'first_name': 'Wave4MigregDirtyB', 'last_name': 'Tester',
})
env.cr.commit()
print("SEED_OK a1=%s a2=%s" % (a1.id, a2.id))
"""

SEED_AML_CLEAN = """
country = env.ref('base.de')
env['aml.fatf.jurisdiction'].create({'country_id': country.id, 'risk_level': 'grey'})
env['aml.risk.factor'].create({'name': 'Wave4 Migreg Clean Factor', 'code': 'WAVE4-MIGREG-CLEAN', 'category': 'customer', 'weight': 1.0})
env['aml.sanctions.list'].create({'listed_name': 'Wave4 Migreg Clean Sanction', 'list_source': 'un'})
env.cr.commit()
print("SEED_OK country=%s" % country.name)
"""

SEED_AML_DIRTY = """
country = env.ref('base.fr')
j1 = env['aml.fatf.jurisdiction'].create({'country_id': country.id, 'risk_level': 'grey'})
j2 = env['aml.fatf.jurisdiction'].create({'country_id': country.id, 'risk_level': 'black'})
r1 = env['aml.risk.factor'].create({'name': 'Wave4 Migreg Dup A', 'code': 'WAVE4-MIGREG-DUP', 'category': 'customer', 'weight': 1.0})
r2 = env['aml.risk.factor'].create({'name': 'Wave4 Migreg Dup B', 'code': 'WAVE4-MIGREG-DUP', 'category': 'customer', 'weight': 2.0})
r3 = env['aml.risk.factor'].create({'name': 'Wave4 Migreg Negative', 'code': 'WAVE4-MIGREG-NEG', 'category': 'customer', 'weight': -1.0})
s1 = env['aml.sanctions.list'].create({'listed_name': 'Wave4 Migreg Dup Sanction', 'list_source': 'un'})
s2 = env['aml.sanctions.list'].create({'listed_name': 'Wave4 Migreg Dup Sanction', 'list_source': 'un'})
env.cr.commit()
print("SEED_OK j1=%s j2=%s r1=%s r2=%s r3=%s s1=%s s2=%s" % (j1.id, j2.id, r1.id, r2.id, r3.id, s1.id, s2.id))
"""

VERIFY_KYC_ROUTING = """
app = env['kyc.application'].search([('kyc_id', '=', 'KYC-MIGREG-CLEAN-001')], limit=1)
officer = env['res.users'].search([('login', '=', 'wave4_migreg_officer@example.com')], limit=1)
before = env['kyc.approval'].search_count([('kyc_application_id', '=', app.id)])
app._create_approval_and_notify_officer()
after = env['kyc.approval'].search([('kyc_application_id', '=', app.id)])
routed = officer.id in after.mapped('approver_id').ids
print("ROUTING_CHECK before=%s after=%s routed_to_officer=%s" % (before, len(after), routed))
"""


class Failure(AssertionError):
    pass


class Result:
    def __init__(self):
        self.checks = []

    def check(self, label, condition, detail=""):
        status = "PASS" if condition else "FAIL"
        self.checks.append((status, label, detail))
        print("[%s] %s%s" % (status, label, (" -- " + detail) if detail else ""))
        if not condition:
            raise Failure("%s: %s" % (label, detail))

    def summary(self):
        failed = [c for c in self.checks if c[0] == "FAIL"]
        print("\n%d checks, %d passed, %d failed" % (
            len(self.checks), len(self.checks) - len(failed), len(failed)))
        return len(failed) == 0


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def build_snapshot(rev):
    print("Building pre-migration snapshot at %s ..." % rev)
    r = subprocess.run(["git", "archive", rev, "kyc_management", "aml_compliance"],
                        capture_output=True)  # no text=True: this is a binary tar stream
    if r.returncode != 0:
        raise RuntimeError("git archive failed: %s" % r.stderr.decode(errors="replace"))
    snapshot_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        ".wave4_regression_snapshot",
    )
    os.makedirs(snapshot_dir, exist_ok=True)
    tar_path = os.path.join(tempfile.gettempdir(), "wave4_migreg_snapshot.tar")
    with open(tar_path, "wb") as fh:
        fh.write(r.stdout)
    r = sh(["tar", "--force-local", "-xf", tar_path, "-C", snapshot_dir])
    if r.returncode != 0:
        raise RuntimeError("tar extraction failed: %s" % r.stderr)
    os.remove(tar_path)
    return snapshot_dir


def db(name):
    return "%s_%s" % (DB_PREFIX, name)


def recreate_db(name):
    sh(["docker", "exec", "wave4_pg", "dropdb", "-U", "odoo", "--if-exists", db(name)])
    r = sh(["docker", "exec", "wave4_pg", "createdb", "-U", "odoo", db(name)])
    if r.returncode != 0:
        raise RuntimeError("createdb %s failed: %s" % (db(name), r.stderr))


def odoo_install(dbname, module, addons_path):
    args = ["-d", db(dbname), "--db_host=wave4_pg", "--db_user=odoo",
            "-i", module, "--stop-after-init", "--log-level=info", "--no-http"]
    if addons_path:
        args.insert(0, "--addons-path=" + addons_path)
    return run_odoo(args)


def odoo_upgrade(dbname, module):
    args = ["-d", db(dbname), "--db_host=wave4_pg", "--db_user=odoo",
            "-u", module, "--stop-after-init", "--log-level=info", "--no-http"]
    return run_odoo(args)


def odoo_shell(dbname, script, addons_path=None):
    args = ["shell", "-d", db(dbname), "--db_host=wave4_pg", "--db_user=odoo",
            "--no-http", "--log-level=warn"]
    if addons_path:
        args.insert(0, "--addons-path=" + addons_path)
    return run_odoo(args, stdin_text=script)


def constraint_names_present(dbname, names):
    rc, out = run_psql(
        db(dbname),
        "SELECT conname FROM pg_constraint WHERE conname = ANY(ARRAY[%s])" % (
            ",".join("'%s'" % n for n in names)
        ),
    )
    return set(x for x in out.splitlines() if x)


def row_count(dbname, table):
    rc, out = run_psql(db(dbname), "SELECT COUNT(*) FROM %s" % table)
    return int(out.strip())


def module_state(dbname, module):
    rc, out = run_psql(
        db(dbname),
        "SELECT state || ':' || latest_version FROM ir_module_module WHERE name='%s'" % module,
    )
    state, _, version = out.strip().partition(":")
    return state, version


def run_kyc_scenarios(result, addons_path):
    # ---- clean ----
    recreate_db("kyc_clean")
    rc, log = odoo_install("kyc_clean", "kyc_management", addons_path)
    result.check("KYC clean: pre-migration install exits 0", rc == 0, "rc=%s" % rc)
    rc, log = odoo_shell("kyc_clean", SEED_KYC_CLEAN, addons_path)
    result.check("KYC clean: seed succeeds", rc == 0 and "SEED_OK" in log, log[-300:])

    rc, log = odoo_upgrade("kyc_clean", "kyc_management")
    result.check("KYC clean: upgrade exits 0", rc == 0, log[-800:] if rc else "")
    present = constraint_names_present("kyc_clean", KYC_REQUIRED_CONSTRAINTS)
    result.check("KYC clean: constraint present after upgrade",
                 set(KYC_REQUIRED_CONSTRAINTS) <= present, str(present))
    result.check("KYC clean: historical row preserved",
                 row_count("kyc_clean", "kyc_application") == 1)

    rc, log = odoo_shell("kyc_clean", VERIFY_KYC_ROUTING)
    result.check("KYC clean: officer routing works post-upgrade",
                 rc == 0 and "routed_to_officer=True" in log, log[-300:])

    rc, log = odoo_upgrade("kyc_clean", "kyc_management")
    result.check("KYC clean: second update is idempotent (exit 0)", rc == 0, log[-500:] if rc else "")

    # ---- dirty ----
    recreate_db("kyc_dirty")
    rc, log = odoo_install("kyc_dirty", "kyc_management", addons_path)
    result.check("KYC dirty: pre-migration install exits 0", rc == 0, "rc=%s" % rc)
    rc, log = odoo_shell("kyc_dirty", SEED_KYC_DIRTY, addons_path)
    result.check("KYC dirty: seed succeeds (dead constraint allows duplicate)",
                 rc == 0 and "SEED_OK" in log, log[-300:])

    _, before_version = module_state("kyc_dirty", "kyc_management")
    before_count = row_count("kyc_dirty", "kyc_application")

    rc, log = odoo_upgrade("kyc_dirty", "kyc_management")
    result.check("KYC dirty: guarded upgrade is BLOCKED (non-zero exit)", rc != 0, "rc=%s" % rc)
    result.check("KYC dirty: blocking message matches required shape",
                 bool(re.search(r"KYC_UPGRADE_BLOCKED: duplicate kyc_id groups=1; affected rows=2", log)),
                 log[-500:])
    result.check("KYC dirty: no records modified",
                 row_count("kyc_dirty", "kyc_application") == before_count)
    _, after_version = module_state("kyc_dirty", "kyc_management")
    result.check("KYC dirty: module version did not advance",
                 after_version == before_version, "%s -> %s" % (before_version, after_version))
    present = constraint_names_present("kyc_dirty", KYC_REQUIRED_CONSTRAINTS)
    result.check("KYC dirty: no partial constraint state committed", not present, str(present))

    # ---- corrected retry ----
    sh(["docker", "exec", "wave4_pg", "psql", "-U", "odoo", "-d", db("kyc_dirty"), "-c",
        "UPDATE kyc_application SET kyc_id = kyc_id || '-REMEDIATED' "
        "WHERE id = (SELECT id FROM kyc_application ORDER BY id DESC LIMIT 1);"])
    rc, log = odoo_upgrade("kyc_dirty", "kyc_management")
    result.check("KYC dirty: corrected-data retry succeeds", rc == 0, log[-800:] if rc else "")
    present = constraint_names_present("kyc_dirty", KYC_REQUIRED_CONSTRAINTS)
    result.check("KYC dirty: constraint attached after retry",
                 set(KYC_REQUIRED_CONSTRAINTS) <= present, str(present))


def run_aml_scenarios(result, addons_path):
    # ---- clean ----
    recreate_db("aml_clean")
    rc, log = odoo_install("aml_clean", "aml_compliance", addons_path)
    result.check("AML clean: pre-migration install exits 0", rc == 0, "rc=%s" % rc)
    rc, log = odoo_shell("aml_clean", SEED_AML_CLEAN, addons_path)
    result.check("AML clean: seed succeeds", rc == 0 and "SEED_OK" in log, log[-300:])

    rc, log = odoo_upgrade("aml_clean", "aml_compliance")
    result.check("AML clean: upgrade exits 0", rc == 0, log[-800:] if rc else "")
    present = constraint_names_present("aml_clean", AML_REQUIRED_CONSTRAINTS)
    result.check("AML clean: all 4 constraints present after upgrade",
                 set(AML_REQUIRED_CONSTRAINTS) <= present, str(present))

    rc, log = odoo_upgrade("aml_clean", "aml_compliance")
    result.check("AML clean: second update is idempotent (exit 0)", rc == 0, log[-500:] if rc else "")

    # ---- dirty ----
    recreate_db("aml_dirty")
    rc, log = odoo_install("aml_dirty", "aml_compliance", addons_path)
    result.check("AML dirty: pre-migration install exits 0", rc == 0, "rc=%s" % rc)
    rc, log = odoo_shell("aml_dirty", SEED_AML_DIRTY, addons_path)
    result.check("AML dirty: seed succeeds (dead constraints allow conflicts)",
                 rc == 0 and "SEED_OK" in log, log[-300:])

    _, before_version = module_state("aml_dirty", "aml_compliance")
    counts_before = tuple(
        row_count("aml_dirty", t)
        for t in ("aml_fatf_jurisdiction", "aml_risk_factor", "aml_sanctions_list")
    )

    rc, log = odoo_upgrade("aml_dirty", "aml_compliance")
    result.check("AML dirty: guarded upgrade is BLOCKED (non-zero exit)", rc != 0, "rc=%s" % rc)
    result.check(
        "AML dirty: blocking message names all 4 conflict categories",
        bool(re.search(
            r"AML_UPGRADE_BLOCKED: duplicate FATF countries=1; "
            r"duplicate risk-factor codes=1; negative risk-factor weights=1; "
            r"duplicate sanctions name/source groups=1", log)),
        log[-600:],
    )
    counts_after = tuple(
        row_count("aml_dirty", t)
        for t in ("aml_fatf_jurisdiction", "aml_risk_factor", "aml_sanctions_list")
    )
    result.check("AML dirty: no records modified", counts_before == counts_after,
                 "%s -> %s" % (counts_before, counts_after))
    _, after_version = module_state("aml_dirty", "aml_compliance")
    result.check("AML dirty: module version did not advance",
                 after_version == before_version, "%s -> %s" % (before_version, after_version))
    present = constraint_names_present("aml_dirty", AML_REQUIRED_CONSTRAINTS)
    result.check("AML dirty: no partial constraint state committed", not present, str(present))

    # ---- corrected retry ----
    sh(["docker", "exec", "wave4_pg", "psql", "-U", "odoo", "-d", db("aml_dirty"), "-c", """
        WITH dup AS (
          SELECT id FROM aml_fatf_jurisdiction WHERE country_id = (
            SELECT country_id FROM aml_fatf_jurisdiction GROUP BY country_id HAVING COUNT(*) > 1
          ) ORDER BY id DESC LIMIT 1
        )
        UPDATE aml_fatf_jurisdiction SET country_id = (SELECT id FROM res_country WHERE code = 'JP')
        WHERE id IN (SELECT id FROM dup);
        UPDATE aml_risk_factor SET code = code || '-REMEDIATED'
        WHERE id = (SELECT id FROM aml_risk_factor WHERE code LIKE '%MIGREG-DUP%' ORDER BY id DESC LIMIT 1);
        UPDATE aml_risk_factor SET weight = 1.0 WHERE weight < 0;
        UPDATE aml_sanctions_list SET listed_name = listed_name || ' Remediated'
        WHERE id = (SELECT id FROM aml_sanctions_list WHERE listed_name LIKE '%Migreg Dup%' ORDER BY id DESC LIMIT 1);
    """])
    rc, log = odoo_upgrade("aml_dirty", "aml_compliance")
    result.check("AML dirty: corrected-data retry succeeds", rc == 0, log[-800:] if rc else "")
    present = constraint_names_present("aml_dirty", AML_REQUIRED_CONSTRAINTS)
    result.check("AML dirty: all 4 constraints attached after retry",
                 set(AML_REQUIRED_CONSTRAINTS) <= present, str(present))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pre-migration-rev", default=DEFAULT_PREMIGRATION_REV)
    args = parser.parse_args()

    build_snapshot(args.pre_migration_rev)
    result = Result()
    try:
        with secure_pg_auth():
            run_kyc_scenarios(result, SNAPSHOT_ADDONS_PATH)
            run_aml_scenarios(result, SNAPSHOT_ADDONS_PATH)
    except Failure as exc:
        print("\nREGRESSION SUITE FAILED: %s" % exc)
        result.summary()
        return 1

    ok = result.summary()
    print("\nWAVE4_MIGRATION_REGRESSION: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
