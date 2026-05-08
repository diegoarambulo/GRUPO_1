from pydub import AudioSegment
import re
import unicodedata
import speech_recognition as sr

LEET_MAP = {
    "0": "o",
    "1": "i",
    "3": "e",
    "4": "a",
    "5": "s",
    "7": "t"
}

MESES = {
    "enero": "01",
    "febrero": "02",
    "marzo": "03",
    "abril": "04",
    "mayo": "05",
    "junio": "06",
    "julio": "07",
    "agosto": "08",
    "septiembre": "09",
    "setiembre": "09",
    "octubre": "10",
    "noviembre": "11",
    "diciembre": "12"
}

NUMEROS_TEXTO = {
    "uno": "1", "dos": "2", "tres": "3", "cuatro": "4", "cinco": "5",
    "seis": "6", "siete": "7", "ocho": "8", "nueve": "9", "diez": "10"
}

def remove_accents(text: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

def tokenize(text: str):
    return re.findall(r'\d{4}-\d{2}-\d{2}|\w+', text)

def normalize_numbers(text: str) -> str:
    for word, num in NUMEROS_TEXTO.items():
        text = re.sub(rf'\b{word}\b', num, text)
    return text

#filtro leet speak
def normalize_leet_safe(text: str) -> str:
    tokens = tokenize(text)
    new_tokens = []

    for token in tokens:
        # si es fecha → no tocar
        if re.match(r'\d{4}-\d{2}-\d{2}', token):
            new_tokens.append(token)
            continue

        # aplicar leet solo a texto
        new_token = ''.join(LEET_MAP.get(c, c) for c in token)
        new_tokens.append(new_token)

    return ' '.join(new_tokens)

def protect_dates(text: str):
    dates = re.findall(r'\d{4}-\d{2}-\d{2}', text)
    replacements = {}

    for i, d in enumerate(dates):
        key = f"__DATE{i}__"
        replacements[key] = d
        text = text.replace(d, key)

    return text, replacements

def normalize_dates(text: str) -> str:
    # formato completo: 1 de enero del 2026
    pattern_full = re.compile(r'\b(\d{1,2}) de (\w+) del (\d{4})\b')

    def repl_full(match):
        day = int(match.group(1))
        month = MESES.get(match.group(2), "01")
        year = match.group(3)
        return f"{year}-{month}-{day:02d}"

    text = pattern_full.sub(repl_full, text)

    # formato mes-año: marzo del 2026
    pattern_month = re.compile(r'\b(\w+) del (\d{4})\b')

    def repl_month(match):
        month = MESES.get(match.group(1), None)
        if month:
            return f"{match.group(2)}-{month}"
        return match.group(0)

    text = pattern_month.sub(repl_month, text)

    return text


def restore_dates(text: str, replacements: dict):
    for key, value in replacements.items():
        text = text.replace(key, value)
    return text


def remove_repeated_chars(text: str) -> str:
    # reduce repeticiones largas → "yaaaaa" → "ya"
    return re.sub(r'(.)\1{2,}', r'\1', text)


def clean_special_chars(text: str) -> str:
    # elimina todo excepto letras, numeros y espacios
    return re.sub(r'[^a-z0-9\s-]', '', text)

def convert_audio_to_wav(input_path: str, output_path: str) -> str:
    """Convierte un archivo de audio a formato WAV usando pydub."""
    audio = AudioSegment.from_file(input_path)
    audio.export(output_path, format="wav")
    return output_path

# ✅ Validación de cédula ecuatoriana mediante algoritmo de dígito verificador
def es_cedula_ecuatoriana(numero: str) -> bool:
    """
    Valida si un número de 10 dígitos es una cédula ecuatoriana válida.

    Reglas:
      - Exactamente 10 dígitos numéricos.
      - Los 2 primeros dígitos representan la provincia (01-24).
      - El dígito 10 es el verificador, calculado con coeficientes [2,1,2,1,2,1,2,1,2]:
          * Multiplicar cada dígito (1-9) por su coeficiente.
          * Si el resultado >= 10, restar 9.
          * Sumar todos los valores.
          * Dígito verificador = (10 - (suma % 10)) % 10.

    Returns:
        True si es una cédula válida, False en caso contrario.
    """
    if len(numero) != 10 or not numero.isdigit():
        return False

    provincia = int(numero[:2])
    if provincia < 1 or provincia > 24:
        return False

    coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    total = 0
    for i, coef in enumerate(coeficientes):
        valor = int(numero[i]) * coef
        if valor >= 10:
            valor -= 9
        total += valor

    digito_verificador = (10 - (total % 10)) % 10
    return digito_verificador == int(numero[9])


#Pipeline de normalizacion textual - limpieza de entrada
def normalize_content(content: str) -> str:
    if not content:
        return ""

    text = content.lower()

    # quitar acentos
    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

    # normalizar fechas primero
    text = normalize_dates(text)

    # tokenizar correctamente
    tokens = re.findall(r'\d{4}-\d{2}-\d{2}|\w+', text)

    normalized_tokens = []

    for token in tokens:
        # si es fecha → mantener intacta
        if re.match(r'\d{4}-\d{2}-\d{2}', token):
            normalized_tokens.append(token)
            continue

        # ✅ si es puramente numérico → mantener intacto
        # Evita que LEET_MAP destruya cédulas, teléfonos y otros identificadores
        if token.isdigit():
            normalized_tokens.append(token)
            continue

        # leet safe (solo aplica a tokens de texto)
        token = ''.join(LEET_MAP.get(c, c) for c in token)

        # numeros en texto
        for word, num in NUMEROS_TEXTO.items():
            token = re.sub(rf'\b{word}\b', num, token)

        # remover repeticiones
        token = re.sub(r'(.)\1{2,}', r'\1', token)

        # limpiar caracteres raros
        token = re.sub(r'[^a-z0-9]', '', token)

        if token:
            normalized_tokens.append(token)

    return ' '.join(normalized_tokens)

def processVoiceWithGoogleApi(file_path: str) -> str:
    """Procesa un archivo de audio usando la API de Google (a través de SpeechRecognition)."""
    recognizer = sr.Recognizer()
    try:
        # SpeechRecognition soporta formatos como WAV, AIFF, FLAC de forma nativa
        with sr.AudioFile(file_path) as source:
            audio_data = recognizer.record(source)
            # Transcribir usando Google Web Speech API (gratuito, para pruebas)
            text = recognizer.recognize_google(audio_data, language="es-ES")
            return text
    except sr.UnknownValueError:
        return "No se pudo entender el audio"
    except sr.RequestError as e:
        return f"Error al conectarse a la API de Google; {e}"
    except Exception as e:
        return f"Error procesando el audio: {str(e)}"