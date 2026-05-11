from datetime import datetime, timedelta, timezone
from data_loader import load_catalogue
from propagator import compute_positions
import logging

logger = logging.getLogger(__name__)

class Simulator:
    """
    Core Simulation Orchestrator.
    Manages the master orbital catalog and advances the simulation time.
    Provides the propagated Cartesian positions for the 3D scene engine.
    """

    def __init__(self, csv_path):
        """Initializes the simulator and loads the initial dataset."""
        self.df = load_catalogue(csv_path)

        if self.df.empty:
            logger.error("Catalogue is empty. No objects loaded.")
        else:
            logger.info(f"Loaded {len(self.df)} orbital objects successfully.")

        # Set the starting time of the simulation to current UTC
        self.sim_time = datetime.now(timezone.utc)
        self.dv_remaining = 15.0

    def advance(self, minutes=1):
        """
        Advances the simulation clock by the specified delta and computes
        new SGP4 propagated positions for all objects.
        """
        self.sim_time += timedelta(minutes=minutes)

        # Compute SGP4 propagated Cartesian positions (x, y, z) and velocities (vx, vy, vz)
        pos_df = compute_positions(self.df, self.sim_time)
        logger.info(f"Propagated positions for {len(pos_df)} active objects.")

        return {
            'time': self.sim_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            'positions': pos_df.to_dict(orient='records'),
            'count': len(pos_df),
            'dv_remaining': round(self.dv_remaining, 2)
        }