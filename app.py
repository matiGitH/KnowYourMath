import os
import psycopg2
import re
import random
from datetime import datetime, date
from flask import Flask, render_template, redirect, session, request, url_for
from flask_session import Session
from dotenv import load_dotenv
import random as r

from helpers import login_required, connect_db, close_db, binary_entropy_dict, validate_answer, print_beliefs, choose_lvl, update_beliefs, find_breaking_point

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
        session["question_num"] = 0
        session["used_levels"] = []
        session["new_question"] = True
        session["correct_answers"] = []

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
            db_id = user["id"]
            db_username = user["username"]
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
            session["user_id"] = user["id"]

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
    

@app.route("/skip", methods=["POST"])
def skip():
    # Update beliefs based on failure (skip)
    session[f"{session["question"]["category_name"]}_beliefs"] = update_beliefs(False, session["question"]["level"], session[f"{session["question"]["category_name"]}_beliefs"])
    session["question"]["user_answer"] = ""
    session["correct"] = False
    # Update user_answers
    cur, conn = connect_db()

    cur.execute("INSERT INTO user_answers (question_id, is_correct, test_id) VALUES (%s, %s, %s);", (session["question"]["id"], False, session[f"{session["question"]["category_name"]}_test_id"]))
    conn.commit()

    close_db(cur, conn)
    return redirect(url_for("feedback"))

        
@app.route("/check", methods=["POST"])
def check():
    if session["question"]["type_name"] == "ma":
        session["question"]["user_answer"] = request.form.getlist("answer")
        result = validate_answer(session["question"]["user_answer"], session["question"]["id"], True)
    else:
        session["question"]["user_answer"] = request.form.get("answer") or ""
        result = validate_answer(session["question"]["user_answer"], session["question"]["id"])

    if result:
        print("CORRECTO!!")
        session["correct"] = True
        cur, conn = connect_db()

        cur.execute("INSERT INTO user_answers (question_id, is_correct, test_id) VALUES (%s, %s, %s);", (session["question"]["id"], True, session[f"{session["question"]["category_name"]}_test_id"]))
        conn.commit()

        close_db(cur, conn)
        session[f"{session["question"]["category_name"]}_beliefs"] = update_beliefs(True, session["question"]["level"], session[f"{session["question"]["category_name"]}_beliefs"])
    else:
        print("INCORRECTO!!")
        session["correct"] = False

        cur, conn = connect_db()
        cur.execute("INSERT INTO user_answers (question_id, is_correct, test_id) VALUES (%s, %s, %s);", (session["question"]["id"], False, session[f"{session["question"]["category_name"]}_test_id"]))
        conn.commit()
        close_db(cur, conn)
        session[f"{session["question"]["category_name"]}_beliefs"] = update_beliefs(False, session["question"]["level"], session[f"{session["question"]["category_name"]}_beliefs"])

    # Redirect to feedback
    return redirect(url_for("feedback"))
    

@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if request.method == "POST":
        session["new_question"] = True
        return redirect(url_for("test"))
    elif request.method == "GET":
        if session["question"]["type_name"] == "nti":
            if session["correct"]:
                session["question"]["answer_txt"] = session["question"]["answer_txt"].replace("__", f"<input type='text' name='answer' class='answer-input' value='{session["question"]["user_answer"]}' style='color: green; background-color: #d4edda; border: 1px solid #28a745;' autocomplete='off' disabled>")
            else:
                # Show correct answer
                session["question"]["correct_answer_txt"] = session["question"]["answer_txt"].replace("__", f"\\( {session['question']['correct_answer']} \\)")
                # Show user's answer (wrong)
                session["question"]["answer_txt"] = session["question"]["answer_txt"].replace("__", f"<input type='text' name='answer' class='answer-input' value='{session["question"]["user_answer"]}' style='color: red; background-color: #f8d7da; border: 1px solid #dc3545;' autocomplete='off' disabled>")

            return render_template("feedback.html",
                                question=session["question"],
                                username=session["username"],
                                correct=session["correct"],
                                )
        
        elif session["question"]["type_name"] == "mc" or session["question"]["type_name"] == "ma":
            for answer in session["question"]["answers"]:
                if answer["answer"] in session["question"]["user_answer"]:
                    answer["selected"] = True
                else:
                    answer["selected"] = False
            

            return render_template("feedback.html",
                                question=session["question"],
                                username=session["username"],
                                correct=session["correct"],
                                )

        elif session["question"]["type_name"] == "fb":
            if session["correct"]:
                select_html = "<select disabled class='answer-select correct'>"
            else:
                select_html = "<select disabled class='answer-select incorrect'>"
            select_html += f"<option value='' disabled selected>{session['question']['user_answer']}</option>"
            select_html += "</select>"
            session["question"]["statement_improved"] = session["question"]["statement"].replace("__", select_html)
            return render_template("feedback.html",
                                question=session["question"],
                                username=session["username"],
                                correct=session["correct"],
                                )

