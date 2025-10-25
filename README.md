
# 🧠 NLP Query Engine for Employee Data

A **production-ready, schema-adaptive Natural Language Query Engine** for structured employee databases and unstructured HR documents.

This system intelligently discovers unknown database schemas, generates safe SQL from natural language, performs **semantic document retrieval**, and merges results — all within a fast, cache-optimized API and a clean, modern web UI.

---

## 🚀 Highlights

- 🧩 **Zero Schema Assumptions** — Works with any HR schema 
- 🔍 **Hybrid Query Engine** — Combine SQL + document search seamlessly.
- ⚡ **FastAPI + React** — Async backend with a responsive Bootstrap 5.3 UI (dark/light modes).
- 🧠 **Embeddings + Caching** — Sentence-transformers + Redis with invalidation and metrics.
- 📊 **Production UX** — Pagination, metrics dashboard, CSV/JSON export, connection pooling.

---

## 🏗️ Tech Stack

| Layer          | Tools                                                          |
| :------------- | :------------------------------------------------------------- |
| **Backend**    | FastAPI, SQLAlchemy, Uvicorn, Redis, Loguru                    |
| **Database**   | PostgreSQL (MySQL/SQLite supported for demo)                   |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2`, FAISS-like CPU index |
| **Frontend**   | React + Bootstrap 5.3 (with `data-bs-theme` toggle)            |

---
```
## 📁 Project Structure

project/
├── backend/
│ ├── api/
│ │ └── routes/
│ │ ├── ingestion.py 
│ │ ├── query.py 
│ │ └── schema_routes.py
| ├── db_scripts
| | ├──init_db.sql
│ ├── services/
│ │ ├── schema_discovery.py 
│ │ ├── document_processor.py 
│ │ ├── query_parser.py 
│ │ ├── sql_builder.py 
│ │ └── query_engine.py 
│ ├── models/
│ │ └── db.py 
│ ├── tests/
│ │ ├── init.py
│ │ ├── test_query_parser.py 
│ │ └── test_integration.py
│ ├── main.py 
│ └── .env 
│
├── frontend/
│ ├── public/
│ │ └── index.html 
│ └── src/
│ ├── components/
│ │ ├── DatabaseConnector.js
│ │ ├── DocumentUploader.js
│ │ ├── QueryPanel.js
│ │ ├── ResultsView.js
│ │ ├── MetricsDashboard.js
│ │ ├── ThemeToggle.js
│ │ └── ToastHost.js
│ ├── App.js
│ └── index.js
│
├── tools/
│ └── bench_p95.py 
│
├── requirements.txt
├── package.json
└── README.md
```
---

## ⚙️ Prerequisites

- **Python** 3.10+
- **Node.js** 18+
- **PostgreSQL** 13+
- **Redis** 5+

> 🪟 On Windows, ensure PostgreSQL and Redis services are running and added to PATH.

---


## 🧩 Setup

### 1️⃣ Clone and Create Environments

git clone https://github.com/rayyan776/NLP-Employee-Query-Engine.git
cd ai-nlp-query-engine

# Backend environment
cd backend
python -m venv venv
source venv/bin/activate    # (Linux/macOS)
# or
venv\Scripts\activate       # (Windows)

pip install -r requirements.txt

# Frontend setup
cd frontend
npm install
npm start

### 2️⃣ Configure Environment
```
Create a `.env` file in `backend/`:
DATABASE_URL=postgresql://user:pass@localhost:5432/employees_db
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_TTL=300
EMBEDDINGS_MODEL=sentence-transformers/all-MiniLM-L6-v2
BATCH_SIZE=32
POOL_SIZE=10
DOC_MAX_MB=10
```


## 🗄️ Database Setup

### Step 1: Install PostgreSQL

**Windows:**
- Download from: https://www.postgresql.org/download/windows/
- Run installer and remember your superuser password

**macOS:**
```
brew install postgresql@15
brew services start postgresql@15
```

**Linux:**
```
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### Step 2: Create Database and User

Open PostgreSQL shell:

```
# Windows: Open 'SQL Shell (psql)' from Start Menu
# Mac/Linux: Run this in terminal
psql -U postgres
```

In the PostgreSQL prompt, run:

```
-- Create user
CREATE USER your_username WITH PASSWORD 'your_password';

-- Create database
CREATE DATABASE employees_db;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE employees_db TO your_username;

-- Connect to the database
\c employees_db

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO your_username;

-- Exit
\q
```

### Step 3: Run Schema and Seed Data

```
# Navigate to backend folder
cd backend

# Run the SQL file
psql -U your_username -d employees_db -f db_scripts/init_db.sql
```

**Or manually:**
1. Open `backend/db_scripts/init_db.sql`
2. Copy all contents
3. Open pgAdmin or DBeaver
4. Connect to `employees_db`
5. Paste and execute

### Step 4: Configure Connection String

