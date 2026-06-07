from flask import Flask, render_template, request
import re

app = Flask(__name__)

# DICCIONARIO (SEMÁNTICA)
DICCIONARIO_ENFERMEDADES = {
    "A00": "Cólera",
    "J00": "Rinitis aguda (Resfriado común)",
    "E10": "Diabetes tipo 1",
    "I10": "Hipertensión esencial (primaria)",
    "U07": "COVID-19"
}

# LÉXICO (TOKENIZADOR)
def tokenizar_diagnostico(texto_diagnostico):

    codigo = texto_diagnostico.strip().upper()
    patron = r'^[A-Z]\d{2}$'

    if len(codigo) == 0:
        return {"tipo": "TOKEN_VACIO", "valor": ""}

    if re.match(patron, codigo):
        return {"tipo": "TOKEN_CODIGO_MEDICO", "valor": codigo}
    else:
        return {"tipo": "TOKEN_ERROR_LEXICO", "valor": codigo}


# SINTAXIS (NUEVO PARSER)
def analizar_sintaxis(nombre, apellido, dni, edad, token_diagnostico):
    errores = []

    # Regla de estructura general (GRAMÁTICA SIMPLE)
    # PACIENTE → NOMBRE APELLIDO DNI EDAD DIAGNÓSTICO

    if len(nombre.strip()) == 0:
        errores.append("Error Sintáctico: Falta nombre")

    if len(apellido.strip()) == 0:
        errores.append("Error Sintáctico: Falta apellido")

    if len(dni.strip()) == 0:
        errores.append("Error Sintáctico: Falta DNI")

    if len(edad.strip()) == 0:
        errores.append("Error Sintáctico: Falta edad")

    if token_diagnostico is None:
        errores.append("Error Sintáctico: Falta diagnóstico")

    return errores

# SEMÁNTICA
def validar_semantica(nombre, apellido, dni, edad, token_diagnostico):
    errores = []

    try:
        edad_num = int(edad)
        if edad_num < 0 or edad_num > 120:
            errores.append("Edad fuera de rango")
    except:
        errores.append("La edad debe ser numérica")

    if len(dni.strip()) != 8 or not dni.isdigit():
        errores.append("DNI debe tener 8 dígitos")

    # Diagnóstico semántico
    if token_diagnostico["tipo"] == "TOKEN_VACIO":
        errores.append("Error Léxico: Diagnóstico vacío")

    elif token_diagnostico["tipo"] == "TOKEN_ERROR_LEXICO":
        errores.append(f"Error Léxico: Código inválido {token_diagnostico['valor']}")

    elif token_diagnostico["tipo"] == "TOKEN_CODIGO_MEDICO":
        if token_diagnostico["valor"] not in DICCIONARIO_ENFERMEDADES:
            errores.append("Error Semántico: Código no existe en diccionario")

    return errores

# FLASK APP
@app.route("/", methods=["GET", "POST"])
def home():
    resultado = ""

    if request.method == "POST":

        nombre = request.form["nombre"]
        apellido = request.form["apellido"]
        dni = request.form["dni"]
        edad = request.form["edad"]
        diagnostico_input = request.form["diagnostico"]

        # 1. LÉXICO
        token_diagnostico = tokenizar_diagnostico(diagnostico_input)

        # 2. SINTAXIS
        errores = analizar_sintaxis(nombre, apellido, dni, edad, token_diagnostico)

        # 3. SEMÁNTICA
        errores += validar_semantica(nombre, apellido, dni, edad, token_diagnostico)

        # RESULTADO
        if errores:
            resultado = "<br>".join(f"• {e}" for e in errores)
        else:
            codigo = token_diagnostico["valor"]
            enfermedad = DICCIONARIO_ENFERMEDADES[codigo]

            resultado = f"""
            <h3 style="color:green;">✔ Compilación exitosa</h3>
            <b>Paciente:</b> {nombre} {apellido}<br>
            <b>DNI:</b> {dni}<br>
            <b>Edad:</b> {edad}<br>
            <b>Diagnóstico:</b> {enfermedad} ({codigo})<br>
            <br>
            <b>Token:</b> {token_diagnostico}
            """

    return render_template("index.html", resultado=resultado)

if __name__ == "__main__":
    app.run(debug=True)