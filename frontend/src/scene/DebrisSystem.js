/**
 * AESH Debris System
 * Generates realistic 3D space debris: rocks, rocket bodies, satellite fragments.
 * Handles debris orbital propagation and collision detection.
 */

import * as THREE from 'three';

export const DEBRIS_COUNT = 40;

// ─── DEBRIS MESH TYPES ────────────────────────────────────────────────────────
// Each type uses a different procedural geometry to look distinct.

function makeRock(size) {
  // Irregular dodecahedron distorted = rock-like
  const geo = new THREE.DodecahedronGeometry(size, 0);
  const pos = geo.attributes.position;
  for (let i = 0; i < pos.count; i++) {
    pos.setXYZ(
      i,
      pos.getX(i) * (0.75 + Math.random() * 0.5),
      pos.getY(i) * (0.75 + Math.random() * 0.5),
      pos.getZ(i) * (0.75 + Math.random() * 0.5)
    );
  }
  geo.computeVertexNormals();
  return geo;
}

function makePanel(size) {
  // Old solar panel fragment – thin rectangle, slightly bent
  return new THREE.BoxGeometry(size * 2.5, size * 0.08, size * 1.2);
}

function makeRocketBody(size) {
  // Cylinder = spent rocket stage
  return new THREE.CylinderGeometry(size * 0.25, size * 0.3, size * 1.8, 10);
}

function makeShard(size) {
  // Tetrahedron = sharp metal fragment
  const geo = new THREE.TetrahedronGeometry(size, 0);
  const pos = geo.attributes.position;
  for (let i = 0; i < pos.count; i++) {
    pos.setXYZ(i, pos.getX(i) * (0.6 + Math.random() * 0.8),
                  pos.getY(i) * (0.6 + Math.random() * 0.8),
                  pos.getZ(i) * (0.6 + Math.random() * 0.8));
  }
  geo.computeVertexNormals();
  return geo;
}

const DEBRIS_TYPES = [
  { name: 'ROCK',        geo: makeRock,       mat: () => new THREE.MeshStandardMaterial({ color: 0x665544, roughness: 0.95, metalness: 0.1 }) },
  { name: 'PANEL',       geo: makePanel,      mat: () => new THREE.MeshStandardMaterial({ color: 0x334455, roughness: 0.3,  metalness: 0.8 }) },
  { name: 'ROCKET_BODY', geo: makeRocketBody, mat: () => new THREE.MeshStandardMaterial({ color: 0x888888, roughness: 0.6,  metalness: 0.7 }) },
  { name: 'SHARD',       geo: makeShard,      mat: () => new THREE.MeshStandardMaterial({ color: 0x997755, roughness: 0.7,  metalness: 0.5 }) },
];

// ─── BUILD DEBRIS ─────────────────────────────────────────────────────────────
export function buildDebrisField(scene, earthRadius) {
  const debrisList = [];

  for (let i = 0; i < DEBRIS_COUNT; i++) {
    const typeIdx = Math.floor(Math.random() * DEBRIS_TYPES.length);
    const type    = DEBRIS_TYPES[typeIdx];
    const size    = 0.06 + Math.random() * 0.18;

    const geo  = type.geo(size);
    const mat  = type.mat();
    const mesh = new THREE.Mesh(geo, mat);
    mesh.castShadow = true;

    // Random orbit: altitude between LEO and MEO in scene units
    const orbitRadius = earthRadius + 3 + Math.random() * 8;
    const inclination = (Math.random() - 0.5) * Math.PI;
    const raan        = Math.random() * Math.PI * 2;
    const anomaly     = Math.random() * Math.PI * 2;

    // Initial position
    const pos = new THREE.Vector3();
    computeDebrisPos(pos, raan, anomaly, inclination, orbitRadius);
    mesh.position.copy(pos);

    // Random spin rates for tumbling effect
    const spin = {
      x: (Math.random() - 0.5) * 0.04,
      y: (Math.random() - 0.5) * 0.06,
      z: (Math.random() - 0.5) * 0.04,
    };

    scene.add(mesh);

    debrisList.push({
      id:          i,
      mesh,
      type:        type.name,
      orbitRadius,
      inclination,
      raan,
      anomaly,
      spin,
      size,
      pos:         pos.clone(),
      active:      true, // false when destroyed
    });
  }

  return debrisList;
}

// ─── POSITION HELPER ─────────────────────────────────────────────────────────
export function computeDebrisPos(target, raan, anomaly, inc, r) {
  const cosR = Math.cos(raan), sinR = Math.sin(raan);
  const cosA = Math.cos(anomaly), sinA = Math.sin(anomaly);
  const cosI = Math.cos(inc), sinI = Math.sin(inc);

  target.x = r * (cosR * cosA - sinR * sinA * cosI);
  target.y = r * (sinA * sinI);
  target.z = r * (sinR * cosA + cosR * sinA * cosI);
}

// ─── PROPAGATE DEBRIS ────────────────────────────────────────────────────────
export function propagateDebris(debrisList, deltaT) {
  debrisList.forEach(d => {
    if (!d.active) return;

    // Orbital angular velocity (faster for lower orbits)
    const omega = Math.sqrt(1 / (d.orbitRadius ** 3)) * 18;
    d.anomaly += omega * deltaT;

    computeDebrisPos(d.pos, d.raan, d.anomaly, d.inclination, d.orbitRadius);
    d.mesh.position.copy(d.pos);

    // Tumbling rotation
    d.mesh.rotation.x += d.spin.x;
    d.mesh.rotation.y += d.spin.y;
    d.mesh.rotation.z += d.spin.z;
  });
}

