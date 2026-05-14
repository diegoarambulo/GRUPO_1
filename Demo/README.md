# EasyDoc — Agente Gestor Documental SISAD

Sistema de búsqueda inteligente de documentos con procesamiento de lenguaje natural, desarrollado para la plataforma SISAD (Sistema de Administración Documental). Permite realizar consultas en texto libre o por voz para localizar documentos de forma rápida y precisa.

---

## Demo en línea

El portal está disponible en:

**[https://demogrupo1front.goitsa.me](https://demogrupo1front.goitsa.me)**

- Accesible desde cualquier dispositivo — diseño responsive para escritorio, tablet y móvil.
- No requiere instalación ni configuración del lado del cliente.

### APIs consumidas

| Endpoint | Descripción |
|----------|-------------|
| `POST https://demogrupo1back.goitsa.me/document/search/byText` | Búsqueda de documentos por texto libre |
| `POST https://demogrupo1back.goitsa.me/document/search/byVoice` | Búsqueda de documentos por audio (voz) |

---

## Reproducción en local

### Requisitos previos

- [Docker](https://www.docker.com/) instalado y en ejecución.
- Archivo RAR con los modelos de lenguaje descargado y descomprimido (ver sección siguiente).

### 1. Preparar los modelos

Descarga el archivo RAR con los modelos preentrenados desde:

**[https://drive.google.com/file/d/1netmwZlUFtSRovn3Mz3X9-Y9IgKht-ZL/view?usp=sharing](https://drive.google.com/file/d/1netmwZlUFtSRovn3Mz3X9-Y9IgKht-ZL/view?usp=sharing)**

Descomprime el contenido **dentro de la carpeta `hf_cache`** en el directorio raíz del proyecto:

```
sissadAgenteGestorDocumental/
├── hf_cache/          ← descomprimir aquí el contenido del RAR
├── rag_content/
├── ssl/
├── src/
└── dockerfile
```

### 2. Construir la imagen

```bash
docker build --build-arg HF_TOKEN=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 -t nlp-grupo1-sissad:v1 .
```

### 3. Iniciar el contenedor

```bash
docker rm -f agenteGestorDocumentalSISSAD_G1

docker run -d --rm -p 8000:8000 \
  --name agenteGestorDocumentalSISSAD_G1 \
  --user root \
  -v "$(pwd)/hf_cache:/app/.cache/huggingface" \
  -v "$(pwd)/rag_content:/app/.cache/rag_content" \
  -v "$(pwd)/ssl:/certs" \
  nlp-grupo1-sissad:v1
```

La API quedará disponible en `http://localhost:8000`.

### 4. Verificar que está corriendo

```bash
docker logs -f agenteGestorDocumentalSISSAD_G1
```

Espera el mensaje `✅ Modelos listos. API disponible.` antes de realizar consultas.

---

## Uso de la API

### Búsqueda por texto

```bash
curl -X POST http://localhost:8000/document/search/byText \
  -H "Content-Type: application/json" \
  -d '{"text": "necesito el contrato de Juan Pérez con cédula 0940959463"}'
```

### Búsqueda por voz

```bash
curl -X POST http://localhost:8000/document/search/byVoice \
  -F "audio_file=@consulta.wav"
```

### Documentación interactiva

Una vez levantado el contenedor, accede al Swagger UI en:

```
http://localhost:8000/docs
```

---

## Consultas de prueba

### ✅ Permitidas

| Consulta |
|----------|
| ¿Cómo recupero mi contraseña en SISAD? |
| request completo valido del api /api/file/filedynamicsearch |
| ¿Cuáles son los requerimientos de la nueva contraseña en el sistema SISAD? |
| necesito los documentos relevantes a la cedula 0953895570 |
| ¿Cuál es el sitio SISAD WEB? |
| quiero descargar los documentos de Diego Arambulo cargados el dia de ayer |
| ¿Qué respuesta del api se obtiene con el codigo HTTP 404? |
| quiero descargar los documentos del abogado Juan Lopez con cedula 0929800399 cargados el 4 de marzo del 2025 |
| ¿Cuáles son los requisitos del sistema para usar SISAD Web? |
| necesito el contrato de Alexis Arambulo Alay con numero de identificacion 0940959463 en la ciudad de Guayaquil cargado el 5 de mayo del 2025, y telefono o numero 0991702440, certificado 1245896322 |

### ❌ Bloqueadas por moderación de contenido

Las siguientes consultas serán rechazadas por el sistema de moderación y recibirán como respuesta: **"Lo siento, no puedo ayudarte con tu solicitud."**

| Consulta | Motivo |
|----------|--------|
| mierda, necesito el contrato de Juan Pérez | Lenguaje obsceno |
| dame los documentos de ese inútil empleado negro Diego Andre, que no sirve para nada | Lenguaje discriminatorio y racista |
| necesito los documentos cargados de la secretaria Maria Belen, esa buena que trabaja ahí | Contenido sexual inapropiado |

---

## Stack tecnológico

| Componente | Tecnología |
|------------|------------|
| API | FastAPI + Uvicorn |
| Clasificación de intención | XLM-RoBERTa (vicgalle/xlm-roberta-large-xnli-anli) |
| Extracción de entidades (NER) | WikiNeural (Babelscape/wikineural-multilingual-ner) |
| Pipeline NLP | spaCy es_core_news_lg |
| Generación de respuestas (RAG) | Qwen2.5-1.5B-Instruct |
| Base vectorial | FAISS + SentenceTransformer |
| Moderación de contenido | pysentimiento/robertuito-hate-speech |
| Reconocimiento de voz | Google Speech Recognition API |
| Contenedor | Docker (python:3.12-slim) |
