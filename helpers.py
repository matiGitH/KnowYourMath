import os
import psycopg2
import random
import math
import statistics
import numpy as np
from psycopg2.extras import RealDictCursor
from flask import redirect, render_template, session, g
from functools import wraps
from dotenv import load_dotenv


# Define constants
TRIGONOMETRY_QUESTIONS_NUM = 142
STATISTICS_QUESTIONS_NUM = 0
ALGEBRA_QUESTIONS_NUM = 0
CALCULUS_QUESTIONS_NUM = 0

CHANGE_FACTOR = 0.15

load_dotenv()

DB_URL = os.getenv("SUPABASE_DB_URL_ipv4")

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function  


def connect_db():
    """ Conects to database and returns cur and conn """
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    return cur, conn

def close_db(cur, conn):
    """ Closes connection. Takes 2 parameters: cur and conn """
    cur.close()
    conn.close()
    return


def validate_answer(answers, question_id, ma=False):
    """ Validates answer. Takes 3 parameters: 
    answer: user answer/s
    ma: is type ma (True/False)
    question_id: question's id
    Returns TRUE (correct) or FALSE (incorrect)
    """
    cur, conn = connect_db()
    if ma:
        user_answers = set(answers)  # lista a set
        cur.execute("SELECT answers.answer FROM answers JOIN questions ON answers.question_id = questions.id WHERE questions.id = %s AND answers.is_correct = TRUE;", (question_id,))
        results = cur.fetchall()
        correct_answers = {row["answer"] for row in results}  # dicts a set
        return user_answers == correct_answers
    else:
        cur.execute("SELECT answers.answer FROM answers JOIN questions ON answers.question_id = questions.id WHERE questions.id = %s AND answers.is_correct = TRUE;", (question_id,))
        results = cur.fetchone()
        if results["answer"] == answers:
            return True
        else:
            return False

    
# def validate_ma(answers, type, question_id):
#     """ Validates ma answer. Takes 2 parameters: answers (a list that contains the answers), question_id.
#     Returns TRUE (correct) or FALSE (incorrect) """

#     user_answers = set(answers)  # lista a set

#     cur, conn = connect_db()
#     cur.execute("SELECT answers.answer FROM answers JOIN questions ON answers.question_id = questions.id WHERE questions.id = %s AND answers.is_correct = TRUE;", (question_id,))
#     results = cur.fetchall()
#     close_db(cur, conn)

#     correct_answers = {row["answer"] for row in results}  # dicts a set

#     return user_answers == correct_answers
                
def choose_lvl(beliefs, used_levels):

    alpha = 200
    beta = 200

    while True:
        # Generamos un número aleatorio siguiendo la distribución Beta.
        random_beta_num = random.betavariate(alpha, beta)

        # Buscamos la key en el diccionario cuyo valor asociado esté más cerca
        # del número generado por Beta.
        chosen_lvl = min(beliefs, key=lambda key: abs(beliefs[key] - random_beta_num))

        # randomizar seleccion de key si value es 0.5
        if beliefs[chosen_lvl] == 0.5:
            chosen_lvl = random.choice(find_uncertain_range(beliefs))
        
        if chosen_lvl and chosen_lvl not in used_levels and 0 != beliefs[chosen_lvl] != 1:
            break

    return chosen_lvl

def update_beliefs(correct, question_lvl, beliefs):
    for level in range(1, 101):
        if correct:
            if level <= question_lvl:
                if level >= question_lvl - 10:
                    beliefs[level] = update_answer(True, beliefs[level], abs(question_lvl-level), True, True)
                else:
                    beliefs[level] = update_answer(True, beliefs[level], abs(question_lvl-level), False, True)
            elif level <= question_lvl + 10:
                beliefs[level] = update_answer(True, beliefs[level], abs(question_lvl-level), True, False)
            else:
                pass
        else:
            if level >= question_lvl:
                if level <= question_lvl + 10:
                    beliefs[level] = update_answer(False, beliefs[level], abs(question_lvl-level), True, True)
                else:
                    beliefs[level] = update_answer(False, beliefs[level], abs(question_lvl-level), False, True)
            elif level >= question_lvl - 10:
                beliefs[level] = update_answer(False, beliefs[level], abs(question_lvl-level), True, False)
            else:
                pass

    return beliefs


