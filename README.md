# Backend LLM API

REST API en Python desarrollada con FastAPI que expone un endpoint de chat impulsado por LLMs (vía OpenRouter) y aterrizado mediante *Retrieval-Augmented Generation (RAG)* usando una base de conocimientos local de la empresa.

Este proyecto resuelve el desafío técnico de arquitectura backend, priorizando simplicidad, bajo acoplamiento, reproducibilidad y excelencia en testing, evitando sobreingeniería.

---

## 🏗️ Architecture Summary

La arquitectura sigue un patrón de **Separación de Responsabilidades (Separation of Concerns)** muy claro:

- **Routes (`api/`)**: Handlers extremadamente delgados que solo definen contratos HTTP (Pydantic models) y manejan códigos de error. No conocen de LLMs ni de SQL.
- **Services (`services/`)**: La lógica de negocio pura. `chat_service.py` actúa como orquestador, tomando el mensaje del usuario, pidiendo contexto a `retrieval_service.py` e invocando al `openrouter_service.py`.
- **Database (`db/`):** Capa de acceso a datos utilizando una base de datos local SQLite (`nuria.db`) gestionada nativamente y por el ORM SQLAlchemy para escalar si se desea. Aislada mediante inyección de dependencias estricta.

## 🚀 Tech Stack

- **Python 3.13**
- **FastAPI** + **Uvicorn**
- **SQLite** + **SQLAlchemy**
- **HTTPX** (Para llamadas asincrónicas limpias al exterior)
- **Pytest** + **TestClient** + **AsyncMock**
- **Docker** + **Docker Compose**

---

## ⚙️ Setup Instructions & Environment Variables

Para ejecutar ya sea localmente o mediante Docker, el primer paso es clonar y configurar el entorno:

```bash
git clone https://github.com/tu-usuario/backend-llm-api.git
cd backend-llm-api
```

Copia el archivo de entorno base:
```bash
cp .env.example .env
```

Abre `.env` en tu editor de texto y configura especialmente la llave de OpenRouter:
```properties
# .env
OPENROUTER_API_KEY=tu_api_key_aqui
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
APP_HOST=0.0.0.0
APP_PORT=8080
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./nuria.db
```

---

## 🐳 Docker Run Instructions (Recomendado)

La forma más limpia y replicable de arrancar la API es usando Docker Compose:

```bash
docker compose up --build
```
> El servicio inicializará automáticamente su base de datos y poblara la información interna. Estará escuchando de forma inmediata en `http://localhost:8080`.

Para detenerlo:
```bash
docker compose down
```

---

## 💻 Local Run Instructions (Desarrollo)

Si prefieres ejecutar el código localmente (útil para hacer pruebas o debug):

1. **Crear y activar el entorno virtual:**
    ```bash
    # Windows (PowerShell)
    python -m venv venv
    .\venv\Scripts\activate
    
    # Linux/Mac
    python3 -m venv venv
    source venv/bin/activate
    ```

2. **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Ejecutar el servidor ASGI:**
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
    ```

---

## 🔗 Example API Usage (`curl`)

### 1. Healthcheck

Comprueba la vitalidad y latencia del servicio (útil en orquestadores):
```bash
curl -X GET http://localhost:8080/health
```
```json
{"status": "ok"}
```

### 2. Conversación de Chat (Conocimiento Interno)

Este comando le pregunta a la API sobre un proceso de la empresa. La API detectará palabras clave, extraerá los documentos y los usará como fuente para la IA.

```bash
curl -X POST http://localhost:8080/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Cuál es la política de vacaciones?"}'
```

```json
{
  "message": "En Nuria Tech Solutions, todos los empleados disponen de 23 días de vacaciones al año. Estas peticiones deben tramitarse mediante BambooHR con al menos 2 semanas de antelación.",
  "model": "meta-llama/llama-3.1-8b-instruct:free",
  "used_context": true,
  "sources": [
    "Vacation Policy"
  ]
}
```

---

## 🧠 Explicación de Recuperación de Contexto (Retrieval Strategy)

En lugar de incrustar complejas infraestructuras de bases de datos vectoriales abstractas (que para bases de RRHH pequeñas es excesivo), hemos incorporado un motor de **Keyword Scoring Local**.

1. El usuario envía un mensaje (`"¿Cuál es el proceso de un ticket Jira?"`).
2. El sistema aplica **Normalización de Texto**: convierte a minúsculas, remueve signos de puntuación, y descarta **Stop Words** ("el", "de", "cual") y palabras menores a 3 caracteres.
3. El sistema extrae los **Keywords** resultantes (`"proceso"`, `"ticket"`, `"jira"`).
4. El motor compara en memoria RAM o vía SQL, asignando pesos dinámicos a las entradas con matches (Tags = 3 Pts, Title = 2 Pts, Content = 1 Pt).
5. Las entradas con una puntuación superior a `0` se ordenan, y se formatean elegantemente como bloques de texto (Max Top `K`), inyectándose transparentemente en el Prompt Final para OpenRouter.

Todo esto está **100% cubierto por Unit Tests** exhaustivos en `test_retrieval.py` que comprueban la heurística de exactitud.

---

## 🧪 Testing

La infraestructura incluye suites de Test exhaustivas (42 pruebas pasando). No se gastan cuotas ya que las peticiones se interceptan vía `AsyncMock`. Además, la BD se genera localmente para los test con `StaticPool` en RAM, siendo ultrarrápida (0.5s en ejecutarse completa).

Ejecutar:
```bash
pytest tests/ -v
```

---

## 💭 Design Decisions

- **Excepciones Abstraídas**: FastAPI expone el error al usuario en JSON predecible. Si la API HTTP de OpenRouter cae o sufre Timeouts, la API local responde adecuadamente con `502` / `504` sin lanzar fallos de código (`500`) inexplicables.
- **Sin LangChain / LlamaIndex**: Se evita *Bloatware*; usar `httpx` desnudo directamente a la red es un 90% más liviano, depurable e higiénico, asegurando un control asíncrono puro.
- **Lifespan**: Se reemplazaron convenciones viejas (`@app.on_event`) en pro del nuevo patrón `lifespan` introducido por FastAPI para arrancar eficientemente el SQLite Logger en background.

## 🚀 Future Improvements

Para evolucionar este prototipo hacia una solución Enterprise de alta concurrencia, propondría lo siguiente:

1. **Redis Cache**: Incluir un caché L1 (hash match de la pregunta) en Redis para ahorrar de manera drástica costes computacionales del LLM si dos empleados preguntan cosas idénticas como `"cual es el wifi?"`.
2. **PostgreSQL / Vector DB**: Si el número de documentos supera los cinco mil (5,000+), saltar del keyword-matching hacia `pgvector` o `qdrant` con embeddings estáticos (`BGE-m3`).
3. **Conversational Memory**: Adjuntar un `session_id` que registre en la base de datos el historial del usuario para inyectar los últimos 10 mensajes, permitiendo mantener un hilo conversacional extendido.
