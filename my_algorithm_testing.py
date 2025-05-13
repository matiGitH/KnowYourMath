# PROBLEMAS:
# 1.  el codigo no puede detectar niveles de 98 o mayor


import random
import numpy as np

def choose_question(my_dict, precision, used_keys):
    """
    Selects a random key with weighted selection depending on the mode.
    Takes 3 arguments:
    my_dict: dictionary to choose from
    precision: takes "exploring", "intermediate" o "precise", selecting question accordingly
    used_keys: takes a list containing the used keys, avoiding choosing them again
    Returns a key (int) with the desired conditions
    """
    # Confirmacion de formato deleteable
    for valor in my_dict.values():
        if not (0 <= valor <= 1):
            raise ValueError("Todos los valores del diccionario deben estar entre 0 y 1.")

    if precision == "low":
        alpha = 40
        beta = 40

    elif precision == "intermediate":
        alpha = 60
        beta = 60 

    elif precision == "high":
        alpha = 200
        beta = 200

    while True:
        # Generamos un número aleatorio siguiendo la distribución Beta.
        numero_aleatorio_beta = random.betavariate(alpha, beta)

        # Buscamos la key en el diccionario cuyo valor asociado esté más cerca
        # del número generado por Beta.
        chosen_key = min(my_dict, key=lambda key: abs(my_dict[key] - numero_aleatorio_beta))

        # randomizar seleccion de key si value es 0.5
        if my_dict[chosen_key] == 0.5:
            chosen_key = random.choice(find_uncertain_range(my_dict))

        # elif precision == "precise":
        #     chosen_key = random.choice(find_uncertain_range(my_dict))
        
        if chosen_key and chosen_key not in used_keys and 0 != my_dict[chosen_key] != 1:
            break


    return chosen_key


def print_beliefs(beliefs):
    for i in beliefs:
        print(f"{i}: {beliefs[i]}")


def encontrar_cambio(diccionario):
    keys_ordenadas = list(diccionario.keys())
    
    for i in range(len(keys_ordenadas) - 1):
        key_actual = keys_ordenadas[i]
        try:
            key_siguiente = keys_ordenadas[i + 1]
        

            if diccionario[key_actual] >= 0.9 and diccionario[key_siguiente] <= 0.1: # and diccionario[key_siguiente2] <= 0.2 and diccionario[key_siguiente3] <= 0.2:
                return key_actual
        except:
            pass # Código para detectar si el usuario es 98, 99, 100

    return None  # Si no encontró ningún cambio


def find_uncertain_range(dict):
    for i in dict:
        if dict[i] == 0.5:
            for j in dict:
                try:
                    if dict[(i+j)] != 0.5:
                        return range(i, i+j)
                except:
                    return range(i, 101)
                

def main_algorithm(user_level):
    beliefs = {i: 0.5 for i in range(1, 101)}
    CHANGE = 0.15
    used_questions = []

    for i in range(50):
        if i < 3:
            selected_question = choose_question(beliefs, precision="high", used_keys=used_questions)
        elif i < 8:
            selected_question = choose_question(beliefs, "high", used_questions)
        else:
            selected_question = choose_question(beliefs, "high", used_questions)
                
        # print(f"question_num: {i+1}, question: {selected_question}, belief: {beliefs.get(selected_question, 'unknown')}")

        # Remember question
        used_questions.append(selected_question)


        if selected_question <= user_level:
            answer = "Y"
        elif selected_question >= user_level:
            answer = "N"

        if answer == "Y":
            beliefs[selected_question] = 1
            count = 1
            for j in range(selected_question, 0, -1):
                if 0 < j < 101:
                    beliefs[j] = max(0, min(1, beliefs[j] + CHANGE + (CHANGE - 0.14) * count))
                    count +=1

        elif answer == "N":
            beliefs[selected_question] = 0
            for j in range(selected_question + 1, 101):
                if 0 < j < 101:
                    beliefs[j] = max(0, min(1, beliefs[j] - CHANGE - (CHANGE - 0.14) * (j-selected_question)))

        

        level_key = encontrar_cambio(beliefs)


        # print_beliefs(beliefs)

        if level_key:
            # print(f"ES EL {level_key}. Tomo {i+1} preguntas")
            summary = (i+1)
            break

    return summary

summary = []
for i in range (1, 100):
    summary.append(main_algorithm(i))

for num in summary:
    print(num)