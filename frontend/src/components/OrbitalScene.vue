<template>
  <div style="position:relative;width:100%;height:100vh;overflow:hidden;background:#050508;">
    <div ref="canvasMount" style="position:absolute;inset:0;"></div>

    <GlobalHUD
      v-if="!activeSat && !isExploding"
      :satellites="satellites"
      :time="utcTime"
      :debris-count="currentDebrisCount"
      :risk-level="'NOMINAL'"
      @select="enterCockpit"
      @layer-change="onLayerChange"
      @simulate-start="timeScale = 30"
      @simulate-end="timeScale = 1"
    />

    <CockpitHUD
      v-if="activeSat && !isExploding"
      :sat="activeSat"
      :time="utcTime"
      @exit="exitCockpit"
    />

    <div v-if="isExploding" class="collision-overlay">
      <div style="text-align:center;">
        <div class="alert-text">⚠ CRITICAL ALERT</div>
        <div class="collision-title">COLLISION EVENT DETECTED</div>
        <button @click="resetAfterCollision" class="return-btn">
          RETURN TO GLOBAL VIEW
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, shallowRef, onMounted, onUnmounted } from 'vue';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import gsap from 'gsap';

import GlobalHUD from './GlobalHUD.vue';
import CockpitHUD from './CockpitHUD.vue';

import { EARTH_RADIUS } from '../physics/OrbitalPhysics.js';
import { buildEarth, buildLights, buildStarfield, buildSatelliteCloud, buildCubeSat } from '../scene/SceneBuilder.js';
import { tickExplosion } from '../scene/DebrisSystem.js';

// 30 (Earth Mesh Radius) / 6371 (Earth Actual Radius in km)
const SCALE_FACTOR = 0.004708837; 

const canvasMount = ref(null);
const satellites = shallowRef([]);
const activeSat = ref(null);
const utcTime = ref('');
const isExploding = ref(false);
const timeScale = ref(1);
const socket = ref(null);
const rawOrbitalData = shallowRef([]);
const currentDebrisCount = ref(0);

const activeLayers = ref({
  satellites: true,
  debris: true,
  orbits: false
});

let scene, camera, renderer, controls, earth, clouds, satPoints, cubeSat;
let explosionParticles = [];
let lastSatPos = new THREE.Vector3();
let raycaster = new THREE.Raycaster();
let mouse = new THREE.Vector2();
let frameCount = 0;
let cockpitMode = false;
let isWaitingForFrame = false;

raycaster.params.Points.threshold = 0.15;

onMounted(() => {
  initThree();
  buildScene();
  connectToBackend();
  startRenderLoop();

  window.addEventListener('resize', onResize);
  window.addEventListener('mousemove', onMouseMove);
  canvasMount.value.addEventListener('click', onCanvasClick);
});

onUnmounted(() => {
  window.removeEventListener('resize', onResize);
  window.removeEventListener('mousemove', onMouseMove);
  socket.value?.close();
  renderer?.dispose();
});

function initThree() {
  scene = new THREE.Scene();

  camera = new THREE.PerspectiveCamera(
    45,
    window.innerWidth / window.innerHeight,
    0.1,
    10000
  );
  camera.position.set(0, 80, 200);
  camera.lookAt(0, 0, 0);

  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(window.innerWidth, window.innerHeight);
  canvasMount.value.appendChild(renderer.domElement);

  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
}

function buildScene() {
  buildLights(scene);
  buildStarfield(scene);

  const earthObjs = buildEarth(scene, EARTH_RADIUS);
  earth = earthObjs.earth;
  clouds = earthObjs.clouds;

  // Initially empty, will be rebuilt when data arrives
  satPoints = buildSatelliteCloud(scene, 0);

  cubeSat = buildCubeSat(scene);
  cubeSat.visible = false;
}

function connectToBackend() {
  socket.value = new WebSocket('ws://127.0.0.1:8000/ws');

  socket.value.onopen = () => {
    console.log("WebSocket connected");
  };

let hasMappedSatellites = false;

// ...

socket.value.onmessage = (event) => {
  isWaitingForFrame = false;
  let data;
  try {
    data = JSON.parse(event.data);
  } catch (e) {
    return;
  }

  if (!data.positions) {
    return;
  }

  rawOrbitalData.value = data.positions;
};
}

function startRenderLoop() {
  renderer.setAnimationLoop(tick);
}