// ─── COLLISION DETECTION ─────────────────────────────────────────────────────
/**
 * Check if activeSat (position vector) collides with any debris.
 * Returns the debris object that was hit, or null.
 * @param {THREE.Vector3} satPos
 * @param {Array} debrisList
 * @param {number} threshold — collision distance in scene units
 */
export function detectCollision(satPos, debrisList, threshold = 0.5) {
  for (const d of debrisList) {
    if (!d.active) continue;
    const dist = satPos.distanceTo(d.pos);
    if (dist < threshold) return d;
  }
  return null;
}

// ─── EXPLOSION PARTICLE SYSTEM ────────────────────────────────────────────────
export function createExplosion(scene, position) {
  const particles = [];

  // Core flash
  const flashGeo = new THREE.SphereGeometry(0.3, 16, 16);
  const flashMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 1 });
  const flash    = new THREE.Mesh(flashGeo, flashMat);
  flash.position.copy(position);
  scene.add(flash);
  particles.push({ mesh: flash, life: 1.0, type: 'flash' });

  // Orange fireball
  const fireGeo = new THREE.SphereGeometry(0.15, 12, 12);
  const fireMat = new THREE.MeshBasicMaterial({ color: 0xff6600, transparent: true, opacity: 0.9, blending: THREE.AdditiveBlending });
  const fire    = new THREE.Mesh(fireGeo, fireMat);
  fire.position.copy(position);
  scene.add(fire);
  particles.push({ mesh: fire, life: 1.0, type: 'fire' });

  // Shockwave ring
  const ringGeo = new THREE.TorusGeometry(0.1, 0.04, 16, 64);
  const ringMat = new THREE.MeshBasicMaterial({ color: 0xffaa44, transparent: true, opacity: 0.9, blending: THREE.AdditiveBlending, side: THREE.DoubleSide });
  const ring = new THREE.Mesh(ringGeo, ringMat);
  ring.position.copy(position);
  ring.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, 0);
  scene.add(ring);
  particles.push({ mesh: ring, life: 1.0, type: 'shockwave' });

  // Shrapnel chunks (20–30 pieces for dramatic effect)
  const shrapnelCount = 20 + Math.floor(Math.random() * 10);
  for (let i = 0; i < shrapnelCount; i++) {
    const sGeo = new THREE.TetrahedronGeometry(0.04 + Math.random() * 0.08, 0);
    const sMat = new THREE.MeshStandardMaterial({
      color: Math.random() > 0.5 ? 0xffaa33 : 0x888888,
      emissive: 0xff4400, emissiveIntensity: 0.5,
    });
    const shard = new THREE.Mesh(sGeo, sMat);
    shard.position.copy(position);
    scene.add(shard);

    const velocity = new THREE.Vector3(
      (Math.random() - 0.5) * 0.15,
      (Math.random() - 0.5) * 0.15,
      (Math.random() - 0.5) * 0.15,
    );
    particles.push({ mesh: shard, velocity, life: 1.0, type: 'shard', spin: (Math.random() - 0.5) * 0.3 });
  }

  // Smoke puffs (translucent spheres)
  for (let i = 0; i < 6; i++) {
    const smokeGeo = new THREE.SphereGeometry(0.08 + Math.random() * 0.12, 8, 8);
    const smokeMat = new THREE.MeshBasicMaterial({
      color: 0x444444, transparent: true, opacity: 0.5,
      blending: THREE.AdditiveBlending, depthWrite: false,
    });
    const smoke = new THREE.Mesh(smokeGeo, smokeMat);
    smoke.position.copy(position);
    scene.add(smoke);

    const vel = new THREE.Vector3(
      (Math.random() - 0.5) * 0.08,
      (Math.random() - 0.5) * 0.08,
      (Math.random() - 0.5) * 0.08,
    );
    particles.push({ mesh: smoke, velocity: vel, life: 1.0, type: 'smoke' });
  }

  return particles;
}

// ─── ANIMATE EXPLOSION ────────────────────────────────────────────────────────
/**
 * Call every frame.  Returns true while still alive.
 */
export function tickExplosion(particles, scene) {
  let anyAlive = false;

  particles.forEach(p => {
    if (p.life <= 0) {
      if (!p._removed) { scene.remove(p.mesh); p._removed = true; }
      return;
    }

    p.life -= 0.025;
    anyAlive = true;

    if (p.type === 'flash') {
      p.mesh.scale.setScalar(1 + (1 - p.life) * 8);
      p.mesh.material.opacity = p.life * p.life;
    }
    if (p.type === 'fire') {
      p.mesh.scale.setScalar(1 + (1 - p.life) * 6);
      p.mesh.material.opacity = p.life * 0.9;
    }
    if (p.type === 'shockwave') {
      p.mesh.scale.setScalar(1 + (1 - p.life) * 35);
      p.mesh.material.opacity = p.life * p.life;
    }
    if (p.type === 'shard') {
      p.mesh.position.addScaledVector(p.velocity, 1);
      p.mesh.rotation.y += p.spin;
      p.mesh.material.emissiveIntensity = p.life * 0.5;
      if (p.life < 0.4) p.mesh.material.opacity = p.life / 0.4;
    }
    if (p.type === 'smoke') {
      p.mesh.position.addScaledVector(p.velocity, 1);
      p.mesh.scale.setScalar(1 + (1 - p.life) * 3);
      p.mesh.material.opacity = p.life * 0.4;
    }
  });

  return anyAlive;
}
