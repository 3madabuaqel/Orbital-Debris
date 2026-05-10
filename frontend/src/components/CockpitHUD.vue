<template>
  <!--
    CockpitHUD — Tactical satellite control interface.
    Layout: 4 corners, each independently positioned. No overlap possible.
    - TOP-LEFT:  Satellite telemetry panel
    - TOP-RIGHT: Exit + UTC clock
    - BOT-LEFT:  Proximity sonar radar
    - BOT-RIGHT: Thruster control pad
    - CENTER:    Targeting crosshair (pointer-events none)
  -->

  <!-- ═══════════════════ TOP-LEFT: TELEMETRY PANEL ═══════════════════ -->
  <div style="position:absolute;top:14px;left:14px;z-index:50;width:290px;pointer-events:auto;">
    <div style="background:rgba(8,12,22,0.92);backdrop-filter:blur(16px);
                border:1px solid rgba(88,166,255,0.25);border-radius:12px;padding:18px 20px;
                box-shadow:0 0 40px rgba(88,166,255,0.07);">
      
      <!-- Header -->
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
        <h2 style="color:#fff;font-size:17px;font-weight:700;letter-spacing:1.5px;
                   white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:190px;">
          {{ sat.name }}
        </h2>
        <div style="width:9px;height:9px;border-radius:50%;background:#2ea043;
                    box-shadow:0 0 10px #2ea043;flex-shrink:0;"></div>
      </div>
      <div style="color:#58a6ff;font-size:9px;letter-spacing:3px;font-weight:600;text-transform:uppercase;
                  margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid rgba(255,255,255,0.08);">
        AESH TELEMETRY / OBSERVATION
      </div>

      <!-- Telemetry Grid -->
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px;">
        <div v-for="field in telemetryFields" :key="field.label"
             style="background:rgba(0,0,0,0.35);border:1px solid rgba(255,255,255,0.07);border-radius:6px;padding:8px 10px;">
          <div style="font-size:8px;color:#8b949e;letter-spacing:2px;font-weight:700;margin-bottom:4px;">{{ field.label }}</div>
          <div style="font-size:15px;font-weight:700;color:#58a6ff;font-family:'Courier New',monospace;
                      white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
            {{ field.value }}
            <span style="font-size:9px;color:#8b949e;font-weight:400;">{{ field.unit }}</span>
          </div>
        </div>
      </div>

    </div>
  </div>

  <!-- ═══════════════════ TOP-RIGHT: CLOCK + EXIT ═══════════════════ -->
  <div style="position:absolute;top:14px;right:14px;z-index:50;display:flex;flex-direction:column;align-items:flex-end;gap:10px;pointer-events:auto;">
    
    <button @click="$emit('exit')"
      style="padding:8px 20px;background:rgba(248,81,73,0.12);color:#f85149;
             border:1px solid rgba(248,81,73,0.4);border-radius:7px;cursor:pointer;
             font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;
             transition:all 0.2s;backdrop-filter:blur(8px);"
      @mouseenter="$event.target.style.background='rgba(248,81,73,0.3)'"
      @mouseleave="$event.target.style.background='rgba(248,81,73,0.12)'">
      ✕ DETACH MODULE
    </button>

    <div style="background:rgba(8,12,22,0.85);backdrop-filter:blur(12px);
                border:1px solid rgba(30,50,80,0.5);border-radius:8px;padding:8px 14px;text-align:right;">
      <div style="font-size:9px;color:#8b949e;letter-spacing:2px;margin-bottom:2px;">SYSTEM TIME (UTC)</div>
      <div style="font-size:13px;color:#58a6ff;font-family:'Courier New',monospace;letter-spacing:1px;">{{ time }}</div>
    </div>

  </div>

  <!-- ═══════════════════ BOT-LEFT: PROXIMITY SONAR RADAR ═══════════════════ -->
  <div style="position:absolute;bottom:14px;left:14px;z-index:50;pointer-events:auto;">
    <div style="font-size:9px;color:#58a6ff;letter-spacing:2px;font-weight:700;text-transform:uppercase;
                margin-bottom:8px;display:flex;align-items:center;gap:6px;">
      <div style="width:6px;height:6px;border-radius:50%;background:#58a6ff;animation:pulse 1.5s infinite;"></div>
      PROXIMITY SCANNER
    </div>

    <div style="width:240px;height:240px;position:relative;
                background:rgba(4,8,16,0.92);backdrop-filter:blur(10px);
                border:1px solid rgba(88,166,255,0.2);border-radius:50%;
                overflow:hidden;display:flex;align-items:center;justify-content:center;">
      
      <!-- Concentric rings -->
      <div v-for="r in [33,66,99]" :key="r" style="position:absolute;border-radius:50%;border:1px solid rgba(88,166,255,0.12);"
           :style="{ width: r+'%', height: r+'%' }"></div>
      
      <!-- Crosshairs -->
      <div style="position:absolute;width:100%;height:1px;background:rgba(88,166,255,0.1);"></div>
      <div style="position:absolute;height:100%;width:1px;background:rgba(88,166,255,0.1);"></div>

      <!-- Cardinal labels -->
      <div style="position:absolute;top:6px;font-size:8px;color:rgba(88,166,255,0.5);letter-spacing:1px;font-weight:700;">N</div>
      <div style="position:absolute;bottom:6px;font-size:8px;color:rgba(88,166,255,0.5);letter-spacing:1px;font-weight:700;">S</div>
      <div style="position:absolute;left:6px;font-size:8px;color:rgba(88,166,255,0.5);letter-spacing:1px;font-weight:700;">W</div>
      <div style="position:absolute;right:6px;font-size:8px;color:rgba(88,166,255,0.5);letter-spacing:1px;font-weight:700;">E</div>

      <!-- Sweep -->
      <div style="position:absolute;inset:0;border-radius:50%;" class="radar-sweep"></div>

      <!-- Center dot (self) -->
      <div style="width:8px;height:8px;border-radius:50%;background:#fff;z-index:10;
                  box-shadow:0 0 10px #fff,0 0 20px rgba(88,166,255,0.8);"></div>

      <!-- Debris hazard dots (red) -->
      <div v-for="d in debris" :key="d.id"
           style="position:absolute;width:8px;height:8px;border-radius:50%;
                  background:#f85149;box-shadow:0 0 10px #f85149;z-index:10;
                  transition:left 0.1s linear,top 0.1s linear;"
           :style="{ left: d.x+'%', top: d.y+'%', marginLeft:'-4px', marginTop:'-4px' }">
        <div style="position:absolute;inset:-2px;border-radius:50%;border:1px solid #f85149;animation:ping 2s infinite;"></div>
      </div>
    </div>

    <!-- Debris count -->
    <div style="margin-top:6px;font-size:9px;color:#f85149;letter-spacing:1px;font-weight:600;">
      {{ debris ? debris.length : 0 }} HAZARD{{ (!debris || debris.length !== 1) ? 'S' : '' }} DETECTED
    </div>
  </div>



  <!-- ═══════════════════ CENTER: CROSSHAIR (no pointer events) ═══════════════════ -->
  <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
              pointer-events:none;z-index:30;opacity:0.55;">
    <div style="position:relative;width:80px;height:80px;display:flex;align-items:center;justify-content:center;">
      <div style="position:absolute;width:100%;height:100%;border-radius:50%;border:1px solid rgba(88,166,255,0.4);"></div>
      <!-- N/S bars -->
      <div style="position:absolute;top:-16px;left:50%;width:1px;height:12px;background:#58a6ff;transform:translateX(-50%);"></div>
      <div style="position:absolute;bottom:-16px;left:50%;width:1px;height:12px;background:#58a6ff;transform:translateX(-50%);"></div>
      <!-- E/W bars -->
      <div style="position:absolute;left:-16px;top:50%;width:12px;height:1px;background:#58a6ff;transform:translateY(-50%);"></div>
      <div style="position:absolute;right:-16px;top:50%;width:12px;height:1px;background:#58a6ff;transform:translateY(-50%);"></div>
      <!-- Center dot -->
      <div style="width:4px;height:4px;border-radius:50%;background:#f85149;box-shadow:0 0 8px #f85149;"></div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  sat:            Object,
  debris:         Array,
  time:           String,
});

