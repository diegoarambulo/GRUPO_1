import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from TextUtils import normalize_content, processVoiceWithGoogleApi, convert_audio_to_wav
from flowRunner import FlowRunner
from modelHandlers import ModelHandlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ✅ Modelo para la entrada de texto
class TextQuery(BaseModel):
    text: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Iniciando aplicación — cargando modelos...")
    ModelHandlers.load_models()
    logger.info("✅ Modelos listos. API disponible.")
    yield
    logger.info("🛑 Cerrando aplicación.")

app = FastAPI(
    title="API de Búsqueda de Documentos",
    description="API para buscar documentos por texto o voz.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ✅ FlowRunner se instancia UNA SOLA VEZ al arrancar, no en cada request
_flow_runner: FlowRunner = None

@app.post("/document/search/byText")
async def search_by_text(query: TextQuery):
    """Busca documentos basándose en una cadena de texto."""
    global _flow_runner
    if _flow_runner is None:
        _flow_runner = FlowRunner()

    logger.info(f"Recibida solicitud de búsqueda por texto: {query.text}")
    #normalized_text = normalize_content(query.text)
    normalized_text = query.text

    response = _flow_runner.procesar_consulta(normalized_text)

    return {
        "query": query.text,
        "resultado": response["result"],
        "tipo": response["type"],
        "modelResponse": response["modelResponse"],
    }

@app.post("/document/search/byVoice")
async def search_by_voice(audio_file: UploadFile = File(...)):
    """Busca documentos basándose en un archivo de audio."""
    global _flow_runner
    if _flow_runner is None:
        _flow_runner = FlowRunner()

    logger.info(f"Recibida solicitud de búsqueda por voz: {audio_file.filename}")

    original_file_location = f"/tmp/{audio_file.filename}"
    with open(original_file_location, "wb") as f:
        f.write(audio_file.file.read())

    wav_file_location = f"/tmp/converted_{audio_file.filename}.wav"
    try:
        convert_audio_to_wav(original_file_location, wav_file_location)
    except Exception as e:
        return {"message": f"Error al convertir el audio: {str(e)}", "filename": audio_file.filename, "results": []}

    transcription = processVoiceWithGoogleApi(wav_file_location)
    #transcription = normalize_content(transcription)
    resultado = _flow_runner.procesar_consulta(transcription)

    return {
        "query": transcription,
        "resultado": resultado["result"],
        "tipo": resultado["type"],
        "modelResponse": resultado["modelResponse"],
    }
