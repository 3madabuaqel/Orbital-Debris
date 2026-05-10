import * as THREE from 'three';

// Use the same scale as your backend (usually 1 unit = 1km or scaled)
export const EARTH_RADIUS = 15; 
const SCALE_FACTOR = 0.0023; // Adjust this to fit your Earth model size

/**
 * This class handles the connection to the FastAPI WebSocket
 * and manages the 10,000 objects.
 * 
 * DEPRECATED: Do not use individual THREE.Mesh objects for each satellite.
 * It will crash the browser for datasets > 10,000. Use BufferGeometry instead.
 * See OrbitalScene.vue for the correct implementation.
 */
export class OrbitalManager {
    constructor(scene) {
        this.scene = scene;
        this.satellites = new Map(); // Store objects by ID for quick access
        this.socket = null;
    }

    connect() {
        console.warn("OrbitalManager is deprecated. Use BufferGeometry in OrbitalScene.vue instead.");
    }
}