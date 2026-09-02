import xmlrpc.client
import urllib.request
import json

url = "http://localhost:8069"
db = "demo_presentation_19"
pwd = "admin"

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, "admin", pwd, {})
print("uid:", uid)
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

# Create a published demo property with sale_lease + brochure to prove new fields work
country_ids = models.execute_kw(db, uid, pwd, "sgc.realestate.destination.country", "search", [[]], {"limit": 1})
prop_id = models.execute_kw(db, uid, pwd, "sgc.realestate.property", "create", [{
    "title": "Verification Test Villa",
    "property_type": "villa",
    "sale_lease": "for_rent",
    "price": 100000,
    "bedrooms": 3,
    "bathrooms": 2,
    "website_published": True,
    "destination_country_id": country_ids[0] if country_ids else False,
}])
print("created property id:", prop_id)

rec = models.execute_kw(db, uid, pwd, "sgc.realestate.property", "read", [[prop_id]],
                         {"fields": ["title", "sale_lease", "website_published"]})
print("readback:", rec)

# Inquiry endpoint (JSON-RPC, public, no auth needed)
req = urllib.request.Request(
    f"{url}/realestate/inquiry",
    data=json.dumps({"jsonrpc": "2.0", "method": "call",
                     "params": {"name": "Test Lead", "email": "test@example.com",
                                "phone": "+97100000000", "message": "hi",
                                "property_id": prop_id}}).encode(),
    headers={"Content-Type": "application/json", "X-Odoo-Database": db},
)
with urllib.request.urlopen(req) as resp:
    print("inquiry response:", json.loads(resp.read())["result"])

count = models.execute_kw(db, uid, pwd, "sgc.realestate.consultation", "search_count",
                           [[["property_id", "=", prop_id]]])
print("consultation records linked to test property:", count)
