import numpy as np
from skyfield.api import EarthSatellite, load
from datetime import datetime, timedelta

ts = load.timescale()

def plan_manoeuvre(sat_tle: tuple, threat_tle: tuple, current_time: datetime, tca_time: datetime, max_dv: float = 0.1):
    """
    Calculate an optimal avoidance burn to maximize miss distance at Time of Closest Approach (TCA).
    
    sat_tle: (line1, line2) of the protected satellite
    threat_tle: (line1, line2) of the debris
    current_time: Time of execution
    tca_time: Predicted time of closest approach
    max_dv: Maximum delta-V allowed in km/s (0.1 km/s = 100 m/s is quite high for cold gas, usually 0.1 m/s)
    """
    # Note: max_dv in prompt was 0.1 m/s, but the snippet used km/s. 
    # Let's stick to SI units for internal math where possible, then convert.
    # The prompt says max_dv = 0.1 m/s (0.0001 km/s).
    
    # Actually, the snippet in the prompt says: max_dv=0.1 (likely m/s)
    # But then it does: dv_magnitude_m_s = np.linalg.norm(best_dv) * 1000 (meaning best_dv was in km/s)
    # I will use km/s for best_dv to be consistent with Skyfield.
    
    # Correcting max_dv for cold gas: 0.1 m/s = 0.0001 km/s
    MAX_DV_KMS = 0.0001 
    
    sat_sf = EarthSatellite(sat_tle[0], sat_tle[1])
    threat_sf = EarthSatellite(threat_tle[0], threat_tle[1])
    
    t_burn = ts.utc(current_time.year, current_time.month, current_time.day,
                    current_time.hour, current_time.minute, current_time.second)
    t_tca = ts.utc(tca_time.year, tca_time.month, tca_time.day,
                   tca_time.hour, tca_time.minute, tca_time.second)
    
    # Original states at TCA
    pos_sat_orig = sat_sf.at(t_tca).position.km
    pos_threat = threat_sf.at(t_tca).position.km
    miss_orig = np.linalg.norm(pos_sat_orig - pos_threat)
    
    # Velocity at burn epoch (In-track direction)
    state_burn = sat_sf.at(t_burn)
    vel_burn = state_burn.velocity.km_per_s
    v_unit = vel_burn / np.linalg.norm(vel_burn)
    
    # Cross-track direction
    r_unit = state_burn.position.km / np.linalg.norm(state_burn.position.km)
    cross_unit = np.cross(r_unit, v_unit)
    cross_unit /= np.linalg.norm(cross_unit)
    
    # Radial direction
    radial_unit = np.cross(v_unit, cross_unit)
    
    best_dv_vector = None
    best_miss = miss_orig
    
    # Search grid for optimal burn direction
    # We try In-track, Anti-track, Radial, Anti-radial, Cross-track, Anti-cross-track
    directions = [v_unit, -v_unit, radial_unit, -radial_unit, cross_unit, -cross_unit]
    
    delta_t_sec = (tca_time - current_time).total_seconds()
    
    for direction in directions:
        for dv_mag in [MAX_DV_KMS * 0.5, MAX_DV_KMS]:
            dv_vec = direction * dv_mag
            
            # Linear approximation of displacement at TCA: delta_r = delta_v * delta_t
            # This is a first-order approximation (Clohessy-Wiltshire like)
            delta_r = dv_vec * delta_t_sec
            new_pos_sat = pos_sat_orig + delta_r
            new_miss = np.linalg.norm(new_pos_sat - pos_threat)
            
            if new_miss > best_miss:
                best_miss = new_miss
                best_dv_vector = dv_vec
                
    if best_dv_vector is None:
        return None
    
    dv_mag_m_s = np.linalg.norm(best_dv_vector) * 1000.0
    
    # Fuel Model (Cold Gas GN2, Isp=70s)
    m0 = 100.0 # kg dry mass
    g0 = 9.80665
    Isp = 70.0
    # Rocket Equation: delta_m = m0 * (1 - exp(-dv / (Isp * g0)))
    fuel_used_kg = m0 * (1 - np.exp(-dv_mag_m_s / (Isp * g0)))
    
    return {
        'timestamp': current_time.isoformat(),
        'dv_vector_kms': best_dv_vector.tolist(),
        'dv_magnitude_m_s': float(dv_mag_m_s),
        'new_miss_distance_km': float(best_miss),
        'fuel_used_kg': float(fuel_used_kg),
        'direction': "In-track" if np.dot(best_dv_vector, v_unit) > 0 else "Optimal"
    }
