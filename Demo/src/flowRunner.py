import re
from modelHandlers import ModelHandlers
from dateExtractor import extraer_fechas
from ragHandler import RagHandlers
from documentHandler import DocumentHandler
from TextUtils import es_cedula_ecuatoriana

# Inicialización global
_ragHandler = None
_documentHandler = None

PATRON_RUC        = re.compile(r'\b\d{13}\b')
PATRON_10_DIGITOS = re.compile(r'\b\d{10}\b')
PATRON_NUM_LARGO  = re.compile(r'\b\d{6,}\b')

# ✅ Provincias ecuatorianas válidas (01-24) para validar cédula
PROVINCIAS_EC = {str(i).zfill(2) for i in range(1, 25)}

# ✅ Contexto textual para distinguir cédula vs teléfono
CONTEXTO_CEDULA = re.compile(
    r'(?:cedula|cédula|identificacion|identificación|ci|dni|documento de identidad|numero de id)\D{0,30}(\d{10})',
    re.IGNORECASE
)
CONTEXTO_TELEFONO = re.compile(
    r'(?:telefono|teléfono|celular|movil|móvil|numero de contacto|contacto|cel|telf|tlf)\D{0,20}(\d{10})',
    re.IGNORECASE
)

# ✅ Números precedidos por contexto de referencia/código → ID_NUMERICO
#    Evita que números de certificados, folios, etc. sean clasificados como CEDULA
CONTEXTO_REFERENCIA = re.compile(
    r'(?:certificado|código|codigo|referencia|folio|recibo|factura|orden|no\.?|#)\D{0,20}(\d{6,13})',
    re.IGNORECASE
)

# Keywords para clasificar el type de respuesta
KEYWORDS_NV  = ["navegación", "navegacion", "ubicación", "ubicacion", "menu", "menú",
                 "modulo", "módulo", "pagina", "página", "interfaz", "url", "link"]
KEYWORDS_DLA = ["documentos", "documento", "obtener", "descargar", "solicitar", "leer",
                 "buscar", "planilla", "expediente", "recibo", "contrato", "certificado"]


def _resolver_type(intencion: str, confianza: float) -> str:
    """
    Determina el type según la intención detectada y su confianza.
    - None  → no se detectó intención clara (confianza baja)
    - 'NV'  → navegación / consulta de interfaz
    - 'DLA' → descarga / búsqueda de archivos
    """
    UMBRAL_CONFIANZA = 0.4

    if not intencion or confianza < UMBRAL_CONFIANZA:
        return None

    intencion_lower = intencion.lower()

    if any(k in intencion_lower for k in KEYWORDS_DLA):
        return "DLA"

    if any(k in intencion_lower for k in KEYWORDS_NV):
        return "NV"

    return None


def _fusionar_entidades(entidades: list) -> list:
    if not entidades:
        return []
    fusionadas = []
    actual = dict(entidades[0])
    for siguiente in entidades[1:]:
        mismo_tipo  = siguiente['tipo'] == actual['tipo']
        es_contiguo = siguiente.get('start', 0) <= actual.get('end', 0) + 1
        if mismo_tipo and es_contiguo:
            actual['entidad'] += siguiente['entidad'].replace('##', '')
            actual['end']      = siguiente.get('end', actual.get('end', 0))
        else:
            fusionadas.append({'entidad': actual['entidad'], 'tipo': actual['tipo']})
            actual = dict(siguiente)
    fusionadas.append({'entidad': actual['entidad'], 'tipo': actual['tipo']})
    return fusionadas


