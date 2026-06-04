from flask import Flask, render_template, request

app = Flask(__name__)

# =====================
# VALIDACIÓN SEMÁNTICA
# =====================

def validar_semantica(nombre, edad, diagnostico):

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

    if len(diagnostico.strip()) < 3:
        errores.append("Diagnóstico inválido")

    return errores


# =====================
# RUTA PRINCIPAL
# =====================

@app.route("/", methods=["GET", "POST"])
def home():

    resultado = ""

    if request.method == "POST":

        nombre = request.form["nombre"]
        edad = request.form["edad"]
        diagnostico = request.form["diagnostico"]

        errores = validar_semantica(
            nombre,
            edad,
            diagnostico
        )

        if errores:

            resultado = "<br>".join(errores)

        else:

            resultado = f"""
            Registro médico válido ✅
            <br><br>
            Paciente: {nombre}
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