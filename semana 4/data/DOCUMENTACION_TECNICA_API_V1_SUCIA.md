---

# Documentación de API: Búsqueda Global de Documentos

Esta documentación detalla el uso del endpoint `/api/file/filedynamicsearch` para la recuperación de entidades de archivos basadas en criterios de búsqueda específicos.

---

## 📌 Información General

* **Endpoint completo:** `https://www.centralfile-sisadcloud.com:11431/api/file/filedynamicsearch`
* **Método HTTP:** `POST`
* **Autenticación:** No requerida
* **Formato de Request:** JSON
* **Formato de Response:** JSON

---

## 📥 Estructura del Request

El request consiste en un **array de objetos**, donde cada objeto define un criterio de búsqueda.

### 🔹 Estructura de cada objeto

```json
{
  "Key": "string",
  "Value": "string",
  "Type": ["string"]
}
```

### 🔹 Descripción de campos

| Campo | Tipo          | Descripción                                              |
| ----- | ------------- | -------------------------------------------------------- |
| Key   | string        | Puede ser vacío o uno de los valores del enumerado INDEX |
| Value | string        | Valor de búsqueda                                        |
| Type  | array[string] | Define dónde se aplicará la búsqueda                     |

---

### 🔹 Descripción de campos

| Campo | Tipo          | Descripción                                              |
| ----- | ------------- | -------------------------------------------------------- |
| Key   | string        | Puede ser vacío o uno de los valores del enumerado INDEX |
| Value | string        | Valor de búsqueda                                        |
| Type  | array[string] | Define dónde se aplicará la búsqueda                     |

---

## 🧩 Enumerados

### 🔹 Valores permitidos para `Key` (INDEX)

```
["CEDULA", "NOMBRE", "EMAIL", "DIRECCION", "TELEFONO", "CONTRATO", 
"FECHA DESDE", "FECHA HASTA", "ANEXO", "RUC", "IDENTIFICACION", 
"APELLIDO", "GENERO", "EDAD", "SEXO", "CIUDAD", "PAIS", "AÑO", "JEFE"]
```

### 🔹 Valores permitidos para `Type`

```
["FileType", "Index", "FileName", "DescriptionFile"]
```

> Puede contener uno o varios valores, o estar vacío.

---

## 📘 Ejemplos de Request

### 🔹 Ejemplo 1

```json
[
  {
    "Key": "NOMBRE",
    "Value": "diego arambulo",
    "Type": ["Index"]
  },
  {
    "Key": "",
    "Value": "CEDULA",
    "Type": ["FileType", "Index"]
  }
]
```

📌 **Descripción:**
Busca archivos donde:

* El índice **NOMBRE** sea "diego arambulo"
* Y la cadena "CEDULA" esté presente como:

  * Tipo de archivo
  * Índice

---

### 🔹 Ejemplo 2

```json
[
  {
    "Key": "CEDULA",
    "Value": "0929800399",
    "Type": ["FileType", "Index", "FileName", "DescriptionFile"]
  },
  {
    "Key": "FECHA DESDE",
    "Value": "2025-01-20",
    "Type": [""]
  },
  {
    "Key": "FECHA HASTA",
    "Value": "2025-12-20",
    "Type": [""]
  }
]
```

📌 **Descripción:**
Busca archivos:

* Cargados entre el **20 de enero y el 20 de diciembre de 2025**
* Que contengan la cédula `0929800399` en:

  * Índices
  * Nombre del archivo
  * Descripción
  * Tipo de archivo

---

## 📤 Estructura del Response

### ✅ Respuesta Exitosa (HTTP 200)

```json
{
  "code": 0,
  "message": "OK",
  "documents": [
    {
      "id": "94ec0447-1ccd-47d8-a343-a36da458254c",
      "name": "PDF EN BLANCO - copia (15)",
      "description": "Archivo sin descripción 68515",
      "extension": ".pdf",
      "file": "https://sisadazurestorage.blob.core.windows.net/default/94ec0447-1ccd-47d8-a343-a36da458254c.pdf",
      "size": 36604,
      "fileTypeId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "documentId": "4ec60004-bfde-4ef8-94cf-d71008aa1e07",
      "sequential": 68515,
      "fileTypeName": "OTROS",
      "isBlocked": false
    },
    {
      "id": "8d476018-02c8-458a-9d82-c1f0fbb667e1",
      "name": "PDF EN BLANCO - copia (16)",
      "description": "Archivo sin descripción 68516",
      "extension": ".pdf",
      "file": "https://sisadazurestorage.blob.core.windows.net/default/8d476018-02c8-458a-9d82-c1f0fbb667e1.pdf",
      "size": 36604,
      "fileTypeId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "documentId": "4ec60004-bfde-4ef8-94cf-d71008aa1e07",
      "sequential": 68516,
      "fileTypeName": "OTROS",
      "isBlocked": false
    }
  ]
}
```

---

### 🔹 Descripción de campos del documento

| Campo        | Descripción                         |
| ------------ | ----------------------------------- |
| id           | Identificador único del archivo     |
| name         | Nombre del archivo                  |
| description  | Descripción del archivo             |
| extension    | Extensión del archivo               |
| file         | URL pública del archivo             |
| size         | Tamaño en bytes                     |
| fileTypeId   | Identificador del tipo de archivo   |
| documentId   | Identificador del documento         |
| sequential   | Número secuencial                   |
| fileTypeName | Nombre del tipo de archivo          |
| isBlocked    | Indica si el archivo está bloqueado |

---



### ⚠️ Sin Resultados (HTTP 404)

```json
{
  "code": 2,
  "message": "no hubieron documentos que coincidan con la busqueda",
  "documents": []
}
```

---

### ❌ Error del Sistema (HTTP 500)

```json
{
  "codeeeeeeeeeeeeee": -1,
  "message": "Error general de sistema"
}
```

---

## 🧪 Ejemplo de Consumo con cURL

```bash
curl -X GET "https://www.centralfile-sisadcloud.com:11431/api/file/filedynamicsearch" \
-H "Content-Type: application/json" \
-d '[
  {
    "Key": "NOMBRE",
    "Value": "diego arambulo",
    "Type": ["Index"]
  },
  {
    "Key": "",
    "Value": "CEDULA",
    "Type": ["FileType", "Index"]
  }
]'
```

---

## 📎 Notas Finales

* El endpoint permite combinar múltiples criterios de búsqueda.
* Los filtros se aplican de forma conjunta.
* Se recomienda validar correctamente los valores del enumerado antes de enviar la solicitud.
* Las fechas deben enviarse en formato `YYYY-MM-DD`.

