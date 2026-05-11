<template>
  <div style="position:relative;width:100%;height:100vh;overflow:hidden;background:#050508;">
    <div ref="canvasMount" style="position:absolute;inset:0;"></div>

    <GlobalHUD
      v-if="!activeSat && !isExploding"
      :satellites="satellites"
      :time="utcTime"
      :satellite-count="currentSatelliteCount"
      :rocket-count="currentRocketCount"
      :debris-count="currentDebrisCount"
      @select="enterCockpit"
      @play-collision="onPlayCollision"
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
import { buildEarth, buildLights, buildStarfield, buildInstancedSatellites, buildCubeSat } from '../scene/SceneBuilder.js';
import { tickExplosion } from '../scene/DebrisSystem.js';

// Calculate exact scale factor so it perfectly matches the imported EARTH_RADIUS
const SCALE_FACTOR = EARTH_RADIUS / 6371.0;

const canvasMount = ref(null);
const satellites = shallowRef([]);
const activeSat = ref(null);
const utcTime = ref('');
const isExploding = ref(false);
const timeScale = ref(1);
const socket = ref(null);
const rawOrbitalData = shallowRef([]);
const currentSatelliteCount = ref(0);
const currentRocketCount = ref(0);
const currentDebrisCount = ref(0);

const activeLayers = ref({
  satellites: true,
  rocketBodies: true,
  debris: true
});