defineEmits(['exit']);

const telemetryFields = computed(() => [
  { label: 'TYPE',      value: props.sat?.type  ?? 'UNKNOWN', unit: '' },
  { label: 'ALTITUDE',  value: props.sat?.alt != null ? Math.round(props.sat.alt) : '---', unit: 'km'   },
  { label: 'VELOCITY',  value: props.sat?.vel != null ? props.sat.vel.toFixed(2) : '---', unit: 'km/s' },
  { label: 'INCLINATION',value: props.sat?.inclination != null ? props.sat.inclination.toFixed(2)+'°' : '---', unit: '' },
  { label: 'ECCENTRICITY',value: props.sat?.eccentricity != null ? props.sat.eccentricity.toFixed(5) : '---', unit: '' },
  { label: 'RAAN',      value: props.sat?.raan != null ? props.sat.raan.toFixed(2)+'°' : '---', unit: '' },
  { label: 'ARG OF PERIGEE',value: props.sat?.arg_pe != null ? props.sat.arg_pe.toFixed(2)+'°' : '---', unit: '' },
  { label: 'COUNTRY',   value: props.sat?.country ?? 'UNKNOWN', unit: '' },
  { label: 'RCS SIZE',  value: props.sat?.rcs_size ?? 'UNKNOWN', unit: '' },
  { label: 'PERIOD',    value: props.sat?.period != null ? props.sat.period.toFixed(1) : '---', unit: 'min' }
]);
</script>

<style scoped>
/* Radar sweep animation */
.radar-sweep {
  background: conic-gradient(from 0deg, transparent 75%, rgba(88,166,255,0.12) 95%, rgba(88,166,255,0.7) 100%);
  animation: sweep 3s linear infinite;
}
@keyframes sweep { to { transform: rotate(360deg); } }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.25; }
}
@keyframes ping {
  0%        { transform: scale(1);   opacity: 0.8; }
  75%, 100% { transform: scale(2.5); opacity: 0;   }
}
</style>
