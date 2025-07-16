import os
import psycopg2
import re
import json
from datetime import datetime, date
from flask import Flask, render_template, redirect, session, request, url_for
from flask_session import Session
from dotenv import load_dotenv
import random as r

from helpers import connect_db, close_db, validate_answer, choose_lvl, update_beliefs, find_breaking_point, choose_level_exploring, get_level_summary, plot_beliefs_svg

EXPLORING_FACTOR = 3

# Load env variables
load_dotenv()

# Configure connection with supabase db
DB_URL = os.getenv("SUPABASE_DB_URL_ipv4")  

# Initialize Flask
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

        # Clean session
        if "user_id" in session:
            user_id = session["user_id"]
            username = session["username"]
            session.clear()
            session["user_id"] = user_id
            session["username"] = username
        else:
            session.clear()

        # Clean timeout TESTS
        cur, conn = connect_db()

        cur.execute("DELETE FROM user_answers WHERE test_id IN (SELECT id FROM tests WHERE completed = false AND started_at <= NOW() - INTERVAL '3 hours');")
        cur.execute("DELETE FROM tests WHERE completed = false AND started_at <= NOW() - INTERVAL '3 hours';")
        conn.commit()

        # Progress section data
        if "user_id" in session:
            # Clean user's tests
            cur.execute("DELETE FROM user_answers WHERE test_id IN (SELECT id FROM tests WHERE completed = false AND user_id = %s);", (session["user_id"],))
            cur.execute("DELETE FROM tests WHERE completed = false AND user_id = %s;", (session["user_id"],))
            conn.commit()
            
            # Returns all tests completed by the user with a limit of 5 tests per category
            cur.execute("SELECT id, level_range, created_at, name FROM (SELECT t.id, r.level_range, r.created_at, c.name, ROW_NUMBER() OVER (PARTITION BY c.id ORDER BY r.created_at DESC) AS rn FROM tests t JOIN review_data r ON t.id = r.test_id JOIN categories c ON t.category_id = c.id WHERE t.user_id = %s) AS ranked WHERE rn <= 5 ORDER BY name, created_at DESC;", (session["user_id"],))
            results = cur.fetchall()
            tests = {}

            for row in results:
                category = row["name"]
                
                # Give format: "Month day, year"
                date_str = row["created_at"].strftime("%B %d, %Y")
                
                # Obtain level range
                range_str = f"{row['level_range'][0]}-{row['level_range'][1]}"
                
                test_entry = {
                    "id": row["id"],
                    "date": date_str,
                    "level_range": range_str
                }

                if category not in tests:
                    tests[category] = []
                
                tests[category].append(test_entry)
            
            close_db(cur, conn)
            return render_template("index.html", tests = tests)
        
        close_db(cur, conn)
        return render_template("index.html")
    
    if request.method == "POST":
        selected_test = request.form.get("tests")

        # create session fields
        session["test"] = selected_test
        session["question_num"] = 0
        session["used_levels"] = []
        session["new_question"] = True
        session["test_page"] = True
        session["correct_answers"] = []

        cur, conn = connect_db()

        session["beliefs"] = {i: 0.5 for i in range(1, 101)}
        session["exploring"] = False
        # Insert each test into tests
        cur.execute("SELECT id FROM categories WHERE name = %s", (selected_test,))
        category_db = cur.fetchone()
        cur.execute("INSERT INTO tests (user_id, category_id) VALUES (%s, %s) RETURNING id;", (session["user_id"], category_db["id"],))
        test = cur.fetchone()
        conn.commit()
        session["test_id"] = test["id"]

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
        user = cur.fetchone()

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
        if "user_id" in session:
            return redirect(url_for("index"))
        return render_template("login.html")
    

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to home
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
    session["beliefs"] = update_beliefs(False, session["question"]["level"], session["beliefs"])
    session["question"]["user_answer"] = ""
    session["correct"] = False
    # Update user_answers
    cur, conn = connect_db()

    cur.execute("INSERT INTO user_answers (question_id, is_correct, test_id) VALUES (%s, %s, %s);", (session["question"]["id"], False, session["test_id"]))
    conn.commit()

    close_db(cur, conn)

    session["test_page"] = False
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
        session["correct"] = True
        cur, conn = connect_db()

        cur.execute("INSERT INTO user_answers (question_id, is_correct, test_id) VALUES (%s, %s, %s);", (session["question"]["id"], True, session["test_id"]))
        conn.commit()

        close_db(cur, conn)
        session["beliefs"] = update_beliefs(True, session["question"]["level"], session["beliefs"])
    else:
        session["correct"] = False

        cur, conn = connect_db()
        cur.execute("INSERT INTO user_answers (question_id, is_correct, test_id) VALUES (%s, %s, %s);", (session["question"]["id"], False, session["test_id"]))
        conn.commit()
        close_db(cur, conn)
        session["beliefs"] = update_beliefs(False, session["question"]["level"], session["beliefs"])

    session["test_page"] = False
    # Redirect to feedback
    return redirect(url_for("feedback"))
    

