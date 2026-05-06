import re
from modelHandlers import ModelHandlers
from dateExtractor import extraer_fechas
from ragHandler import RagHandlers
from documentHandler import DocumentHandler

# Inicialización global
_ragHandler = None
_documentHandler = None

PATRON_RUC       = re.compile(r'\b\d{13}\b')
PATRON_CEDULA    = re.compile(r'\b\d{10}\b')
PATRON_NUM_LARGO = re.compile(r'\b\d{6,}\b')

# ✅ Keywords para clasificar el type de respuesta
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
    for match in PATRON_RUC.finditer(texto):
        encontrados.append({'entidad': match.group(), 'tipo': 'RUC'})
    for match in PATRON_CEDULA.finditer(texto):
        if not any(e['entidad'] == match.group() for e in encontrados):
            encontrados.append({'entidad': match.group(), 'tipo': 'CEDULA'})
    for match in PATRON_NUM_LARGO.finditer(texto):
        if not any(e['entidad'] == match.group() for e in encontrados):
            encontrados.append({'entidad': match.group(), 'tipo': 'ID_NUMERICO'})
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

        # D. Identificadores numéricos con regex
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

        # ✅ F. Resolver type
        response_type = _resolver_type(intencion_top, confianza_intencion)

        result = {
            "intencion_detectada": intencion_top,
            "confianza_intencion": round(confianza_intencion, 3),
            "accion_verbo":        verbo_principal,
            "entidades":           entidades_limpias,
        }

        model_response = {}
        #bifurcacion de flujos
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
            "type":   response_type,
            "result": result,
            "modelResponse": model_response
        }