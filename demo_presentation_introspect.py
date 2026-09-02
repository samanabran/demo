import psycopg2

SRC = dict(host="db", dbname="osusproperties_source_v18", user="odoo", password="odoo_demo_pw")
TGT = dict(host="db", dbname="demo_presentation_19", user="odoo", password="odoo_demo_pw")

TABLES = [
    "property_region", "property_res_city", "property_project", "property_sub_project",
    "property_vendor", "property_tag", "property_amenities", "property_specification",
    "payment_schedule", "payment_schedule_line", "property_details",
]

def cols(conn, table):
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name, data_type FROM information_schema.columns
        WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position
    """, (table,))
    return {r[0]: r[1] for r in cur.fetchall()}

src_conn = psycopg2.connect(**SRC)
tgt_conn = psycopg2.connect(**TGT)

for t in TABLES:
    sc = cols(src_conn, t)
    tc = cols(tgt_conn, t)
    if not sc and not tc:
        print(f"=== {t}: MISSING IN BOTH ===")
        continue
    if not sc:
        print(f"=== {t}: MISSING IN SOURCE ===")
        continue
    if not tc:
        print(f"=== {t}: MISSING IN TARGET ===")
        continue
    common = sorted(set(sc) & set(tc))
    only_src = sorted(set(sc) - set(tc))
    only_tgt = sorted(set(tc) - set(sc))
    print(f"=== {t} ===")
    print(f"  COMMON ({len(common)}): {common}")
    print(f"  ONLY_SRC ({len(only_src)}): {only_src}")
    print(f"  ONLY_TGT ({len(only_tgt)}): {only_tgt}")