@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if request.method == "POST":
        session["new_question"] = True
        session["test_page"] = True
        return redirect(url_for("test"))
    elif request.method == "GET":
        # If accessed illegaly
        if not "test" in session:
            return render_template("error.html", error_title = "No active test found", error_message = "You accessed this page without selecting a test first. Please go back to the homepage and choose one to begin.", button_message="Back to Homepage", button_href = "/")
        if session["test_page"]:
            session["new_question"] = False
            return redirect(url_for("test"))

        if session["question"]["type_name"] == "nti":
            if session["correct"]:
                session["question"]["answer_txt"] = session["question"]["answer_txt"].replace("__", f"<input type='text' name='answer' class='answer-input' value='{session["question"]["user_answer"]}' style='color: green; background-color: #d4edda; border: 1px solid #28a745;' autocomplete='off' disabled>")
            else:
                # Show correct answer
                session["question"]["correct_answer_txt"] = session["question"]["answer_txt_original"].replace("__", f"\\( {session['question']['correct_answer']} \\)")
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
    if not "test" in session:
        return render_template("error.html", error_title = "No active test found", error_message = "You accessed this page without selecting a test first. Please go back to the homepage and choose one to begin.", button_message="Back to Homepage", button_href = "/")
    if not session["test_page"]:
        return redirect(url_for("feedback"))
    if session["new_question"]:
        session["new_question"] = False
        
        # Set exploring to False if question number 0
        try:
            exploring = session["exploring"]
        except: 
            exploring = False
        cur, conn = connect_db()

        if not exploring and session["question_num"] != 0:
            # Check if breaking point found
            breaking_point = find_breaking_point(session["beliefs"])

            if breaking_point:
                session["final_level"] = breaking_point
                session["exploring"] = True
        # CHOOSE QUESTION
        if exploring == True:
            user_level = session["final_level"]
            chosen_lvl = choose_level_exploring(user_level, session["used_levels"], EXPLORING_FACTOR)
            # If no more levels available (end of exploring)
            if not chosen_lvl:
                # Update test as completed in db
                cur.execute("UPDATE tests SET completed = %s WHERE user_id = %s AND id = %s;", (True, session["user_id"], session["test_id"],))
                conn.commit()

                close_db(cur, conn)
                return redirect(url_for("test_final"))
        else:
            if session["question_num"] >= 20:
                if "test" in session:
                    del session["test"]
                return render_template("error.html", error_title = "We could not figure out your level!", error_message = "Please, go back to our Homepage and try again.", button_message="Back to Homepage", button_href = "/")
            # Choose question
            chosen_lvl = choose_lvl(session["beliefs"], session["used_levels"])

        session["question_num"] += 1
        
        # Remember used_levels
        session["used_levels"].append(chosen_lvl)
        # Select random question from chosen level (every needed field)
        cur.execute("SELECT questions.id, questions.level, questions.statement, questions.equation, questions.question, questions.image_url, questions.format_hint, questions.answer_txt, questions.calculator, categories.name AS category_name, question_types.name AS type_name FROM questions JOIN categories ON questions.category_id = categories.id JOIN question_types ON questions.type_id = question_types.id WHERE questions.level = %s AND categories.name = %s ORDER BY RANDOM() LIMIT 1;", (chosen_lvl, session["test"],)) 
        session["question"] = cur.fetchone()

        # Update needed fields for selected type question
        if session["question"]["type_name"] == "nti":
            session["question"]["answer_txt_nti"] = session["question"]["answer_txt"].replace("__", "<input form='answer_form' type='text' name='answer' class='answer-input' maxlength='15' autocomplete='off' required>")
            cur.execute("SELECT answer FROM answers WHERE question_id = %s", (session["question"]["id"],))
            correct_answer = cur.fetchone()
            session["question"]["correct_answer"] = correct_answer["answer"]
            session["question"]["answer_txt_original"] = session["question"]["answer_txt"]
            
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

            # Create <select> HTML
            select_html = "<select form='answer_form' name='answer' class='answer-select'>"
            select_html += "<option value='' disabled selected>Select an option</option>"
            for a in answers:
                if a["is_correct"] == True:
                    session["question"]["correct_answer"] = a["answer"]
                select_html += f"<option value='{a['answer']}'>{a['answer']}</option>"
            select_html += "</select>"

            # Replace "__" for <select>
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
    
        
@app.route("/test_final", methods=["GET"])
def test_final():
    estimated_level = (session['final_level'].stop + session['final_level'].start) / 2
    summary_text = get_level_summary(estimated_level)

    plot_data = plot_beliefs_svg(session["beliefs"])

    extended_min = max(session['final_level'].start - 15, 0)
    extended_max = min(session['final_level'].stop + 15, 100)
    cur, conn = connect_db()
    cur.execute("SELECT user_answers.id, user_answers.is_correct, subjects.name AS subject_name FROM user_answers JOIN questions ON user_answers.question_id = questions.id JOIN subjects ON questions.subject_id = subjects.id WHERE user_answers.test_id = %s AND questions.level > %s AND questions.level < %s", (session["test_id"], extended_min, extended_max,))
    user_answers = cur.fetchall()
    counts = {}
    for answer in user_answers:
        subject = answer["subject_name"]
        is_correct = answer["is_correct"]

        if subject not in counts:
            counts[subject] = {"total": 0, "correct": 0}
        counts[subject]["total"] += 1
        counts[subject]["correct"] += int(is_correct)

    final_result = {}
    weaknesses = []
    strengths = []
    for subject, stats in counts.items():
        total = stats["total"]
        correct = stats["correct"]

        ratio = correct / total
        if ratio < 0.7:
            classification = "weakness"
        elif ratio == 1.0:
            classification = "strength"
        else:
            classification = "neutral"

        final_result[subject] = classification

        if final_result[subject] == "weakness":
            weaknesses.append(subject)
        elif final_result[subject] == "strength":
            strengths.append(subject)
    
    # Add missing strengths
    cur.execute("SELECT user_answers.id, user_answers.is_correct, subjects.name AS subject_name FROM user_answers JOIN questions ON user_answers.question_id = questions.id JOIN subjects ON questions.subject_id = subjects.id WHERE user_answers.test_id = %s", (session["test_id"],))
    user_answers = cur.fetchall()
    counts = {}
    for answer in user_answers:
        subject = answer["subject_name"]
        is_correct = answer["is_correct"]

        if subject not in counts:
            counts[subject] = {"total": 0, "correct": 0}
        counts[subject]["total"] += 1
        counts[subject]["correct"] += int(is_correct)

    for subject, stats in counts.items():
        total = stats["total"]
        correct = stats["correct"]

        ratio = correct / total
        if ratio == 1.0:
            classification = "strength"
        else:
            classification = "neutral"

        final_result[subject] = classification

        if final_result[subject] == "strength" and subject not in strengths:
            strengths.append(subject)

    final_weak_materials = []
    if weaknesses:
        weak_placeholders = ', '.join(['%s'] * len(weaknesses))
        weak_query = f"SELECT m.title, m.url, m.summary, s.name FROM materials m JOIN subjects_materials sm ON m.id = sm.material_id JOIN subjects s ON sm.subject_id = s.id WHERE s.name IN ({weak_placeholders}) AND %s BETWEEN m.level_start AND m.level_stop"
        params = weaknesses + [estimated_level]
        
        cur.execute(weak_query, params)
        weak_materials = cur.fetchall()

        weak_subject_map = {}

        for row in weak_materials:
            subject_name = row["name"]
            material_info = {
                "title": row["title"],
                "url": row["url"],
                "summary": row["summary"]
            }

            if subject_name not in weak_subject_map:
                # New subject entry
                subject_entry = {
                    "subject": subject_name,
                    "materials": [material_info]
                }
                final_weak_materials.append(subject_entry)
                weak_subject_map[subject_name] = subject_entry
            else:
                # Append material to existent entry
                weak_subject_map[subject_name]["materials"].append(material_info)

    final_strong_materials = []
    if strengths:
        strong_placeholders = ', '.join(['%s'] * len(strengths))

        strong_query = f"SELECT m.title, m.url, m.summary, s.name FROM materials m JOIN subjects_materials sm ON m.id = sm.material_id JOIN subjects s ON sm.subject_id = s.id WHERE s.name IN ({strong_placeholders})"

        params = strengths
        cur.execute(strong_query, params)
        strong_materials = cur.fetchall()

        strong_subject_map = {}

        for row in strong_materials:
            subject_name = row["name"]
            material_info = {
                "title": row["title"],
                "url": row["url"],
                "summary": row["summary"]
            }

            if subject_name not in strong_subject_map:
                # New entry
                subject_entry = {
                    "subject": subject_name,
                    "materials": [material_info]
                }
                final_strong_materials.append(subject_entry)
                strong_subject_map[subject_name] = subject_entry
            else:
                # Append material to existent entry
                strong_subject_map[subject_name]["materials"].append(material_info)

    session["weaknesses"] = final_weak_materials
    session["strengths"] = final_strong_materials
    session["summary_text"] = summary_text

    json_weaknesses = json.dumps(session["weaknesses"])
    json_strengths = json.dumps(session["strengths"])
    json_beliefs = json.dumps(session["beliefs"])


    session["plot_data"] = plot_data

    level_range = [session["final_level"].start, session["final_level"].stop]

    cur.execute("INSERT INTO review_data (test_id, level_range, weaknesses, strengths, beliefs) VALUES (%s, %s, %s, %s, %s)", (session["test_id"], level_range, json_weaknesses, json_strengths, json_beliefs,))
    conn.commit()

    cur.execute("DELETE FROM user_answers WHERE test_id = %s", (session["test_id"],))
    conn.commit()
    close_db(cur, conn) 
    session["review"] = True
    if "test" in session:
        del session["test"]
    return redirect(url_for("review"))


