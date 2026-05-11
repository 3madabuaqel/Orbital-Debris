import * as THREE from 'three';
import * as BufferGeometryUtils from 'three/examples/jsm/utils/BufferGeometryUtils.js';

const TEXTURES = {
  earth: 'https://raw.githubusercontent.com/mrdoob/three.js/master/examples/textures/planets/earth_atmos_2048.jpg',
  earthSpec: 'https://raw.githubusercontent.com/mrdoob/three.js/master/examples/textures/planets/earth_specular_2048.jpg',
  earthCloud: 'https://raw.githubusercontent.com/mrdoob/three.js/master/examples/textures/planets/earth_clouds_1024.png',
};

// ───────────────────────────── EARTH ─────────────────────────────
export function buildEarth(scene, EARTH_RADIUS) {
  const loader = new THREE.TextureLoader();

  const earth = new THREE.Mesh(
    new THREE.SphereGeometry(EARTH_RADIUS, 128, 128),
    new THREE.MeshPhongMaterial({
      map: loader.load(TEXTURES.earth),
      specularMap: loader.load(TEXTURES.earthSpec),
      bumpMap: loader.load(TEXTURES.earthSpec),
      bumpScale: 0.6,
      specular: new THREE.Color(0x4466cc),
      shininess: 45,
    })
  );
  scene.add(earth);

  const clouds = new THREE.Mesh(
    new THREE.SphereGeometry(EARTH_RADIUS + 0.12, 64, 64),
    new THREE.MeshPhongMaterial({
      map: loader.load(TEXTURES.earthCloud),
      transparent: true,
      opacity: 0.85,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    })
  );
  earth.add(clouds);

  const atmo = new THREE.Mesh(
    new THREE.SphereGeometry(EARTH_RADIUS + 0.8, 64, 64),
    new THREE.MeshPhongMaterial({
      color: 0x1133aa,
      side: THREE.BackSide,
      transparent: true,
      opacity: 0.08,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    })
  );
  scene.add(atmo);

  const grid = new THREE.PolarGridHelper(
    EARTH_RADIUS * 4,
    32,
    16,
    64,
    0x112244,
    0x081122
  );

  grid.material.transparent = true;
  grid.material.opacity = 0.4;

  scene.add(grid);

  return { earth, clouds };
}

// ───────────────────────────── LIGHTS ─────────────────────────────
export function buildLights(scene) {
  const sun = new THREE.DirectionalLight(0xffffff, 4.5);
  sun.position.set(150, 30, 80);
  scene.add(sun);

  const fill = new THREE.DirectionalLight(0x4466ff, 0.4);
  fill.position.set(-100, -20, -60);
  scene.add(fill);

  scene.add(new THREE.AmbientLight(0x0a101d, 1.2));
}

// ───────────────────────────── STARFIELD ─────────────────────────────
export function buildStarfield(scene) {
  const verts = [];
  const colors = [];
  const color = new THREE.Color();

  for (let i = 0; i < 12000; i++) {
    const r = 2000 + Math.random() * 1000;

    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);

    const x = r * Math.sin(phi) * Math.cos(theta);
    const y = r * Math.cos(phi);
    const z = r * Math.sin(phi) * Math.sin(theta);

    verts.push(x, y, z);

    const t = Math.random();
    if (t > 0.9) color.setHex(0xffaa88);
    else if (t > 0.8) color.setHex(0x88ccff);
    else color.setHex(0xffffff);

    colors.push(color.r, color.g, color.b);
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(verts, 3));
  geo.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));

  const mat = new THREE.PointsMaterial({
    size: 2,
    sizeAttenuation: false,
    vertexColors: true,
  });

  scene.add(new THREE.Points(geo, mat));
}

// ───────────────────────────── DETAILED 3D GEOMETRIES ─────────────────────────────
function createSatelliteGeometry() {
  const bodyGeo = new THREE.BoxGeometry(0.6, 0.6, 0.6);
  
  const panel1 = new THREE.BoxGeometry(1.8, 0.05, 0.4);
  panel1.translate(1.2, 0, 0);
  
  const panel2 = new THREE.BoxGeometry(1.8, 0.05, 0.4);
  panel2.translate(-1.2, 0, 0);
  
  const merged = BufferGeometryUtils.mergeGeometries([bodyGeo, panel1, panel2]);
  return merged;
}

