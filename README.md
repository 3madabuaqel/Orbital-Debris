# 🛰️ Orbital Shield – Autonomous Collision Assessment System

A production-grade, scientifically grounded simulation platform for monitoring orbital debris and forecasting long-term orbital risks in Low Earth Orbit (LEO) using advanced Machine Learning and Time-Aware Spatial Indexing.

## 🚀 Scientific Foundation

### The Debris Problem
Space debris between 1 cm and 10 cm in LEO travels at ~7.5 km/s, carrying kinetic energy equivalent to hand grenades. These objects are untrackable by ground-based radar (tracking limit ≥ 10 cm), making them "invisible bullets" for operational satellites.

### Protection Strategy & Simulation Models
1. **Dynamic Dataset Ingestion**: Drop any valid orbital CSV data into the `source_data` folder and the platform dynamically loads and deduplicates it for the global simulation.
2. **SGP4 Multi-Step Propagation**: High-fidelity orbital mechanics using the industry-standard SGP4 model via Skyfield. The predictive engine computes multiple time steps ($t_0, t_{+10m}, t_{+30m}, t_{+1h}, t_{+6h}$) to evaluate true temporal collision risks.
3. **Regime-Split Spatial Indexing (HNSW)**: Utilizes Hierarchical Navigable Small World (HNSW) graphs dynamically split by orbital regimes (LEO, MEO, GEO) for ultra-fast, $O(n \log n)$ spatial nearest-neighbor search among tens of thousands of objects.
4. **Isotonic-Calibrated XGBoost Engine**: The probability of collision (Pc) is evaluated using a custom XGBoost model trained on Physics-driven Monte Carlo simulations (injecting noise into covariance calculations). It includes an Isotonic Regression calibration layer to output true probabilistic maneuver thresholds.

## 🛠️ Technology Stack

- **Backend**: Python 3.11+, FastAPI (WebSockets), XGBoost, scikit-learn, hnswlib, SGP4 (Skyfield), NumPy, Pandas.
- **Frontend**: Vue 3 (Composition API), CesiumJS / Three.js (3D Engine), Tailwind CSS.
- **Real-Time**: Bi-directional communication via WebSockets for low-latency simulation updates and 3D visual triggers.

## 📦 Project Structure

```text
orbital-shield/
├── backend/
│   ├── source_data/          # Drop your orbital CSV datasets here
│   ├── app.py                # FastAPI & WebSocket Server (API & /reload)
│   ├── simulation.py         # SGP4 Orchestration Logic
│   ├── prediction.py         # Advanced Time-Aware ML Prediction Engine
│   ├── propagator.py         # SGP4/Skyfield Wrapper
│   └── data_loader.py        # Dynamic TLE Ingestion from source_data/
└── frontend/
    ├── src/
    │   ├── components/       # Vue Components (OrbitalScene, HUDs)
    │   ├── scene/            # 3D Scene builders and physics
    │   ├── App.vue           # Main Dashboard
    │   └── assets/           # Design System & CSS
    └── vite.config.js        # Vite configuration
```

## 🛠️ Setup Instructions

### 1. Backend Setup
Place your orbital data files (`.csv`) inside the `backend/source_data/` directory. If the directory doesn't exist, create it.
```bash
cd backend
pip install -r requirements.txt
python app.py
```
*(You can hot-reload the data anytime by selecting a new file from the UI dropdown).*

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 3. Usage
1. Open `http://localhost:5173` (or the Vite provided port).
2. The 3D global view will load data dynamically from the backend WebSocket.
3. Click **"RUN SIMULATION"** on the right panel to trigger the Advanced Time-Aware Prediction Engine.
4. Click on any **Predicted Event** to initiate **Conjunction Focus Mode**, flying the 3D camera directly to the satellite and rendering a physical laser-line to the predicted threat.

---
**Developed by Antigravity AI for Advanced Agentic Coding.**