let scene, camera, renderer, controls, earth, clouds, cubeSat;
let payloadMesh, rocketMesh, debrisMesh;
let meshMappings = { payload: [], rocket: [], debris: [] };
let explosionParticles = [];
let lastSatPos = new THREE.Vector3();
let raycaster = new THREE.Raycaster();
let mouse = new THREE.Vector2();
let frameCount = 0;
let cockpitMode = false;
let isWaitingForFrame = false;
let collisionLine = null;

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

  // Initially empty
  const initialCounts = { payload: 0, rocket: 0, debris: 0 };
  const meshes = buildInstancedSatellites(scene, initialCounts);
  payloadMesh = meshes.payloadMesh;
  rocketMesh = meshes.rocketMesh;
  debrisMesh = meshes.debrisMesh;

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

  if (rawOrbitalData.value !== undefined) {
    updatePoints();
    
    // Sync Vue UI state synchronously with the render loop
    currentSatelliteCount.value = rawOrbitalData.value.filter(s => s.type === 'PAYLOAD').length;
    currentRocketCount.value = rawOrbitalData.value.filter(s => s.type === 'ROCKET BODY').length;
    currentDebrisCount.value = rawOrbitalData.value.filter(s => s.type !== 'PAYLOAD' && s.type !== 'ROCKET BODY').length;
    if (rawOrbitalData.value.length === 0 || satellites.value.length === 0 || frameCount % 60 === 0) {
      satellites.value = rawOrbitalData.value;
    }
  }

  if (cockpitMode && activeSat.value) {
    cubeSat.position.copy(activeSat.value.pos);
    controls.target.copy(activeSat.value.pos);
    
    // Update collision line if active
    if (collisionLine && activeSat.value.hazardName) {
      const hazardData = rawOrbitalData.value.find(s => s.name === activeSat.value.hazardName);
      if (hazardData) {
        const getVisualPos = (sat) => {
          const trueDist = Math.sqrt(sat.x*sat.x + sat.y*sat.y + sat.z*sat.z) * SCALE_FACTOR;
          const trueAlt = trueDist - EARTH_RADIUS; 
          const visualDist = EARTH_RADIUS + (trueAlt * 2.0); 
          const ratio = visualDist / trueDist;
          return new THREE.Vector3((sat.x * SCALE_FACTOR) * ratio, (sat.z * SCALE_FACTOR) * ratio, -(sat.y * SCALE_FACTOR) * ratio);
        };
        const pPos = activeSat.value.pos;
        const hPos = getVisualPos(hazardData);
        collisionLine.geometry.setFromPoints([pPos, hPos]);
      }
    }
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
  
  if (!data || data.length === 0) {
    if (payloadMesh) { scene.remove(payloadMesh); payloadMesh.geometry.dispose(); payloadMesh.material.dispose(); payloadMesh = null; }
    if (rocketMesh) { scene.remove(rocketMesh); rocketMesh.geometry.dispose(); rocketMesh.material.dispose(); rocketMesh = null; }
    if (debrisMesh) { scene.remove(debrisMesh); debrisMesh.geometry.dispose(); debrisMesh.material.dispose(); debrisMesh = null; }
    return;
  }

  const currentPayloadCount = payloadMesh ? payloadMesh.count : 0;
  const currentRocketCount = rocketMesh ? rocketMesh.count : 0;
  const currentDebrisCount = debrisMesh ? debrisMesh.count : 0;

  const actualPayloadCount = data.filter(s => s.type === 'PAYLOAD').length;
  const actualRocketCount = data.filter(s => s.type === 'ROCKET BODY').length;
  const actualDebrisCount = data.filter(s => s.type !== 'PAYLOAD' && s.type !== 'ROCKET BODY').length;

  if (currentPayloadCount !== actualPayloadCount || currentRocketCount !== actualRocketCount || currentDebrisCount !== actualDebrisCount) {
    if (payloadMesh) {
      scene.remove(payloadMesh); payloadMesh.geometry.dispose(); payloadMesh.material.dispose();
      scene.remove(rocketMesh); rocketMesh.geometry.dispose(); rocketMesh.material.dispose();
      scene.remove(debrisMesh); debrisMesh.geometry.dispose(); debrisMesh.material.dispose();
    }
    const meshes = buildInstancedSatellites(scene, { payload: actualPayloadCount, rocket: actualRocketCount, debris: actualDebrisCount });
    payloadMesh = meshes.payloadMesh;
    rocketMesh = meshes.rocketMesh;
    debrisMesh = meshes.debrisMesh;
    meshMappings = { payload: [], rocket: [], debris: [] };
  }

  payloadMesh.visible = !cockpitMode;
  rocketMesh.visible = !cockpitMode;
  debrisMesh.visible = !cockpitMode;

  const dummy = new THREE.Object3D();
  let pIdx = 0, rIdx = 0, dIdx = 0;

  for (let i = 0; i < data.length; i++) {
    const sat = data[i];
    if (!sat) continue;

    let isVisible = true;
    let targetMesh = null;
    let idx = 0;

    if (sat.type === 'PAYLOAD') {
      isVisible = activeLayers.value.satellites;
      targetMesh = payloadMesh;
      idx = pIdx++;
      meshMappings.payload[idx] = sat;
    } else if (sat.type === 'ROCKET BODY') {
      isVisible = activeLayers.value.rocketBodies;
      targetMesh = rocketMesh;
      idx = rIdx++;
      meshMappings.rocket[idx] = sat;
    } else {
      isVisible = activeLayers.value.debris;
      targetMesh = debrisMesh;
      idx = dIdx++;
      meshMappings.debris[idx] = sat;
    }

    if (!isVisible) {
      dummy.scale.set(0, 0, 0);
    } else {
      // Scale realistically based on RCS_SIZE from the CSV
      let s = 0.12; // Base scale (reduced to be smaller)
      if (sat.rcs_size === 'LARGE') s = 0.22;
      else if (sat.rcs_size === 'MEDIUM') s = 0.12;
      else if (sat.rcs_size === 'SMALL') s = 0.08;
      
      dummy.scale.set(s, s, s);
      
      // Calculate true distance in Three.js units
      const trueDist = Math.sqrt(sat.x*sat.x + sat.y*sat.y + sat.z*sat.z) * SCALE_FACTOR;
      const trueAlt = trueDist - EARTH_RADIUS; 
      
      // The visual atmosphere extends to EARTH_RADIUS + 0.8
      // Multiply the true altitude by 2.0 to give a logical visual gap, avoiding the "stuck to Earth" illusion
      const visualDist = EARTH_RADIUS + (trueAlt * 2.0); 
      const ratio = visualDist / trueDist;

      // Map Skyfield GCRS (Z-up) to Three.js (Y-up) and apply ratio
      dummy.position.set(
        (sat.x * SCALE_FACTOR) * ratio, 
        (sat.z * SCALE_FACTOR) * ratio, 
        -(sat.y * SCALE_FACTOR) * ratio 
      );
      dummy.lookAt(0, 0, 0); // Face Earth
    }
    dummy.updateMatrix();
    targetMesh.setMatrixAt(idx, dummy.matrix);
  }

  payloadMesh.instanceMatrix.needsUpdate = true;
  rocketMesh.instanceMatrix.needsUpdate = true;
  debrisMesh.instanceMatrix.needsUpdate = true;
}

