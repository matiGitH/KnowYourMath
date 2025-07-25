import os
import psycopg2
import random
import math
import numpy as np
import io
import matplotlib
matplotlib.use('Agg') # Prevent matplotlib from using Tkinter
import matplotlib.pyplot as plt
from psycopg2.extras import RealDictCursor
from flask import redirect, render_template, session, g
from functools import wraps
from dotenv import load_dotenv


# Define constants
CHANGE_FACTOR = 0.15

load_dotenv()

DB_URL = os.getenv("SUPABASE_DB_URL_ipv4")

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
        user_answers = set(answers)
        cur.execute("SELECT answers.answer FROM answers JOIN questions ON answers.question_id = questions.id WHERE questions.id = %s AND answers.is_correct = TRUE;", (question_id,))
        results = cur.fetchall()
        correct_answers = {row["answer"] for row in results}
        return user_answers == correct_answers
    else:
        cur.execute("SELECT answers.answer FROM answers JOIN questions ON answers.question_id = questions.id WHERE questions.id = %s AND answers.is_correct = TRUE;", (question_id,))
        results = cur.fetchone()
        if results["answer"] == answers:
            return True
        else:
            return False
        
def find_uncertain_range(dict):
    """ Finds and returns range of keys that have a value 0.5 if existing. """
    for i in dict:
        if dict[i] == 0.5:
            for j in dict:
                try:
                    if dict[(i+j)] != 0.5:
                        return range(i, i+j)
                except:
                    return range(i, 101)
                
def choose_lvl(beliefs, used_levels):

    alpha = 200
    beta = 200


    # Generate a random number following the Beta distribution (close to 0.5).
    random_beta_num = random.betavariate(alpha, beta)

    # New dict with only available levels
    available_beliefs = {k: v for k, v in beliefs.items() if k not in used_levels and 0 != v != 1}


    # Select the key which has the closest value to our random generated number
    chosen_lvl = min(available_beliefs, key=lambda key: abs(beliefs[key] - random_beta_num))

    # randomize key selection if value is 0.5
    if available_beliefs[chosen_lvl] == 0.5:
        chosen_lvl = random.choice(find_uncertain_range(available_beliefs))

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
    Args:
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
    """
    Finds the 'breaking point' in a 100-level test where performance drops sharply.
    Args:
        my_dict (dict): beliefs dict.
    Returns:
        6-level range: The range where performance drops sharply comparing first and last three numbers.
        None: if no breaking point found.

    """
    levels = list(my_dict.keys())

    # Check first 3
    for i in range(1, 4):
        avg_first_3 = np.mean([my_dict[k] for k in range(1, 4)])
        if avg_first_3 <= 0.25: return range(1, 4)

    # Check last 5
    for i in range(100, 94, -1):
        average = np.mean([my_dict[i], my_dict[i-1]])
        if average >= 0.8:
            return range(95, 100)
    
    # Check all middle levels
    for i in range(len(levels) - 5):
        keys = [levels[i + j] for j in range(6)]

        avg_first_3 = np.mean([my_dict[k] for k in keys[:3]])
        avg_last_3  = np.mean([my_dict[k] for k in keys[3:]])

        if avg_first_3 >= 0.75 and avg_last_3 <= 0.25:
            return range(keys[0], keys[-1])

    return None  # No breaking point detected

def print_beliefs(beliefs):
    """
    Args:
        beliefs (dict[int, float]): Maps each level (1-100) to the user's success probability.
        
    Does not return anything. Prints the dict row by row.
    """
    for i in beliefs:
        print(f"{i}: {round(beliefs[i], 2)}")

def choose_level_exploring(my_range: range, used_levels: list, extension: int):
    """
    Choose a level in exploring mode. Parameters:
    my_range: user's level range
    used_levels: already used levels
    extension: how much to extend the user's level range to look for questions
    """
    start = my_range.start
    end = my_range.stop - 1

    new_start = max(1, start - extension)
    new_end = min(100, end + extension)

    if new_start > new_end:
        raise ValueError("new_start > new_end choose_level_exploring")

    possible_levels = set(range(new_start, new_end + 1))
    used_levels = set(used_levels)

    available_levels = possible_levels - used_levels

    if not available_levels:
        return False
    return random.choice(list(available_levels))

LEVEL_SUMMARIES = {
    "1-20": "You're just starting out on your journey. Many fundamental concepts are still unfamiliar, but that's completely normal. This review will guide you step by step toward a stronger foundation.",
    "21-40": "You've grasped some of the basics, but there's still work ahead. This review will help you identify what to reinforce and how to move confidently into the next level.",
    "41-60": "You're right in the middle of the path — with a solid grasp of many core ideas. There's room to grow, and this review highlights exactly where your strengths and weaknesses lie.",
    "61-80": "You've reached an advanced understanding of the subject. While you've mastered much, some fine-tuning can push you even further. Let's dive into your performance and uncover where to focus next.",
    "81-100": "You're performing at a near-expert level. Your understanding is deep, and only minor adjustments remain. This review will show where you can sharpen your edge even further."
}

def get_level_summary(level):
    if level <= 20:
        return LEVEL_SUMMARIES["1-20"]
    elif level <= 40:
        return LEVEL_SUMMARIES["21-40"]
    elif level <= 60:
        return LEVEL_SUMMARIES["41-60"]
    elif level <= 80:
        return LEVEL_SUMMARIES["61-80"]
    else:
        return LEVEL_SUMMARIES["81-100"]

def plot_beliefs_svg(beliefs_dict):
    fig, ax = plt.subplots(figsize=(5, 4))
    levels = list(beliefs_dict.keys())
    probs = list(beliefs_dict.values())

    ax.plot(levels, probs, color='orange')
    ax.set_xlabel("Question's level")
    ax.set_ylabel("Success probability")
    ax.set_title("System's beliefs")
    ax.grid(True)
    ax.set_ylim(0, 1)

    # Save plot as SVG
    img = io.BytesIO()
    plt.savefig(img, format='svg')
    plt.close(fig)
    img.seek(0)

    # return SVG as string
    return img.getvalue().decode('utf-8')


