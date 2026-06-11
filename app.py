from flask import Flask, render_template, request
import re
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuración para archivos subidos
UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = {'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# DICCIONARIO DE ENFERMEDADES (CIE-10)
DICCIONARIO_ENFERMEDADES = {
    "A00": "Cólera",
    "J00": "Rinitis aguda (Resfriado común)",
    "E10": "Diabetes tipo 1",
    "I10": "Hipertensión esencial (primaria)",
    "U07": "COVID-19"
}

# Tipos de sangre válidos
TIPOS_SANGRE_VALIDOS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}

# Especialidades válidas para el salón
ESPECIALIDADES_VALIDAS = {"MI", "CIR", "PED", "GO"}

# ========== LÉXICO ==========
def tokenizar_diagnostico(texto_diagnostico):
    codigo = texto_diagnostico.strip().upper()
    patron = r'^[A-Z]\d{2}$'
    if len(codigo) == 0:
        return {"tipo": "TOKEN_VACIO", "valor": ""}
    if re.match(patron, codigo):
        return {"tipo": "TOKEN_CODIGO_MEDICO", "valor": codigo}
    else:
        return {"tipo": "TOKEN_ERROR_LEXICO", "valor": codigo}

# ========== SINTAXIS ==========
def analizar_sintaxis(datos):
    campos_requeridos = [
        'nombre', 'apellido', 'dni', 'edad', 'diagnostico',
        'fecha', 'hora', 'hospital_clinica', 'laboratorio',
        'salon', 'examenes', 'enfermera_medico', 'tipo_sangre'
    ]
    errores = []
    for campo in campos_requeridos:
        if campo not in datos or not datos[campo] or len(datos[campo].strip()) == 0:
            errores.append(("SINTÁCTICO", f"Falta el campo '{campo}' en el archivo"))
    return errores

# ========== SEMÁNTICA ==========
def validar_semantica(datos, token_diagnostico):
    errores = []
    nombre = datos['nombre']
    apellido = datos['apellido']
    dni = datos['dni']
    edad = datos['edad']
    fecha = datos['fecha']
    hora = datos['hora']
    hospital = datos['hospital_clinica']
    laboratorio = datos['laboratorio']
    salon = datos['salon']
    examenes = datos['examenes']
    enfermera = datos['enfermera_medico']
    tipo_sangre = datos['tipo_sangre'].upper()

    # Validaciones de los campos originales
    if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', nombre.strip()):
        errores.append(("SEMÁNTICO", "El nombre solo debe contener letras"))
    if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', apellido.strip()):
        errores.append(("SEMÁNTICO", "El apellido solo debe contener letras"))
    try:
        edad_num = int(edad)
        if edad_num < 0 or edad_num > 120:
            errores.append(("SEMÁNTICO", "Edad fuera de rango (0-120)"))
    except ValueError:
        errores.append(("SEMÁNTICO", "La edad debe ser un número entero"))
    if len(dni.strip()) != 8 or not dni.isdigit():
        errores.append(("SEMÁNTICO", "El DNI debe tener exactamente 8 dígitos numéricos"))

    # Diagnóstico
    if token_diagnostico["tipo"] == "TOKEN_ERROR_LEXICO":
        errores.append(("LÉXICO", f"Código inválido: {token_diagnostico['valor']}"))
    elif token_diagnostico["tipo"] == "TOKEN_CODIGO_MEDICO":
        if token_diagnostico["valor"] not in DICCIONARIO_ENFERMEDADES:
            errores.append(("SEMÁNTICO", f"Código {token_diagnostico['valor']} no existe en el diccionario"))

    # Fecha (formato YYYY-MM-DD)
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
    except ValueError:
        errores.append(("SEMÁNTICO", "Fecha inválida. Use el formato YYYY-MM-DD (ej: 2025-03-15)"))

    # Hora (formato HH:MM)
    if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', hora):
        errores.append(("SEMÁNTICO", "Hora inválida. Use formato HH:MM (24h, ej: 14:30)"))

    # Hospital/Clínica (letras, espacios, puntos, guiones)
    if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\.\-]+$', hospital):
        errores.append(("SEMÁNTICO", "Hospital/Clínica solo puede contener letras, espacios, puntos y guiones"))

    # Laboratorio (alfanumérico y espacios, guiones bajos)
    if not re.match(r'^[a-zA-Z0-9\s\-_]+$', laboratorio):
        errores.append(("SEMÁNTICO", "Laboratorio solo puede contener letras, números, espacios, guiones y guiones bajos"))

    # Salón: formato ESPECIALIDAD-P[0-9]+-[0-9]+  ej: MI-P2-103
    patron_salon = r'^(MI|CIR|PED|GO)-P(\d+)-(\d+)$'
    match_salon = re.match(patron_salon, salon.strip().upper())
    if not match_salon:
        errores.append(("SEMÁNTICO", "Salón inválido. Formato esperado: ESPECIALIDAD-P[PISO]-[NÚMERO], ej: MI-P2-103. Especialidades: MI, CIR, PED, GO"))
    else:
        especialidad = match_salon.group(1)
        piso = int(match_salon.group(2))
        numero = int(match_salon.group(3))
        # Validaciones adicionales (opcional: rango de piso, etc.)
        if piso < 1 or piso > 10:
            errores.append(("SEMÁNTICO", "El piso debe estar entre 1 y 10"))
        if numero < 1 or numero > 999:
            errores.append(("SEMÁNTICO", "El número de salón debe estar entre 1 y 999"))

    # Exámenes (texto libre, no obligamos formato específico pero no vacío)
    if len(examenes.strip()) == 0:
        errores.append(("SEMÁNTICO", "El campo exámenes no puede estar vacío"))

    # Enfermera/Médico (letras, espacios, puntos, títulos como Dr., Dra.)
    if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\.]+$', enfermera):
        errores.append(("SEMÁNTICO", "Enfermera/Médico solo puede contener letras, espacios y puntos"))

    # Tipo de sangre
    if tipo_sangre not in TIPOS_SANGRE_VALIDOS:
        errores.append(("SEMÁNTICO", f"Tipo de sangre inválido. Válidos: {', '.join(TIPOS_SANGRE_VALIDOS)}"))

    return errores

