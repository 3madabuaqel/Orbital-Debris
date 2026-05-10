from scipy.spatial import KDTree
import numpy as np

def detect_risk(positions_df, risk_radius=5.0):
    """Detects conjunctions within the risk_radius (km)."""
    df = positions_df.dropna(subset=['x','y','z'])
    if len(df) < 2: return []
    
    coords = df[['x','y','z']].values
    tree = KDTree(coords)
    pairs = tree.query_pairs(r=risk_radius)
    
    events = []
    for i, j in pairs:
        a, b = df.iloc[i], df.iloc[j]
        dist = np.linalg.norm(coords[i] - coords[j])
        events.append({
            'obj1': a['name'], 
            'obj2': b['name'],
            'distance': float(dist),
            'risk': 'HIGH' if dist < 1.0 else 'MEDIUM'
        })
    return sorted(events, key=lambda x: x['distance'])
