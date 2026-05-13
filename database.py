# database.py
DATABASE = {
    "domates": {"stok": 45, "esik": 50, "tedarikci": "tarim@koop.com"},
    "zeytinyagi": {"stok": 120, "esik": 30, "tedarikci": "ege@koop.com"},
    "salca": {"stok": 15, "esik": 30, "tedarikci": "fabrika@koop.com"}
}

def get_product_data(name: str):
    return DATABASE.get(name.lower().replace("ı", "i"), None)