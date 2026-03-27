# Backend LLM API

REST API en Python que integra un LLM (a través de OpenRouter) con una base de conocimiento interna para responder preguntas de forma contextualizada.

> **Estado actual**: Estructura base + configuración + servidor FastAPI con endpoint `/health`.

---

## Tech Stack

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.13+ |
| Framework | FastAPI |
| Servidor | Uvicorn |
| Validación | Pydantic |
| Base de datos | SQLite |
| HTTP Client | httpx |
| Testing | pytest |
| Linting | Ruff |
| Contenedores | Docker |

---

## Requisitos previos

- **Python 3.13+** instalado y disponible en el PATH
- **Git** (para clonar el repositorio)

---

## Instalación y ejecución local

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/backend-llm-api.git
cd backend-llm-api
```

### 2. Crear y activar el entorno virtual

```bash
python -m venv venv
```

**Activar en Windows (PowerShell):**
```powershell
.\venv\Scripts\activate
```

**Activar en Linux/macOS:**
```bash
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo de ejemplo y edítalo con tus valores:

```bash
cp .env.example .env
```

Variables disponibles:

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `OPENROUTER_API_KEY` | API key de OpenRouter | *(vacío, requerido para chat)* |
| `OPENROUTER_MODEL` | Modelo LLM a usar | `meta-llama/llama-3.1-8b-instruct:free` |
| `APP_HOST` | Host del servidor | `0.0.0.0` |
| `APP_PORT` | Puerto del servidor | `8080` |
| `LOG_LEVEL` | Nivel de logging | `INFO` |
| `DATABASE_URL` | URL de la base de datos SQLite | `sqlite:///./nuria.db` |

### 5. Arrancar el servidor

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Con recarga automática (recomendado para desarrollo):

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

El servidor estará disponible en: **http://localhost:8080**

---

## Endpoints disponibles

### `GET /health`

Verifica que el servicio está funcionando.

**Con curl:**
```bash
curl http://localhost:8080/health
```

**Respuesta:**
```json
{"status": "ok"}
```

### `POST /chat/` *(próximamente)*

---

## Documentación interactiva

FastAPI genera documentación interactiva automáticamente:

- **Swagger UI**: http://localhost:8080/docs — permite probar endpoints directamente desde el navegador
- **ReDoc**: http://localhost:8080/redoc — documentación en formato lectura

---

## Estructura del proyecto

```
backend-llm-api/
├── app/
│   ├── main.py              # Punto de entrada de la aplicación FastAPI
│   ├── api/
│   │   └── routes_chat.py   # Definición de rutas/endpoints
│   ├── core/
│   │   ├── config.py        # Configuración centralizada (variables de entorno)
│   │   ├── logging.py       # Configuración de logging
│   │   └── prompts.py       # Templates de prompts para el LLM
│   ├── services/
│   │   ├── chat_service.py        # Orquestación del flujo de chat
│   │   ├── openrouter_service.py  # Cliente para la API de OpenRouter
│   │   └── retrieval_service.py   # Búsqueda en la base de conocimiento
│   ├── db/
│   │   ├── session.py       # Conexión a SQLite
│   │   ├── models.py        # Modelos de la base de datos
│   │   └── seed.py          # Script para poblar datos iniciales
│   ├── schemas/
│   │   └── chat.py          # Modelos Pydantic de request/response
│   └── data/
│       └── seed_data.json   # Datos semilla de conocimiento interno
├── tests/
│   ├── test_health.py
│   ├── test_chat.py
│   └── test_retrieval.py
├── .env.example             # Variables de entorno de ejemplo
├── requirements.txt         # Dependencias Python
├── Dockerfile
├── docker-compose.yml
└── Makefile
```

---

## Testing

```bash
pytest tests/ -v
```

*(Tests en desarrollo)*

---

## Decisiones de diseño

- **pydantic-settings** para configuración: carga automática desde `.env` con validación de tipos
- **Logging estructurado**: formato consistente con timestamps, fácil de parsear
- **Lifespan async**: patrón moderno de FastAPI para startup/shutdown (sin decoradores `@app.on_event` deprecados)
- **Separación de responsabilidades**: rutas → servicios → datos, sin lógica de negocio en los handlers