function enterCockpit(sat) {
  const trueDist = Math.sqrt(sat.x*sat.x + sat.y*sat.y + sat.z*sat.z) * SCALE_FACTOR;
  const trueAlt = trueDist - EARTH_RADIUS; 
  const visualDist = EARTH_RADIUS + (trueAlt * 2.0); 
  const ratio = visualDist / trueDist;

  const target = new THREE.Vector3(
    (sat.x * SCALE_FACTOR) * ratio,
    (sat.z * SCALE_FACTOR) * ratio,
    -(sat.y * SCALE_FACTOR) * ratio
  );

  activeSat.value = { ...sat, pos: target.clone() };
  cockpitMode = true;

  cubeSat.visible = true;
  if (payloadMesh) payloadMesh.visible = false;
  if (rocketMesh) rocketMesh.visible = false;
  if (debrisMesh) debrisMesh.visible = false;

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
  if (payloadMesh) payloadMesh.visible = true;
  if (rocketMesh) rocketMesh.visible = true;
  if (debrisMesh) debrisMesh.visible = true;

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

  const meshes = [];
  if (payloadMesh) meshes.push(payloadMesh);
  if (rocketMesh) meshes.push(rocketMesh);
  if (debrisMesh) meshes.push(debrisMesh);

  const intersects = raycaster.intersectObjects(meshes);

  if (intersects.length > 0) {
    const intersect = intersects[0];
    const obj = intersect.object;
    const instId = intersect.instanceId;

    let sat;
    if (obj === payloadMesh) sat = meshMappings.payload[instId];
    else if (obj === rocketMesh) sat = meshMappings.rocket[instId];
    else if (obj === debrisMesh) sat = meshMappings.debris[instId];

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

function onPlayCollision(ev) {
  const payloadData = rawOrbitalData.value.find(s => s.name === ev.satellite?.name);
  const hazardData = rawOrbitalData.value.find(s => s.name === ev.hazard_name);

  if (!payloadData || !hazardData) {
    alert("Objects not found in current orbital data frame.");
    return;
  }

  // Remove existing line
  if (collisionLine) {
    scene.remove(collisionLine);
    collisionLine.geometry.dispose();
    collisionLine.material.dispose();
  }

  const getVisualPos = (sat) => {
    const trueDist = Math.sqrt(sat.x*sat.x + sat.y*sat.y + sat.z*sat.z) * SCALE_FACTOR;
    const trueAlt = trueDist - EARTH_RADIUS; 
    const visualDist = EARTH_RADIUS + (trueAlt * 2.0); 
    const ratio = visualDist / trueDist;
    return new THREE.Vector3(
      (sat.x * SCALE_FACTOR) * ratio,
      (sat.z * SCALE_FACTOR) * ratio,
      -(sat.y * SCALE_FACTOR) * ratio
    );
  };

  const pPos = getVisualPos(payloadData);
  const hPos = getVisualPos(hazardData);

  const material = new THREE.LineBasicMaterial({ color: 0xff0000 });
  const geometry = new THREE.BufferGeometry().setFromPoints([pPos, hPos]);
  collisionLine = new THREE.Line(geometry, material);
  scene.add(collisionLine);

  enterCockpit(payloadData);
  activeSat.value.hazardName = ev.hazard_name; // Store hazard name to update line dynamically
  isExploding.value = true;
}

function resetAfterCollision() {
  isExploding.value = false;
  if (collisionLine) {
    scene.remove(collisionLine);
    collisionLine.geometry.dispose();
    collisionLine.material.dispose();
    collisionLine = null;
  }
  exitCockpit();
}

function onLayerChange(payload) {
  activeLayers.value[payload.key] = payload.on;
}
</script>