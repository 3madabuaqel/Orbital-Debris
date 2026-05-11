import math
import pandas as pd
import numpy as np
import hnswlib
from xgboost import XGBRegressor
from sklearn.isotonic import IsotonicRegression
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

SIGMA_KM = 1.0  
HBR_KM = 0.02   

def train_calibrated_model():
    """
    Trains a high-fidelity synthetic XGBoost model with Physics-driven Monte Carlo noise
    and calibrates it using Isotonic Regression.
    Features: [miss_dist, rel_vel, tca, col_angle, closing_vel_proj, energy_proxy, orbital_region_id, uncert_rad]
    """
    logger.info("Initializing and training High-Fidelity XGBoost Regressor with Calibration...")
    X_synth = []
    y_synth = []
    
    np.random.seed(42)
    for _ in range(50000):
        miss_dist = np.random.exponential(scale=5.0) 
        rel_vel = np.random.uniform(0.1, 15.0)   
        tca = np.random.exponential(scale=60.0)  
        col_angle = np.random.uniform(0, math.pi)
        
        closing_vel_proj = rel_vel * math.cos(col_angle)
        energy_proxy = 0.5 * (rel_vel**2)
        orbital_region_id = np.random.choice([0, 1, 2])
        
        # Time-based uncertainty radius (grows with TCA) + noise
        uncert_rad = 1.0 + (0.01 * tca) + np.random.normal(0, 0.2)
        uncert_rad = max(0.1, uncert_rad)
        
        # Improved Probability Model
        pc_exponent = -(miss_dist**2) / (2 * uncert_rad**2)
        raw_pc = math.exp(pc_exponent) * 1e-4
        
        v_factor = 1.0 + (energy_proxy / 100.0)
        geom_factor = 1.0 + (math.pi - col_angle) / math.pi
        
        raw_pc = raw_pc * v_factor * geom_factor
        
        # Noise injection to simulate orbital uncertainty bias
        raw_pc *= np.random.lognormal(mean=0.0, sigma=0.3)
        
        risk_percentage = min(100.0, (raw_pc / 1e-4) * 100.0)
        
        X_synth.append([miss_dist, rel_vel, tca, col_angle, closing_vel_proj, energy_proxy, orbital_region_id, uncert_rad])
        y_synth.append(risk_percentage)
        
    X_synth = np.array(X_synth)
    y_synth = np.array(y_synth)
    
    model = XGBRegressor(
        n_estimators=300, 
        max_depth=6, 
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )
    model.fit(X_synth, y_synth)
    
    # Calibration Layer (Isotonic Regression)
    preds = model.predict(X_synth)
    calibrator = IsotonicRegression(out_of_bounds='clip')
    calibrator.fit(preds, y_synth)
    
    logger.info("High-Fidelity XGBoost & Calibrator trained successfully.")
    return model, calibrator

# Train models once at startup
xgb_model, calibrator = train_calibrated_model()

def calculate_conjunction_physics(p_row, h_row):
    """Calculates true 3D relative kinematics including collision angle."""
    try:
        rA = np.array([p_row['x'], p_row['y'], p_row['z']])
        vA = np.array([p_row['vx'], p_row['vy'], p_row['vz']])
        
        rB = np.array([h_row['x'], h_row['y'], h_row['z']])
        vB = np.array([h_row['vx'], h_row['vy'], h_row['vz']])
        
        dr = rA - rB
        dv = vA - vB
        
        rel_vel = np.linalg.norm(dv)
        if rel_vel == 0:
            return 9999.0, 0.0, 0.0, 0.0
            
        norm_vA = np.linalg.norm(vA)
        norm_vB = np.linalg.norm(vB)
        if norm_vA > 0 and norm_vB > 0:
            cos_theta = np.clip(np.dot(vA, vB) / (norm_vA * norm_vB), -1.0, 1.0)
            col_angle = np.arccos(cos_theta)
        else:
            col_angle = 0.0
            
        tca = -np.dot(dr, dv) / np.dot(dv, dv)
        if tca < 0:
            tca = 0.0
            
        dr_min = dr + dv * tca
        miss_dist = np.linalg.norm(dr_min)
        
        return miss_dist, rel_vel, tca, col_angle
    except Exception:
        return 9999.0, 0.0, 0.0, 0.0

def get_regime(alt):
    if alt <= 2000: return 0
    if alt <= 35786: return 1
    return 2

