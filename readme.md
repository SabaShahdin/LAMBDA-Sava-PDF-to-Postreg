# 🧠 Lambda Lab – Document Upload Microservice

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.x-orange.svg)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-20.x-blue.svg)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-v1.27-blue.svg)](https://kubernetes.io/)

This project is a **containerized microservice architecture** for uploading and storing documents in a PostgreSQL database. It uses **Flask** for the backend, **Docker** for containerization, and **Kubernetes** for orchestration.

---

## 📁 Project Structure

```
LAMBDA-LAB/
├── frontend/
│   ├── nginx/
│   │   └── default.conf
│   └── index.html
├── invoker/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── worker/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
└── k8s/
    ├── 00-namespace.yaml
    ├── 01-db-secret.yaml
    ├── 02-postgres.yaml
    ├── 03-pgadmin.yaml
    ├── 04-invoker.yaml
    └── 05-frontend.yaml
```

---

## 🚀 Architecture Overview

```mermaid
flowchart LR
    A[Frontend (Nginx)] -->|HTTPUpload| B[Invoker Service]
    B -->|WritesFilePath| C[Worker Service]
    C -->|StoresFileContent| D[(PostgreSQL)]
    C -->|OptionalLogsEvents| E[MinIO / Observability]

```

**Description:**

* **Frontend:** Provides a simple web interface for uploading files.
* **Invoker:** Handles requests, sets environment variables for the worker.
* **Worker:** Reads file from `/uploads` and stores it in PostgreSQL.
* **PostgreSQL:** Stores documents in binary (`BYTEA`) format.
* **MinIO/Observability:** Optional storage or logging solution.

---

## 🔧 Worker Environment Variables

| Variable      | Description                           |
| ------------- | ------------------------------------- |
| `DB_HOST`     | PostgreSQL host (default: `postgres`) |
| `DB_PORT`     | PostgreSQL port (default: `5432`)     |
| `DB_NAME`     | Name of the database                  |
| `DB_USER`     | Database username                     |
| `DB_PASSWORD` | Database password                     |
| `FILE_NAME`   | Name of the file to upload            |

---

## 📦 Dependencies

* Python 3.11
* Flask
* psycopg2

Install locally:

```bash
pip install -r requirements.txt
```

---

## 🐳 Docker Usage

Build the worker image:

```bash
docker build -t worker-service ./worker
```

Run the container:

```bash
docker run -e DB_NAME=your_db \
           -e DB_USER=your_user \
           -e DB_PASSWORD=your_password \
           -e FILE_NAME=your_file.pdf \
           -v /path/to/uploads:/uploads \
           worker-service
```

---

## ☸️ Kubernetes Deployment

1. Apply all manifests in the `k8s/` directory:

```bash
kubectl apply -f k8s/
```

2. Ensure **secrets** and **persistent volumes** are configured for PostgreSQL and file uploads.

3. Check pod status:

```bash
kubectl get pods -n lambda-lab
```

---

## 🗃️ Database Schema

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    filename TEXT NOT NULL,
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    content BYTEA NOT NULL
);
```

---

## 📌 Notes

* The service exits with error codes if the file is missing or environment variables are not set.
* Designed for modularity—can be extended with authentication, file type validation, or frontend integration.
* Supports Kubernetes horizontal scaling by deploying multiple worker replicas.

---

## 🧪 Testing Locally

1. Place the file in `/uploads`.
2. Set environment variables.
3. Run:

```bash
python app.py
```

---

## 🏗️ CI/CD Integration Example (GitHub Actions)

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r worker/requirements.txt
      - name: Lint & Test
        run: |
          echo "Add linting and testing commands here"
      - name: Build Docker Images
        run: docker build -t worker-service ./worker
      - name: Push & Deploy to Kubernetes
        run: |
          kubectl apply -f k8s/
```

---

## 🔗 References

* [Flask Documentation](https://flask.palletsprojects.com/)
* [Docker Documentation](https://docs.docker.com/)
* [Kubernetes Documentation](https://kubernetes.io/docs/)
* [PostgreSQL BYTEA Storage](https://www.postgresql.org/docs/current/datatype-binary.html)

