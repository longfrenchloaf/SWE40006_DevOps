import os
import psycopg2
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_menu_items():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "cafe"),
            user=os.getenv("DB_USER", "admin"),
            password=os.getenv("DB_PASSWORD", "admin123")
        )
        cur = conn.cursor()
        cur.execute("SELECT item_id, name, price, image FROM menu_items;")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        menu = []
        for row in rows:
            menu.append({
                "id": row[0],
                "name": row[1],
                "price": float(row[2]),
                "image": row[3],
            })
        return menu
    except Exception as e:
        print("Database connection failed:", e)
        return []


@app.route("/menu", methods=["GET"])
def menu():
    items = get_menu_items()
    return jsonify(items)

@app.route("/billing", methods=["POST"])
def billing():
    data = request.get_json()
    items = data.get("items", [])
    apply_discount = data.get("apply_discount", False)

    total = 0.0
    for item in items:
        price = item.get("price", 0)
        qty = item.get("qty", 0)
        total += price * qty

    if apply_discount:
        total *= 0.5  # apply 50% discount

    return jsonify({"total": round(total, 2)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