function createRocketGeometry() {
  const stage = new THREE.CylinderGeometry(0.2, 0.2, 1.2, 16);
  
  const cone = new THREE.ConeGeometry(0.2, 0.4, 16);
  cone.translate(0, 0.8, 0);
  
  const nozzle = new THREE.CylinderGeometry(0.15, 0.05, 0.3, 16);
  nozzle.translate(0, -0.75, 0);
  
  const merged = BufferGeometryUtils.mergeGeometries([stage, cone, nozzle]);
  return merged;
}

function createDebrisGeometry() {
  const t1 = new THREE.TetrahedronGeometry(0.4, 0);
  
  const t2 = new THREE.TetrahedronGeometry(0.3, 0);
  t2.rotateX(Math.PI / 4);
  t2.translate(0.2, 0.1, -0.1);
  
  const t3 = new THREE.TetrahedronGeometry(0.25, 0);
  t3.rotateY(Math.PI / 3);
  t3.translate(-0.1, -0.2, 0.2);
  
  const merged = BufferGeometryUtils.mergeGeometries([t1, t2, t3]);
  return merged;
}

// ───────────────────────────── INSTANCED SATELLITES ─────────────────────────────
export function buildInstancedSatellites(scene, counts) {
  const dummy = new THREE.Object3D();
  dummy.scale.set(0, 0, 0);
  dummy.updateMatrix();

  // 1. Payloads -> Realistic Satellite
  const payloadGeo = createSatelliteGeometry();
  const payloadMat = new THREE.MeshPhongMaterial({ 
    color: 0x88ccff, emissive: 0x112244, shininess: 100 
  });
  const payloadMesh = new THREE.InstancedMesh(payloadGeo, payloadMat, counts.payload);
  payloadMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  payloadMesh.frustumCulled = false;
  scene.add(payloadMesh);

  // 2. Rocket Bodies -> Realistic Rocket Stage
  const rocketGeo = createRocketGeometry();
  const rocketMat = new THREE.MeshPhongMaterial({ 
    color: 0xffaa00, emissive: 0x442200, shininess: 80 
  });
  const rocketMesh = new THREE.InstancedMesh(rocketGeo, rocketMat, counts.rocket);
  rocketMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  rocketMesh.frustumCulled = false;
  scene.add(rocketMesh);

  // 3. Debris -> Realistic Jagged Fragments
  const debrisGeo = createDebrisGeometry();
  const debrisMat = new THREE.MeshPhongMaterial({ 
    color: 0xaaaaaa, emissive: 0x222222, shininess: 50 
  });
  const debrisMesh = new THREE.InstancedMesh(debrisGeo, debrisMat, counts.debris);
  debrisMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  debrisMesh.frustumCulled = false;
  scene.add(debrisMesh);

  for (let i = 0; i < counts.payload; i++) payloadMesh.setMatrixAt(i, dummy.matrix);
  for (let i = 0; i < counts.rocket; i++) rocketMesh.setMatrixAt(i, dummy.matrix);
  for (let i = 0; i < counts.debris; i++) debrisMesh.setMatrixAt(i, dummy.matrix);

  payloadMesh.instanceMatrix.needsUpdate = true;
  rocketMesh.instanceMatrix.needsUpdate = true;
  debrisMesh.instanceMatrix.needsUpdate = true;

  return { payloadMesh, rocketMesh, debrisMesh };
}
// ───────────────────────────── CUBE SAT ─────────────────────────────
export function buildCubeSat(scene) {
  const group = new THREE.Group();

  const body = new THREE.Mesh(
    new THREE.BoxGeometry(0.7, 0.7, 0.9),
    new THREE.MeshStandardMaterial({
      color: 0x111111,
      metalness: 0.9,
      roughness: 0.3,
    })
  );

  group.add(body);

  const solar = new THREE.Mesh(
    new THREE.BoxGeometry(2, 0.6, 0.05),
    new THREE.MeshStandardMaterial({
      color: 0x091828,
      metalness: 0.5,
      roughness: 0.1,
    })
  );

  solar.position.x = 1.4;
  group.add(solar);

  const solar2 = solar.clone();
  solar2.position.x = -1.4;
  group.add(solar2);

  group.scale.setScalar(0.6);
  group.visible = false;

  scene.add(group);
  return group;
}