import os
from datetime import date, datetime
from functools import wraps

import pymysql
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

CATEGORIES = [
    "Food",
    "Transport",
    "Shopping",
    "Bills",
    "Health",
    "Entertainment",
    "Other",
]


def get_db():
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        mobile_no = request.form.get("mobile_no", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not mobile_no.isdigit() or len(mobile_no) < 10:
            flash("Enter a valid mobile number (at least 10 digits).", "danger")
            return render_template("register.html")

        if len(password) < 4:
            flash("Password must be at least 4 characters.", "danger")
            return render_template("register.html")

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        try:
            conn = get_db()
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE mobile_no = %s", (mobile_no,))
                if cur.fetchone():
                    flash("This mobile number is already registered.", "danger")
                    return render_template("register.html")

                cur.execute(
                    "INSERT INTO users (mobile_no, password_hash) VALUES (%s, %s)",
                    (mobile_no, generate_password_hash(password)),
                )
            conn.close()
            flash("Account created. Please log in.", "success")
            return redirect(url_for("login"))
        except Exception as exc:
            flash(f"Could not register: {exc}", "danger")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        mobile_no = request.form.get("mobile_no", "").strip()
        password = request.form.get("password", "")

        try:
            conn = get_db()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, password_hash FROM users WHERE mobile_no = %s",
                    (mobile_no,),
                )
                user = cur.fetchone()
            conn.close()

            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session["user_id"] = user["id"]
                session["mobile_no"] = mobile_no
                return redirect(url_for("dashboard"))

            flash("Invalid mobile number or password.", "danger")
        except Exception as exc:
            flash(f"Login failed: {exc}", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    today = date.today()

    if request.method == "POST":
        amount = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        expense_date = request.form.get("expense_date", "").strip() or today.isoformat()

        try:
            amount_val = float(amount)
            if amount_val <= 0:
                raise ValueError("Amount must be greater than 0")
            if category not in CATEGORIES:
                raise ValueError("Invalid category")
            parsed_date = datetime.strptime(expense_date, "%Y-%m-%d").date()

            conn = get_db()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO expenses (user_id, amount, category, description, expense_date)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        session["user_id"],
                        amount_val,
                        category,
                        description[:255],
                        parsed_date,
                    ),
                )
            conn.close()
            flash("Expense added.", "success")
            return redirect(url_for("dashboard"))
        except ValueError as exc:
            flash(str(exc), "danger")
        except Exception as exc:
            flash(f"Could not save expense: {exc}", "danger")

    expenses = []
    total_today = 0

    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, amount, category, description, expense_date
                FROM expenses
                WHERE user_id = %s AND expense_date = %s
                ORDER BY created_at DESC
                """,
                (session["user_id"], today),
            )
            expenses = cur.fetchall()
            total_today = sum(float(row["amount"]) for row in expenses)
        conn.close()
    except Exception as exc:
        flash(f"Could not load expenses: {exc}", "danger")

    return render_template(
        "dashboard.html",
        expenses=expenses,
        total_today=total_today,
        today=today.isoformat(),
        categories=CATEGORIES,
    )


@app.route("/history")
@login_required
def history():
    selected_date = request.args.get("date", "").strip()
    if not selected_date:
        selected_date = date.today().isoformat()

    try:
        parsed_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
    except ValueError:
        flash("Invalid date.", "danger")
        return redirect(url_for("history"))

    expenses = []
    total = 0
    day_totals = []

    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, amount, category, description, expense_date, created_at
                FROM expenses
                WHERE user_id = %s AND expense_date = %s
                ORDER BY created_at DESC
                """,
                (session["user_id"], parsed_date),
            )
            expenses = cur.fetchall()
            total = sum(float(row["amount"]) for row in expenses)

            cur.execute(
                """
                SELECT expense_date, SUM(amount) AS day_total, COUNT(*) AS item_count
                FROM expenses
                WHERE user_id = %s
                GROUP BY expense_date
                ORDER BY expense_date DESC
                LIMIT 30
                """,
                (session["user_id"],),
            )
            day_totals = cur.fetchall()
        conn.close()
    except Exception as exc:
        flash(f"Could not load history: {exc}", "danger")

    return render_template(
        "history.html",
        expenses=expenses,
        total=total,
        selected_date=selected_date,
        day_totals=day_totals,
    )


@app.route("/delete/<int:expense_id>", methods=["POST"])
@login_required
def delete_expense(expense_id):
    next_page = request.form.get("next", "dashboard")
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM expenses WHERE id = %s AND user_id = %s",
                (expense_id, session["user_id"]),
            )
        conn.close()
        flash("Expense deleted.", "success")
    except Exception as exc:
        flash(f"Could not delete expense: {exc}", "danger")

    if next_page == "history":
        selected = request.form.get("date", date.today().isoformat())
        return redirect(url_for("history", date=selected))
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode, host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
