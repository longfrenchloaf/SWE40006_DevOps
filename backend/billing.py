import os
import psycopg2
from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
import logging

app = Flask(__name__, static_folder='templates/static', static_url_path='/static')
app.logger.setLevel(logging.INFO)
CORS(app)

@app.route('/static/<path:filename>')
def custom_static(filename):
    return send_from_directory('templates/static', filename)

@app.route('/')  # This handles requests to the root URL (e.g., http://your_ip:5000/)
def home():
    # return "Hello from Flask!" # For a quick test
    app.logger.info("Serving menu.html")
    return render_template('menu.html') # If main.html is your homepage

@app.route('/cart')
def cart_page():
    app.logger.info("Serving cart.html") # Add this log
    return render_template('cart.html')

def get_menu_items():
    app.logger.info("Attempting to get menu items from DB.")
    try:
        db_host = os.getenv("DB_HOST")
        db_name = os.getenv("DB_NAME")
        db_user = os.getenv("DB_USER", "admin_fallback")
        db_password = os.getenv("DB_PASSWORD")
        db_port = os.getenv("DB_PORT", "5432")
        db_sslmode = os.getenv("DB_SSLMODE", "prefer") # Get from env, default to prefer
        # Log the actual variable values right before connecting
        app.logger.info(f"DB Connect Params (in Python): host={db_host}, dbname={db_name}, user={db_user}, port={db_port}, sslmode={db_sslmode}")
        
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=db_port,
            connect_timeout=10,
            sslmode=db_sslmode # Use the dynamic SSL mode
        )
        app.logger.info("DB connection successful!")

        cur = conn.cursor()
        cur.execute("SELECT id, name, price, image FROM menu_items;")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        app.logger.info(f"Fetched {len(rows)} menu items.")

        menu = []
        for row in rows:
            menu.append({
                "id": row[0],
                "name": row[1],
                "price": float(row[2]),
                "image": row[3],
            })
        return menu
    except psycopg2.OperationalError as e:
        app.logger.error(f"DB OperationalError: {e}")
        return []
    except Exception as e:
        print("Database connection failed:", e)
        return []


@app.route("/menu", methods=["GET"])
def menu():
    app.logger.info("Received GET request for /menu") # Add this log
    items = get_menu_items()
    return jsonify(items)

@app.route("/billing", methods=["POST"])
def billing():
    app.logger.info("Received POST request for /billing") # Add this log
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
    app.logger.info("Starting Flask development server.") # Keep this log
    app.run(host="0.0.0.0", port=5000, debug=True)
