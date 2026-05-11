import pandas as pd
import logging
import os
import glob
from skyfield.api import EarthSatellite, load

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ts = load.timescale()

def load_catalogue(data_path: str) -> pd.DataFrame:
    """
    Dynamically loads and validates TLE data from a single CSV or a directory of CSVs.
    Converts valid TLE pairs into precomputed Skyfield EarthSatellite objects.
    """
    try:
        csv_files = []
        if os.path.isdir(data_path):
            csv_files = glob.glob(os.path.join(data_path, "*.csv"))
            if not csv_files:
                logger.warning(f"No CSV files found in directory {data_path}")
                return pd.DataFrame()
        elif os.path.isfile(data_path):
            csv_files = [data_path]
        else:
            logger.error(f"Path does not exist: {data_path}")
            return pd.DataFrame()

        processed_data = []

        for csv_path in csv_files:
            logger.info(f"Ingesting dataset: {csv_path}")
            df_raw = pd.read_csv(csv_path)

            required = ['TLE_LINE1', 'TLE_LINE2', 'OBJECT_NAME', 'OBJECT_TYPE', 'NORAD_CAT_ID']
            if not all(col in df_raw.columns for col in required):
                logger.error(f"Missing mandatory columns in {csv_path}.")
                continue

            for _, row in df_raw.iterrows():
                try:
                    l1 = str(row['TLE_LINE1']).strip()
                    l2 = str(row['TLE_LINE2']).strip()

                    # Basic TLE syntax validation
                    if not l1.startswith("1 ") or not l2.startswith("2 "):
                        continue

                    processed_data.append({
                        'id': int(row['NORAD_CAT_ID']),
                        'name': str(row['OBJECT_NAME']).strip(),
                        'type': str(row['OBJECT_TYPE']).strip(),
                        'rcs_size': row.get('RCS_SIZE', 'UNKNOWN'),
                        'country': row.get('COUNTRY', 'UNKNOWN'),
                        'period': row.get('PERIOD', 0),
                        'sat_obj': EarthSatellite(l1, l2, str(row['OBJECT_NAME']).strip(), ts),
                        'tle1': l1,
                        'tle2': l2
                    })

                except Exception:
                    # Silently skip corrupted rows to maintain loading performance
                    continue

        df_final = pd.DataFrame(processed_data)
        
        if not df_final.empty:
            # Drop cross-file duplicates favoring the latest ingested record
            df_final.drop_duplicates(subset=['id'], keep='last', inplace=True)

        logger.info(f"Successfully loaded {len(df_final)} unique orbital objects.")
        return df_final

    except Exception as e:
        logger.error(f"Critical error during catalogue loading: {e}")
        return pd.DataFrame()