def update_answer(correct, value, answered_distance, neighbourhood, accumulated):
    """
    Arguments:
    correct (boolean): if answer was correct (True) or not (False)
    value (float): the value to modify
    answered_distance: distance from 

    Returns:
    value (float) with the added weight, accumulated weight and neighbourhood weight (positive or negative)
    """

    # Find distance between value and middle (0.5)
    middle_distance = max(abs(value - 0.5), 0.01)

    # if this was the answered question
    if answered_distance == 0:
        weight = (0.2 / (middle_distance + 0.4) - 0.12)
        if correct: return max(min(value + weight, 1), 0)
        elif not correct: return max(min(value - weight, 1), 0)

    # Calculate weight based on middle distance
    weight = (-46.897 * (middle_distance ** 5)) + (76.44 * (middle_distance ** 4)) - (54.08 * (middle_distance ** 3)) + (22.52 * (middle_distance ** 2)) - (5.96 * middle_distance) + 0.8

    if neighbourhood:
        neighbourhood_weight = 0.239 * ((math.e) ** (-0.305 * answered_distance))
    else:
        neighbourhood_weight = 0


    if accumulated:
        accumulated_weight = ((0.015)/(3)) * answered_distance + 0.02
    else:
        accumulated_weight = 0

    total_weight = weight * (neighbourhood_weight+accumulated_weight)

    if correct: return max(min(value + total_weight, 1), 0)

    elif not correct: return max(min(value - total_weight, 1), 0)


def find_breaking_point(my_dict):
    levels = list(my_dict.keys())

    # Check first 3
    for i in range(1, 4):
        avg_first_3 = np.mean([my_dict[k] for k in range(1, 4)])
        if avg_first_3 <= 0.25: return range(1, 4)

    # Check last 5
    for i in range(100, 94, -1):
        average = np.mean([my_dict[i], my_dict[i-1]])
        if average >= 0.75: return i
    
    # Check all middle levels
    for i in range(len(levels) - 5):
        keys = [levels[i + j] for j in range(6)]

        avg_first_3 = np.mean([my_dict[k] for k in keys[:3]])
        avg_last_3  = np.mean([my_dict[k] for k in keys[3:]])

        if avg_first_3 >= 0.75 and avg_last_3 <= 0.25:
            return range(keys[0], keys[-1])



    return None  # No breaking point detected

def binary_entropy(p):
    if p == 0 or p == 1:
        return 0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)

def binary_entropy_dict(dictionary):
    return sum(binary_entropy(p) for p in dictionary.values())

    
def print_beliefs(beliefs):
    for i in beliefs:
        print(f"{i}: {round(beliefs[i], 2)}")


def find_uncertain_range(dict):
    for i in dict:
        if dict[i] == 0.5:
            for j in dict:
                try:
                    if dict[(i+j)] != 0.5:
                        return range(i, i+j)
                except:
                    return range(i, 101)


# def choose_lvl(beliefs, used_levels):
#     information_gain_dict = {}

#     for level in beliefs:
#         p_correct = beliefs[level]
#         p_wrong = 1 - p_correct

#         positive_beliefs = update_beliefs(True, level, beliefs.copy(), False)
#         gain_if_correct = sum(positive_beliefs.values()) - sum(beliefs.values())

#         negative_beliefs = update_beliefs(False, level, beliefs.copy(), False)
#         gain_if_wrong = max(sum(beliefs.values()) - sum(negative_beliefs.values()), 0)

#         information_gain_dict[f"{level}"] = (p_correct * gain_if_correct + p_wrong * gain_if_wrong)

#     max_value = max(information_gain_dict.values())

#     print_beliefs(information_gain_dict)

#     for i in information_gain_dict:
#         if information_gain_dict[i] == max_value:
#             if i in used_levels:
#                 raise ValueError("We screwed up goofy")
#             return i