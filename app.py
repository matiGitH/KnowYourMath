import os
import psycopg2
import re
import random
from datetime import datetime, date
from flask import Flask, render_template, redirect, session, request, url_for
from flask_session import Session
from dotenv import load_dotenv
import random as r

from helpers import login_required, connect_db, close_db, binary_entropy_dict, validate_nti_mc_fb, print_beliefs, validate_ma, choose_lvl, update_beliefs, find_breaking_point

CATEGORIES = ["trigonometry","algebra","statistics","calculus"]

# Cargar variables de entorno
load_dotenv()

# Configurar la conexión con PostgreSQL en Supabase
DB_URL = os.getenv("SUPABASE_DB_URL_ipv4")  

# Inicializar Flask
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":

        # Clean incomplete TESTS
        cur, conn = connect_db()

        cur.execute("DELETE FROM user_answers WHERE test_id IN (SELECT id FROM tests WHERE completed = false);")
        cur.execute("DELETE FROM tests WHERE completed = false;") # AND started_at < now() - interval '30 minutes'; (logic for deleting only those that are 30 minutes old)

        conn.commit()

        close_db(cur, conn)

        return render_template("index.html")
    
    if request.method == "POST":
        selected_test = request.form.getlist("tests")

        # create session fields
        session["tests"] = selected_test
        session["finished_tests"] = []
        session["question_id"] = 0
        session["question_num"] = 0
        session["used_levels"] = []

        cur, conn = connect_db()

        for category in selected_test:
            session[f"{category}_beliefs"] = {i: 0.5 for i in range(1, 101)}

            # Insert each test into tests
            cur.execute("SELECT id FROM categories WHERE name = %s", (category,))
            category_db = cur.fetchone()
            cur.execute("INSERT INTO tests (user_id, category_id) VALUES (%s, %s) RETURNING id;", (session["user_id"], category_db["id"],))
            test = cur.fetchone()
            conn.commit()
            session[f"{category}_test_id"] = test["id"]

        close_db(cur, conn)

        return redirect(url_for("test"))

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # User submits login
    if request.method == "POST":

        # Define variables
        username = request.form.get("username")
        email = request.form.get("email")
        # Ensure username was submitted
        if not username:
            return render_template("login.html", error="Must provide username.")

        # Ensure password was submitted
        elif not email:
            return render_template("login.html", error="Must provide email.")

        cur, conn = connect_db()

        # Query database for email
        cur.execute("SELECT id, username FROM users WHERE email = %s", (email,))
        user = cur.fetchone()  # Obtener resultados

        if user:
            db_id = user['id']
            db_username = user['username']
        else:
            return render_template("login.html", error="Email doesn't exist.")

        close_db(cur, conn)

        if db_username != username:
            return render_template("login.html", error="Username doesn't match email.")

        # Remember which user has logged in
        session["user_id"] = db_id

        session["username"] = username

        # Redirect user to home page
        return redirect(url_for("index"))

    # User reached route via GET (as by clicking a link or via redirect)
    elif request.method == "GET":
        # Devolver a index al usuario si ya esta logueado
        if "user_id" in session:
            return redirect(url_for("index"))
        return render_template("login.html")
    

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect(url_for("index"))
    

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Check if username is blank
        username = request.form.get("username")
        if not username:
            return render_template("register.html", error="Missing username.")

        # Check if email is blank
        email = request.form.get("email")
        if not email:
            return render_template("register.html", error="Missing email.")
        
        # Check if email is valid
        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_pattern, email):
            return render_template("register.html", error="Invalid email format.")
            
        # Check if birth date is blank
        birth_date = request.form.get("birth-date")
        if not birth_date:
            return render_template("register.html", error="Missing birth date.")
        
        try:
            birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d").date()
        except ValueError:
            return render_template("register.html", error="Invalid date format.")
        
        # Get user's age

        today = date.today()
        age = today.year - birth_date_obj.year - ((today.month, today.day) < (birth_date_obj.month, birth_date_obj.day))

        # Catch impossible ages
        if birth_date_obj > today:
            return render_template("register.html", error="Birth date cannot be in the future.")
        if age > 120:
            return render_template("register.html", error="Please enter a valid birth date.")
        # Add user data to users table
        try:
            cur, conn = connect_db()
            cur.execute("INSERT INTO users (username, email, birth_date) VALUES (%s, %s, %s)", (username, email, birth_date,)) 
            conn.commit()

            # Obtain new ID
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            user = cur.fetchone()

            # Remember which user has logged in
            session["user_id"] = user['id']

            session["username"] = username

            # Close connection
            close_db(cur, conn)

            # Remember which user has logged in
            return redirect(url_for("index"))
        except psycopg2.IntegrityError:
            conn.rollback()
            return render_template("register.html", error="Email already in use.")

    if request.method == "GET":
        return render_template("register.html")
    