@app.route("/test", methods=["GET"])
def test():    
    if session["new_question"] or session["question_num"] == 0:
        session["new_question"] = False

        if session["question_num"] != 0:
            # Check if breaking point found
            breaking_point = find_breaking_point(session[f"{session["question"]["category_name"]}_beliefs"])

            if breaking_point:
                session[f"{session["question"]["category_name"]}_final_level"] = breaking_point
                session["tests"].remove(session["question"]["category_name"])

                # Add to session finished tests and update tests (completed)
                session["finished_tests"].append(session["question"]["category_name"])

                print(f"user id = {session["user_id"]}")
                print(f"category_id = {session[f"{session["question"]["category_name"]}_test_id"]}")
                cur, conn = connect_db()
                cur.execute("UPDATE tests SET completed = %s WHERE user_id = %s AND id = %s;", (True, session["user_id"], session[f"{session["question"]["category_name"]}_test_id"],))
                conn.commit()
                close_db(cur, conn)

                # Check if any tests left
                if session["tests"] == []:
                    return redirect(url_for("test_final"))
                
        session["question_num"] += 1

        cur, conn = connect_db()
        print_beliefs(session["trigonometry_beliefs"])
        print(binary_entropy_dict(session["trigonometry_beliefs"]))

        # Determine random category
        selected_tests = session.get("tests")
        random_category = selected_tests[r.randint(0, len(selected_tests) - 1)]


        # Choose question
        chosen_lvl = choose_lvl(session[f"{random_category}_beliefs"], session["used_levels"])

        # Remember used_levels
        session["used_levels"].append(chosen_lvl)

        # Select random question from chosen level (every needed field)
        cur.execute("SELECT questions.id, questions.level, questions.statement, questions.equation, questions.question, questions.image_url, questions.format_hint, questions.answer_txt, questions.calculator, categories.name AS category_name, question_types.name AS type_name FROM questions JOIN categories ON questions.category_id = categories.id JOIN question_types ON questions.type_id = question_types.id WHERE questions.level = %s AND categories.name = %s ORDER BY RANDOM() LIMIT 1;", (chosen_lvl, random_category,)) 


        session["question"] = cur.fetchone()
        
        # Update needed fields for selected type question
        if session["question"]["type_name"] == "nti":

            session["question"]["answer_txt_nti"] = session["question"]["answer_txt"].replace("__", "<input form='answer_form' type='text' name='answer' class='answer-input' maxlength='15' autocomplete='off'>")
            cur.execute("SELECT answer FROM answers WHERE question_id = %s", (session["question"]["id"],))
            correct_answer = cur.fetchone()
            session["question"]["correct_answer"] = correct_answer["answer"]
            
        elif session["question"]["type_name"] == "mc" or session["question"]["type_name"] == "ma":

            cur.execute("SELECT answer, is_correct FROM answers WHERE question_id = %s", (session["question"]["id"],))
            answers = cur.fetchall()

            r.shuffle(answers)
            for answer in answers:
                if len(answer["answer"]) <= 100:
                    answer["type"] = "text"
                else:
                    answer["type"] = "img"
            
            session["question"]["answers"] = answers
        
        elif session["question"]["type_name"] == "fb":

            cur.execute("SELECT answer, is_correct FROM answers WHERE question_id = %s", (session["question"]["id"],)) 
            answers = cur.fetchall()

            r.shuffle(answers)  # shuffle answers

            session["question"]["answers"] = answers

            # Crear el HTML del <select>
            select_html = "<select form='answer_form' name='answer' class='answer-select'>"
            select_html += "<option value='' disabled selected>Select an option</option>"
            for a in answers:
                if a["is_correct"] == True:
                    session["question"]["correct_answer"] = a["answer"]
                select_html += f"<option value='{a['answer']}'>{a['answer']}</option>"
            select_html += "</select>"

            # Reemplazar "__" en el statement por el <select>
            session["question"]["statement_improved"] = session["question"]["statement"].replace("__", select_html)

        close_db(cur, conn)
        return render_template("test.html",
                            question=session["question"],
                            username=session["username"],
                            )

    else:
        # Return same question               
        return render_template("test.html",
                            question=session["question"],
                            username=session["username"],
                            )
        


@app.route("/exit-test", methods=["POST"])
def exit_test():
    del session["question"]
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
