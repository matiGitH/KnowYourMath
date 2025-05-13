def calcular_promedio_una_columna(nombre_archivo):
    """
    Lee un archivo de texto con un valor numérico por línea
    y calcula el promedio de esos valores.

    Args:
        nombre_archivo (str): La ruta al archivo de texto.

    Returns:
        float: El promedio de los valores,
               o None si el archivo está vacío o no se pueden extraer valores.
    """
    valores = []
    try:
        with open(nombre_archivo, "r", encoding="utf-16") as archivo:
            for linea in archivo:
                linea = linea.strip()
                if linea:
                    try:
                        valor = int(linea)
                        valores.append(valor)
                    except ValueError:
                        print(f"Advertencia: No se pudo convertir a número el valor '{linea}'.")
    except FileNotFoundError:
        print(f"Error: El archivo '{nombre_archivo}' no fue encontrado.")
        return None

    if valores:
        promedio = sum(valores) / len(valores)
        return promedio
    else:
        print("Advertencia: No se encontraron valores válidos en el archivo.")
        return None

# Especifica el nombre de tu archivo
nombre_del_archivo = 'high.txt'

# Calcula el promedio
promedio_de_valores = calcular_promedio_una_columna(nombre_del_archivo)

# Imprime el resultado
if promedio_de_valores is not None:
    print(f"El promedio de los valores es: {promedio_de_valores}")