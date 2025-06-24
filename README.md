# HIPAA‑RAG

A minimal Retrieval‑Augmented Generation system that answers questions about the HIPAA regulation (§160, §162, §164) using:

* **LangGraph / LangChain** for dynamic RAG flow (skip retrieval when not needed)
* **PostgreSQL 16 + pgvector** as the vector store
* **FastAPI** backend
* **Streamlit** chat UI
* **PgAdmin 4** for database inspection
* **Docker Compose** for reproducible deployment
* **Poetry** to lock Python dependencies in each service

---

## Directory layout

```
hipaa-rag/
├─ docker-compose.yml          # orchestration of all services
├─ .env.example                # template with required environment variables
│
├─ data/
│  └─ hipaa.pdf                # <‑‑ place the HIPAA PDF here
│
├─ app/                        # FastAPI + RAG graph + ingest
│  ├─ pyproject.toml           # Poetry manifest
│  ├─ dockerfile
│  ├─ ingest.py                # one‑time population of pgvector
│  ├─ rag_graph.py             # LangGraph pipeline
│  └─ api.py                   # REST endpoints (/api/chat, /api/health)
│
├─ ui/                         # Streamlit chat frontend
│  ├─ pyproject.toml
│  ├─ dockerfile
│  └─ streamlit_app.py
│
└─ nginx/
    └─ nginx.conf              # reverse‑proxy (80 → UI, /api/ → backend)
```

---

## Prerequisites

* Docker ≥ 24
* docker‑compose plugin (or Docker Desktop)
* An **OpenAI API key** with access to `gpt-4o‑mini` (or adjust the model name in `app/rag_graph.py`)

---

## 1. Clone & prepare

```bash
git clone https://github.com/your‑org/hipaa-rag.git
cd hipaa-rag

# copy environment template → real env file
cp .env.example .env
# edit .env and set at least OPENAI_API_KEY

# add the regulation PDF
mkdir -p data
mv /path/to/HIPAA_questions.pdf data/hipaa.pdf
```

---

## 2. Build & run

```bash
docker compose up --build
```

The first start will:

1. create the `hipaa` database and install the **pgvector** extension;
2. execute `ingest.py` inside the *api* container → extracts \~3 000 chunks and stores them in `hipaa_chunks` table;
3. launch all four services:

   * **db**      : PostgreSQL 16
   * **api**     : FastAPI on port **8000** (internal)
   * **ui**      : Streamlit on port **8501** (internal)
   * **pgadmin** : PgAdmin 4 on **5050** (external)
   * **nginx**   : public port **80** → [http://localhost](http://localhost)

> **Tip:** subsequent `docker compose up` skips ingest if the table already contains data.

---

## 3. Usage

| URL                                                    | Purpose                 | Default creds                                  |
| ------------------------------------------------------ | ----------------------- | ---------------------------------------------- |
| [http://localhost](http://localhost)                   | Streamlit chat (UI)     | –                                              |
| [http://localhost/api/chat](http://localhost/api/chat) | POST → JSON RAG answers | –                                              |
| [http://localhost/health](http://localhost/health)     | GET → `{"status":"ok"}` | –                                              |
| [http://localhost:5051](http://localhost:5051)         | PgAdmin 4               | user → `pgadmin@local.test`  pwd → `secret123` |

### Example API call

```bash
curl -X POST http://localhost/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"What is a covered entity?"}' | jq
```

---

## 4. Local development (optional)

> Requires Python 3.11, Poetry 1.8+ installed on the host.

```bash
# backend
cd app && poetry install --with dev
poetry run python ingest.py   # populate pgvector locally
poetry run uvicorn api:app --reload

# frontend
cd ui && poetry install
poetry run streamlit run streamlit_app.py
```

---

## 5. Troubleshooting

| Symptom                                              | Likely cause                  | Fix                                                                                   |
| ---------------------------------------------------- | ----------------------------- | ------------------------------------------------------------------------------------- |
| UI answers without citations, logs show `context=[]` | vector store is empty         | re‑run `python ingest.py` or delete the `dbdata` volume and restart                   |
| Docker error `exec: "tini": not found`               | tini not installed            | either remove `ENTRYPOINT ["tini", "--"]` or add `apt-get install tini` in Dockerfile |
| PgAdmin cannot connect                               | wrong credentials or hostname | host should be **db**, port **5432**, user/pass from `.env`                           |

---

## 6. Extending the project

* Switch retrieval to **MMR** or **Self‑Query** (see `rag_graph.py`)
* Enable TLS: mount certs into `nginx` and add `listen 443 ssl;`
* Replace Streamlit with React + Next.js (nginx config already separates `/api/`)
* Deploy on Fly.io / Render / AWS ECS — works out‑of‑the‑box because everything is containerized.

---

## License

MIT — do whatever you want but please include a copy of the license.

---

## Credits

* Example LangGraph flow adapted from the [LangChain RAG tutorial](https://python.langchain.com/docs/tutorials/rag/)
* PgVector image by @ankane
