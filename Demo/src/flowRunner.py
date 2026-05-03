from modelHandlers import ModelHandlers

class FlowRunner:
    """
    Clase para procesar documentos/consultas usando los modelos cargados.
    """
    def __init__(self):
        # Obtener las instancias de los modelos ya cargados o cargarlos si es la primera vez
        self.nlp_final = ModelHandlers.get_nlp_final()
        self.clasificador_intencion = ModelHandlers.get_clasificador_intencion()
        self.extractor_ner = ModelHandlers.get_extractor_ner()
        print("FlowRunner inicializado y listo para usar los modelos.")

    def procesar_consulta(self, texto: str):
        # Definir las intenciones posibles de tu sistema (pueden venir de un config, etc.)
        intenciones_sistema = [
            "Navegación: ubicación en el sistema, acceder a menú, encontrar módulo, dónde hacer algo, url, link, ir a página, interfaz, cargar, subir",
            "Documentos: obtener, descargar, solicitar, leer, buscar planillas, expedientes, recibos, contratos o certificados"
        ]

        # A. Clasificación de Intención
        res_intencion = self.clasificador_intencion(texto, intenciones_sistema)
        intencion_top = res_intencion['labels'][0]
        confianza_intencion = res_intencion['scores'][0]

        # B. Extracción de Acción (Verbo) con spaCy
        doc = self.nlp_final(texto)
        verbo_principal = next((token.lemma_ for token in doc if token.pos_ == "VERB"), None)

        # C. Extracción de Entidades (Transformer NER + spaCy fallback)
        entidades_tf = self.extractor_ner(texto)
        entidades_limpias = [{'entidad': e['word'], 'tipo': e['entity_group']} for e in entidades_tf] if entidades_tf else []

        # D. Construir el objeto de respuesta
        return {
            "consulta": texto,
            "intencion_detectada": intencion_top,
            "confianza_intencion": round(confianza_intencion, 3),
            "accion_verbo": verbo_principal,
            "entidades": entidades_limpias
        }