# ========== PARSEO DEL ARCHIVO TXT ==========
def parsear_archivo_txt(contenido):
    # Mapeo de posibles nombres de campo a clave interna
    mapeo_campos = {
        'nombre': ['nombre'],
        'apellido': ['apellido'],
        'dni': ['dni'],
        'edad': ['edad'],
        'diagnostico': ['diagnostico', 'código diagnóstico', 'codigo'],
        'fecha': ['fecha'],
        'hora': ['hora'],
        'hospital_clinica': ['hospital/clínica', 'hospital', 'clinica', 'clínica', 'hospital_clinica'],
        'laboratorio': ['laboratorio'],
        'salon': ['salón', 'salon', 'sala'],
        'examenes': ['exámenes', 'examenes', 'pruebas'],
        'enfermera_medico': ['enfermera/médico', 'enfermera', 'medico', 'médico', 'enfermera_medico'],
        'tipo_sangre': ['tipo de sangre', 'tipo sangre', 'rh', 'tipo_sangre']
    }
    # Invertir para buscar por sinónimos
    sinonimos = {}
    for clave, lista in mapeo_campos.items():
        for sin in lista:
            sinonimos[sin.lower()] = clave

    datos = {}
    lineas = contenido.splitlines()
    patron_campo = re.compile(r'^\s*([^:]+?)\s*:\s*(.*)$')
    for linea in lineas:
        if linea.strip() == "":
            continue
        match = patron_campo.match(linea)
        if not match:
            raise ValueError(f"Línea con formato incorrecto: {linea}")
        nombre_campo_raw = match.group(1).strip().lower()
        valor = match.group(2).strip()
        # Buscar la clave interna
        clave_interna = sinonimos.get(nombre_campo_raw)
        if clave_interna:
            datos[clave_interna] = valor
        # Si no se reconoce, se ignora (podría agregarse advertencia)
    # Verificar que todos los campos requeridos estén
    required = set(mapeo_campos.keys())
    if not required.issubset(datos.keys()):
        faltantes = required - set(datos.keys())
        raise ValueError(f"Faltan los campos en el archivo: {', '.join(faltantes)}")
    return datos

# ========== RUTA PRINCIPAL ==========
@app.route("/", methods=["GET", "POST"])
def home():
    resultado = None
    errores_por_fase = {"LÉXICO": [], "SINTÁCTICO": [], "SEMÁNTICO": []}
    mensaje_error_general = None

    if request.method == "POST":
        if 'archivo' not in request.files:
            mensaje_error_general = "No se seleccionó ningún archivo"
        else:
            archivo = request.files['archivo']
            if archivo.filename == '':
                mensaje_error_general = "Nombre de archivo vacío"
            elif not allowed_file(archivo.filename):
                mensaje_error_general = "Formato no permitido. Use archivos .txt"
            else:
                try:
                    contenido = archivo.read().decode('utf-8')
                    datos = parsear_archivo_txt(contenido)

                    # Extraer campos
                    nombre = datos['nombre']
                    apellido = datos['apellido']
                    dni = datos['dni']
                    edad = datos['edad']
                    diagnostico_input = datos['diagnostico']
                    fecha = datos['fecha']
                    hora = datos['hora']
                    hospital_clinica = datos['hospital_clinica']
                    laboratorio = datos['laboratorio']
                    salon = datos['salon']
                    examenes = datos['examenes']
                    enfermera_medico = datos['enfermera_medico']
                    tipo_sangre = datos['tipo_sangre'].upper()

                    # 1. Léxico
                    token_diagnostico = tokenizar_diagnostico(diagnostico_input)

                    # 2. Sintaxis
                    errores_sintaxis = analizar_sintaxis(datos)

                    # 3. Semántica
                    errores_semantica = validar_semantica(datos, token_diagnostico)

                    # Consolidar errores
                    for fase, msg in errores_sintaxis:
                        errores_por_fase[fase].append(msg)
                    for fase, msg in errores_semantica:
                        errores_por_fase[fase].append(msg)

                    total_errores = len(errores_por_fase["LÉXICO"]) + len(errores_por_fase["SINTÁCTICO"]) + len(errores_por_fase["SEMÁNTICO"])

                    if total_errores == 0:
                        codigo = token_diagnostico["valor"]
                        enfermedad = DICCIONARIO_ENFERMEDADES[codigo]
                        resultado = {
                            "exito": True,
                            "nombre": nombre,
                            "apellido": apellido,
                            "dni": dni,
                            "edad": edad,
                            "diagnostico_nombre": enfermedad,
                            "codigo": codigo,
                            "token": token_diagnostico,
                            "fecha": fecha,
                            "hora": hora,
                            "hospital_clinica": hospital_clinica,
                            "laboratorio": laboratorio,
                            "salon": salon.upper(),
                            "examenes": examenes,
                            "enfermera_medico": enfermera_medico,
                            "tipo_sangre": tipo_sangre
                        }
                    else:
                        resultado = {
                            "exito": False,
                            "errores": errores_por_fase
                        }
                except Exception as e:
                    mensaje_error_general = f"Error al procesar el archivo: {str(e)}"

    return render_template("index.html", resultado=resultado, mensaje_error_general=mensaje_error_general)

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true")