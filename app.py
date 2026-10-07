import os
import sqlite3
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, session, url_for


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "motos_boris.sqlite3"

app = Flask(__name__)
app.config["DATABASE"] = DATABASE
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "cambia-esta-clave-en-produccion")
app.config["ADMIN_USERNAME"] = os.environ.get("ADMIN_USERNAME", "admin")
app.config["ADMIN_PASSWORD"] = os.environ.get("ADMIN_PASSWORD", "motosboris")
app.config["WHATSAPP_NUMBER"] = os.environ.get("WHATSAPP_NUMBER", "")


def get_db():
    connection = sqlite3.connect(app.config["DATABASE"])
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    with get_db() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS brands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE
            );

            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_id INTEGER NOT NULL,
                name TEXT NOT NULL COLLATE NOCASE,
                UNIQUE(brand_id, name),
                FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE
            );

            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER NOT NULL,
                service_id INTEGER NOT NULL,
                price_cents INTEGER NOT NULL CHECK(price_cents >= 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(model_id, service_id),
                FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
                FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE
            );
            """
        )


def get_brands():
    with get_db() as connection:
        return connection.execute("SELECT id, name FROM brands ORDER BY name").fetchall()


@app.template_filter("pesos")
def pesos(cents):
    return f"$ {cents:,.0f}".replace(",", ".")


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("admin_authenticated"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped_view


@app.route("/")
def index():
    return render_template("index.html", brands=get_brands())


@app.get("/api/models/<int:brand_id>")
def models_for_brand(brand_id):
    with get_db() as connection:
        models = connection.execute(
            "SELECT id, name FROM models WHERE brand_id = ? ORDER BY name",
            (brand_id,),
        ).fetchall()
    return jsonify([dict(model) for model in models])


@app.get("/api/services/<int:model_id>")
def services_for_model(model_id):
    with get_db() as connection:
        services = connection.execute(
            """
            SELECT services.id, services.name, prices.price_cents
            FROM prices
            JOIN services ON services.id = prices.service_id
            WHERE prices.model_id = ?
            ORDER BY services.name
            """,
            (model_id,),
        ).fetchall()
    return jsonify([dict(service) for service in services])


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username.lower() == app.config["ADMIN_USERNAME"].lower() and password == app.config["ADMIN_PASSWORD"]:
            session["admin_authenticated"] = True
            return redirect(request.args.get("next") or url_for("admin"))
        error = "Usuario o contraseña incorrectos."
    return render_template("login.html", error=error)


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/admin", methods=["GET", "POST"])
@admin_required
def admin():
    error = None
    if request.method == "POST":
        brand_name = request.form.get("brand", "").strip()
        model_name = request.form.get("model", "").strip()
        service_name = request.form.get("service", "").strip()
        price_value = request.form.get("price", "").strip().replace(",", ".")

        try:
            price_cents = round(float(price_value))
            if price_cents < 0:
                raise ValueError
        except (TypeError, ValueError):
            price_cents = None

        if not all((brand_name, model_name, service_name)) or price_cents is None:
            error = "Completa todos los campos con un precio válido."
        else:
            with get_db() as connection:
                connection.execute("INSERT OR IGNORE INTO brands (name) VALUES (?)", (brand_name,))
                brand = connection.execute(
                    "SELECT id FROM brands WHERE name = ? COLLATE NOCASE", (brand_name,)
                ).fetchone()
                connection.execute(
                    "INSERT OR IGNORE INTO models (brand_id, name) VALUES (?, ?)",
                    (brand["id"], model_name),
                )
                model = connection.execute(
                    "SELECT id FROM models WHERE brand_id = ? AND name = ? COLLATE NOCASE",
                    (brand["id"], model_name),
                ).fetchone()
                connection.execute("INSERT OR IGNORE INTO services (name) VALUES (?)", (service_name,))
                service = connection.execute(
                    "SELECT id FROM services WHERE name = ? COLLATE NOCASE", (service_name,)
                ).fetchone()
                connection.execute(
                    """
                    INSERT INTO prices (model_id, service_id, price_cents)
                    VALUES (?, ?, ?)
                    ON CONFLICT(model_id, service_id) DO UPDATE SET price_cents = excluded.price_cents
                    """,
                    (model["id"], service["id"], price_cents),
                )
            return redirect(url_for("admin", saved="1"))

    with get_db() as connection:
        prices = connection.execute(
            """
            SELECT prices.id, brands.name AS brand, models.name AS model,
                   services.name AS service, prices.price_cents
            FROM prices
            JOIN models ON models.id = prices.model_id
            JOIN brands ON brands.id = models.brand_id
            JOIN services ON services.id = prices.service_id
            ORDER BY brands.name, models.name, services.name
            """
        ).fetchall()
    return render_template("admin.html", brands=get_brands(), prices=prices, error=error)


def get_price(price_id):
    with get_db() as connection:
        return connection.execute(
            """
            SELECT prices.id, prices.model_id, prices.service_id, prices.price_cents,
                   brands.name AS brand, models.name AS model, services.name AS service
            FROM prices
            JOIN models ON models.id = prices.model_id
            JOIN brands ON brands.id = models.brand_id
            JOIN services ON services.id = prices.service_id
            WHERE prices.id = ?
            """,
            (price_id,),
        ).fetchone()


@app.route("/admin/price/<int:price_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_price(price_id):
    current_price = get_price(price_id)
    if current_price is None:
        return redirect(url_for("admin"))

    error = None
    if request.method == "POST":
        brand_name = request.form.get("brand", "").strip()
        model_name = request.form.get("model", "").strip()
        service_name = request.form.get("service", "").strip()
        price_value = request.form.get("price", "").strip().replace(",", ".")
        try:
            price_value = round(float(price_value))
            if price_value < 0:
                raise ValueError
        except (TypeError, ValueError):
            price_value = None

        if not all((brand_name, model_name, service_name)) or price_value is None:
            error = "Completa todos los campos con un precio válido."
        else:
            try:
                with get_db() as connection:
                    connection.execute("INSERT OR IGNORE INTO brands (name) VALUES (?)", (brand_name,))
                    brand = connection.execute(
                        "SELECT id FROM brands WHERE name = ? COLLATE NOCASE", (brand_name,)
                    ).fetchone()
                    connection.execute(
                        "INSERT OR IGNORE INTO models (brand_id, name) VALUES (?, ?)",
                        (brand["id"], model_name),
                    )
                    model = connection.execute(
                        "SELECT id FROM models WHERE brand_id = ? AND name = ? COLLATE NOCASE",
                        (brand["id"], model_name),
                    ).fetchone()
                    connection.execute("INSERT OR IGNORE INTO services (name) VALUES (?)", (service_name,))
                    service = connection.execute(
                        "SELECT id FROM services WHERE name = ? COLLATE NOCASE", (service_name,)
                    ).fetchone()
                    connection.execute(
                        "UPDATE prices SET model_id = ?, service_id = ?, price_cents = ? WHERE id = ?",
                        (model["id"], service["id"], price_value, price_id),
                    )
            except sqlite3.IntegrityError:
                error = "Ya existe ese servicio para ese modelo."
            else:
                return redirect(url_for("admin", updated="1"))

    return render_template(
        "edit_price.html", price=current_price, brands=get_brands(), error=error
    )


@app.post("/admin/price/<int:price_id>/delete")
@admin_required
def delete_price(price_id):
    with get_db() as connection:
        connection.execute("DELETE FROM prices WHERE id = ?", (price_id,))
        connection.execute(
            "DELETE FROM services WHERE NOT EXISTS (SELECT 1 FROM prices WHERE prices.service_id = services.id)"
        )
        connection.execute(
            "DELETE FROM models WHERE NOT EXISTS (SELECT 1 FROM prices WHERE prices.model_id = models.id)"
        )
        connection.execute(
            "DELETE FROM brands WHERE NOT EXISTS (SELECT 1 FROM models WHERE models.brand_id = brands.id)"
        )
    return redirect(url_for("admin", deleted="1"))


@app.post("/admin/increase-prices")
@admin_required
def increase_prices():
    percentage_value = request.form.get("percentage", "").strip().replace(",", ".")
    try:
        percentage = float(percentage_value)
        if percentage < 0 or percentage > 10000:
            raise ValueError
    except (TypeError, ValueError):
        return redirect(url_for("admin", error="Porcentaje inválido"))

    with get_db() as connection:
        connection.execute(
            "UPDATE prices SET price_cents = CAST(ROUND(price_cents * (1 + ? / 100.0)) AS INTEGER)",
            (percentage,),
        )
    return redirect(url_for("admin", increased=f"{percentage:g}"))


init_db()


if __name__ == "__main__":
    app.run(debug=True)