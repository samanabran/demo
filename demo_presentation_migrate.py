import psycopg2
import psycopg2.extras
import json

SRC = dict(host="db", dbname="osusproperties_source_v18", user="odoo", password="odoo_demo_pw")
TGT = dict(host="db", dbname="demo_presentation_19", user="odoo", password="odoo_demo_pw")

COMPANY_ID = 1
AED_ID = 129

src = psycopg2.connect(**SRC)
tgt = psycopg2.connect(**TGT)
tgt.autocommit = False

def col_types(conn, table):
    cur = conn.cursor()
    cur.execute("""SELECT column_name, data_type FROM information_schema.columns
                   WHERE table_schema='public' AND table_name=%s""", (table,))
    return {r[0]: r[1] for r in cur.fetchall()}

TGT_TYPES = {}

def get_tgt_types(table):
    if table not in TGT_TYPES:
        TGT_TYPES[table] = col_types(tgt, table)
    return TGT_TYPES[table]

def to_jsonb_if_needed(table, col, value):
    types = get_tgt_types(table)
    tgt_is_jsonb = types.get(col) == "jsonb"
    if isinstance(value, dict):
        # source gave us a translated jsonb value
        if tgt_is_jsonb:
            return json.dumps(value)
        return value.get("en_US") or (next(iter(value.values())) if value else None)
    if tgt_is_jsonb and value is not None:
        return json.dumps({"en_US": str(value)})
    return value

def fetch_all(table, cols):
    cur = src.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(f"SELECT {', '.join(cols)} FROM {table}")
    return cur.fetchall()

def insert_row(table, data):
    cols = list(data.keys())
    vals = [to_jsonb_if_needed(table, c, data[c]) for c in cols]
    placeholders = ", ".join(["%s"] * len(cols))
    q = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders}) RETURNING id"
    cur = tgt.cursor()
    cur.execute(q, vals)
    return cur.fetchone()[0]

stats = {}

# 1. property_region
region_map = {}
for r in fetch_all("property_region", ["id", "name", "create_uid", "write_uid"]):
    new_id = insert_row("property_region", {"name": r["name"]})
    region_map[r["id"]] = new_id
stats["property_region"] = len(region_map)

# 2. property_res_city
city_map = {}
city_name = {}
for r in fetch_all("property_res_city", ["id", "name"]):
    new_id = insert_row("property_res_city", {"name": r["name"]})
    city_map[r["id"]] = new_id
    city_name[r["id"]] = r["name"]
stats["property_res_city"] = len(city_map)

# 3. property_amenities
amenities_map = {}
for r in fetch_all("property_amenities", ["id", "title", "sequence"]):
    new_id = insert_row("property_amenities", {"title": r["title"], "sequence": r["sequence"]})
    amenities_map[r["id"]] = new_id
stats["property_amenities"] = len(amenities_map)

# 4. property_specification
spec_map = {}
for r in fetch_all("property_specification", ["id", "title", "description"]):
    new_id = insert_row("property_specification", {"title": r["title"], "description": r["description"]})
    spec_map[r["id"]] = new_id
stats["property_specification"] = len(spec_map)

# 5. property_tag
tag_map = {}
for r in fetch_all("property_tag", ["id", "title"]):
    new_id = insert_row("property_tag", {"title": r["title"]})
    tag_map[r["id"]] = new_id
stats["property_tag"] = len(tag_map)

# 6. payment_schedule
schedule_map = {}
for r in fetch_all("payment_schedule", ["id", "name", "description", "schedule_type", "sequence", "total_percentage", "active"]):
    new_id = insert_row("payment_schedule", {
        "name": r["name"], "description": r["description"], "schedule_type": r["schedule_type"],
        "sequence": r["sequence"], "total_percentage": r["total_percentage"], "active": r["active"],
        "company_id": COMPANY_ID,
    })
    schedule_map[r["id"]] = new_id
stats["payment_schedule"] = len(schedule_map)

# 7. payment_schedule_line
line_count = 0
for r in fetch_all("payment_schedule_line", ["id", "schedule_id", "name", "note", "sequence",
                                              "percentage", "number_of_installments", "installment_frequency", "days_after"]):
    if r["schedule_id"] not in schedule_map:
        continue
    insert_row("payment_schedule_line", {
        "schedule_id": schedule_map[r["schedule_id"]], "name": r["name"], "note": r["note"],
        "sequence": r["sequence"], "percentage": r["percentage"],
        "number_of_installments": r["number_of_installments"],
        "installment_frequency": r["installment_frequency"], "days_after": r["days_after"],
    })
    line_count += 1
stats["payment_schedule_line"] = line_count

