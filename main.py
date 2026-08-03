import logging
import sys
import os
import uuid
from fastapi import FastAPI, Header, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# 1. Add CV Engine to sys.path
CV_ENGINE_SRC = "C:/Users/AKILA/OneDrive/ドキュメント/SPECTRAGUARD/spectraguard-cv-engine/src"
if CV_ENGINE_SRC not in sys.path:
    sys.path.insert(0, CV_ENGINE_SRC)

from inference.predictor import SpectraGuardPredictor

predictor = None

def run_cv_engine_pipeline(file_path: str, filename: str) -> dict:
    global predictor
    if predictor is None:
        raise RuntimeError("Predictor is not initialized.")
    orig_cwd = os.getcwd()
    try:
        os.chdir("C:/Users/AKILA/OneDrive/ドキュメント/SPECTRAGUARD/spectraguard-cv-engine")
        return predictor.predict_video(file_path)
    finally:
        os.chdir(orig_cwd)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("spectraguard-mock-backend")

app = FastAPI(
    title="SpectraGuard Mock API Gateway",
    version="1.0.0-RC1",
    description="Deterministic mock api staging environment to validate connectivity."
)

@app.on_event("startup")
def startup_event():
    global predictor
    logger.info("Initializing SpectraGuard inference engine...")
    orig_cwd = os.getcwd()
    try:
        os.chdir("C:/Users/AKILA/OneDrive/ドキュメント/SPECTRAGUARD/spectraguard-cv-engine")
        predictor = SpectraGuardPredictor(release_version="v1.0.0")
        
        # Print the clean operational banner exactly as requested via logger.info
        logger.info("\n" + "\n".join([
            "============================",
            "Production Runtime Loaded",
            "============================",
            f"Release Version: {predictor.release_version}",
            f"Model Type: {predictor.model_type}",
            f"Model Path: {predictor.model_path}",
            f"Scaler Path: {predictor.scaler_path}",
            f"Metadata Path: {predictor.meta_path}",
            f"Expected Features: {predictor.expected_features}",
            f"SHA256: {predictor.model_hash}",
            "============================"
        ]))
    except Exception as e:
        logger.error(f"CRITICAL: Failed to load production runtime: {str(e)}")
        # Exit backend to fail fast if anything is inconsistent
        os._exit(1)
    finally:
        os.chdir(orig_cwd)

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

# In-memory database tables
predictions_history = []

cameras_db = [
    {
        "id": "CAM-01",
        "name": "Lobby Entrance",
        "location": "Main Lobby Port A",
        "status": "online",
        "resolution": "1920x1080",
        "fps": 30,
        "integrityScore": 0.998,
        "thumbnail": "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=600&q=80"
    },
    {
        "id": "CAM-02",
        "name": "Warehouse Gate",
        "location": "Warehouse Block A",
        "status": "anomalous",
        "resolution": "1920x1080",
        "fps": 24,
        "integrityScore": 0.942,
        "thumbnail": "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?auto=format&fit=crop&w=600&q=80"
    },
    {
        "id": "CAM-03",
        "name": "Parking Zone B",
        "location": "East Parking Area",
        "status": "anomalous",
        "resolution": "1280x720",
        "fps": 15,
        "integrityScore": 0.814,
        "thumbnail": "https://images.unsplash.com/photo-1506521781263-d8422e82f27a?auto=format&fit=crop&w=600&q=80"
    },
    {
        "id": "CAM-04",
        "name": "Main Corridor",
        "location": "Administration Wing",
        "status": "online",
        "resolution": "1920x1080",
        "fps": 30,
        "integrityScore": 0.991,
        "thumbnail": "https://images.unsplash.com/photo-1517502884422-41eaead166d4?auto=format&fit=crop&w=600&q=80"
    }
]

