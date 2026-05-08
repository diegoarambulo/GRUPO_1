import json
import logging
import os
import requests

logger = logging.getLogger(__name__)


class DocumentHandler:

    def call_document_service(self, limpias) -> dict:
        new_entities = self.buildServiceRequest(limpias)

        url          = os.environ["SISSAD_FILE_URL"]
        timeout      = float(os.environ.get("SISSAD_FILE_TIMEOUT", 10))
        read_timeout = float(os.environ.get("SISSAD_FILE_READ_TIMEOUT", 30))

        logger.info("SISSAD_FILE request  | url=%s | body=%s", url, json.dumps(new_entities, ensure_ascii=False))

        response = requests.post(
            url,
            json=new_entities,
            timeout=(timeout, read_timeout),
        )
        response.raise_for_status()

        logger.info("SISSAD_FILE response | status=%s | body=%s", response.status_code, response.text)

        if response.status_code == 204:
            return {"documents": [], "count": 0}

        documents = [
            {
                "name":        item["name"],
                "description": item["description"],
                "extension":   item["extension"],
                "fileUrl":     item["fileUrl"],
            }
            for item in response.json()
        ]
        return {"documents": documents, "count": len(documents)}


    def buildServiceRequest(self, entidades: list[dict]) -> list[dict]:
        result = []

        for e in entidades:
            tipo  = e.get("tipo", "")
            valor = e.get("entidad", "")

            if tipo == "PER":
                partes   = valor.split()
                nombre   = partes[0]             if len(partes) > 0 else ""
                apellido = partes[1]             if len(partes) > 1 else ""
                result.append({"Key": "NOMBRE",   "Value": nombre,   "Type": ["Index"]})
                result.append({"Key": "APELLIDO",  "Value": apellido, "Type": ["Index"]})

            elif tipo == "LOC":
                for key in ("CIUDAD", "PAIS", "LUGAR"):
                    result.append({"Key": key, "Value": valor, "Type": ["Index"]})

            elif tipo in ("CEDULA", "FECHA", "FECHA_INICIO", "FECHA_FIN"):
                result.append({"Key": tipo, "Value": valor, "Type": ["Index"]})

            elif tipo == "TELEFONO_CELULAR":
                result.append({"Key": "TELEFONO", "Value": valor, "Type": ["Index"]})
                result.append({"Key": "CELULAR",  "Value": valor, "Type": ["Index"]})

            elif tipo == "ID_NUMERICO":
                result.append({"Key": "", "Value": valor, "Type": ["FileType", "FileName", "DescriptionFile"]})

        return result

