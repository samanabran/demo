import xmlrpc.client

url = "http://localhost:8069"
db = "demo_presentation_19"

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
for pwd in ["admin", "odoo_demo_pw"]:
    uid = common.authenticate(db, "admin", pwd, {})
    print(f"password={pwd!r} -> uid={uid}")
    if uid:
        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
        count = models.execute_kw(db, uid, pwd, "property.details", "search_count", [[]])
        print("property.details count:", count)
        ids = models.execute_kw(db, uid, pwd, "property.details", "search", [[]], {"limit": 3})
        recs = models.execute_kw(db, uid, pwd, "property.details", "read", [ids], {"fields": ["name", "price", "currency_id", "project_id"]})
        print("sample records:", recs)
        att_ids = models.execute_kw(db, uid, pwd, "ir.attachment", "search",
                                     [[["res_model", "=", "property.details"], ["res_id", "=", ids[0]]]])
        print("attachment ids for first property:", att_ids)
        if att_ids:
            data = models.execute_kw(db, uid, pwd, "ir.attachment", "read", [att_ids[:1]], {"fields": ["datas"]})
            b64 = data[0]["datas"]
            print("image base64 length:", len(b64) if b64 else 0)
        break