events_db = [
    {
        "id": "evt-1",
        "time": "09:42 AM",
        "camera": "Lobby Entrance",
        "status": "online",
        "event": "Integrity Verified"
    },
    {
        "id": "evt-2",
        "time": "09:37 AM",
        "camera": "Warehouse Gate",
        "status": "anomalous",
        "event": "Blur Detected"
    },
    {
        "id": "evt-3",
        "time": "09:31 AM",
        "camera": "Parking Zone B",
        "status": "anomalous",
        "event": "Lens Obstruction"
    },
    {
        "id": "evt-4",
        "time": "09:25 AM",
        "camera": "Main Corridor",
        "status": "online",
        "event": "Integrity Verified"
    }
]

@app.post("/api/v1/auth/login")
def login(payload: LoginRequest):
    logger.info(f"Mock login request received for operator: {payload.username}")
    username_upper = payload.username.upper()
    if not username_upper.startswith("OP-") or payload.password != "spectra":
        logger.warning(f"Authentication failed for operator: {payload.username}")
        raise HTTPException(status_code=401, detail="Unauthorized operator credentials.")
    return {
        "token": "spectraguard_secure_validation_token_xyz",
        "accessToken": "spectraguard_secure_validation_token_xyz",
        "expiresIn": 900
    }

@app.post("/api/v1/auth/logout")
def logout(token: str = Depends(verify_token)):
    logger.info("Mock logout request received.")
    return {
        "success": True,
        "message": "Session invalidated."
    }

@app.get("/api/v1/me")
def get_me(token: str = Depends(verify_token)):
    logger.info("Retrieving operator user profile context.")
    return {
        "username": "op-4471",
        "role": "Lead Security Operator",
        "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=100&q=80"
    }

@app.get("/api/v1/dashboard/summary")
def get_summary(token: str = Depends(verify_token)):
    logger.info("Calculating dashboard operational summary.")
    # Derive summary metrics from in-memory cameras state
    total_cameras = len(cameras_db)
    anomalous = len([c for c in cameras_db if c["status"] == "anomalous"])
    average_integrity = sum([c["integrityScore"] for c in cameras_db]) / total_cameras if total_cameras > 0 else 1.0
    
    return {
        "systemIntegrity": f"{average_integrity * 100:.1f}%",
        "activeCameras": total_cameras,
        "integrityAlerts": anomalous,
        "predictionsToday": len(predictions_history)
    }

@app.get("/api/v1/dashboard/sidebar")
def get_sidebar_status(token: str = Depends(verify_token)):
    logger.info("Retrieving active system components statuses.")
    total_cameras = len(cameras_db)
    return {
        "backendStatus": "healthy",
        "databaseStatus": "healthy",
        "cvEngineStatus": "healthy",
        "connectedCameras": total_cameras,
        "platformHealth": 0.99
    }

@app.get("/api/v1/cameras")
def get_cameras(token: str = Depends(verify_token)):
    logger.info("Cameras retrieval triggered.")
    return cameras_db

@app.get("/api/v1/events")
def get_events(token: str = Depends(verify_token)):
    logger.info("Events timeline query triggered.")
    return events_db

@app.get("/api/v1/notifications")
def get_notifications(token: str = Depends(verify_token)):
    logger.info("Notifications drawer query triggered.")
    return [
        {
            "id": "notif-1",
            "title": "System Core Online",
            "message": "SpectraGuard security core is fully synchronized.",
            "time": "Just Now",
            "category": "System",
            "read": False
        },
        {
            "id": "notif-2",
            "title": "Camera CAM-02 Flagged",
            "message": "Degraded signal status flag raised on Warehouse Gate.",
            "time": "10m ago",
            "category": "Update",
            "read": False
        }
    ]


@app.get("/api/v1/predictions/history")
def get_predictions_history(token: str = Depends(verify_token)):
    logger.info("Predictions history retrieval triggered.")
    return predictions_history

