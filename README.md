# 🛰️ Orbital Shield – Autonomous Collision Avoidance Simulator

A production-grade, scientifically grounded simulation platform for monitoring orbital debris, executing autonomous collision avoidance manoeuvres, and forecasting long-term orbital risks (Kessler Syndrome) in Low Earth Orbit (LEO).

## 🚀 Scientific Foundation

### The Debris Problem
Space debris between 1 cm and 10 cm in LEO travels at ~7.5 km/s, carrying kinetic energy equivalent to hand grenades. These objects are untrackable by ground-based radar (tracking limit ≥ 10 cm), making them "invisible bullets" for operational satellites.

### Protection Strategy & Simulation Models
1. **Hybrid Catalogue**: Merges real-world TLE data with synthetic spatial density models (NASA ORDEM / ESA MASTER) to simulate uncatalogued debris.
2. **Dynamic Dataset Ingestion**: Drop any valid orbital CSV data into the `source_data` folder and the platform dynamically loads and deduplicates it for the global simulation.
3. **NASA-like Prediction Engine**: Simulates up to 50 years into the future using realistic atmospheric drag (orbital decay) and probabilistic collision event models based on spatial density, realistically demonstrating the Kessler Syndrome.
4. **SGP4 Propagation**: High-fidelity orbital mechanics using the industry-standard SGP4 model via Skyfield for short-term tracking and conjunction focus mode.
5. **Autonomous Manoeuvre Planner**: Real-time numerical optimization of impulsive burns using cold-gas thrusters to maximize miss distance.

## 🛠️ Technology Stack

- **Backend**: Python 3.11+, FastAPI (WebSockets), SGP4, Skyfield, NumPy, SciPy, Pandas.
- **Frontend**: Vue 3 (Composition API), CesiumJS / Three.js (3D Engine), Tailwind CSS.
- **Real-Time**: Bi-directional communication via WebSockets for low-latency simulation updates.

## 📦 Project Structure

```
orbital-shield/
├── backend/
│   ├── source_data/          # Drop your orbital CSV datasets here
│   ├── app.py                # FastAPI & WebSocket Server (API & /reload)
│   ├── simulation.py         # Orchestration Logic
│   ├── prediction.py         # NASA-like Long-term Risk & Kessler Prediction
│   ├── propagator.py         # SGP4/Skyfield Wrapper
│   ├── collision_detector.py # KD-Tree Spatial Search
│   ├── manoeuvre_planner.py  # Burn Optimization
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
*(You can hot-reload the data anytime by sending a POST request to `http://localhost:8000/reload` without restarting the server).*

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 3. Usage
1. Open `http://localhost:5173` (or the Vite provided port).
2. The 3D global view will load data dynamically from the backend WebSocket.
3. Access the prediction API at `http://localhost:8000/predict?time_horizon_years=50` to view the realistic 50-year orbital density evolution.
4. Select a **Protected Asset** from the UI to track conjunctions and initiate the **Conjunction Focus Mode**.

---
**Developed by Antigravity AI for Advanced Agentic Coding.**
