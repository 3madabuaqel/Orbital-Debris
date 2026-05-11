import math
from skyfield.api import EarthSatellite, load
import pandas as pd
import logging

ts = load.timescale()

logger = logging.getLogger(__name__)

def compute_positions(df, utc_datetime):
    """
    Computes precise spatial positions and velocity vectors for all orbital objects 
    at a specific UTC time using the SGP4 mathematical model.
    Filters out decayed or invalid objects.
    """
    t = ts.utc(
        utc_datetime.year,
        utc_datetime.month,
        utc_datetime.day,
        utc_datetime.hour,
        utc_datetime.minute,
        utc_datetime.second
    )

    results = []

    for sat_obj, sat_id, name, type_val, country, rcs, period in zip(
        df['sat_obj'], df['id'], df['name'], df['type'], df['country'], df['rcs_size'], df['period']
    ):
        try:
            geo = sat_obj.at(t)
            
            # Cartesian coordinates in km
            pos = geo.position.km
            vel = geo.velocity.km_per_s
            
            # Check for NaN (decayed satellite or invalid TLE for this time)
            if math.isnan(pos[0]) or math.isnan(pos[1]) or math.isnan(pos[2]):
                continue

            sub = geo.subpoint()
            v_mag = math.sqrt(vel[0]**2 + vel[1]**2 + vel[2]**2)

            # High-fidelity TLE elements from sgp4 model
            model = sat_obj.model
            inclination = math.degrees(model.inclo)
            eccentricity = model.ecco
            raan = math.degrees(model.nodeo)
            arg_pe = math.degrees(model.argpo)

            def clean_float(val):
                if val is None or math.isnan(val):
                    return None
                return float(val)

            results.append({
                'id': sat_id,
                'name': name,
                'type': type_val,

                'lat': clean_float(sub.latitude.degrees),
                'lon': clean_float(sub.longitude.degrees),
                'alt': clean_float(sub.elevation.km),
                'vel': clean_float(v_mag),

                # Cartesian coordinates
                'x': clean_float(pos[0]),
                'y': clean_float(pos[1]),
                'z': clean_float(pos[2]),
                
                # Cartesian velocity vectors
                'vx': clean_float(vel[0]),
                'vy': clean_float(vel[1]),
                'vz': clean_float(vel[2]),
                
                # High-fidelity parameters for UI
                'inclination': clean_float(inclination),
                'eccentricity': clean_float(eccentricity),
                'raan': clean_float(raan),
                'arg_pe': clean_float(arg_pe),

                # Additional details for UI
                'country': country if country and str(country) != 'nan' else 'UNKNOWN',
                'rcs_size': rcs if rcs and str(rcs) != 'nan' else 'UNKNOWN',
                'period': clean_float(period)
            })

        except Exception as e:
            pass # Keep it fast, skip failed ones silently instead of logging thousands of errors

    return pd.DataFrame(results)