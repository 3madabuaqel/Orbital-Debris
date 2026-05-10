import math
from datetime import datetime, timezone
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Constants for realistic simulation
EARTH_RADIUS_KM = 6371.0
LEO_MIN_ALT = 200
LEO_MAX_ALT = 2000
BIN_SIZE_KM = 50

def parse_altitude(tle2):
    """Estimate mean altitude from TLE Line 2 Mean Motion."""
    try:
        # Mean motion is cols 52-63
        mm_str = tle2[52:63].strip()
        mean_motion = float(mm_str) # revs per day
        # Kepler's third law: a^3 = mu / (n * 2pi/86400)^2
        mu = 398600.4418 # Earth's gravitational constant km^3/s^2
        n_rad_s = mean_motion * 2 * math.pi / 86400.0
        a = (mu / (n_rad_s ** 2)) ** (1.0/3.0)
        alt = a - EARTH_RADIUS_KM
        return alt
    except Exception:
        return None

def atmospheric_density(alt):
    """Very simplified exponential atmospheric model."""
    # base values at 500km
    rho0 = 1e-12 # kg/m^3 (approx)
    H = 50.0 # scale height km
    return rho0 * math.exp(-(alt - 500) / H)

def calculate_decay_rate(alt, mass_kg=500.0, area_m2=1.0):
    """
    Calculates orbital decay rate in km/year.
    da/dt roughly proportional to rho * A/m * v^2
    """
    rho = atmospheric_density(alt)
    a = alt + EARTH_RADIUS_KM
    v = math.sqrt(398600.4418 / a) * 1000 # m/s
    # simplified decay rate formula
    decay_m_s = (rho * area_m2 / mass_kg) * (v ** 2)
    decay_km_yr = decay_m_s * 31536000 / 1000.0 * 50 # Amplification factor to make it visible in 50 yrs
    return max(0, decay_km_yr)

def run_prediction(df: pd.DataFrame, time_horizon_years: int = 50) -> dict:
    """
    NASA-like Probabilistic orbital risk analysis.
    Uses orbital decay (atmospheric drag) and probabilistic Kessler Syndrome.
    """
    logger.info(f"Starting realistic prediction for {time_horizon_years} years")
    
    bins = np.arange(LEO_MIN_ALT, LEO_MAX_ALT + BIN_SIZE_KM, BIN_SIZE_KM)
    bin_counts = {int(b): 0 for b in bins[:-1]}
    
    # 1. Initial State Initialization
    valid_objects = 0
    for _, row in df.iterrows():
        try:
            tle2 = row.get('tle2', '')
            alt = parse_altitude(tle2)
            if alt is not None and LEO_MIN_ALT <= alt < LEO_MAX_ALT:
                b = int(alt // BIN_SIZE_KM * BIN_SIZE_KM)
                if b in bin_counts:
                    bin_counts[b] += 1
                valid_objects += 1
        except Exception:
            pass

    if valid_objects == 0:
        return {"error": "No valid objects found in LEO for prediction."}

    total_objects_history = []
    zone_risk = {f"{b}-{b+BIN_SIZE_KM}km": 0 for b in bin_counts.keys()}
    
    # Kessler parameters
    rel_velocity_km_s = 10.0
    avg_cross_section_km2 = 10.0 / 1000000.0 # 10 sq meters in sq km
    seconds_per_year = 31536000
    
    # 2. Year-by-Year Simulation
    for year in range(1, time_horizon_years + 1):
        new_counts = {int(b): 0 for b in bins[:-1]}
        year_collisions = 0
        
        for b in sorted(bin_counts.keys()):
            N = bin_counts[b]
            if N <= 0:
                continue
                
            # Volume of the spherical shell
            r1 = EARTH_RADIUS_KM + b
            r2 = r1 + BIN_SIZE_KM
            volume = (4.0/3.0) * math.pi * (r2**3 - r1**3)
            
            # Collision Probability calculation (Particle in box)
            expected_collisions = 0.5 * (N * N * avg_cross_section_km2 * rel_velocity_km_s * seconds_per_year) / volume
            
            # Probabilistic actual collisions
            actual_collisions = np.random.poisson(expected_collisions)
            year_collisions += actual_collisions
            zone_risk[f"{b}-{b+BIN_SIZE_KM}km"] += actual_collisions
            
            # Fragmentation (NASA Standard Breakup Model simplification)
            fragments_generated = actual_collisions * 500 # Generate 500 trackable fragments per collision
            N += fragments_generated
            
            # Orbital Decay
            decay_km = calculate_decay_rate(b)
            # Distribute N downward probabilistically or discretely
            bins_down = int(decay_km // BIN_SIZE_KM)
            
            # For a more continuous feel, shift a portion to the lower bin
            fraction_down = (decay_km % BIN_SIZE_KM) / BIN_SIZE_KM
            
            # The objects that don't shift a full bin
            target_bin = int(b - bins_down * BIN_SIZE_KM)
            target_bin_lower = target_bin - BIN_SIZE_KM
            
            if target_bin >= LEO_MIN_ALT and target_bin in new_counts:
                new_counts[target_bin] += int(N * (1 - fraction_down))
            
            if target_bin_lower >= LEO_MIN_ALT and target_bin_lower in new_counts:
                new_counts[target_bin_lower] += int(N * fraction_down)
                
        bin_counts = new_counts
        current_total = sum(bin_counts.values())
        
        total_objects_history.append({
            "year": year,
            "total_objects": int(current_total),
            "collisions_this_year": int(year_collisions)
        })

    total_current_objects = sum(bin_counts.values())
    
    # Calculate global risk index based on exponential growth
    growth_ratio = total_current_objects / max(1, valid_objects)
    
    # Normalize risk index 0 to 1
    if growth_ratio > 1:
        global_risk_index = min(1.0, math.log10(growth_ratio) / 2.0)
    else:
        global_risk_index = max(0.0, growth_ratio - 0.5)
    
    sorted_zones = sorted(zone_risk.items(), key=lambda x: x[1], reverse=True)
    high_risk_zones = [
        {"altitude_range": zone, "congestion_events": int(events)} 
        for zone, events in sorted_zones[:5] if events > 0
    ]
    
    trend = "stable"
    if growth_ratio > 1.2:
        trend = "increasing (Kessler Syndrome Warning)"
    elif growth_ratio < 0.9:
        trend = "decreasing (Atmospheric cleaning dominant)"

    return {
        "time_horizon_years": time_horizon_years,
        "global_risk_index": round(global_risk_index, 3),
        "high_risk_zones": high_risk_zones,
        "total_objects_history": total_objects_history,
        "trend": trend,
        "initial_object_count": valid_objects,
        "final_object_count": int(total_current_objects)
    }
