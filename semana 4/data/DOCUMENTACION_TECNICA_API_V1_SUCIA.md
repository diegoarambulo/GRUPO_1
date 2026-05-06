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

## 📌 Mision de la empresa

* **Contenido:** Proveer soluciones tecnológicas innovadoras para la gestión documental que permitan a las organizaciones optimizar sus procesos, garantizar la seguridad de la información y mejorar la eficiencia operativa mediante herramientas digitales accesibles, escalables y confiables.

---

## 📌 Vision de la empresa

* **Contenido:** Ser una empresa líder en soluciones de gestión documental a nivel regional, reconocida por su innovación, calidad y capacidad de transformar digitalmente a las organizaciones, impulsando entornos más eficientes, sostenibles y orientados a datos.

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

## 🏢 Infraestructura Corporativa

Nuestra empresa cuenta con modernas instalaciones diseñadas para fomentar la innovación, la colaboración y el desarrollo tecnológico. A lo largo de los años, la infraestructura ha evolucionado para reflejar nuestro compromiso con la excelencia y la transformación digital.

### 📸 Edificio Corporativo Principal

![Image](https://static.wixstatic.com/media/21927d_bf62bd8fb4b04a2cb26a3b7ead85812d~mv2.webp/v1/fill/w_980%2Ch_653%2Cal_c%2Cq_85%2Cusm_0.66_1.00_0.01%2Cenc_avif%2Cquality_auto/21927d_bf62bd8fb4b04a2cb26a3b7ead85812d~mv2.webp)

![Image](https://in.saint-gobain-glass.com/sites/in.saint-gobain-glass.com/files/styles/node_blog_image/public/2025-06/Glass%20facades.jpg?itok=kR4u2m_J)

El edificio principal representa nuestra identidad como empresa tecnológica: estructuras modernas, fachadas de vidrio y espacios abiertos que promueven la transparencia, la eficiencia y el trabajo colaborativo. Este tipo de arquitectura es común en organizaciones tecnológicas debido a su enfoque en iluminación natural, eficiencia energética y estética corporativa contemporánea. ([Pexels][1])

---

## 📘 Ejemplos de Requessssssssssssssstttttttttttt

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

Perfecto, aquí tienes la sección corregida con **tu ejemplo real de respuesta exitosa** en lugar del genérico:

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
| id           | Identificador único del archivo     |
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

## 🧪 Ejemplo de Consumo con cURL @@@##$$%%^^&&&&&&&

```bash
curl -X GET "http://localhost:8080/documents/searchAll" \
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

---

## 🏢 Historia de la Empresa

La historia de la compañía se remonta a la década de 1970, en un contexto donde la tecnología apenas comenzaba a abrirse paso en el mundo empresarial. Su fundador, un joven emprendedor con una visión clara sobre el potencial de la organización documental, inició operaciones con un capital modesto obtenido mediante un préstamo personal, apostándolo todo a una idea que en ese momento parecía adelantada a su tiempo.

En sus primeros años, la empresa enfrentó múltiples desafíos: recursos limitados, infraestructura precaria y un mercado que aún no comprendía el valor de sistematizar la información. Sin embargo, gracias a la perseverancia, disciplina y una firme convicción en la calidad del trabajo, logró consolidarse como un proveedor confiable en soluciones documentales tradicionales.

Con la llegada de la segunda generación, la empresa experimentó una transformación clave. Se adoptaron las primeras tecnologías digitales, migrando de procesos físicos a sistemas informatizados. Este cambio no solo permitió modernizar los servicios, sino también establecer nuevos estándares internos de calidad, orientados a la precisión, trazabilidad y seguridad de la información.

En la actualidad, bajo la dirección de la tercera generación, la organización ha evolucionado hacia una empresa tecnológica consolidada, especializada en soluciones avanzadas de gestión documental y desarrollo de software. Su enfoque se centra en la innovación continua, la automatización inteligente y la integración de herramientas digitales que responden a las necesidades actuales del mercado.

A lo largo de más de cinco décadas, la empresa ha demostrado que la resiliencia, la adaptación y el compromiso con la excelencia son pilares fundamentales para trascender generaciones. Hoy, no solo mantiene el legado de sus fundadores, sino que también ha logrado redefinir los estándares de calidad en el desarrollo de software y gestión documental, posicionándose como un referente en el sector.
