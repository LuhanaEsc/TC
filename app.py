from flask import Flask, render_template, request
import re

app = Flask(__name__)

# DICCIONARIO DE CÓDIGOS MÉDICOS (El "Minicompilador" buscará aquí)
DICCIONARIO_ENFERMEDADES = {
    "A00": "Cólera",
    "J00": "Rinitis aguda (Resfriado común)",
    "E10": "Diabetes mellitus tipo 1",
    "I10": "Hipertensión esencial (primaria)",
    "K21": "Enfermedad por reflujo gastroesofágico",
    "N39": "Infección de vías urinarias",
    "U07": "COVID-19",
    "B01": "Varicela"
}

# VALIDACIÓN SEMÁNTICA
def validar_semantica(nombre, apellido, dni, edad, diagnostico_codigo):
    errores = []

    # Validación de Edad
    try:
        edad_int = int(edad)
        if edad_int < 0:
            errores.append("Edad negativa")
        if edad_int > 120:
            errores.append("Edad fuera de rango")
    except ValueError:
        errores.append("La edad debe ser numérica")

    # Validación de Nombre
    if len(nombre.strip()) == 0:
        errores.append("Nombre vacío")
    elif not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$', nombre.strip()):
        errores.append("El nombre solo puede contener letras")
    
    # Validación de Apellido
    if len(apellido.strip()) == 0:
        errores.append("Apellido vacío")
    elif not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$', apellido.strip()):
        errores.append("El apellido solo puede contener letras")

    # Validación de DNI
    dni_clean = dni.strip()
    if len(dni_clean) == 0:
        errores.append("DNI vacío")
    else:
        if len(dni_clean) != 8:
            errores.append("El DNI debe tener 8 caracteres")
        elif not dni_clean.isdigit():
            errores.append("El DNI solo puede contener números")

    # VALIDACIÓN DEL CÓDIGO DE ENFERMEDAD (Minicompilador)
    codigo_clean = diagnostico_codigo.strip().upper() # Lo pasamos a mayúsculas para evitar errores
    if len(codigo_clean) == 0:
        errores.append("Código de diagnóstico vacío")
    elif codigo_clean not in DICCIONARIO_ENFERMEDADES:
        errores.append(f"Error de Compilación: El código '{codigo_clean}' no corresponde a ninguna enfermedad registrada")

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
        diagnostico_codigo = request.form["diagnostico"] # Aquí el doctor pone el código

        errores = validar_semantica(
            nombre,
            apellido,
            dni,
            edad,
            diagnostico_codigo
        )

        if errores:
            # Mostramos los errores formateados
            resultado = "<div style='color: red;'><b>Errores encontrados:</b><br>" + "<br>".join(f"• {err}" for err in errores) + "</div>"
        else:
            # Traducimos el código usando nuestro diccionario
            codigo_up = diagnostico_codigo.strip().upper()
            enfermedad_traducida = DICCIONARIO_ENFERMEDADES[codigo_up]

            # Imprimimos la ficha médica completa con la traducción
            resultado = f"""
            <div style="border: 2px solid green; padding: 15px; background-color: #f9fff9;">
                <h3 style="color: green; margin-top: 0;">Registro Médico Válido ✅</h3>
                <hr>
                <b>Paciente:</b> {apellido.strip().upper()}, {nombre.strip()} <br>
                <b>DNI:</b> {dni.strip()} <br>
                <b>Edad:</b> {edad} años <br>
                <hr>
                <b>Código CIE:</b> <span style="background-color: #ffffcc; padding: 2px 5px;">{codigo_up}</span> <br>
                <b>Enfermedad Traducida:</b> <span style="color: blue; font-weight: bold;">{enfermedad_traducida}</span>
            </div>
            """

    return render_template(
        "index.html",
        resultado=resultado
    )

if __name__ == "__main__":
    app.run(debug=True)
