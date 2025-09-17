from fastapi import FastAPI
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()

@app.get("/")
async def root():
    message = "Instance has received the request"
    logger.info(message)
    return {"message": message}

@app.get("/cluster1")
async def cluster1():
    message = "Request received by cluster1 instance"
    logger.info(message)
    return {"status": "ok", "host": "cluster1", "message": message}

@app.get("/cluster2")
async def cluster2():
    message = "Request received by cluster2 instance"
    logger.info(message)
    return {"status": "ok", "host": "cluster2", "message": message}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
