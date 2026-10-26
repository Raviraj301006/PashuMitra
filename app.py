
from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import date

app = Flask(__name__)
app.secret_key = "pashumitra_secret_key"


def get_db_connection():
    connection = sqlite3.connect("database/pashumitra.db")
    connection.row_factory = sqlite3.Row
    return connection


@app.route("/")
def home():
    return render_template("splash.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        mobile = request.form["mobile"]
        email = request.form.get("email") or None
        password = request.form["password"]
        state = request.form["state"]

        connection = get_db_connection()

        connection.execute("""
            INSERT INTO users (name, mobile, email, password, state)
            VALUES (?, ?, ?, ?, ?)
        """, (name, mobile, email, password, state))

        connection.commit()
        connection.close()

        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        mobile = request.form["mobile"]
        password = request.form["password"]

        connection = get_db_connection()

        user = connection.execute("""
            SELECT * FROM users
            WHERE mobile = ? AND password = ?
        """, (mobile, password)).fetchone()

        connection.close()

        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect("/dashboard")

        return "Invalid mobile number or password"

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    connection = get_db_connection()

    user_id = session["user_id"]
    today = date.today()
    today_string = today.isoformat()

    selected_period = request.args.get("period", "daily")

    if selected_period not in ["daily", "monthly", "overall"]:
        selected_period = "daily"

    month_options = []

    for month_number in range(1, 13):
        month_date = date(today.year, month_number, 1)

        if month_date <= today.replace(day=1):
            month_options.append((
                month_date.strftime("%Y-%m"),
                month_date.strftime("%B %Y")
            ))

    month_options.reverse()

    selected_month = request.args.get(
        "month",
        today.strftime("%Y-%m")
    )

    valid_months = []

    for month_value, month_label in month_options:
        valid_months.append(month_value)

    if selected_month not in valid_months:
        selected_month = today.strftime("%Y-%m")

    month_name = today.strftime("%B %Y")

    if selected_period == "daily":
        start_date = today_string
        end_date = today_string

    elif selected_period == "monthly":
        year = int(selected_month[:4])
        month = int(selected_month[5:7])

        selected_month_date = date(year, month, 1)
        month_name = selected_month_date.strftime("%B %Y")
        start_date = selected_month_date.isoformat()

        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)

        end_date = next_month.isoformat()

    else:
        start_date = None
        end_date = None

    total_animals = connection.execute("""
        SELECT COUNT(*) AS total
        FROM animals
        WHERE user_id = ?
    """, (user_id,)).fetchone()["total"]

    if selected_period == "overall":
        records = connection.execute("""
            SELECT daily_records.*
            FROM daily_records
            JOIN animals
            ON daily_records.animal_id = animals.id
            WHERE animals.user_id = ?
        """, (user_id,)).fetchall()

    elif selected_period == "daily":
        records = connection.execute("""
            SELECT daily_records.*
            FROM daily_records
            JOIN animals
            ON daily_records.animal_id = animals.id
            WHERE animals.user_id = ?
            AND daily_records.record_date = ?
        """, (user_id, today_string)).fetchall()

    else:
        records = connection.execute("""
            SELECT daily_records.*
            FROM daily_records
            JOIN animals
            ON daily_records.animal_id = animals.id
            WHERE animals.user_id = ?
            AND daily_records.record_date >= ?
            AND daily_records.record_date < ?
        """, (user_id, start_date, end_date)).fetchall()

    total_milk = 0
    total_expenses = 0
    total_income = 0

    for record in records:
        total_expenses += record["cattle_feed"] or 0
        total_expenses += record["regular_grass"] or 0
        total_expenses += record["doctor_cost"] or 0

        total_milk += record["morning_milk"] or 0
        total_milk += record["evening_milk"] or 0

        total_income += record["income"] or 0

    total_profit = total_income - total_expenses

    connection.close()

    return render_template(
        "dashboard.html",
        name=session["user_name"],
        total_animals=total_animals,
        total_milk=total_milk,
        total_expenses=total_expenses,
        total_income=total_income,
        total_profit=total_profit,
        selected_period=selected_period,
        month_name=month_name,
        month_options=month_options,
        selected_month=selected_month
    )