@app.get("/api/v1/search")
def search(q: str = "", token: str = Depends(verify_token)):
    logger.info(f"Global search requested for query: {q}")
    query = q.lower().strip()
    if not query:
        return {"cameras": [], "events": [], "predictions": []}
        
    matching_cameras = [
        c for c in cameras_db 
        if query in c["name"].lower() or query in c["location"].lower() or query in c["id"].lower()
    ]
    matching_events = [
        e for e in events_db 
        if query in e["camera"].lower() or query in e["event"].lower() or query in e["status"].lower()
    ]
    matching_predictions = [
        p for p in predictions_history 
        if query in p.get("prediction", "").lower() or query in p.get("filename", "").lower()
    ]
    
    return {
        "cameras": matching_cameras,
        "events": matching_events,
        "predictions": matching_predictions
    }

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
async def predict(file: UploadFile = File(...), authorization: Optional[str] = Header(None)):
    _token = verify_token(authorization)
    logger.info(f"Prediction request received for file: {file.filename}")
    
    from pathlib import Path

    try:
        # 1. Ensure the upload directory exists
        uploads_dir = Path("data/uploads")
        uploads_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. Resolve absolute path of saved file
        upload_path = (uploads_dir / file.filename).resolve()
        
        # 3. Write uploaded file to disk
        with open(upload_path, "wb") as f:
            f.write(await file.read())
            
        # 4. Verify file exists after writing
        if not upload_path.exists():
            raise RuntimeError(f"Written file could not be verified on disk: {upload_path}")
            
        # 5. Add Logging
        file_size = upload_path.stat().st_size
        logger.info(f"Upload directory: {uploads_dir}")
        logger.info(f"Saved file: {file.filename}")
        logger.info(f"Absolute path: {upload_path}")
        logger.info(f"Exists: {upload_path.exists()}")
        logger.info(f"Size: {file_size} bytes")
        
    except Exception as e:
        logger.error(f"Failed to save uploaded file to disk: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file to disk: {str(e)}")

    # 6. Invoke CV Engine Pipeline
    logger.info("Starting CV inference...")
    try:
        cv_results = run_cv_engine_pipeline(str(upload_path), file.filename)
        logger.info("Explainability completed")
    except Exception as e:
        logger.error(f"CV Engine inference failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"CV Engine inference failed: {str(e)}")
        
    # 7. Store prediction details under prediction_id
    prediction_id = cv_results.get("prediction_id") or f"pred_{uuid.uuid4().hex[:6]}"
    
    prediction_record = {
        "prediction_id": prediction_id,
        "status": "completed",
        "filename": file.filename,
        "file_path": str(upload_path),
        "camera": "Lobby Entrance",
        "operator": "op-4471",
        "timestamp": cv_results["prediction_timestamp"],
        "prediction": cv_results["prediction"],
        "confidence": cv_results["confidence"],
        "confidence_tier": cv_results["confidence_tier"],
        "severity": cv_results["severity"],
        "action_required": cv_results["action_required"],
        "rationale": cv_results["rationale"],
        "shap_attributions": cv_results["shap_attributions"],
        "feature_snapshot": cv_results["feature_snapshot"],
        "latency_ms": cv_results["latency_ms"]
    }
    logger.info("Prediction packaged")
    
    predictions_history.append(prediction_record)
    logger.info("Prediction stored")
    logger.info(f"Prediction ID: {prediction_id}")
    
    # 8. Return locked response contract
    logger.info("Returning prediction_id")
    return {
        "prediction_id": prediction_id,
        "status": "completed"
    }

@app.get("/api/v1/predictions/{prediction_id}")
def get_prediction(prediction_id: str, authorization: Optional[str] = Header(None)):
    _token = verify_token(authorization)
    logger.info(f"Retrieving prediction details for ID: {prediction_id}")
    pred = next((p for p in predictions_history if p["prediction_id"] == prediction_id), None)
    if not pred:
        raise HTTPException(status_code=404, detail="Prediction ID not found")
    return pred

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