function tick() {
  frameCount++;

  const now = new Date();
  utcTime.value = now.toISOString().substring(11, 19) + " UTC";

  // Request new data only if backend finished previous request
  if (
    socket.value?.readyState === WebSocket.OPEN &&
    !isWaitingForFrame &&
    frameCount % 10 === 0
  ) {
    isWaitingForFrame = true;
    socket.value.send(
      JSON.stringify({
        action: 'advance',
        minutes: timeScale.value
      })
    );
  }

  if (rawOrbitalData.value?.length > 0) {
    updatePoints();
    
    // Sync Vue UI state synchronously with the render loop
    currentDebrisCount.value = rawOrbitalData.value.length;
    if (satellites.value.length === 0 || frameCount % 60 === 0) {
      satellites.value = rawOrbitalData.value;
    }
  }

  if (cockpitMode && activeSat.value) {
    cubeSat.position.copy(activeSat.value.pos);
    controls.target.copy(activeSat.value.pos);
  }

  if (earth) earth.rotation.y += 0.0001;
  if (clouds) clouds.rotation.y += 0.00015;

  if (explosionParticles.length > 0)
    tickExplosion(explosionParticles, scene);

  controls.update();
  renderer.render(scene, camera);
}

function updatePoints() {
  const data = rawOrbitalData.value;
  if (!data || data.length === 0) return;

  const currentCount = satPoints ? satPoints.geometry.attributes.position.count : 0;
  
  if (currentCount !== data.length) {
    if (satPoints) {
        scene.remove(satPoints);
        satPoints.geometry.dispose();
        satPoints.material.dispose();
    }
    satPoints = buildSatelliteCloud(scene, data.length);
    satPoints.visible = !cockpitMode;
  }

  const positions = satPoints.geometry.attributes.position.array;
  const colors = satPoints.geometry.attributes.color.array;

  for (let i = 0; i < data.length; i++) {
    const sat = data[i];

    if (sat) {
      // 👁️ Layer Visibility
      let isVisible = true;
      if (sat.type === "PAYLOAD" && !activeLayers.value.satellites) isVisible = false;
      if (sat.type !== "PAYLOAD" && !activeLayers.value.debris) isVisible = false;

      if (!isVisible) {
        // Hide by collapsing to origin
        positions[i * 3] = 0;
        positions[i * 3 + 1] = 0;
        positions[i * 3 + 2] = 0;
        continue;
      }

      const x = sat.x * SCALE_FACTOR;
      const y = sat.y * SCALE_FACTOR;
      const z = sat.z * SCALE_FACTOR;

      positions[i * 3] = x;
      positions[i * 3 + 1] = y;
      positions[i * 3 + 2] = z;

      // 🎨 coloring حسب النوع
      if (sat.type === "PAYLOAD") {
        colors[i * 3] = 0.2;
        colors[i * 3 + 1] = 0.8;
        colors[i * 3 + 2] = 1.0;
      } else {
        colors[i * 3] = 1.0;
        colors[i * 3 + 1] = 1.0;
        colors[i * 3 + 2] = 0.2;
      }
    }
  }

  satPoints.geometry.attributes.position.needsUpdate = true;
  satPoints.geometry.attributes.color.needsUpdate = true;
}

function enterCockpit(sat) {
  const target = new THREE.Vector3(
    sat.x * SCALE_FACTOR,
    sat.y * SCALE_FACTOR,
    sat.z * SCALE_FACTOR
  );

  activeSat.value = { ...sat, pos: target.clone() };
  cockpitMode = true;

  cubeSat.visible = true;
  satPoints.visible = false;

  gsap.to(camera.position, {
    x: target.x + 5,
    y: target.y + 2,
    z: target.z + 5,
    duration: 2
  });
}

function exitCockpit() {
  cockpitMode = false;
  activeSat.value = null;

  cubeSat.visible = false;
  satPoints.visible = true;

  gsap.to(camera.position, {
    x: 0,
    y: 150,
    z: 400,
    duration: 2
  });
}

function onCanvasClick() {
  if (cockpitMode) return;

  raycaster.setFromCamera(mouse, camera);

  const intersects = raycaster.intersectObject(satPoints);

  if (intersects.length > 0) {
    const sat = rawOrbitalData.value[intersects[0].index];

    if (sat) {
      enterCockpit(sat);
    }
  }
}

function onMouseMove(e) {
  mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
  mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
}

function onResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}

function resetAfterCollision() {
  isExploding.value = false;
  exitCockpit();
}

function onLayerChange(layers) {
  activeLayers.value = { ...layers };
  // 3D scene handles this in tick() using updatePoints()
}
</script>