def _extraer_identificadores_regex(texto: str) -> list:
    encontrados = []

    # ── RUC (13 dígitos) — primero para evitar colisión ──────────────────────
    for match in PATRON_RUC.finditer(texto):
        encontrados.append({'entidad': match.group(), 'tipo': 'RUC'})

    # ✅ Contexto textual para desempate
    cedulas_por_contexto   = {m.group(1) for m in CONTEXTO_CEDULA.finditer(texto)}
    telefonos_por_contexto = {m.group(1) for m in CONTEXTO_TELEFONO.finditer(texto)}

    # ── Números de 10 dígitos ─────────────────────────────────────────────────
    for match in PATRON_10_DIGITOS.finditer(texto):
        numero = match.group()
        if any(e['entidad'] == numero for e in encontrados):
            continue

        es_cedula_valida = es_cedula_ecuatoriana(numero)

        if es_cedula_valida and (numero in cedulas_por_contexto or numero not in telefonos_por_contexto):
            # Pasa validación matemática; contexto de cédula tiene prioridad sobre teléfono
            tipo = 'CEDULA'
        elif not es_cedula_valida and numero in cedulas_por_contexto:
            # Contexto dice que es cédula pero no pasa validación → marcar igual
            # (podría ser un error de digitación, se respeta el contexto)
            tipo = 'CEDULA'
        elif numero in telefonos_por_contexto:
            tipo = 'TELEFONO_CELULAR' if numero.startswith('09') else 'TELEFONO_CONVENCIONAL'
        elif numero.startswith('09'):
            # No pasa validación de cédula y empieza con 09 → celular
            tipo = 'TELEFONO_CELULAR'
        elif numero[0] == '0' and numero[1] in '2345678':
            tipo = 'TELEFONO_CONVENCIONAL'
        else:
            tipo = 'ID_NUMERICO'

        encontrados.append({'entidad': numero, 'tipo': tipo})

    # ── Otros números largos (6+ dígitos) no capturados ──────────────────────
    for match in PATRON_NUM_LARGO.finditer(texto):
        numero = match.group()
        if not any(e['entidad'] == numero for e in encontrados):
            encontrados.append({'entidad': numero, 'tipo': 'ID_NUMERICO'})

    return encontrados


class FlowRunner:
    def __init__(self):
        self.nlp_final              = ModelHandlers.get_nlp_final()
        self.clasificador_intencion = ModelHandlers.get_clasificador_intencion()
        self.extractor_ner          = ModelHandlers.get_extractor_ner()
        print("FlowRunner inicializado y listo para usar los modelos.")

    def procesar_consulta(self, texto: str):

        global _ragHandler
        global _documentHandler

        if _ragHandler is None:
            _ragHandler = RagHandlers()

        if _documentHandler is None:
            _documentHandler = DocumentHandler()

        intenciones_sistema = [
            "Navegación: ubicación en el sistema, acceder a menú, encontrar módulo, dónde hacer algo, url, link, ir a página, interfaz, cargar, subir",
            "Documentos: obtener, descargar, solicitar, leer, buscar planillas, expedientes, recibos, contratos o certificados"
        ]

        # A. Clasificación de intención
        res_intencion       = self.clasificador_intencion(texto, intenciones_sistema)
        intencion_top       = res_intencion['labels'][0]
        confianza_intencion = res_intencion['scores'][0]

        # B. Extracción de verbo con spaCy
        doc             = self.nlp_final(texto)
        verbo_principal = next((token.lemma_ for token in doc if token.pos_ == "VERB"), None)

        # C. NER con transformers
        entidades_raw     = self.extractor_ner(texto)
        entidades_con_pos = [
            {
                'entidad': e['word'],
                'tipo':    e['entity_group'],
                'start':   e.get('start', 0),
                'end':     e.get('end', 0),
            }
            for e in entidades_raw
        ] if entidades_raw else []

        entidades_fusionadas = _fusionar_entidades(entidades_con_pos)

        # D. Identificadores numéricos con regex (CEDULA / TELEFONO / RUC)
        ids_regex = _extraer_identificadores_regex(texto)
        for id_regex in ids_regex:
            ya_existe = any(
                id_regex['entidad'] in e['entidad'] or e['entidad'] in id_regex['entidad']
                for e in entidades_fusionadas
            )
            if not ya_existe:
                entidades_fusionadas.append(id_regex)
            else:
                for e in entidades_fusionadas:
                    if e['entidad'] in id_regex['entidad']:
                        e['entidad'] = id_regex['entidad']
                        e['tipo']    = id_regex['tipo']

        # E. Extracción de fechas y rangos temporales
        fechas = extraer_fechas(texto)
        for f in fechas:
            entidades_fusionadas.append({'entidad': f['valor'], 'tipo': f['tipo']})

        entidades_limpias = [
            {'entidad': e['entidad'], 'tipo': e['tipo']}
            for e in entidades_fusionadas
        ]

        # F. Resolver type
        response_type = _resolver_type(intencion_top, confianza_intencion)

        result = {
            "intencion_detectada": intencion_top,
            "confianza_intencion": round(confianza_intencion, 3),
            "accion_verbo":        verbo_principal,
            "entidades":           entidades_limpias,
        }

        model_response = {}

        # G. Bifurcación de flujos
        match response_type:
            case "NV":
                model_response = _ragHandler.rag_query(texto)

            case "DLA":
                model_response = _documentHandler.call_document_service(entidades_limpias)

            case _:
                model_response = {
                    "error": f"Tipo de respuesta no soportado: {response_type}"
                }

        return {
            "type":          response_type,
            "result":        result,
            "modelResponse": model_response
        }