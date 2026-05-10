import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import os
import glob
from skyfield.api import EarthSatellite, load

ts = load.timescale()

def load_catalogue(data_path: str) -> pd.DataFrame:
    """
    Load and validate TLE catalogue from a directory of CSVs or a single CSV.
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
            logger.info(f"Reading dataset: {csv_path}")
            df_raw = pd.read_csv(csv_path)

            required = [
                'TLE_LINE1',
                'TLE_LINE2',
                'OBJECT_NAME',
                'OBJECT_TYPE',
                'NORAD_CAT_ID'
            ]

            if not all(col in df_raw.columns for col in required):
                logger.error(f"Missing mandatory columns in {csv_path}. Found: {list(df_raw.columns)}")
                continue

            for _, row in df_raw.iterrows():
                try:
                    l1 = str(row['TLE_LINE1']).strip()
                    l2 = str(row['TLE_LINE2']).strip()

                    # Basic TLE validation
                    if not l1.startswith("1 ") or not l2.startswith("2 "):
                        continue

                    processed_data.append({
                        'id': int(row['NORAD_CAT_ID']),
                        'name': str(row['OBJECT_NAME']).strip(),
                        'type': str(row['OBJECT_TYPE']).strip(),
                        'rcs_size': row.get('RCS_SIZE', 'UNKNOWN'),
                        'country': row.get('COUNTRY', 'UNKNOWN'),
                        'period': row.get('PERIOD', 0),

                        # Precompute Skyfield satellite object
                        'sat_obj': EarthSatellite(l1, l2, str(row['OBJECT_NAME']).strip(), ts),

                        # Keep raw TLE only
                        'tle1': l1,
                        'tle2': l2
                    })

                except Exception as e:
                    # Silently skip corrupted row
                    continue

        df_final = pd.DataFrame(processed_data)
        
        if not df_final.empty:
            # Remove duplicates in case multiple CSVs contain the same satellite ID
            df_final.drop_duplicates(subset=['id'], keep='last', inplace=True)

        logger.info(
            f"✅ Successfully loaded {len(df_final)} unique "
            f"orbital objects from {len(csv_files)} files."
        )

        return df_final

    except Exception as e:
        logger.error(f"❌ Critical error during catalogue loading: {e}")
        return pd.DataFrame()