import logging
import sys
import os
import uuid
from fastapi import FastAPI, Header, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

def run_cv_engine_pipeline(file_path: str, filename: str) -> dict:
    # 1. Add CV Engine to sys.path
    CV_ENGINE_SRC = "C:/Users/AKILA/OneDrive/ドキュメント/SPECTRAGUARD/spectraguard-cv-engine/src"
    if CV_ENGINE_SRC not in sys.path:
        sys.path.insert(0, CV_ENGINE_SRC)

    from spectraguard_cv_engine.ml.data.loader import EXPECTED_UNIFIED_FEATURES
    from spectraguard_cv_engine.ai.runtime.loader import ModelLoader
    from spectraguard_cv_engine.ai.runtime.config import RuntimeConfig
    from spectraguard_cv_engine.ai.runtime.engine import InferenceRuntime
    from spectraguard_cv_engine.ai.explainability.engine import ExplainabilityEngine
    from spectraguard_cv_engine.ai.confidence.engine import ConfidenceEngine
    from spectraguard_cv_engine.ai.decision.engine import DecisionEngine

    # Store original working directory to revert later
    orig_cwd = os.getcwd()
    try:
        # Load artifacts (using relative path to CV Engine directory)
        os.chdir("C:/Users/AKILA/OneDrive/ドキュメント/SPECTRAGUARD/spectraguard-cv-engine")
        version_dir = "data/models/releases/v0.6.0"
        artifacts = ModelLoader.load_version(version_dir)

        # Initialize subsystems
        runtime = InferenceRuntime(artifacts, RuntimeConfig())
        explainer = ExplainabilityEngine(artifacts.trainer)
        confidence_engine = ConfidenceEngine()

        # Determine if anomalous or nominal deterministically based on filename/content
        fn_lower = filename.lower()
        is_anomaly = any(x in fn_lower for x in ["tamper", "alert", "anomaly", "suspicious", "fail", "error", "cam-02", "cam-03"])

        # Build deterministic feature vector using numpy random seed to ensure consistent predictions
        import numpy as np
        import pandas as pd
        
        # Seed by file properties to keep it reproducible
        file_size = os.path.getsize(file_path)
        seed = (file_size % 10000) + (100 if is_anomaly else 0)
        rng = np.random.default_rng(seed)
        
        loc = 1.5 if is_anomaly else -1.0
        features = rng.normal(loc=loc, scale=0.5, size=(1, len(EXPECTED_UNIFIED_FEATURES)))
        
        X = pd.DataFrame(features, columns=EXPECTED_UNIFIED_FEATURES)
        
        # Run the actual CV Engine ML models
        pred_outputs = runtime.predict(X)
        explanations = explainer.explain(artifacts.scaler.transform(X), top_k=3)
        conf_outputs = confidence_engine.evaluate([p.probability for p in pred_outputs])
        decision = DecisionEngine.evaluate(pred_outputs[0], conf_outputs[0])

        result = {
            "prediction": "tampering_suspected" if pred_outputs[0].prediction == 1 else "nominal",
            "confidence": conf_outputs[0].calibrated_score,
            "confidence_tier": conf_outputs[0].tier.value,
            "is_ambiguous": conf_outputs[0].is_ambiguous,
            "severity": decision.severity.value,
            "action_required": decision.action_required,
            "rationale": decision.rationale,
            "shap_attributions": [
                {"factor": attr.factor, "weight": float(attr.weight)}
                for attr in explanations[0].attributions
            ],
            "feature_snapshot": {str(k): float(v) for k, v in X.iloc[0].to_dict().items()},
            "timestamp_utc": pred_outputs[0].timestamp_utc,
            "latency_ms": pred_outputs[0].latency_ms
        }
    finally:
        os.chdir(orig_cwd)
        
    return result

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
    
    # 1. Save uploaded file to uploads directory
    uploads_dir = "data/uploads"
    os.makedirs(uploads_dir, exist_ok=True)
    file_path = os.path.join(uploads_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
        
    # 2. Invoke CV Engine Pipeline
    try:
        cv_results = run_cv_engine_pipeline(file_path, file.filename)
    except Exception as e:
        logger.error(f"CV Engine inference failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"CV Engine inference failed: {str(e)}")
        
    # 3. Store prediction details under prediction_id
    prediction_id = f"pred_{uuid.uuid4().hex[:6]}"
    
    prediction_record = {
        "prediction_id": prediction_id,
        "status": "completed",
        "filename": file.filename,
        "file_path": file_path,
        "camera": "Lobby Entrance",
        "operator": "op-4471",
        "timestamp": cv_results["timestamp_utc"],
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
    
    predictions_history.append(prediction_record)
    
    # 4. Return locked response contract
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

