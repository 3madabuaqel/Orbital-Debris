<template>
  <!-- TOP BAR -->
  <div style="position:absolute;top:0;left:0;right:0;height:52px;z-index:50;
              background:rgba(10,12,20,0.92);backdrop-filter:blur(12px);
              border-bottom:1px solid rgba(30,50,80,0.6);
              display:flex;align-items:center;justify-content:space-between;padding:0 16px;">
    
    <div style="display:flex;align-items:center;gap:10px;">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#58a6ff" stroke-width="2">
        <path d="M13 10V3L4 14h7v7l9-11h-7z" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <span style="color:#fff;font-weight:700;font-size:15px;letter-spacing:2px;">AESH</span>
      <span style="color:#8b949e;font-size:11px;letter-spacing:3px;font-weight:300;">BASTION</span>
      <span style="background:rgba(46,160,67,0.15);color:#2ea043;border:1px solid rgba(46,160,67,0.4);
                   padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;letter-spacing:1px;
                   display:flex;align-items:center;gap:4px;margin-left:12px;">
        <span class="dot-pulse" style="width:6px;height:6px;border-radius:50%;background:#2ea043;display:inline-block;"></span>
        LIVE
      </span>
    </div>

    <div style="display:flex;align-items:center;gap:28px;font-family:'Courier New',monospace;">
      <div style="text-align:center;">
        <div style="color:#fff;font-size:16px;line-height:1.2;">{{ time }}</div>
        <div style="color:#8b949e;font-size:9px;letter-spacing:2px;">UTC</div>
      </div>
      <div style="width:1px;height:28px;background:rgba(255,255,255,0.1);"></div>
      <div style="text-align:center;">
        <div style="color:#fff;font-size:16px;line-height:1.2;">{{ satelliteCount }}</div>
        <div style="color:#8b949e;font-size:9px;letter-spacing:2px;">TRACKED</div>
      </div>
      <div style="width:1px;height:28px;background:rgba(255,255,255,0.1);"></div>
      <div style="text-align:center;">
        <div style="color:#f85149;font-size:16px;line-height:1.2;">{{ debrisCount }}</div>
        <div style="color:#8b949e;font-size:9px;letter-spacing:2px;">DEBRIS</div>
      </div>
      <div style="width:1px;height:28px;background:rgba(255,255,255,0.1);"></div>
      <div style="text-align:center;">
        <div style="color:#d29922;font-size:16px;line-height:1.2;">{{ rocketCount }}</div>
        <div style="color:#8b949e;font-size:9px;letter-spacing:2px;">ROCKETS</div>
      </div>
    </div>

    <div style="display:flex;align-items:center;gap:10px;">
      <select v-model="selectedFile" @change="onFileChange"
              style="background:rgba(0,0,0,0.4);border:1px solid rgba(88,166,255,0.3);border-radius:4px;
                     color:#58a6ff;font-size:11px;font-weight:700;padding:4px 8px;outline:none;cursor:pointer;">
        <option value="" disabled>Select Source File</option>
        <option value="ALL">All Files (Entire Directory)</option>
        <option v-for="file in availableFiles" :key="file" :value="file">{{ file }}</option>
      </select>

      <div :style="{ background: riskLevel === 'HIGH' ? 'rgba(248,81,73,0.15)' : 'rgba(46,160,67,0.15)',
                     border: riskLevel === 'HIGH' ? '1px solid rgba(248,81,73,0.4)' : '1px solid rgba(46,160,67,0.4)',
                     padding:'3px 10px', borderRadius:'4px', display:'flex', alignItems:'center', gap:'5px' }">
        <div :style="{ width:'7px', height:'7px', borderRadius:'50%',
                       background: riskLevel === 'HIGH' ? '#f85149' : '#2ea043' }" class="dot-pulse"></div>
        <span :style="{ color: riskLevel === 'HIGH' ? '#f85149' : '#2ea043', fontSize:'11px', fontWeight:'600', letterSpacing:'1px' }">
          {{ riskLevel === 'HIGH' ? 'COLLISION RISK' : 'NOMINAL' }}
        </span>
      </div>
      <div style="width:32px;height:32px;border-radius:50%;background:#161b22;border:1px solid #30363d;
                  display:flex;align-items:center;justify-content:center;color:#8b949e;font-size:11px;font-weight:700;">JS</div>
    </div>
  </div>

  <!-- LEFT SIDEBAR -->
  <div style="position:absolute;top:52px;left:0;bottom:0;width:300px;z-index:40;
              background:rgba(10,12,20,0.92);backdrop-filter:blur(12px);
              border-right:1px solid rgba(30,50,80,0.6);
              display:flex;flex-direction:column;overflow:hidden;">
    
    <!-- Tabs -->
    <div style="display:flex;border-bottom:1px solid rgba(30,50,80,0.6);flex-shrink:0;">
      <div @click="activeTab = 'payloads'"
           style="flex:1;padding:10px 0;text-align:center;font-size:9px;font-weight:700;letter-spacing:1px;cursor:pointer;transition:all 0.2s;"
           :style="{ color: activeTab==='payloads' ? '#fff':'#8b949e',
                     borderBottom: activeTab==='payloads' ? '2px solid #58a6ff':'2px solid transparent' }">PAYLOADS</div>
      <div @click="activeTab = 'rockets'"
           style="flex:1;padding:10px 0;text-align:center;font-size:9px;font-weight:700;letter-spacing:1px;cursor:pointer;transition:all 0.2s;"
           :style="{ color: activeTab==='rockets' ? '#fff':'#8b949e',
                     borderBottom: activeTab==='rockets' ? '2px solid #58a6ff':'2px solid transparent' }">ROCKETS</div>
      <div @click="activeTab = 'debris'"
           style="flex:1;padding:10px 0;text-align:center;font-size:9px;font-weight:700;letter-spacing:1px;cursor:pointer;transition:all 0.2s;"
           :style="{ color: activeTab==='debris' ? '#fff':'#8b949e',
                     borderBottom: activeTab==='debris' ? '2px solid #58a6ff':'2px solid transparent' }">DEBRIS</div>
    </div>

    <!-- ── LIST TAB ── -->
    <template v-if="['payloads', 'rockets', 'debris'].includes(activeTab)">
      <div style="padding:10px 12px;border-bottom:1px solid rgba(30,50,80,0.4);flex-shrink:0;">
        <input v-model="search" placeholder="Filter satellites…"
          style="width:100%;background:rgba(0,0,0,0.4);border:1px solid rgba(255,255,255,0.1);
                 border-radius:6px;padding:7px 12px;color:#c9d1d9;font-size:11px;outline:none;box-sizing:border-box;"
          @focus="$event.target.style.borderColor='#58a6ff'"
          @blur="$event.target.style.borderColor='rgba(255,255,255,0.1)'"
        />
      </div>
      <div style="display:grid;grid-template-columns:1fr 60px 60px;padding:6px 14px;
                  font-size:9px;color:#8b949e;letter-spacing:1.5px;font-weight:700;
                  border-bottom:1px solid rgba(30,50,80,0.4);flex-shrink:0;">
        <span>TARGET ({{ satellites ? satellites.length : 0 }})</span><span style="text-align:right;">VEL</span><span style="text-align:right;">ALT</span>
      </div>
      <div style="flex:1;overflow-y:auto;" class="aess-scroll">
        <div v-for="sat in filteredSats" :key="sat.id"
             @click="$emit('select', sat)"
             style="display:grid;grid-template-columns:1fr 60px 60px;padding:9px 14px;
                    border-bottom:1px solid rgba(255,255,255,0.04);cursor:pointer;transition:background 0.15s;"
             @mouseenter="$event.currentTarget.style.background='rgba(88,166,255,0.07)'"
             @mouseleave="$event.currentTarget.style.background='transparent'">
          <div>
            <div style="font-size:11px;font-weight:600;color:#58a6ff;letter-spacing:0.5px;">{{ sat.name }}</div>
            <div style="font-size:9px;margin-top:2px;letter-spacing:1px;"
                 :style="{ color: sat.type === 'RELAY' ? '#2ea043' : '#8b949e' }">{{ sat.type }}</div>
          </div>
          <div style="font-size:10px;color:#8b949e;font-family:'Courier New',monospace;text-align:right;align-self:center;">7.6 km/s</div>
          <div style="font-size:10px;color:#8b949e;font-family:'Courier New',monospace;text-align:right;align-self:center;">{{ Math.round(sat.alt) }} km</div>
        </div>
      </div>
    </template>

    <!-- ── NETWORK TAB ── -->
    <template v-if="activeTab === 'network'">
      <div style="flex:1;overflow-y:auto;padding:14px;" class="aess-scroll">
        
        <!-- Network Health -->
        <div style="font-size:10px;color:#8b949e;letter-spacing:2px;font-weight:700;margin-bottom:10px;">NETWORK HEALTH</div>
        <div v-for="m in networkMetrics" :key="m.label"
             style="background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.06);border-radius:8px;
                    padding:10px 12px;margin-bottom:8px;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
            <span style="font-size:10px;color:#c9d1d9;">{{ m.label }}</span>
            <span style="font-size:11px;font-weight:700;font-family:'Courier New',monospace;"
                  :style="{ color: m.color }">{{ m.value }}</span>
          </div>
          <div style="width:100%;height:3px;background:rgba(255,255,255,0.08);border-radius:3px;overflow:hidden;">
            <div style="height:100%;border-radius:3px;transition:width 1s ease;"
                 :style="{ width: m.pct+'%', background: m.color }"></div>
          </div>
        </div>

        <!-- ISL Matrix -->
        <div style="font-size:10px;color:#8b949e;letter-spacing:2px;font-weight:700;margin:16px 0 10px;">ACTIVE ISL LINKS</div>
        <div v-for="link in islLinks" :key="link.id"
             style="display:flex;justify-content:space-between;align-items:center;
                    padding:7px 10px;border-bottom:1px solid rgba(255,255,255,0.04);">
          <div style="font-size:10px;color:#58a6ff;font-family:'Courier New',monospace;">{{ link.from }} ↔ {{ link.to }}</div>
          <div style="display:flex;align-items:center;gap:6px;">
            <div style="width:5px;height:5px;border-radius:50%;"
                 :style="{ background: link.status === 'OK' ? '#2ea043' : '#f85149' }"></div>
            <span style="font-size:9px;font-family:'Courier New',monospace;"
                  :style="{ color: link.status === 'OK' ? '#2ea043' : '#f85149' }">{{ link.latency }}</span>
          </div>
        </div>

        <!-- Ground Stations -->
        <div style="font-size:10px;color:#8b949e;letter-spacing:2px;font-weight:700;margin:16px 0 10px;">GROUND STATIONS</div>
        <div v-for="gs in groundStations" :key="gs.name"
             style="display:flex;justify-content:space-between;align-items:center;
                    padding:7px 10px;border-bottom:1px solid rgba(255,255,255,0.04);">
          <div>
            <div style="font-size:10px;color:#c9d1d9;font-weight:600;">{{ gs.name }}</div>
            <div style="font-size:9px;color:#8b949e;margin-top:2px;">{{ gs.location }}</div>
          </div>
          <div style="text-align:right;">
            <div style="font-size:9px;font-family:'Courier New',monospace;"
                 :style="{ color: gs.online ? '#2ea043' : '#f85149' }">{{ gs.online ? 'ONLINE' : 'OFFLINE' }}</div>
            <div style="font-size:9px;color:#8b949e;font-family:'Courier New',monospace;">{{ gs.uplink }}</div>
          </div>
        </div>
      </div>
    </template>
  </div>

  <!-- RIGHT PANEL: Layer Control + TLE -->
  <div style="position:absolute;top:68px;right:12px;width:224px;z-index:40;
              background:rgba(10,12,20,0.9);backdrop-filter:blur(12px);
              border:1px solid rgba(30,50,80,0.5);border-radius:10px;padding:14px 16px;">
    
    <div style="font-size:10px;font-weight:700;color:#fff;letter-spacing:2px;margin-bottom:12px;">LAYER CONTROL</div>
    <div v-for="(layer, key) in layers" :key="key"
         style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
      <span style="font-size:11px;color:#c9d1d9;">{{ layer.label }}</span>
      <div style="width:32px;height:17px;border-radius:9px;cursor:pointer;position:relative;transition:background 0.2s;"
           :style="{ background: layer.on ? '#58a6ff' : '#30363d' }"
           @click="toggleLayer(key)">
        <div style="width:13px;height:13px;border-radius:50%;background:#fff;position:absolute;top:2px;transition:left 0.2s;"
             :style="{ left: layer.on ? '17px' : '2px' }"></div>
      </div>
    </div>

    <div style="border-top:1px solid rgba(30,50,80,0.5);margin-top:14px;padding-top:14px;">
      <div style="font-size:10px;font-weight:700;color:#fff;letter-spacing:2px;margin-bottom:8px;">TLE INFO</div>
      <div style="font-size:10px;color:#8b949e;font-family:'Courier New',monospace;line-height:1.9;">
        <div>NORAD ID: <span style="color:#c9d1d9;">25544</span></div>
        <div>Epoch: <span style="color:#c9d1d9;">16031.259</span></div>
        <div>Retrieved: <span style="color:#c9d1d9;">{{ time }} UTC</span></div>
      </div>
    </div>

    <!-- PREDICTIVE SIMULATION -->
    <div style="border-top:1px solid rgba(30,50,80,0.5);margin-top:14px;padding-top:14px;">
      <div style="font-size:10px;font-weight:700;color:#fff;letter-spacing:2px;margin-bottom:10px;display:flex;align-items:center;gap:6px;">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#58a6ff" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        PREDICTIVE ENGINE
      </div>
      
      <div style="display:flex;gap:8px;margin-bottom:10px;">
        <input type="number" v-model="simValue" min="1" max="100"
               style="width:50px;background:rgba(0,0,0,0.4);border:1px solid rgba(88,166,255,0.3);border-radius:4px;
                      color:#fff;font-family:'Courier New',monospace;font-size:11px;text-align:center;padding:4px;outline:none;" />
        <select v-model="simUnit"
                style="flex:1;background:rgba(0,0,0,0.4);border:1px solid rgba(88,166,255,0.3);border-radius:4px;
                       color:#58a6ff;font-size:10px;font-weight:700;padding:4px;outline:none;">
          <option value="months">MONTHS</option>
          <option value="years">YEARS</option>
        </select>
      </div>
      
      <button @click="runSimulation" :disabled="isSimulating"
              style="width:100%;padding:8px;background:rgba(88,166,255,0.15);color:#58a6ff;
                     border:1px solid rgba(88,166,255,0.4);border-radius:4px;cursor:pointer;
                     font-size:10px;font-weight:700;letter-spacing:2px;transition:all 0.2s;"
              @mouseenter="!isSimulating && ($event.target.style.background='rgba(88,166,255,0.3)')"
              @mouseleave="!isSimulating && ($event.target.style.background='rgba(88,166,255,0.15)')">
        {{ isSimulating ? 'CALCULATING...' : 'RUN SIMULATION' }}
      </button>

      <!-- Results -->
      <div v-if="simResult" style="margin-top:12px;padding:10px;border-radius:6px;background:rgba(0,0,0,0.4);border:1px solid;"
           :style="{ borderColor: simResult.safe ? 'rgba(46,160,67,0.4)' : 'rgba(248,81,73,0.4)' }">
        <div style="font-size:9px;color:#8b949e;letter-spacing:1px;margin-bottom:4px;">PREDICTION RESULT:</div>
        <div style="display:flex;align-items:center;gap:6px;font-size:12px;font-weight:700;letter-spacing:2px;"
             :style="{ color: simResult.safe ? '#2ea043' : '#f85149' }">
          <div style="width:6px;height:6px;border-radius:50%;" :style="{ background: simResult.safe ? '#2ea043' : '#f85149' }"></div>
          {{ simResult.safe ? 'ORBIT SAFE' : 'HAZARD DETECTED' }}
        </div>
        
        <div v-if="!simResult.safe" style="margin-top:10px;">
          <div style="font-size:8px;color:#8b949e;letter-spacing:1px;margin-bottom:6px;">PREDICTED EVENTS (CLICK TO VIEW):</div>
          <div v-for="ev in simResult.events" :key="ev.id"
               @click="$emit('play-collision', ev)"
               style="background:rgba(248,81,73,0.1);border:1px solid rgba(248,81,73,0.3);border-radius:4px;padding:6px 8px;
                      margin-bottom:6px;cursor:pointer;transition:all 0.2s;"
               @mouseenter="$event.currentTarget.style.background='rgba(248,81,73,0.2)'"
               @mouseleave="$event.currentTarget.style.background='rgba(248,81,73,0.1)'">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
              <span style="font-size:10px;color:#fff;font-weight:700;">{{ ev.satellite?.name }}</span>
              <span style="font-size:9px;color:#f85149;font-family:'Courier New',monospace;">{{ ev.tca }}</span>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:8px;color:#c9d1d9;">
              <span>Risk: {{ ev.probability }}</span>
              <span>{{ ev.kineticEnergy }}</span>
            </div>
            <div style="font-size:8px;color:#d29922;margin-top:4px;">Threat: {{ ev.hazard_name }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Bottom hint -->
  <div style="position:absolute;bottom:14px;left:50%;transform:translateX(-50%);z-index:40;pointer-events:none;
              background:rgba(10,12,20,0.75);backdrop-filter:blur(8px);
              border:1px solid rgba(88,166,255,0.2);border-radius:20px;padding:6px 18px;">
    <span style="font-size:10px;color:#8b949e;letter-spacing:1px;">CLICK ANY SATELLITE TO VIEW TELEMETRY</span>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';

const props = defineProps({
  satellites: { type: Array, default: () => [] },
  time:       { type: String, default: '' },
  satelliteCount:{ type: Number, default: 0 },
  rocketCount:{ type: Number, default: 0 },
  debrisCount:{ type: Number, default: 0 },
  riskLevel:  { type: String, default: 'LOW' },
});

const emit = defineEmits(['select', 'layer-change', 'simulate-start', 'simulate-end', 'play-collision']);

const availableFiles = ref([]);
const selectedFile = ref('');

onMounted(async () => {
  try {
    const res = await fetch('http://127.0.0.1:8000/files');
    const data = await res.json();
    if (data.files && data.files.length > 0) {
      availableFiles.value = data.files;
      // We don't automatically trigger reload here since backend starts with a default, 
      // but we set the UI dropdown to the first item (which is usually what's loaded)
      selectedFile.value = data.files[0];
    }
  } catch (e) {
    console.error("Failed to load files", e);
  }
});

async function onFileChange() {
  if (!selectedFile.value) return;
  try {
    const filenameParam = selectedFile.value === 'ALL' ? '' : `?filename=${encodeURIComponent(selectedFile.value)}`;
    await fetch(`http://127.0.0.1:8000/reload${filenameParam}`, {
      method: 'POST'
    });
  } catch (e) {
    console.error("Failed to reload file", e);
  }
}

const activeTab = ref('payloads');
const search    = ref('');

const layers = ref({
  satellites:   { label: 'Satellites',    on: true },
  rocketBodies: { label: 'Rocket Bodies', on: true },
  debris:       { label: 'Debris',        on: true },
});

function toggleLayer(key) {
  layers.value[key].on = !layers.value[key].on;
  emit('layer-change', { key, on: layers.value[key].on });
}

// Predictive Simulation Logic
const simValue = ref(3);
const simUnit = ref('months');
const isSimulating = ref(false);
const simResult = ref(null);

async function runSimulation() {
  if (isSimulating.value) return;
  isSimulating.value = true;
  simResult.value = null;
  emit('simulate-start');
  
  try {
    let totalYears = simUnit.value === 'years' ? simValue.value : Math.ceil(simValue.value / 12);
    // minimum 1 year
    if (totalYears < 1) totalYears = 1;

    const res = await fetch(`http://127.0.0.1:8000/predict?time_horizon_years=${totalYears}`);
    const data = await res.json();
    
    // Parse real physics data
    const isSafe = data.global_risk_index < 0.5 && !data.trend.includes('Warning');
    
    const events = [];
    if (data.high_risk_zones && data.high_risk_zones.length > 0) {
      data.high_risk_zones.forEach((ev, idx) => {
        events.push({
          id: idx,
          satellite: ev.satellite,
          tca: ev.tca,
          probability: ev.probability,
          kineticEnergy: ev.kineticEnergy,
          hazard_name: ev.hazard_name
        });
      });
    }

    simResult.value = { 
      safe: isSafe, 
      events: events,
      trend: data.trend,
      finalObjectCount: data.final_object_count
    };

  } catch (e) {
    console.error("Prediction failed:", e);
    simResult.value = { safe: false, events: [{ id: 0, satellite: { name: 'SYSTEM ERROR' }, tca: 'N/A', probability: '1.0', kineticEnergy: '0' }] };
  } finally {
    isSimulating.value = false;
    emit('simulate-end');
  }
}

const filteredSats = computed(() => {
  let list = props.satellites;
  if (activeTab.value === 'payloads') list = list.filter(s => s.type === 'PAYLOAD');
  else if (activeTab.value === 'rockets') list = list.filter(s => s.type === 'ROCKET BODY');
  else if (activeTab.value === 'debris') list = list.filter(s => s.type !== 'PAYLOAD' && s.type !== 'ROCKET BODY');
  
  if (search.value) {
    const q = search.value.toLowerCase();
    list = list.filter(s => s.name && s.name.toLowerCase().includes(q));
  }
  return list.slice(0, 150); // limit DOM elements for performance while allowing global search
});

// Network tab data (realistic ISL mesh)
const networkMetrics = computed(() => [
  { label: 'Link Availability',  value: '99.2%', pct: 99,  color: '#2ea043' },
  { label: 'Avg Latency (ms)',   value: '18ms',  pct: 82,  color: '#58a6ff' },
  { label: 'Data Throughput',    value: '2.4Gbps',pct: 72, color: '#58a6ff' },
  { label: 'Network Load',       value: '41%',   pct: 41,  color: '#d29922' },
]);

const islLinks = ref(
  Array.from({ length: 8 }, (_, i) => ({
    id:      i,
    from:    `AESH-0${String(i).padStart(3,'0')}`,
    to:      `AESH-0${String((i+1)%6).padStart(3,'0')}`,
    latency: `${10 + Math.floor(Math.random()*30)}ms`,
    status:  Math.random() > 0.15 ? 'OK' : 'DEGRADED',
  }))
);

const groundStations = ref([
  { name: 'GS-RIYADH',  location: 'Saudi Arabia',  online: true,  uplink: '↑ 512 Mbps' },
  { name: 'GS-LONDON',  location: 'United Kingdom', online: true,  uplink: '↑ 1.2 Gbps' },
  { name: 'GS-NAIROBI', location: 'Kenya',          online: false, uplink: '—' },
  { name: 'GS-TOKYO',   location: 'Japan',          online: true,  uplink: '↑ 800 Mbps' },
]);
</script>

<style scoped>
.aess-scroll::-webkit-scrollbar { width: 4px; }
.aess-scroll::-webkit-scrollbar-thumb { background: #30363d; border-radius: 4px; }
.aess-scroll::-webkit-scrollbar-thumb:hover { background: #58a6ff; }

.dot-pulse { animation: pulse 2s infinite; }
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.25; } }
</style>
