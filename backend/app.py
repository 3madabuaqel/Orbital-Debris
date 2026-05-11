from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from simulation import Simulator
from prediction import run_prediction
import uvicorn
import os
import logging
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OrbitalShield")

app = FastAPI()

# Allow Frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = "source_data"
sim = None

def init_simulator(target_path=None):
    """
    Initializes the global Simulator instance with the target CSV or directory.
    """
    global sim
    path_to_load = target_path if target_path else DATA_DIR
    if os.path.exists(path_to_load):
        logger.info(f"Loading records from path {path_to_load}...")
        try:
            sim = Simulator(path_to_load)
            logger.info("Simulator initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to load Simulator: {e}")
    else:
        logger.warning(f"Path {path_to_load} not found!")

# Initialize on startup
init_simulator()

@app.get("/predict")
async def predict_risk(time_horizon_years: int = Query(50, description="Time horizon in years")):
    """
    Triggers the Advanced Time-Aware Prediction Engine to forecast risks.
    """
    if not sim or sim.df.empty:
        return {"error": "No simulation data available."}
    try:
        result = run_prediction(sim.df, sim.sim_time, time_horizon_years)
        return result
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        return {"error": str(e)}

@app.get("/files")
async def list_files():
    """Returns a list of CSV files available in the source_data directory."""
    try:
        if not os.path.exists(DATA_DIR):
            return {"files": []}
        files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv')]
        return {"files": files}
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return {"error": str(e)}

@app.post("/reload")
async def reload_data(filename: str = Query(None, description="Specific CSV filename to load")):
    """
    Endpoint to reload CSV files dynamically without restarting the server.
    """
    try:
        if filename:
            target_path = os.path.join(DATA_DIR, filename)
            init_simulator(target_path)
        else:
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
    Main bi-directional communication channel between the physics engine and the 3D UI.
    """
    await websocket.accept()
    logger.info("Frontend connected to WebSocket.")
    
    try:
        if sim:
            initial_data = sim.advance(0)
            logger.info(f"Sending {len(initial_data['positions'])} objects to frontend.")
            await websocket.send_json(initial_data)
        
        while True:
            raw_data = await websocket.receive_text()
            message = json.loads(raw_data)
            
            if message.get('action') == 'advance':
                minutes = message.get('minutes', 1)
                updated_state = sim.advance(minutes)
                await websocket.send_json(updated_state)
                
    except WebSocketDisconnect:
        logger.info("Frontend disconnected.")
    except Exception as e:
        logger.error(f"Error in WebSocket: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)