# 8. property_project
project_map = {}
for r in fetch_all("property_project", ["id", "name", "description", "region_id"]):
    new_id = insert_row("property_project", {
        "name": r["name"], "description": r["description"],
        "region_id": region_map.get(r["region_id"]),
        "company_id": COMPANY_ID,
    })
    project_map[r["id"]] = new_id
stats["property_project"] = len(project_map)

# 9. property_sub_project
subproject_map = {}
for r in fetch_all("property_sub_project", ["id", "name", "description", "property_project_id"]):
    new_id = insert_row("property_sub_project", {
        "name": r["name"], "description": r["description"],
        "project_id": project_map.get(r["property_project_id"]),
        "company_id": COMPANY_ID,
    })
    subproject_map[r["id"]] = new_id
stats["property_sub_project"] = len(subproject_map)

# 10. res_partner subset (landlords referenced by property_details)
partner_map = {}
landlord_ids = set()
cur = src.cursor()
cur.execute("SELECT DISTINCT landlord_id FROM property_details WHERE landlord_id IS NOT NULL")
for (pid,) in cur.fetchall():
    landlord_ids.add(pid)

if landlord_ids:
    cur = src.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""SELECT id, name, email, phone, street, city, is_company, function
                   FROM res_partner WHERE id = ANY(%s)""", (list(landlord_ids),))
    for r in cur.fetchall():
        new_id = insert_row("res_partner", {
            "name": r["name"] or f"Partner {r['id']}",
            "email": r["email"], "phone": r["phone"],
            "street": r["street"], "city": r["city"], "is_company": r["is_company"],
            "function": r["function"], "company_id": COMPANY_ID,
            "autopost_bills": "ask",
        })
        partner_map[r["id"]] = new_id
stats["res_partner"] = len(partner_map)

# 11. property_details (main table)
detail_cols = ["id", "property_seq", "type", "sale_lease", "bed", "bathroom",
               "region_id", "property_project_id", "subproject_id", "state_id", "country_id",
               "city_id", "landlord_id", "payment_schedule_id", "zip",
               "price", "sale_price", "admin_fee", "dld_fee", "dld_fee_percentage",
               "booking_percentage", "booking_type", "total_customer_obligation", "total_maintenance",
               "is_maintenance_service", "is_extra_service", "is_payment_plan", "company_id"]
rows = fetch_all("property_details", detail_cols)
property_map = {}
for r in rows:
    data = {
        "name": r["property_seq"] or f"Property {r['id']}",
        "property_code": r["property_seq"],
        "property_type": r["type"],
        "sale_lease": r["sale_lease"],
        "bedrooms": r["bed"],
        "bathrooms": r["bathroom"],
        "region_id": region_map.get(r["region_id"]),
        "project_id": project_map.get(r["property_project_id"]),
        "sub_project_id": subproject_map.get(r["subproject_id"]),
        "city": city_name.get(r["city_id"]),
        "landlord_id": partner_map.get(r["landlord_id"]),
        "owner_id": partner_map.get(r["landlord_id"]),
        "payment_schedule_id": schedule_map.get(r["payment_schedule_id"]),
        "zip": r["zip"],
        "price": r["price"],
        "sale_price": r["sale_price"],
        "admin_fee": r["admin_fee"],
        "dld_fee": r["dld_fee"],
        "dld_fee_percentage": r["dld_fee_percentage"],
        "booking_percentage": r["booking_percentage"],
        "booking_type": r["booking_type"],
        "total_customer_obligation": r["total_customer_obligation"],
        "total_maintenance": r["total_maintenance"],
        "is_maintenance_service": r["is_maintenance_service"],
        "is_extra_service": r["is_extra_service"],
        "is_payment_plan": r["is_payment_plan"],
        "company_id": COMPANY_ID,
        "currency_id": AED_ID,
        "active": True,
    }
    new_id = insert_row("property_details", data)
    property_map[r["id"]] = new_id
stats["property_details"] = len(property_map)
tgt.commit()

# 12. ir_attachment for property.details images (remap res_id + res_model, keep store_fname/checksum)
cur = src.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur.execute("""SELECT id, name, res_id, res_model, type, url, mimetype, store_fname, checksum, file_size, public
               FROM ir_attachment WHERE res_model = 'property.details' AND res_id = ANY(%s)""",
            (list(property_map.keys()),))
att_count = 0
for r in cur.fetchall():
    new_res_id = property_map.get(r["res_id"])
    if not new_res_id:
        continue
    insert_row("ir_attachment", {
        "name": r["name"], "res_id": new_res_id, "res_model": "property.details",
        "type": r["type"], "url": r["url"], "mimetype": r["mimetype"],
        "store_fname": r["store_fname"], "checksum": r["checksum"],
        "file_size": r["file_size"], "public": r["public"],
        "company_id": COMPANY_ID,
    })
    att_count += 1
stats["ir_attachment (property images)"] = att_count
tgt.commit()

print(json.dumps(stats, indent=2))
