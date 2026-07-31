import logging
from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("spectraguard-mock-backend")

app = FastAPI(
    title="SpectraGuard Mock API Gateway",
    version="1.0.0-RC1",
    description="Deterministic mock api staging environment to validate connectivity."
)

# Enable wide CORS policy for client integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    username: str
    password: str

def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization:
        logger.warning("Missing Authorization header")
        raise HTTPException(status_code=401, detail="Unauthorized Access")
    
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0] != "Bearer" or parts[1] != "spectraguard_secure_validation_token_xyz":
        logger.warning(f"Unauthorized or invalid token received: {authorization}")
        raise HTTPException(status_code=401, detail="Unauthorized Access")
    
    return parts[1]

@app.post("/api/v1/auth/login")
def login(payload: LoginRequest):
    logger.info(f"Mock login request received for operator: {payload.username}")
    return {
        "token": "spectraguard_secure_validation_token_xyz",
        "accessToken": "spectraguard_secure_validation_token_xyz",
        "expiresIn": 900
    }

@app.get("/api/v1/cameras")
def get_cameras(token: str = Depends(verify_token)):
    logger.info("Mock cameras retrieval triggered.")
    return [
        {
            "id": "CAM-01",
            "name": "Front Entrance Camera",
            "location": "Main Lobby Port A",
            "status": "online",
            "resolution": "1920x1080",
            "fps": 30,
            "integrityScore": 0.98
        },
        {
            "id": "CAM-02",
            "name": "Server Room A Camera",
            "location": "Secure Unit Port B",
            "status": "offline",
            "resolution": "1920x1080",
            "fps": 24,
            "integrityScore": 0.72
        }
    ]

@app.get("/api/v1/forensics/{camera_id}")
def get_forensics(camera_id: str):
    logger.info(f"Mock forensic package query for ID: {camera_id}")
    return {
        "success": True,
        "data": {
            "id": f"pkg-{camera_id}",
            "alertId": "evt-88213",
            "cameraName": "Server Room A",
            "pathType": "fast",
            "decisionPath": [
                "Frame Grabber Ingest",
                "Spatial Variance Scan",
                "Log Spectral Energy Drop",
                "Mitosis Trigger Threshold"
            ],
            "shapFactors": [
                {"factor": "laplacian_variance", "weight": 0.42},
                {"factor": "spectral_flatness", "weight": 0.28}
            ],
            "heatmapCells": [
                {"x": 4, "y": 7, "weight": 0.89}
            ],
            "signedHash": "0x8f3c7a1b9e2d4f5c",
            "signedAt": "2026-07-28T12:04:15Z",
            "operator": "op-4471",
            "ntpOffsetMs": 12
        }
    }

@app.post("/api/v1/predict")
def predict():
    logger.info("Mock inference upload target prediction request received.")
    return {
        "success": True,
        "prediction": "nominal",
        "confidence": 0.9823
    }

@app.get("/api/v1/system/health")
def health():
    logger.info("Mock system health check triggered.")
    return {
        "success": True,
        "data": [
            {
                "id": "node-01",
                "name": "Edge Node Alpha",
                "role": "Ingest & FFT",
                "status": "healthy",
                "uptime": "14d 6h",
                "restarts24h": 0,
                "queueDepth": 2
            }
        ]
    }

@app.get("/api/v1/system/simulate-error/{status_code}")
async def simulate_error(status_code: int):
    logger.info(f"Simulating error for HTTP status code: {status_code}")
    raise HTTPException(status_code=status_code, detail=f"Simulated fault engine code: {status_code}")
