from flask import Flask, render_template, request

app = Flask(__name__)

# VALIDACIÓN SEMÁNTICA

def validar_semantica(nombre, apellido, dni, edad, diagnostico):
    errores = []

    try:
        edad = int(edad)

        if edad < 0:
            errores.append("Edad negativa")

        if edad > 120:
            errores.append("Edad fuera de rango")

    except:
        errores.append("La edad debe ser numérica")

    if len(nombre.strip()) == 0:
        errores.append("Nombre vacío")
    elif not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$', nombre.strip()):  # devuelve True si NO hay coincidencia
        errores.append("El nombre solo puede contener letras")
    
    if len(apellido.strip()) == 0:
        errores.append("Apellido vacío")
    elif not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$', apellido.strip()):
        errores.append("El apellido solo puede contener letras")

    if len(dni.strip()) == 0:
        errores.append("DNI vacío")
    else:
        if len(dni.strip()) != 8:
            errores.append("El DNI debe tener 8 caracteres")
        elif not dni.strip().isdigit():
            errores.append("El DNI solo puede contener números")

    if len(diagnostico.strip()) < 3:
        errores.append("Diagnóstico inválido")

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
        diagnostico = request.form["diagnostico"]

        errores = validar_semantica(
            nombre,
            apellido,
            dni,
            edad,
            diagnostico
        )

        if errores:
            resultado = "<br>".join(errores)
        else:
            resultado = f"""
            Registro médico válido ✅
            <br><br>
            Paciente: {nombre} {apellido}
            <br>
            DNI: {dni}
            <br>
            Edad: {edad}
            <br>
            Diagnóstico: {diagnostico}
            """

    return render_template(
        "index.html",
        resultado=resultado
    )

if __name__ == "__main__":
    app.run(debug=True)