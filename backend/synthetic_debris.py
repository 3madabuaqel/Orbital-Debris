import numpy as np

def generate_synthetic_debris(sat_pos, sat_vel, count=50, radius=50.0):
    """
    Generate synthetic debris particles within a sphere of 'radius' km around the satellite.
    Simulates on-board radar/lidar detections of uncatalogued small debris.
    
    sat_pos: numpy array (3,) - ECI position in km
    sat_vel: numpy array (3,) - ECI velocity in km/s
    """
    debris = []
    for i in range(count):
        # Uniform volumetric distribution in a sphere
        # 1. Random direction
        direction = np.random.normal(size=3)
        direction /= np.linalg.norm(direction)
        
        # 2. Random distance with cubic root for uniform volume density
        dist = radius * (np.random.random() ** (1/3))
        
        pos = sat_pos + direction * dist
        
        # Velocity: Realistic LEO speed (~7.5 km/s) with random direction
        # In a real scenario, debris velocity is constrained by orbital mechanics,
        # but for short-range simulation, a random vector around the orbital speed is a good proxy.
        v_dir = np.random.normal(size=3)
        v_dir /= np.linalg.norm(v_dir)
        
        # Mean speed of 7.5 km/s with 0.5 km/s std dev
        speed = 7.5 + 0.5 * np.random.randn()
        vel = v_dir * speed
        
        debris.append({
            'id': f'SYNTH_{i}',
            'name': f'Small Debris {i}',
            'type': 'SYNTHETIC_DEBRIS',
            'x': pos[0],
            'y': pos[1],
            'z': pos[2],
            'vx': vel[0],
            'vy': vel[1],
            'vz': vel[2],
            'lat': 0.0, # Will be calculated if needed, or ignored for local relative viz
            'lon': 0.0,
            'alt_km': np.linalg.norm(pos) - 6371.0 # Simple altitude approx
        })
        
    return debris
