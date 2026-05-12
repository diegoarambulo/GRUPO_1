import os
import logging
import threading
import pickle

# ✅ CRÍTICO: variables de entorno ANTES de cualquier import de torch/transformers
os.environ["TOKENIZERS_PARALLELISM"]  = "false"
os.environ["OMP_NUM_THREADS"]         = "1"
os.environ["MKL_NUM_THREADS"]         = "1"
os.environ["OPENBLAS_NUM_THREADS"]    = "1"
os.environ["VECLIB_MAXIMUM_THREADS"]  = "1"
os.environ["NUMEXPR_NUM_THREADS"]     = "1"
os.environ["TRANSFORMERS_OFFLINE"]    = os.environ.get("TRANSFORMERS_OFFLINE", "1")
os.environ["HF_DATASETS_OFFLINE"]     = os.environ.get("HF_DATASETS_OFFLINE",  "1")

import torch
torch.set_num_threads(1)
torch.set_num_interop_threads(1)

import faiss
import spacy
from huggingface_hub import snapshot_download
from sentence_transformers import SentenceTransformer
from transformers import (
    pipeline,
    AutoModelForSequenceClassification,
    AutoModelForTokenClassification,
    AutoModelForCausalLM,
    AutoTokenizer,
)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

HF_HOME = os.environ.get("HF_HOME", os.path.join(os.path.expanduser("~"), ".cache", "huggingface"))

MODELO_INTENCION  = "vicgalle/xlm-roberta-large-xnli-anli"
MODELO_NER        = "Babelscape/wikineural-multilingual-ner"
MODELO_QWEN       = "Qwen/Qwen2.5-1.5B-Instruct"
MODELO_EMBED      = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# ✅ Paths de los archivos FAISS — sobreescribibles por variable de entorno
FAISS_INDEX_PATH  = os.environ.get("FAISS_INDEX_PATH",  "/app/.cache/rag_content/sisad_index.faiss")
FAISS_CHUNKS_PATH = os.environ.get("FAISS_CHUNKS_PATH", "/app/.cache/rag_content/sisad_chunks.pkl")

logger.info(f"📦 HF_HOME            : {HF_HOME}")
logger.info(f"🔒 TRANSFORMERS_OFFLINE: {os.environ['TRANSFORMERS_OFFLINE']}")
logger.info(f"🖥️  Dispositivo        : {'CUDA' if torch.cuda.is_available() else 'CPU'}")

_load_lock = threading.Lock()


