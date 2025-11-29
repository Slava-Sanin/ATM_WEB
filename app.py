from flask import Flask, render_template, request, redirect, url_for, session, flash
from db import init_db, get_customer_by_name, get_customer_balance, update_balance, update_pin

app = Flask(__name__)
app.secret_key = "change_this_secret_to_something_random_and_secret"

# Initialize database on startup
init_db()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "customer_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

@app.route("/", methods=["GET"])
def index():
    if "customer_id" in session:
        return redirect(url_for("menu"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Enter name.")
            return redirect(url_for("login"))
        customer = get_customer_by_name(name)
        if not customer:
            flash("User not found.")
            return redirect(url_for("login"))

        # Check PIN (max 3 attempts). Store attempts in session
        attempts = session.get("pin_attempts", 0)
        pin = request.form.get("pin", "")
        if pin == customer["pin"]:
            session.clear()
            session["customer_id"] = customer["id"]
            session["customer_name"] = customer["name"]
            return redirect(url_for("menu"))
        else:
            attempts += 1
            session["pin_attempts"] = attempts
            if attempts >= 3:
                flash("Too many incorrect PIN attempts. Try again later.")
                session.pop("pin_attempts", None)
                return redirect(url_for("login"))
            else:
                flash(f"Incorrect PIN. Attempts: {attempts}/3")
                return redirect(url_for("login"))

    # GET
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.")
    return redirect(url_for("login"))

@app.route("/menu")
@login_required
def menu():
    cust = get_customer_by_name(session.get("customer_name"))
    # Sync balance with DB
    if cust:
        session["balance"] = get_customer_balance(cust["id"])
    return render_template("menu.html", name=session.get("customer_name"), balance=session.get("balance"))

@app.route("/balance")
@login_required
def balance():
    cust = get_customer_by_name(session.get("customer_name"))
    if cust:
        balance = get_customer_balance(cust["id"])
        session["balance"] = balance
    else:
        flash("User not found.")
        return redirect(url_for("logout"))
    return render_template("balance.html", balance=session["balance"])

@app.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    cust = get_customer_by_name(session.get("customer_name"))
    if not cust:
        flash("User not found.")
        return redirect(url_for("logout"))

    if request.method == "POST":
        try:
            amount = int(request.form.get("amount", "0"))
        except ValueError:
            flash("Invalid amount.")
            return redirect(url_for("deposit"))

        if amount <= 0:
            flash("Amount must be positive.")
            return redirect(url_for("deposit"))

        # Check: multiple of 20,50 or 100 (same logic as in atm.py)
        if not any(amount % m == 0 for m in (20,50,100)):
            flash("Amount must be multiple of 20, 50 or 100.")
            return redirect(url_for("deposit"))

        new_balance = cust["balance"] + amount
        update_balance(cust["id"], new_balance)
        flash(f"Deposited {amount} NIS. New balance: {new_balance} NIS.")
        return redirect(url_for("menu"))

    return render_template("deposit.html")

@app.route("/withdraw", methods=["GET", "POST"])
@login_required
def withdraw():
    cust = get_customer_by_name(session.get("customer_name"))
    if not cust:
        flash("User not found.")
        return redirect(url_for("logout"))

    amounts_map = {"1": 50, "2": 100, "3": 150, "4": 300}

    if request.method == "POST":
        option = request.form.get("option")
        if option in amounts_map:
            withdraw_amount = amounts_map[option]
        elif option == "5":
            try:
                withdraw_amount = int(request.form.get("other_amount", "0"))
            except ValueError:
                flash("Invalid amount.")
                return redirect(url_for("withdraw"))
        else:
            flash("Invalid selection.")
            return redirect(url_for("withdraw"))

        if withdraw_amount <= 0:
            flash("Amount must be positive.")
            return redirect(url_for("withdraw"))

        # Check balance
        balance = get_customer_balance(cust["id"])
        if withdraw_amount > balance:
            flash("Insufficient funds.")
            return redirect(url_for("withdraw"))

        new_balance = balance - withdraw_amount
        update_balance(cust["id"], new_balance)
        flash(f"Withdrew {withdraw_amount} NIS. Remaining: {new_balance} NIS.")
        return redirect(url_for("menu"))

    return render_template("withdraw.html")

@app.route("/change_pin", methods=["GET", "POST"])
@login_required
def change_pin_route():
    cust = get_customer_by_name(session.get("customer_name"))
    if not cust:
        flash("User not found.")
        return redirect(url_for("logout"))

    if request.method == "POST":
        new_pin = request.form.get("new_pin", "")
        if len(new_pin) == 4 and new_pin.isdigit():
            update_pin(cust["id"], new_pin)
            flash("PIN changed successfully.")
            return redirect(url_for("menu"))
        else:
            flash("Invalid PIN format. Must be 4 digits.")
            return redirect(url_for("change_pin_route"))

    return render_template("change_pin.html")

@app.route("/receipt")
@login_required
def receipt():
    cust = get_customer_by_name(session.get("customer_name"))
    if not cust:
        flash("User not found.")
        return redirect(url_for("logout"))
    balance = get_customer_balance(cust["id"])
    from datetime import datetime
    now = datetime.now().strftime("%d/%m/%y %H:%M:%S")
    return render_template("receipt.html", name=cust["name"], balance=balance, now=now)

if __name__ == "__main__":
    app.run(debug=True)
