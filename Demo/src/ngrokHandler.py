import os
from pyngrok import ngrok
import uvicorn

# ✅ En Docker no se usa ngrok — uvicorn corre directamente en el thread principal
# ✅ ngrokHandler solo se usa en desarrollo local / Colab

# Cierra cualquier túnel ngrok existente
ngrok.kill()

ngrok_auth_token = "3C6RbXVl84G8wT75IufyBXPhwv2_3moCnsaWpVueFRL9g8AsR"

if ngrok_auth_token != "TU_TOKEN_AQUI":
    ngrok.set_auth_token(ngrok_auth_token)

    try:
        public_url = ngrok.connect(8000)
        print(f"✅ Tu API pública está disponible en: {public_url}")
        print(f"📖 Swagger UI: {public_url}/docs")
    except Exception as e:
        print(f"❌ Error al iniciar ngrok: {e}")

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