class ModelHandlers:

    _nlp_final              = None
    _clasificador_intencion = None
    _extractor_ner          = None
    _qwen_model             = None
    _qwen_tokenizer         = None
    _faiss_index            = None
    _faiss_chunks           = None
    _embed_model            = None
    _modelos_cargados       = False

    @classmethod
    def load_models(cls):
        if cls._modelos_cargados:
            return

        with _load_lock:
            if cls._modelos_cargados:
                return

            logger.info("⏳ Iniciando carga de modelos desde cache local...")

            # ── spaCy ─────────────────────────────────────────────────────────
            try:
                cls._nlp_final = spacy.load("es_core_news_lg")
                logger.info("✅ spaCy 'es_core_news_lg' cargado.")
            except Exception as e:
                logger.error(f"❌ Error al cargar spaCy: {e}")

            # ── XLM-RoBERTa ───────────────────────────────────────────────────
            try:
                logger.info(f"⏳ Cargando clasificador de intención: {MODELO_INTENCION}")
                tok = AutoTokenizer.from_pretrained(MODELO_INTENCION, local_files_only=True, fix_mistral_regex=True)
                mod = AutoModelForSequenceClassification.from_pretrained(MODELO_INTENCION, local_files_only=True)
                cls._clasificador_intencion = pipeline(
                    "zero-shot-classification",
                    model=mod,
                    tokenizer=tok,
                    device=-1,
                    num_workers=0,
                    multi_label=False,
                )
                logger.info("✅ Clasificador de intención cargado.")
            except Exception as e:
                logger.error(f"❌ Error al cargar clasificador de intención: {e}")

            # ── WikiNeural NER ────────────────────────────────────────────────
            try:
                logger.info(f"⏳ Cargando extractor NER: {MODELO_NER}")
                tok = AutoTokenizer.from_pretrained(MODELO_NER, local_files_only=True)
                mod = AutoModelForTokenClassification.from_pretrained(MODELO_NER, local_files_only=True)
                cls._extractor_ner = pipeline(
                    "ner",
                    model=mod,
                    tokenizer=tok,
                    aggregation_strategy="simple",
                    device=-1,
                    num_workers=0,
                )
                logger.info("✅ Extractor NER cargado.")
            except Exception as e:
                logger.error(f"❌ Error al cargar extractor NER: {e}")

            # ── Qwen2.5-1.5B-Instruct ─────────────────────────────────────────
            try:
                logger.info(f"⏳ Cargando LLM: {MODELO_QWEN}")
                cls._qwen_tokenizer = AutoTokenizer.from_pretrained(MODELO_QWEN, local_files_only=True)
                cls._qwen_model = AutoModelForCausalLM.from_pretrained(
                    MODELO_QWEN,
                    dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    device_map="auto" if torch.cuda.is_available() else "cpu",
                    local_files_only=True,
                )
                cls._qwen_model.eval()
                logger.info("✅ Qwen2.5-1.5B-Instruct cargado.")
            except Exception as e:
                logger.error(f"❌ Error al cargar Qwen: {e}")

            # ── FAISS Index ───────────────────────────────────────────────────
            try:
                logger.info(f"⏳ Cargando índice FAISS: {FAISS_INDEX_PATH}")
                cls._faiss_index = faiss.read_index(FAISS_INDEX_PATH)
                logger.info(f"✅ Índice FAISS cargado: {cls._faiss_index.ntotal} vectores.")
            except Exception as e:
                logger.error(f"❌ Error al cargar índice FAISS: {e}")

            # ── FAISS Chunks ──────────────────────────────────────────────────
            try:
                logger.info(f"⏳ Cargando chunks: {FAISS_CHUNKS_PATH}")
                with open(FAISS_CHUNKS_PATH, 'rb') as f:
                    cls._faiss_chunks = pickle.load(f)
                logger.info(f"✅ Chunks cargados: {len(cls._faiss_chunks)} chunks.")
            except Exception as e:
                logger.error(f"❌ Error al cargar chunks: {e}")

            # ── Modelo de Embeddings (SentenceTransformer) ────────────────────
            try:
                logger.info(f"⏳ Cargando modelo de embeddings: {MODELO_EMBED}")
                device = "cuda" if torch.cuda.is_available() else "cpu"
                local_path = snapshot_download(MODELO_EMBED, local_files_only=True, cache_dir=HF_HOME)
                cls._embed_model = SentenceTransformer(local_path, device=device)
                logger.info("✅ Modelo de embeddings cargado.")
            except Exception as e:
                logger.error(f"❌ Error al cargar modelo de embeddings: {e}")

            cls._modelos_cargados = True
            logger.info("✅ Proceso de carga de modelos completado.")

    # ── Getters ───────────────────────────────────────────────────────────────

    @classmethod
    def get_nlp_final(cls):
        if not cls._modelos_cargados:
            cls.load_models()
        if cls._nlp_final is None:
            raise RuntimeError("spaCy 'es_core_news_lg' no pudo ser cargado.")
        return cls._nlp_final

    @classmethod
    def get_clasificador_intencion(cls):
        if not cls._modelos_cargados:
            cls.load_models()
        if cls._clasificador_intencion is None:
            raise RuntimeError(f"Clasificador '{MODELO_INTENCION}' no pudo ser cargado.")
        return cls._clasificador_intencion

    @classmethod
    def get_extractor_ner(cls):
        if not cls._modelos_cargados:
            cls.load_models()
        if cls._extractor_ner is None:
            raise RuntimeError(f"Extractor NER '{MODELO_NER}' no pudo ser cargado.")
        return cls._extractor_ner

    @classmethod
    def get_qwen_model(cls):
        if not cls._modelos_cargados:
            cls.load_models()
        if cls._qwen_model is None:
            raise RuntimeError(f"Modelo Qwen '{MODELO_QWEN}' no pudo ser cargado.")
        return cls._qwen_model

    @classmethod
    def get_qwen_tokenizer(cls):
        if not cls._modelos_cargados:
            cls.load_models()
        if cls._qwen_tokenizer is None:
            raise RuntimeError(f"Tokenizer Qwen '{MODELO_QWEN}' no pudo ser cargado.")
        return cls._qwen_tokenizer

    @classmethod
    def get_faiss_index(cls):
        if not cls._modelos_cargados:
            cls.load_models()
        if cls._faiss_index is None:
            raise RuntimeError(f"Índice FAISS '{FAISS_INDEX_PATH}' no pudo ser cargado.")
        return cls._faiss_index

    @classmethod
    def get_faiss_chunks(cls):
        if not cls._modelos_cargados:
            cls.load_models()
        if cls._faiss_chunks is None:
            raise RuntimeError(f"Chunks FAISS '{FAISS_CHUNKS_PATH}' no pudieron ser cargados.")
        return cls._faiss_chunks

    @classmethod
    def get_embed_model(cls):
        if not cls._modelos_cargados:
            cls.load_models()
        if cls._embed_model is None:
            raise RuntimeError(f"Modelo de embeddings '{MODELO_EMBED}' no pudo ser cargado.")
        return cls._embed_model