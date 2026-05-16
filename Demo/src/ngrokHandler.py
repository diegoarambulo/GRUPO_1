import os
from pyngrok import ngrok
import uvicorn

# ✅ En Docker no se usa ngrok — uvicorn corre directamente en el thread principal
# ✅ ngrokHandler solo se usa en desarrollo local / Colab
#
# Variable de entorno requerida para activar ngrok:
#   NGROK_AUTH_TOKEN=<tu_token>
#
# Si la variable no está definida, ngrok NO se activa y la API
# queda accesible solo de forma local en el puerto 8000.

ngrok_auth_token = os.environ.get("NGROK_AUTH_TOKEN", "").strip()

if ngrok_auth_token:
    # Cierra cualquier túnel previo antes de abrir uno nuevo
    try:
        ngrok.kill()
    except Exception:
        pass

    ngrok.set_auth_token(ngrok_auth_token)

    try:
        public_url = ngrok.connect(8000)
        print(f"✅ Tu API pública está disponible en: {public_url}")
        print(f"📖 Swagger UI: {public_url}/docs")
    except Exception as e:
        print(f"❌ Error al iniciar ngrok: {e}")
else:
    print("ℹ️  NGROK_AUTH_TOKEN no definido — ngrok desactivado. API disponible solo en localhost:8000")

# ✅ CRÍTICO: uvicorn.run() debe correr en el thread PRINCIPAL, no en un thread secundario.
#    Esto evita el error "cannot schedule new futures after interpreter shutdown"
#    cuando transformers intenta crear threads durante la carga de modelos.
ssl_keyfile  = os.environ.get("SSL_KEYFILE")
ssl_certfile = os.environ.get("SSL_CERTFILE")

uvicorn.run(
    "main:app",
    host="0.0.0.0",
    port=8000,
    log_level="info",
    ssl_keyfile=ssl_keyfile or None,
    ssl_certfile=ssl_certfile or None,
)