Update `backend/.env`:

```
DATABASE_URL=postgresql://your_username:your_password@localhost:5432/employees_db
```

**Example:**
```
DATABASE_URL=postgresql://john:secret123@localhost:5432/employees_db
```

### Step 5: Test Connection

```
cd backend
python -c "from models.db import engine; print(engine().connect()); print('✅ Connected!')"
```


---

## ▶️ Running the Project

### Start Redis

redis-server
# Check with:
redis-cli ping  # → PONG


### Start Backend

cd backend
uvicorn main:app --reload --port 8000


### Start Frontend

cd frontend
npm start

Your app will open at **[http://localhost:3000](http://localhost:3000)** (proxying to FastAPI on 8000).

---

## 🌐 API Endpoints

| Method | Endpoint                | Description                             |
| :----- | :---------------------- | :-------------------------------------- |
| POST | `/api/ingest/database`  | Discover schema from DB connection      |
| POST | `/api/ingest/documents` | Upload multiple docs (PDF/DOCX/TXT/CSV) |
| GET  | `/api/ingest/status`    | Check ingestion job progress            |
| POST | `/api/query`            | Run NL→SQL/Doc/Hybrid query             |
| GET  | `/api/query/history`    | Fetch past queries and metrics          |
| GET  | `/api/schema`           | Return last discovered schema           |
| GET  | `/health`               | Service health check                    |

---

## 💡 Frontend Features

- 🧠 **Database Connector** — enter connection string, auto-discover schema.
- 📄 **Document Uploader** — drag-drop, progress tracking, per-file validation.
- 💬 **Query Panel** — smart autocomplete from schema vocabulary.
- 📊 **Results View** — SQL tables, document snippets, CSV/JSON export.
- ⚙️ **Metrics Dashboard** — latency, cache hit rate, health, schema stats.
- 🌗 **Theme Toggle** — light/dark mode with Bootstrap `data-bs-theme`.

---

## 🧮 Example Queries

- “Average salary by department”
- “How many employees do we have?”
- “Average salary by city”
- “Employees with salary over 120000”
- “Average salary by city; show office_location and average salary.”
- “Employees with salary over 120000; include department.”
- “Top 3 highest paid in Engineering; show name and salary.”
- “Count of documents per employee; show full_name and document count.”
- “Show backend developers with salary above 110000; include department.”
- “Who reports to Anjali Gupta?”
- “Show me performance reviews for engineers hired last year; list name, department, and a snippet.”
- “Employees with Python skills earning over 100000; include department.”

---

## 🔐 Security & Reliability

- ✅ Parameterized SQL only — **no DDL/DML generation**
- ✅ File validation & sanitization
- ✅ CORS-safe configuration
- ✅ Redis cache with invalidation and graceful fallback
- ✅ Health and metrics endpoints for observability

---

## ⚡ Performance & Benchmark

- Connection pooling (SQLAlchemy QueuePool)
- Async ingestion + batch embeddings
- Caching via Redis (TTL + invalidation)
- `p95` benchmark under 50 ms (local 10-user test)

Run benchmark:

```bash
pip install aiohttp
python tools/bench_p95.py --users 10 --duration 60 --query "Average salary by department"
```

📊 Example Result:

```
p95 = 45 ms | avg = 36 ms | errors = 0 (0.0%)
```

---

## 🧰 Testing

- **Unit Tests:** schema discovery, NL→SQL mapping, caching, document chunking.
- **Integration Tests:** run across schema variants (`employees/departments`, `staff/divisions`).
- **Benchmark:** verify p95 < 2000 ms under load.

### Test Coverage

**Unit Tests** (`tests/test_query_parser.py`):
- Query operation detection (COUNT, AGGREGATE, LIST)
- Grouping detection (by department, by city)
- Filter parsing (numeric, date filters)
- Window function detection (Top N per group)
- Relationship detection ("reports to")

**Integration Tests** (`tests/test_integration.py`):
- End-to-end SQL generation for grouped aggregations
- End-to-end SQL generation for relationship queries
- Validation of SQL structure (JOINs, GROUP BY, HAVING)

**Expected Output:**

tests/test_integration.py::test_avg_by_dept_sql_generation PASSED
tests/test_integration.py::test_reports_to_sql_generation PASSED
tests/test_query_parser.py::test_detect_count PASSED
tests/test_query_parser.py::test_detect_group_avg_by_dept PASSED
tests/test_query_parser.py::test_detect_salary_filter PASSED
tests/test_query_parser.py::test_detect_window_top_each_dept PASSED
tests/test_query_parser.py::test_detect_reports_to PASSED

7 passed in 0.XX s


## ⚙️ Configuration

All environment variables live in `backend/.env`.
Optional **Docker Compose** setup can be added for API, DB, and Redis orchestration.

---

## 🧾 License

For **evaluation and demonstration** purposes only.
All third-party libraries retain their original licenses.

