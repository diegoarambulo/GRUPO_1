docker rm -f agenteGestorDocumentalSISSAD_G1
docker build --build-arg HF_TOKEN=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 -t nlp-grupo1-sissad:v1 .
docker run -d --rm -p 8000:8000 --name agenteGestorDocumentalSISSAD_G1 -v %CD%/hf_cache:/app/.cache/huggingface -v %CD%/rag_content:/app/.cache/rag_content nlp-grupo1-sissad:v1