from datetime import datetime, timedelta, timezone
from data_loader import load_catalogue
from propagator import compute_positions
from collision_detector import detect_risk

import logging

logger = logging.getLogger(__name__)

class Simulator:

    def __init__(self, csv_path):

        self.df = load_catalogue(csv_path)

        if self.df.empty:
            logger.error("❌ Catalogue is empty.")
        else:
            logger.info(f"✅ Loaded {len(self.df)} orbital objects.")

        self.sim_time = datetime.now(timezone.utc)

        self.dv_remaining = 15.0

    def advance(self, minutes=1):

        self.sim_time += timedelta(minutes=minutes)

        # Compute propagated positions
        pos_df = compute_positions(
            self.df,
            self.sim_time
        )

        logger.info(
            f"🛰️ Propagated objects: {len(pos_df)}"
        )

        # Collision analysis
        risks = detect_risk(pos_df)

        return {

            'time': self.sim_time.strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            ),

            # IMPORTANT:
            # Must be JSON serializable
            'positions': pos_df.to_dict(
                orient='records'
            ),

            'count': len(pos_df),

            'dv_remaining': round(
                self.dv_remaining,
                2
            ),

            'alerts': risks[:10]
        }