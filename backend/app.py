from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from simulation import Simulator
from prediction import run_prediction
import json
import uvicorn
import os
import logging

# 1. Setup logging to track what's happening in the background
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OrbitalShield")

app = FastAPI()

# 2. Allow the Frontend (Vue/Cesium) to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Path to your source data directory
DATA_DIR = "source_data"

# 4. Global simulator instance
sim = None

def init_simulator():
    global sim
    if os.path.exists(DATA_DIR):
        logger.info(f"Loading records from directory {DATA_DIR}...")
        try:
            sim = Simulator(DATA_DIR)
            logger.info("Simulator initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to load Simulator: {e}")
    else:
        logger.warning(f"Directory {DATA_DIR} not found! Please create it and add your CSV files.")

# Initialize on startup
init_simulator()

@app.get("/predict")
async def predict_risk(time_horizon_years: int = Query(50, description="Time horizon in years")):
    if not sim or sim.df.empty:
        return {"error": "No simulation data available."}
    try:
        result = run_prediction(sim.df, time_horizon_years)
        return result
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        return {"error": str(e)}

@app.post("/reload")
async def reload_data():
    """
    Endpoint to reload all CSV files from the source_data directory.
    """
    try:
        init_simulator()
        if sim and not sim.df.empty:
            return {"status": "success", "message": f"Successfully loaded {len(sim.df)} objects."}
        else:
            return {"status": "warning", "message": "Reload attempted, but no data was found or loaded."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main communication channel between the physics engine and the 3D UI.
    """
    await websocket.accept()
    logger.info("Frontend connected to WebSocket.")
    
    try:
        # Step 1: Send the first batch of positions (Time: Now)
        if sim:
            initial_data = sim.advance(0)
            logger.info(
                        f"Sending {len(initial_data['positions'])} objects to frontend."
                    )
            await websocket.send_json(initial_data)
        
        # Step 2: Listen for commands from the UI
        while True:
            raw_data = await websocket.receive_text()
            message = json.loads(raw_data)
            
            # If UI asks to move the simulation forward
            if message.get('action') == 'advance':
                minutes = message.get('minutes', 1)
                
                # Physics calculation for all 10,000 objects
                updated_state = sim.advance(minutes)
                
                # Send back to Frontend
                await websocket.send_json(updated_state)
                
    except WebSocketDisconnect:
        logger.info("Frontend disconnected.")
    except Exception as e:
        logger.error(f"Error in WebSocket: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)