def run_prediction(df: pd.DataFrame, current_time, time_horizon_years: int = 50) -> dict:
    """
    Advanced Time-Aware Prediction Engine.
    Performs multi-step SGP4 propagation and aggregates weighted risks from top-K hazards 
    using Regime-Split HNSW spatial indices.
    """
    logger.info("Running Advanced Time-Aware Prediction Engine...")
    
    from propagator import compute_positions
    
    time_steps = [
        ("t0", 0),
        ("t+10m", 10),
        ("t+30m", 30),
        ("t+1h", 60),
        ("t+6h", 360)
    ]
    
    payload_risk_profiles = {}
    
    for step_name, offset_minutes in time_steps:
        eval_time = current_time + timedelta(minutes=offset_minutes)
        # SGP4 Propagate to this time step
        pos_df = compute_positions(df, eval_time)
        
        req_cols = ['x', 'y', 'z', 'vx', 'vy', 'vz', 'alt']
        payloads = pos_df[pos_df['type'] == 'PAYLOAD'].dropna(subset=req_cols).copy()
        hazards = pos_df[pos_df['type'].isin(['DEBRIS', 'ROCKET BODY'])].dropna(subset=req_cols).copy()
        
        if payloads.empty or hazards.empty:
            continue
            
        payloads['regime'] = payloads['alt'].apply(get_regime)
        hazards['regime'] = hazards['alt'].apply(get_regime)
        
        # Regime-Split HNSW Indexing
        indices = {}
        for r in [0, 1, 2]:
            h_sub = hazards[hazards['regime'] == r].copy()
            if len(h_sub) > 0:
                h_coords = h_sub[['x', 'y', 'z']].values.astype('float32')
                p = hnswlib.Index(space='l2', dim=3)
                p.init_index(max_elements=len(h_coords), ef_construction=100, M=16)
                p.add_items(h_coords, np.arange(len(h_coords)))
                p.set_ef(50)
                indices[r] = (p, h_sub.reset_index(drop=True))
                
        # Evaluate Payload Risks
        for r in [0, 1, 2]:
            p_sub = payloads[payloads['regime'] == r].reset_index(drop=True)
            if len(p_sub) == 0 or r not in indices:
                continue
                
            p_index, h_df = indices[r]
            p_coords = p_sub[['x', 'y', 'z']].values.astype('float32')
            
            # Top-K evaluation per orbital region
            k = min(5, len(h_df))
            labels, distances = p_index.knn_query(p_coords, k=k)
            
            for i in range(len(p_sub)):
                p_row = p_sub.iloc[i]
                pid = str(p_row['name'])
                
                if pid not in payload_risk_profiles:
                    payload_risk_profiles[pid] = {
                        'satellite': {'name': pid},
                        'max_risk': -1.0,
                        'time_of_max_risk': None,
                        'max_risk_details': None
                    }
                
                step_features = []
                step_hazards = []
                
                for j in range(k):
                    h_idx = labels[i][j]
                    h_row = h_df.iloc[h_idx]
                    
                    miss_dist, rel_vel, tca, col_angle = calculate_conjunction_physics(p_row, h_row)
                    closing_vel_proj = rel_vel * math.cos(col_angle)
                    energy_proxy = 0.5 * (rel_vel**2)
                    uncert_rad = 1.0 + (0.01 * tca)
                    
                    step_features.append([miss_dist, rel_vel, tca, col_angle, closing_vel_proj, energy_proxy, r, uncert_rad])
                    step_hazards.append(h_row)
                    
                if step_features:
                    X_pred = np.array(step_features)
                    raw_preds = xgb_model.predict(X_pred)
                    calibrated_preds = calibrator.predict(raw_preds)
                    
                    # Aggregate TOTAL_RISK = Σ (risk_i * exp(-distance_weight))
                    total_step_risk = 0.0
                    for idx_h, pred_risk in enumerate(calibrated_preds):
                        dist = step_features[idx_h][0]
                        weighted_risk = max(0, pred_risk) * math.exp(-dist / 50.0)
                        total_step_risk += weighted_risk
                        
                    if total_step_risk > payload_risk_profiles[pid]['max_risk']:
                        max_idx = np.argmax(calibrated_preds)
                        payload_risk_profiles[pid]['max_risk'] = total_step_risk
                        payload_risk_profiles[pid]['time_of_max_risk'] = step_name
                        payload_risk_profiles[pid]['max_risk_details'] = {
                            'hazard': str(step_hazards[max_idx]['name']),
                            'miss_dist': step_features[max_idx][0],
                            'rel_vel': step_features[max_idx][1],
                            'tca': step_features[max_idx][2] + (offset_minutes * 60)
                        }

    # Format Results
    results_list = list(payload_risk_profiles.values())
    results_list.sort(key=lambda x: x['max_risk'], reverse=True)
    top_risks = results_list[:15]
    
    formatted_events = []
    for r in top_risks:
        if r['max_risk_details']:
            formatted_events.append({
                'satellite': r['satellite'],
                'tca': f"TCA: {r['max_risk_details']['tca']:.1f}s",
                'probability': f"{min(100.0, r['max_risk']):.2f}%",
                'kineticEnergy': f"Rel.Vel: {r['max_risk_details']['rel_vel']:.1f}km/s",
                'hazard_name': r['max_risk_details']['hazard'],
                
                # Enhanced output structure requested by user
                'max_risk_over_time': float(min(100.0, r['max_risk'])),
                'time_of_max_risk': r['time_of_max_risk'],
                'risk_breakdown': {
                    'distance_contribution': float(math.exp(-r['max_risk_details']['miss_dist']/50.0)),
                    'temporal_contribution': r['time_of_max_risk']
                }
            })

    # Global metrics
    all_risks = [r['max_risk'] for r in results_list if r['max_risk'] > 0]
    global_risk_index = (np.mean(all_risks) / 100.0) if all_risks else 0.0
    trend = "CRITICAL RISK" if global_risk_index > 0.4 else "Nominal Protection"

    return {
        "time_horizon_years": time_horizon_years,
        "global_risk_index": float(global_risk_index),
        "high_risk_zones": formatted_events, 
        "trend": trend,
        "initial_object_count": len(df),
        "final_object_count": len(df)
    }
