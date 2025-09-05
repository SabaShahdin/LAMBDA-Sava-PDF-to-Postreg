import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from kubernetes import client, config
from pathlib import Path

NAMESPACE = os.getenv("NAMESPACE", "lambda-lab")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/uploads"))  # shared PVC

app = FastAPI(title="Lambda-Like Invoker")

def load_kube():
    # Running inside cluster
    try:
        config.load_incluster_config()
    except Exception:
        # Fallback for local debugging
        config.load_kube_config()

def create_worker_job(filename: str) -> str:
    load_kube()
    batch = client.BatchV1Api()

    job_name = f"worker-{uuid.uuid4().hex[:8]}"
    labels = {"app": "lambda-worker", "job": job_name}

    # Use same PVC name as in k8s/03-uploads-pvc.yaml
    volume_name = "uploads-vol"
    claim_name = "uploads-pvc"

    # Env from Secret for DB
    env_from = [client.V1EnvFromSource(secret_ref=client.V1SecretEnvSource(name="db-secret"))]

    # Individual env vars
    env = [
        client.V1EnvVar(name="NAMESPACE", value=NAMESPACE),
        client.V1EnvVar(name="FILE_NAME", value=filename),
        client.V1EnvVar(name="DB_HOST", value=os.getenv("DB_HOST", "postgres")),
        client.V1EnvVar(name="DB_PORT", value=os.getenv("DB_PORT", "5432")),
        client.V1EnvVar(name="DB_NAME", value_from=client.V1EnvVarSource(secret_key_ref=client.V1SecretKeySelector(name="db-secret", key="POSTGRES_DB"))),
        client.V1EnvVar(name="DB_USER", value_from=client.V1EnvVarSource(secret_key_ref=client.V1SecretKeySelector(name="db-secret", key="POSTGRES_USER"))),
        client.V1EnvVar(name="DB_PASSWORD", value_from=client.V1EnvVarSource(secret_key_ref=client.V1SecretKeySelector(name="db-secret", key="POSTGRES_PASSWORD"))),
    ]

    container = client.V1Container(
        name="worker",
        image=os.getenv("WORKER_IMAGE", "lambda-worker:latest"),
        image_pull_policy="IfNotPresent",
        env=env,
        env_from=env_from,
        volume_mounts=[client.V1VolumeMount(name=volume_name, mount_path="/uploads")]
    )

    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels=labels),
        spec=client.V1PodSpec(
            restart_policy="Never",
            containers=[container],
            volumes=[client.V1Volume(name=volume_name, persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(claim_name=claim_name))]
        )
    )

    job_spec = client.V1JobSpec(template=template, backoff_limit=0)
    job = client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(name=job_name, namespace=NAMESPACE),
        spec=job_spec
    )

    batch.create_namespaced_job(namespace=NAMESPACE, body=job)
    return job_name

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Save to shared PVC so the worker can read it
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}_{file.filename.replace('/', '_')}"[:120]
    dest = UPLOAD_DIR / safe_name
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    with open(dest, "wb") as f:
        f.write(data)

    # Spawn the worker job
    job_name = create_worker_job(safe_name)
    return JSONResponse({"message": "accepted", "job_name": job_name, "stored_as": safe_name})