@app.route("/review/test/<int:test_id>")
def review_test(test_id):
    cur, conn = connect_db()
    cur.execute("SELECT level_range, weaknesses, strengths, beliefs FROM review_data WHERE test_id = %s", (test_id,))
    results = cur.fetchone()

    session["final_level"] = range(results["level_range"][0], results["level_range"][1])
    session["weaknesses"] = results["weaknesses"]
    session["strengths"] = results["strengths"]

    estimated_level = (session['final_level'].start + session['final_level'].stop) / 2

    session["summary_text"] = get_level_summary(estimated_level)

    results["beliefs"] = {int(k): v for k, v in results["beliefs"].items()}

    session["plot_data"] = plot_beliefs_svg(results["beliefs"])

    session["review"] = True
    session["test"] = True
    close_db(cur, conn)
    return redirect(url_for("review"))


@app.route("/review", methods=["GET"])
def review():
    if not "review" in session or not session["review"]:
        return render_template("error.html", error_title = "You haven't finished your test yet", error_message = "To see your performance review, you need to complete the test first.", button_message="Resume your test", button_href = "/test")
    return render_template("review.html", 
                           final_level_start = session["final_level"].start,
                           final_level_stop = session["final_level"].stop,
                           weaknesses = session["weaknesses"],
                           strengths = session["strengths"],
                           summary_text = session["summary_text"],
                           plot_url = session["plot_data"],
                           username= session["username"],
                           )


if __name__ == "__main__":
    app.run(debug=True)
