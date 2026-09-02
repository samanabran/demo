import psycopg2
import psycopg2.extras

SRC = dict(host="db", dbname="osusproperties_source_v18", user="odoo", password="odoo_demo_pw")
TGT = dict(host="db", dbname="demo_presentation_19", user="odoo", password="odoo_demo_pw")
COMPANY_ID = 1

src = psycopg2.connect(**SRC)
tgt = psycopg2.connect(**TGT)
tgt.autocommit = False

# Build source property_seq -> source property_details.id map, and target property_code -> target id map
src_cur = src.cursor()
src_cur.execute("SELECT id, property_seq FROM property_details")
src_seq_by_id = {row[0]: row[1] for row in src_cur.fetchall()}

tgt_cur = tgt.cursor()
tgt_cur.execute("SELECT id, property_code FROM property_details")
tgt_id_by_code = {row[1]: row[0] for row in tgt_cur.fetchall() if row[1]}

# Map source property_details.id -> target property_details.id via property_seq/property_code
prop_map = {}
for src_id, seq in src_seq_by_id.items():
    if seq in tgt_id_by_code:
        prop_map[src_id] = tgt_id_by_code[seq]

print(f"matched {len(prop_map)} of {len(src_seq_by_id)} source properties by code")

# Fetch gallery rows joined with their attachment
src_cur = src.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
src_cur.execute("""
    SELECT pi.id AS image_row_id, pi.property_id, pi.sequence,
           a.id AS att_id, a.name, a.type, a.url, a.mimetype, a.store_fname, a.checksum, a.file_size, a.public
    FROM property_images pi
    JOIN ir_attachment a ON a.res_model = 'property.images' AND a.res_id = pi.id
""")
rows = src_cur.fetchall()
print(f"found {len(rows)} gallery images with attachments in source")

count = 0
skipped_no_property = 0
tgt_cur = tgt.cursor()
for r in rows:
    new_res_id = prop_map.get(r["property_id"])
    if not new_res_id:
        skipped_no_property += 1
        continue
    tgt_cur.execute("""
        INSERT INTO ir_attachment (name, res_id, res_model, type, url, mimetype, store_fname, checksum, file_size, public, company_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (r["name"], new_res_id, "property.details", r["type"], r["url"], r["mimetype"],
          r["store_fname"], r["checksum"], r["file_size"], r["public"], COMPANY_ID))
    count += 1

tgt.commit()
print(f"inserted {count} gallery attachments, skipped {skipped_no_property} (no matching property)")
