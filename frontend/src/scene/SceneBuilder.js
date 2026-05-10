import * as THREE from 'three';

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

// ───────────────────────────── SATELLITE CLOUD (FIXED) ─────────────────────────────
export function buildSatelliteCloud(scene, count) {
  const geometry = new THREE.BufferGeometry();

  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);

  for (let i = 0; i < count; i++) {
    positions[i * 3] = 0;
    positions[i * 3 + 1] = 0;
    positions[i * 3 + 2] = 0;

    // default hidden color
    colors[i * 3] = 0;
    colors[i * 3 + 1] = 0;
    colors[i * 3 + 2] = 0;
  }

  geometry.setAttribute(
    'position',
    new THREE.BufferAttribute(positions, 3)
  );

  geometry.setAttribute(
    'color',
    new THREE.BufferAttribute(colors, 3)
  );

  const material = new THREE.PointsMaterial({
    size: 0.4,
    sizeAttenuation: true,
    vertexColors: true,
    transparent: true,
    opacity: 1.0,
    depthWrite: false
  });

  const points = new THREE.Points(geometry, material);

  points.frustumCulled = false; // 🔥 مهم جدًا (يمنع اختفاء النقاط)

  scene.add(points);

  return points;
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