@app.route("/check", methods=["GET", "POST"])
def check():
    action = request.form.get("action")
    if action == "check":
        result = validate_nti_mc_fb(request.form.get("answer"), session["question_id"])

    elif action == "check_ma":
        result = validate_ma(request.form.getlist("answer"), session["question_id"])

    if result:
            print("CORRECTO!!")
            cur, conn = connect_db()

            cur.execute("INSERT INTO user_answers (question_id, is_correct, test_id) VALUES (%s, %s, %s);", (session["question_id"], True, session[f"{session["question_category"]}_test_id"]))
            conn.commit()

            close_db(cur, conn)
            session[f"{session["question_category"]}_beliefs"] = update_beliefs(True, session["question_level"], session[f"{session["question_category"]}_beliefs"])

    else:
        print("INCORRECTO!!")

        cur, conn = connect_db()
        cur.execute("INSERT INTO user_answers (question_id, is_correct, test_id) VALUES (%s, %s, %s);", (session["question_id"], False, session[f"{session["question_category"]}_test_id"]))
        conn.commit()
        close_db(cur, conn)
        session[f"{session["question_category"]}_beliefs"] = update_beliefs(False, session["question_level"], session[f"{session["question_category"]}_beliefs"])

    # Check if breaking point found
    breaking_point = find_breaking_point(session[f"{session["question_category"]}_beliefs"])

        # Save category's final level and remove finished test
    if breaking_point:
        session[f"{session["question_category"]}_final_level"] = breaking_point
        session["tests"].remove(session["question_category"])

        # Add to session finished tests and update tests (completed)
        session["finished_tests"].append(session["question_category"])

        print(f"user id = {session["user_id"]}")
        print(f"category_id = {session[f"{session["question_category"]}_test_id"]}")
        cur, conn = connect_db()
        cur.execute("UPDATE tests SET completed = %s WHERE user_id = %s AND id = %s;", (True, session["user_id"], session[f"{session["question_category"]}_test_id"],))
        conn.commit()
        close_db(cur, conn)

        # Check if any tests left
        if session["tests"] == []:
            return redirect(url_for("test_final"))
        
    session["question_id"] = 0
    return redirect(url_for("test"))

@app.route("/skip", methods=["GET", "POST"])
def skip():
    print(f"pregunta a responder de nivel {session["question_level"]}")
    # Update beliefs based on failure (skip)
    session[f"{session["question_category"]}_beliefs"] = update_beliefs(False, session["question_level"], session[f"{session["question_category"]}_beliefs"])
    
    # Update user_answers
    cur, conn = connect_db()

    cur.execute("INSERT INTO user_answers (question_id, is_correct, test_id) VALUES (%s, %s, %s);", (session["question_id"], False, session[f"{session["question_category"]}_test_id"]))
    conn.commit()

    close_db(cur, conn)

    session["question_id"] = 0

    # Check if breaking point found
    breaking_point = find_breaking_point(session[f"{session["question_category"]}_beliefs"])

    if breaking_point:
        session[f"{session["question_category"]}_final_level"] = breaking_point
        session["tests"].remove(session["question_category"])

        # Add to session finished tests and update tests (completed)
        session["finished_tests"].append(session["question_category"])

        print(f"user id = {session["user_id"]}")
        print(f"category_id = {session[f"{session["question_category"]}_test_id"]}")
        cur, conn = connect_db()
        cur.execute("UPDATE tests SET completed = %s WHERE user_id = %s AND id = %s;", (True, session["user_id"], session[f"{session["question_category"]}_test_id"],))
        conn.commit()
        close_db(cur, conn)

        # Check if any tests left
        if session["tests"] == []:
            return redirect(url_for("test_final"))
        
    session["question_id"] = 0
    return redirect(url_for("test"))
        