@app.route("/add-animal", methods=["GET", "POST"])
def add_animal():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        animal_name = request.form["animal_name"]
        animal_type = request.form["animal_type"]
        gender = request.form["gender"]

        age_years = request.form.get("age_years") or None
        age_months = request.form.get("age_months") or None

        source = request.form["source"]
        purchase_date = request.form.get("purchase_date") or None
        purchase_cost = request.form.get("purchase_cost") or None

        pregnancy = request.form.get("pregnancy") or None
        pregnancy_date = request.form.get("pregnancy_date") or None
        status = request.form["status"]

        if source == "Born at Home":
            purchase_date = None
            purchase_cost = None

        if gender == "Male":
            pregnancy = None
            pregnancy_date = None

        if pregnancy != "Yes":
            pregnancy_date = None

        connection = get_db_connection()

        connection.execute("""
            INSERT INTO animals (
                user_id, animal_name, animal_type, gender,
                age_years, age_months, source, purchase_date,
                purchase_cost, pregnancy, pregnancy_date, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            animal_name, animal_type, gender,
            age_years, age_months, source, purchase_date,
            purchase_cost, pregnancy, pregnancy_date, status
        ))

        connection.commit()
        connection.close()

        return redirect("/animals")

    return render_template("add_animal.html")


@app.route("/animals")
def animals():
    if "user_id" not in session:
        return redirect("/login")

    connection = get_db_connection()

    animal_list = connection.execute("""
        SELECT * FROM animals
        WHERE user_id = ?
        ORDER BY id DESC
    """, (session["user_id"],)).fetchall()

    connection.close()

    return render_template("animals.html", animals=animal_list)


@app.route("/daily-records")
def daily_records_animals():
    if "user_id" not in session:
        return redirect("/login")

    connection = get_db_connection()

    animal_list = connection.execute("""
        SELECT id, animal_name, animal_type, gender
        FROM animals
        WHERE user_id = ?
        ORDER BY animal_name ASC
    """, (session["user_id"],)).fetchall()

    connection.close()

    return render_template(
        "daily_records_animals.html",
        animals=animal_list
    )


@app.route("/animal/<int:animal_id>")
def animal_history(animal_id):
    if "user_id" not in session:
        return redirect("/login")

    connection = get_db_connection()

    animal = connection.execute("""
        SELECT * FROM animals
        WHERE id = ? AND user_id = ?
    """, (animal_id, session["user_id"])).fetchone()

    connection.close()

    if animal is None:
        return "Animal not found", 404

    return render_template(
        "animal_history.html",
        animal=animal
    )


@app.route("/animal/<int:animal_id>/records")
def daily_record_history(animal_id):
    if "user_id" not in session:
        return redirect("/login")

    connection = get_db_connection()

    animal = connection.execute("""
        SELECT * FROM animals
        WHERE id = ? AND user_id = ?
    """, (animal_id, session["user_id"])).fetchone()

    if animal is None:
        connection.close()
        return "Animal not found", 404

    records = connection.execute("""
        SELECT * FROM daily_records
        WHERE animal_id = ?
        ORDER BY record_date ASC
    """, (animal_id,)).fetchall()

    connection.close()

    return render_template(
        "daily_records_history.html",
        animal=animal,
        records=records
    )


@app.route("/animal/<int:animal_id>/edit", methods=["GET", "POST"])
def edit_animal(animal_id):
    if "user_id" not in session:
        return redirect("/login")

    connection = get_db_connection()

    animal = connection.execute("""
        SELECT * FROM animals
        WHERE id = ? AND user_id = ?
    """, (animal_id, session["user_id"])).fetchone()

    if animal is None:
        connection.close()
        return "Animal not found", 404

    if request.method == "POST":
        animal_name = request.form["animal_name"]
        animal_type = request.form["animal_type"]
        gender = request.form["gender"]

        age_years = request.form.get("age_years") or None
        age_months = request.form.get("age_months") or None

        source = request.form["source"]
        purchase_date = request.form.get("purchase_date") or None
        purchase_cost = request.form.get("purchase_cost") or None

        pregnancy = request.form.get("pregnancy") or None
        pregnancy_date = request.form.get("pregnancy_date") or None
        status = request.form["status"]

        if source == "Born at Home":
            purchase_date = None
            purchase_cost = None

        if gender == "Male":
            pregnancy = None
            pregnancy_date = None

        if pregnancy != "Yes":
            pregnancy_date = None

        connection.execute("""
            UPDATE animals
            SET animal_name = ?,
                animal_type = ?,
                gender = ?,
                age_years = ?,
                age_months = ?,
                source = ?,
                purchase_date = ?,
                purchase_cost = ?,
                pregnancy = ?,
                pregnancy_date = ?,
                status = ?
            WHERE id = ? AND user_id = ?
        """, (
            animal_name, animal_type, gender,
            age_years, age_months, source,
            purchase_date, purchase_cost,
            pregnancy, pregnancy_date, status,
            animal_id, session["user_id"]
        ))

        connection.commit()
        connection.close()

        return redirect("/animal/{}".format(animal_id))

    connection.close()

    return render_template(
        "edit_animal.html",
        animal=animal
    )


@app.route("/animal/<int:animal_id>/daily-record", methods=["GET", "POST"])
def daily_record(animal_id):
    if "user_id" not in session:
        return redirect("/login")

    connection = get_db_connection()

    animal = connection.execute("""
        SELECT * FROM animals
        WHERE id = ? AND user_id = ?
    """, (animal_id, session["user_id"])).fetchone()

    if animal is None:
        connection.close()
        return "Animal not found", 404

    today_string = date.today().isoformat()

    if request.method == "POST":
        cattle_feed = request.form.get("cattle_feed") or 0
        regular_grass = request.form.get("regular_grass") or 0
        doctor_cost = request.form.get("doctor_cost") or 0

        morning_milk = request.form.get("morning_milk") or 0
        evening_milk = request.form.get("evening_milk") or 0

        income = request.form.get("income") or 0

        if animal["gender"] == "Male":
            morning_milk = 0
            evening_milk = 0

        connection.execute("""
            INSERT INTO daily_records (
                animal_id, record_date, cattle_feed, regular_grass,
                doctor_cost, morning_milk, evening_milk, income
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(animal_id, record_date)
            DO UPDATE SET
                cattle_feed = excluded.cattle_feed,
                regular_grass = excluded.regular_grass,
                doctor_cost = excluded.doctor_cost,
                morning_milk = excluded.morning_milk,
                evening_milk = excluded.evening_milk,
                income = excluded.income
        """, (
            animal_id, today_string, cattle_feed, regular_grass,
            doctor_cost, morning_milk, evening_milk, income
        ))

        connection.commit()
        connection.close()

        return redirect("/animal/{}/records".format(animal_id))

    connection.close()

    return render_template(
        "daily_record.html",
        animal=animal,
        today=today_string
    )


@app.route("/delete-animal/<int:animal_id>", methods=["POST"])
def delete_animal(animal_id):
    if "user_id" not in session:
        return redirect("/login")

    connection = get_db_connection()

    connection.execute("""
        DELETE FROM daily_records
        WHERE animal_id = ?
        AND animal_id IN (
            SELECT id FROM animals
            WHERE id = ? AND user_id = ?
        )
    """, (animal_id, animal_id, session["user_id"]))

    connection.execute("""
        DELETE FROM animals
        WHERE id = ? AND user_id = ?
    """, (animal_id, session["user_id"]))

    connection.commit()
    connection.close()

    return redirect("/animals")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
