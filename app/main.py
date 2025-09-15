from fastapi import FastAPI, HTTPException
import socket
import os

app = FastAPI()

HOSTNAME = socket.gethostname()
CLUSTER_NAME = os.getenv("CLUSTER_NAME", "unknown")

@app.get("/")
def health():
    return {"status": "ok", "host": HOSTNAME, "cluster": CLUSTER_NAME}

@app.get("/{cluster}")
def route(cluster: str):
    if cluster != CLUSTER_NAME:
        raise HTTPException(status_code=404, detail="wrong cluster for this instance")
    return {"message": f"Instance {HOSTNAME} in {cluster} is responding now!"}