@app.route("/test", methods=["GET"])
def test():    
    if request.method == "GET":

        cur, conn = connect_db()
        if session["question_id"] == 0:
            print_beliefs(session["trigonometry_beliefs"])
            print(binary_entropy_dict(session["trigonometry_beliefs"]))

            # Determine random category
            selected_tests = session.get("tests")
            random_category = selected_tests[r.randint(0, len(selected_tests) - 1)]


            # Choose question
            chosen_lvl = choose_lvl(session[f"{random_category}_beliefs"], session["used_levels"])

            session["question_num"] += 1 # DISPOSABLE 

            # Remember used_levels
            session["used_levels"].append(chosen_lvl)

            # Select random question from chosen level
            cur.execute("SELECT questions.id, questions.level, questions.statement, questions.equation, questions.question, questions.image_url, questions.format_hint, questions.answer_txt, questions.calculator, categories.name AS category_name, question_types.name AS type_name FROM questions JOIN categories ON questions.category_id = categories.id JOIN question_types ON questions.type_id = question_types.id WHERE questions.level = %s AND categories.name = %s ORDER BY RANDOM() LIMIT 1;", (chosen_lvl, random_category,)) 
            question = cur.fetchone()

            session["question_id"] = question["id"]
            session["question_category"] = question["category_name"]
            session["question_level"] = question["level"]
            
            # Check if it is the correct category and type
            if question['type_name'] == "nti":

                answer_txt = question['answer_txt'].replace("__", "<input form='answer_form' type='text' name='answer' class='answer-input'>")
                
                close_db(cur, conn)
                return render_template("test.html",
                                    question_id=session["question_id"],
                                    question_level = session["question_level"],
                                    username=session["username"],
                                    level=question['level'],
                                    statement=question['statement'],
                                    equation=question['equation'],
                                    question=question['question'],
                                    image_url = question['image_url'],
                                    format_hint = question['format_hint'],
                                    type=question['type_name'],
                                    answer_txt=answer_txt,
                                    calculator=question["calculator"])
            
            elif question["type_name"] == "mc" or question["type_name"] == "ma":

                cur.execute("SELECT answer FROM answers WHERE question_id = %s", (session["question_id"],)) 
                answers = cur.fetchall()

                r.shuffle(answers)
                for answer in answers:
                    if len(answer["answer"]) <= 50:
                        answer["type"] = "text"
                    else:
                        answer["type"] = "img"
                
                close_db(cur, conn)
                return render_template("test.html",
                                    question_id=session["question_id"],
                                    question_level = session["question_level"],
                                    username=session["username"],
                                    level=question['level'],
                                    statement=question['statement'],
                                    equation=question['equation'],
                                    question=question['question'],
                                    image_url = question['image_url'],
                                    type=question['type_name'],
                                    answers=answers,
                                    calculator=question["calculator"])
            
            
            elif question["type_name"] == "fb":

                cur.execute("SELECT answer FROM answers WHERE question_id = %s", (session["question_id"],)) 
                answers = cur.fetchall()  # [{'answer': 'sides'}, {'answer': 'angles'}, ...]

                r.shuffle(answers)  # Mezclar las opciones

                # Crear el HTML del <select>
                select_html = "<select form='answer_form' name='answer' class='answer-select'>"
                select_html += "<option value='' disabled selected>Select an option</option>"
                for a in answers:
                    select_html += f"<option value='{a['answer']}'>{a['answer']}</option>"
                select_html += "</select>"

                # Reemplazar "__" en el statement por el <select>
                statement_fb = question["statement"].replace("__", select_html)

                close_db(cur, conn)
                return render_template("test.html",
                                    question_id=session["question_id"],
                                    question_level = session["question_level"],
                                    username=session["username"],
                                    level=question['level'],
                                    statement_fb=statement_fb,
                                    equation=question['equation'],
                                    image_url=question['image_url'],
                                    type=question['type_name'],
                                    calculator=question["calculator"])



        else:
            # Return same question using question ID
            cur.execute("SELECT questions.id, questions.level, questions.statement, questions.equation, questions.question, questions.image_url, questions.format_hint, questions.answer_txt, questions.calculator, categories.name AS category_name, question_types.name AS type_name FROM questions JOIN categories ON questions.category_id = categories.id JOIN question_types ON questions.type_id = question_types.id WHERE questions.id = %s;", (session["question_id"],)) 
            question = cur.fetchone()
            if question["type_name"] == "mc" or question["type_name"] == "ma" or question["type_name"] == "fb":
                cur.execute("SELECT answer FROM answers WHERE question_id = %s", (session["question_id"],))
                answers = cur.fetchall()
                r.shuffle(answers)
                for answer in answers:
                    if len(answer["answer"]) <= 50:
                        answer["type"] = "text"
                    else:
                        answer["type"] = "img"
                        
            if question["type_name"] == "nti":
                answer_txt = question['answer_txt'].replace("__", "<input form='answer_form' type='text' name='answer' class='answer-input'>")

                close_db(cur, conn)
                return render_template("test.html",
                                    question_id=session["question_id"],
                                    question_level = session["question_level"],
                                    username=session["username"],
                                    level=question['level'],
                                    statement=question['statement'],
                                    equation=question['equation'],
                                    question=question['question'],
                                    image_url=question['image_url'],
                                    format_hint=question['format_hint'],
                                    type=question['type_name'],
                                    answer_txt=answer_txt,
                                    calculator=question["calculator"]
                                    )

            if question["type_name"] == "mc" or question["type_name"] == "ma":
                close_db(cur, conn)
                return render_template("test.html",
                                    question_id=session["question_id"],
                                    question_level = session["question_level"],
                                    username=session["username"],
                                    level=question['level'],
                                    statement=question['statement'],
                                    equation=question['equation'],
                                    question=question['question'],
                                    image_url = question['image_url'],
                                    type=question['type_name'],
                                    answers=answers,
                                    calculator=question["calculator"]
                                    )
            
            if question["type_name"] == "fb":

                # Crear el HTML del <select>
                select_html = "<select form='answer_form' name='answer' class='answer-select'>"
                select_html += "<option value='' disabled selected>Select an option</option>"
                for a in answers:
                    select_html += f"<option value='{a['answer']}'>{a['answer']}</option>"
                select_html += "</select>"

                # Reemplazar "__" en el statement por el <select>
                statement_fb = question["statement"].replace("__", select_html)

                close_db(cur, conn)
                return render_template("test.html",
                                    question_id=session["question_id"],
                                    question_level = session["question_level"],
                                    username=session["username"],
                                    level=question['level'],
                                    statement_fb=statement_fb,
                                    equation=question['equation'],
                                    image_url=question['image_url'],
                                    type=question['type_name'],
                                    calculator=question["calculator"]
                                    )
        


@app.route("/exit-test", methods=["POST"])
def exit_test():
    del session["question_id"]
    del session["tests"]
    del session["question_level"] 
    del session["question_num"]
    del session["used_levels"]
    del session["finished_tests"]

    for category in CATEGORIES:
        if f"{category}_beliefs" in session:
            del session[f"{category}_beliefs"]

        if f"{category}_final_level" in session:
            del session[f"{category}_final_level"]

        if f"{category}_test_id" in session:
            del session[f"{category}_test_id"]


    return redirect(url_for("index"))

@app.route("/test_final", methods=["GET"])
def test_final():
    return render_template("review.html", 
                           trigonometry_final_level = session["trigonometry_final_level"],
                           question_num = session["question_num"])



if __name__ == "__main__":
    app.run(debug=True)
