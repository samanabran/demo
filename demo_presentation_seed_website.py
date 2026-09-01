import xmlrpc.client
import base64

url = "http://localhost:8069"
db = "demo_presentation_19"
pwd = "admin"

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", pwd, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

# Pull real migrated properties (offplan module's property.details) to reuse as realistic seed data
real_props = models.execute_kw(db, uid, pwd, "property.details", "search_read",
                                [[]], {"fields": ["id", "name", "property_type", "sale_lease",
                                                   "bedrooms", "bathrooms", "price"],
                                       "limit": 8})
print(f"found {len(real_props)} real properties to base seed data on")

TYPE_MAP = {"residential": "apartment", "commercial": "commercial", "villa": "villa"}
created_ids = []
for rp in real_props:
    att_ids = models.execute_kw(db, uid, pwd, "ir.attachment", "search",
                                 [[["res_model", "=", "property.details"], ["res_id", "=", rp["id"]],
                                   ["mimetype", "like", "image"]]], {"limit": 1})
    image_b64 = None
    if att_ids:
        data = models.execute_kw(db, uid, pwd, "ir.attachment", "read", [att_ids], {"fields": ["datas"]})
        image_b64 = data[0]["datas"]

    vals = {
        "title": f"Unit {rp['name']} - Whitestone by Axiom Prime",
        "property_type": TYPE_MAP.get(rp.get("property_type"), "apartment"),
        "sale_lease": "for_sale" if rp.get("sale_lease") == "for_sale" else "for_rent",
        "bedrooms": rp.get("bedrooms") or 2,
        "bathrooms": rp.get("bathrooms") or 2,
        "price": rp.get("price") or 1500000,
        "city": "Dubai",
        "destination_country_id": 2,
        "website_published": True,
        "description": "<p>Real unit data migrated from OSUS Properties live portfolio, showcased here as a marketplace demo listing.</p>",
    }
    if image_b64:
        vals["image_1920"] = image_b64
    new_id = models.execute_kw(db, uid, pwd, "sgc.realestate.property", "create", [vals])
    created_ids.append(new_id)

print("created sgc.realestate.property ids:", created_ids)

# Attach a tiny synthetic brochure PDF to the first listing to demo the gated-download feature
if created_ids:
    fake_pdf = base64.b64encode(b"%PDF-1.4\n%Demo brochure for marketplace screenshot\n").decode()
    models.execute_kw(db, uid, pwd, "sgc.realestate.property", "write",
                       [[created_ids[0]], {"brochure": fake_pdf, "brochure_filename": "brochure.pdf"}])
    print("attached demo brochure to property", created_ids[0])

print("FIRST_PROPERTY_ID=%s" % created_ids[0])
