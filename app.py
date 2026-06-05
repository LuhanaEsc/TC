from flask import Flask, render_template, request
import re

app = Flask(__name__)

# Diccionario de enfermedades (Nuestra tabla de símbolos/traducción)
DICCIONARIO_ENFERMEDADES = {
    "A00": "Cólera",
    "J00": "Rinitis aguda (Resfriado común)",
    "E10": "Diabetes mellitus tipo 1",
    "I10": "Hipertensión esencial (primaria)",
    "U07": "COVID-19"
}

# ==========================================
# COMPONENTE: ANALIZADOR LÉXICO (TOKENIZADOR)
# ==========================================
def tokenizar_diagnostico(texto_diagnostico):
    """
    Convierte el texto ingresado en un Token con su Tipo y Valor.
    """
    codigo = texto_diagnostico.strip().upper()
    
    # Expresión regular para validar el formato del código (Una letra seguida de dos números)
    patron_codigo_cie = r'^[A-Z]\d{2}$'
    
    if len(codigo) == 0:
        return {"tipo": "TOKEN_VACIO", "valor": ""}
        
    if re.match(patron_codigo_cie, codigo):
        # Si tiene la estructura correcta, es un token de código médico
        return {"tipo": "TOKEN_CODIGO_MEDICO", "valor": codigo}
    else:
        # Si metió cualquier otra cosa, es un token de error/desconocido
        return {"tipo": "TOKEN_ERROR_LEXICO", "valor": codigo}


# ==========================================
# COMPONENTE: ANALIZADOR SEMÁNTICO
# ==========================================
def validar_semantica(nombre, apellido, dni, edad, token_diagnostico):
    errores = []

    # [Validaciones de Nombre, Apellido, DNI y Edad se mantienen igual...]
    try:
        if int(edad) < 0 or int(edad) > 120: errores.append("Edad fuera de rango")
    except: errores.append("La edad debe ser numérica")
    if len(nombre.strip()) == 0: errores.append("Nombre vacío")
    if len(apellido.strip()) == 0: errores.append("Apellido vacío")
    if len(dni.strip()) != 8 or not dni.strip().isdigit(): errores.append("DNI debe tener 8 dígitos numéricos")

    # VALIDACIÓN SEMÁNTICA USANDO EL TOKEN
    if token_diagnostico["tipo"] == "TOKEN_VACIO":
        errores.append("Error Léxico: El campo de diagnóstico está vacío.")
        
    elif token_diagnostico["tipo"] == "TOKEN_ERROR_LEXICO":
        errores.append(f"Error Léxico: Sintaxis de código inválida '{token_diagnostico['valor']}'. Debe ser una letra y dos números (Ej: A00).")
        
    elif token_diagnostico["tipo"] == "TOKEN_CODIGO_MEDICO":
        # El token existe formalmente, ahora el analizador semántico ve si tiene significado real
        codigo_valor = token_diagnostico["valor"]
        if codigo_valor not in DICCIONARIO_ENFERMEDADES:
            errores.append(f"Error Semántico: El token [{codigo_valor}] es válido formalmente, pero no existe en el diccionario de enfermedades.")

    return errores


# RUTA PRINCIPAL
@app.route("/", methods=["GET", "POST"])
def home():
    resultado = ""

    if request.method == "POST":
        nombre = request.form["nombre"]
        apellido = request.form["apellido"]
        dni = request.form["dni"]
        edad = request.form["edad"]
        diagnostico_input = request.form["diagnostico"]

        # 1. PASO LÉXICO: Generamos el Token
        token_diagnostico = tokenizar_diagnostico(diagnostico_input)

        # 2. PASO SEMÁNTICO: Validamos el Token y los demás datos
        errores = validar_semantica(nombre, apellido, dni, edad, token_diagnostico)

        if errores:
            resultado = "<div style='color: red;'><b>Errores de Compilación:</b><br>" + "<br>".join(f"• {err}" for err in errores) + "</div>"
        else:
            # 3. PASO DE GENERACIÓN DE CÓDIGO / TRADUCCIÓN
            codigo_final = token_diagnostico["valor"]
            enfermedad_traducida = DICCIONARIO_ENFERMEDADES[codigo_final]

            resultado = f"""
            <div style="border: 2px solid green; padding: 15px; background-color: #f9fff9;">
                <h3 style="color: green; margin-top: 0;">¡Compilación Exitosa! ✅</h3>
                <p><b>Token Generado:</b> <code>{{tipo: "{token_diagnostico['tipo']}", valor: "{token_diagnostico['valor']}"}}</code></p>
                <hr>
                <b>Paciente:</b> {apellido.upper()}, {nombre} | <b>DNI:</b> {dni} | <b>Edad:</b> {edad}<br>
                <b>Diagnóstico Traducido:</b> <span style="color: blue; font-weight: bold;">{enfermedad_traducida} ({codigo_final})</span>
            </div>
            """

    return render_template("index.html", resultado=resultado)

if __name__ == "__main__":
    app.run(debug=True)
