/**
 * FireGuard — Application Logic
 * Carto basemaps · NASA FIRMS hotspots · Dijkstra risk-aware routing · ML risk prediction
 */

const CARTO_KEY = "cb1_411n_1_52d3478f6a48862b43f7f2bd";

const CARTO_STYLES = {
  voyager: `https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png?key=${CARTO_KEY}`,
  dark:    `https://basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}{r}.png?key=${CARTO_KEY}`,
  light:   `https://basemaps.cartocdn.com/rastertiles/light_all/{z}/{x}/{y}{r}.png?key=${CARTO_KEY}`
};

const PRESETS = {
  cool_wet: { temp: 18, humidity: 82, wind: 10, rain: 25 },
  normal:   { temp: 26, humidity: 55, wind: 15, rain:  2 },
  dry_hot:  { temp: 37, humidity: 22, wind: 26, rain:  0 },
  extreme:  { temp: 42, humidity: 12, wind: 40, rain:  0 }
};

const appState = {
  map: null,
  currentTileLayer: null,
  fireLayer: null,
  routeShortestLayer: null,
  routeSafestLayer: null,
  shelterLayer: null,
  networkData: null
};

document.addEventListener("DOMContentLoaded", () => {
  initMap();
  initThemeSwitcher();
  initPanelModes();
  initRouting();
  initMLSliders();
  initTestModal();

  loadHotspots();
  loadNetwork();
  evaluateRisk();
  fetchTestResults();
});

/* ── Map Setup ───────────────────────────────────── */
function initMap() {
  const center = [30.15, 78.90];
  appState.map = L.map("map", { center, zoom: 8, zoomControl: false });
  L.control.zoom({ position: "topright" }).addTo(appState.map);

  appState.currentTileLayer = L.tileLayer(CARTO_STYLES.voyager, {
    attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 19
  }).addTo(appState.map);

  appState.fireLayer          = L.layerGroup().addTo(appState.map);
  appState.routeShortestLayer = L.layerGroup().addTo(appState.map);
  appState.routeSafestLayer   = L.layerGroup().addTo(appState.map);
  appState.shelterLayer       = L.layerGroup().addTo(appState.map);

  document.getElementById("recenterBtn").addEventListener("click", () => {
    appState.map.setView(center, 8, { animate: true });
  });
}

function initThemeSwitcher() {
  const btns = document.querySelectorAll("#mapThemeSwitch .segment-btn");
  btns.forEach(btn => {
    btn.addEventListener("click", () => {
      btns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const url = CARTO_STYLES[btn.dataset.theme] || CARTO_STYLES.voyager;
      if (appState.currentTileLayer) appState.map.removeLayer(appState.currentTileLayer);
      appState.currentTileLayer = L.tileLayer(url, { maxZoom: 19 }).addTo(appState.map);
    });
  });
}

/* ── Panel Tabs ──────────────────────────────────── */
function initPanelModes() {
  const tabs = document.querySelectorAll(".mode-tab");
  const routing = document.getElementById("modeRouting");
  const predict = document.getElementById("modePredict");

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      if (tab.dataset.mode === "routing") {
        routing.classList.add("active");
        predict.classList.remove("active");
      } else {
        predict.classList.add("active");
        routing.classList.remove("active");
      }
    });
  });
}

/* ── NASA FIRMS Hotspots ─────────────────────────── */
async function loadHotspots() {
  try {
    const res  = await fetch("/api/hotspots");
    const data = await res.json();

    if (data.status === "success") {
      document.getElementById("activeFiresCountText").textContent =
        `${data.count.toLocaleString()} Active Satellite Fires`;

      appState.fireLayer.clearLayers();
      data.hotspots.forEach(h => {
        const radius = Math.min(14, Math.max(4, Math.sqrt(h.frp) * 2.2));
        const marker = L.circleMarker([h.lat, h.lon], {
          radius,
          fillColor: "#ef4444",
          color: "#b91c1c",
          weight: 1,
          opacity: 0.9,
          fillOpacity: h.confidence === "High" ? 0.85 : 0.6
        });
        marker.bindPopup(`
          <div style="font-size:12px;font-family:sans-serif;">
            <strong style="color:#b91c1c;">🔥 VIIRS Fire Hotspot</strong><br>
            <strong>FRP:</strong> ${h.frp.toFixed(2)} MW<br>
            <strong>Brightness:</strong> ${h.brightness.toFixed(1)} K<br>
            <strong>Confidence:</strong> ${h.confidence}
          </div>
        `);
        appState.fireLayer.addLayer(marker);
      });
    }
  } catch (err) {
    console.error("Hotspots fetch error:", err);
  }
}

/* ── Road Network & Shelters ─────────────────────── */
async function loadNetwork() {
  try {
    const res  = await fetch("/api/network");
    const data = await res.json();
    appState.networkData = data;

    appState.shelterLayer.clearLayers();
    data.shelters.forEach(s => {
      const marker = L.circleMarker([s.lat, s.lon], {
        radius: 7,
        fillColor: "#0284c7",
        color: "#0369a1",
        weight: 2,
        fillOpacity: 0.9
      });
      marker.bindPopup(`
        <div style="font-size:12px;font-family:sans-serif;">
          <strong style="color:#0284c7;">🛡️ ${s.name}</strong><br>
          <strong>Capacity:</strong> ${s.capacity} persons<br>
          <strong>Status:</strong> Active Evacuation Hub
        </div>
      `);
      appState.shelterLayer.addLayer(marker);
    });

    calculateRoute();
  } catch (err) {
    console.error("Network fetch error:", err);
  }
}

/* ── Routing ─────────────────────────────────────── */
function initRouting() {
  document.getElementById("calculateRouteBtn").addEventListener("click", calculateRoute);

  const checkbox   = document.getElementById("blockDirectGorge");
  const card       = document.getElementById("hazardToggleCard");
  const statusLbl  = document.getElementById("toggleStatusLabel");

  // Update visual state immediately when toggled
  checkbox.addEventListener("change", () => {
    const blocked = checkbox.checked;
    card.classList.toggle("blocked", blocked);
    statusLbl.textContent = blocked ? "BLOCKED" : "OPEN";
    calculateRoute();
  });
}

async function calculateRoute() {
  const source = document.getElementById("routeSource").value;
  const target = document.getElementById("routeDestination").value;

  const checkbox = document.getElementById("blockDirectGorge");
  const blocked  = checkbox.checked ? [checkbox.value] : [];

  const btn = document.getElementById("calculateRouteBtn");
  btn.textContent = "Computing...";
  btn.disabled = true;

  try {
    const res  = await fetch("/api/route", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source_id: source,
        target_id: target,
        blocked_edges: blocked,
        risk_multiplier: 6.0
      })
    });
    const data = await res.json();
    if (res.ok && data.success) {
      renderRoute(data);
    }
  } catch (err) {
    console.error("Routing error:", err);
  } finally {
    btn.textContent = "Compute Optimal Route";
    btn.disabled = false;
  }
}

function renderRoute(data) {
  const card = document.getElementById("routeResultsCard");
  card.style.display = "block";

  const s    = data.shortest_route;
  const safe = data.safest_route;
  const comp = data.comparison;

  document.getElementById("shortestDist").textContent = `${s.total_distance_km} km`;
  document.getElementById("safestDist").textContent   = `${safe.total_distance_km} km`;

  const sHaz = document.getElementById("shortestHazard");
  sHaz.textContent = `Hazard: ${s.average_hazard > 0.5 ? "High" : "Low"} (${s.average_hazard})`;
  sHaz.className   = `metric-hazard ${s.average_hazard > 0.5 ? "hazard-danger" : "hazard-safe"}`;

  const safeHaz = document.getElementById("safestHazard");
  safeHaz.textContent = `Hazard: ${safe.average_hazard > 0.5 ? "High" : "Low"} (${safe.average_hazard})`;
  safeHaz.className   = `metric-hazard ${safe.average_hazard > 0.5 ? "hazard-danger" : "hazard-safe"}`;

  const reductionPill = document.getElementById("hazardReductionPill");
  const thesisBadge   = document.getElementById("thesisBadge");
  const thesisText    = document.getElementById("thesisText");

  if (comp.thesis_verified) {
    thesisBadge.textContent   = "AI Safe Detour";
    reductionPill.textContent = `-${comp.hazard_exposure_reduction_pct}% Risk`;
    thesisText.innerHTML = `
      <strong>Principle:</strong> "The shortest route is not necessarily the safest route."
      AI detour bypassed the fire corridor — hazard reduced by <strong>${comp.hazard_exposure_reduction_pct}%</strong>.
    `;
  } else {
    thesisBadge.textContent   = "Direct Route Safe";
    reductionPill.textContent = "";
    thesisText.textContent    = "Direct corridor is clear of critical fire hazards.";
  }

  // Node trail
  const trail = document.getElementById("pathNodesList");
  trail.innerHTML = safe.path_names.map((n, i) => `
    <span class="trail-chip">${n}</span>
    ${i < safe.path_names.length - 1 ? '<span style="color:#94a3b8;">→</span>' : ""}
  `).join("");

  // Map lines
  appState.routeShortestLayer.clearLayers();
  appState.routeSafestLayer.clearLayers();

  if (!comp.paths_are_identical) {
    const directLine = L.polyline(s.coordinates, {
      color: "#ea580c",
      dashArray: "6, 8",
      weight: 3,
      opacity: 0.75
    });
    directLine.bindTooltip("Shortest (High Fire Exposure)");
    appState.routeShortestLayer.addLayer(directLine);
  }

  const safeLine = L.polyline(safe.coordinates, {
    color: "#10b981",
    weight: 4,
    opacity: 0.95
  });
  safeLine.bindTooltip(comp.paths_are_identical ? "Evacuation Route" : "Safest AI Detour");
  appState.routeSafestLayer.addLayer(safeLine);

  appState.map.fitBounds(L.latLngBounds(safe.coordinates), { padding: [60, 60] });
}

/* ── ML Risk Predictor ───────────────────────────── */
function initMLSliders() {
  const temp = document.getElementById("tempInput");
  const hum  = document.getElementById("humidityInput");
  const wind = document.getElementById("windInput");
  const rain = document.getElementById("rainInput");

  const syncLabels = () => {
    document.getElementById("tempValue").textContent     = `${temp.value}°C`;
    document.getElementById("humidityValue").textContent = `${hum.value}%`;
    document.getElementById("windValue").textContent     = `${wind.value} km/h`;
    document.getElementById("rainValue").textContent     = `${rain.value} mm`;
    evaluateRisk();
  };

  [temp, hum, wind, rain].forEach(el => el.addEventListener("input", syncLabels));

  document.querySelectorAll(".preset-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const p = PRESETS[chip.dataset.preset];
      if (!p) return;
      temp.value = p.temp;
      hum.value  = p.humidity;
      wind.value = p.wind;
      rain.value = p.rain;
      syncLabels();
    });
  });
}

async function evaluateRisk() {
  const payload = {
    temperature:            parseFloat(document.getElementById("tempInput").value),
    relative_humidity:      parseFloat(document.getElementById("humidityInput").value),
    wind_speed:             parseFloat(document.getElementById("windInput").value),
    rainfall:               parseFloat(document.getElementById("rainInput").value),
    ndvi:                   0.35,
    distance_to_settlement_km: 2.5,
    active_hotspots_nearby: 3
  };

  try {
    const res  = await fetch("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (res.ok && data.status === "success") {
      document.getElementById("riskScoreNumber").textContent = data.risk_score.toFixed(2);
      const tag = document.getElementById("riskCategoryText");
      tag.textContent = `${data.risk_level.toUpperCase()} RISK`;
      tag.style.color = data.risk_color;
      document.getElementById("riskGuidanceText").textContent = data.guidance;

      const f = data.contributing_factors;
      if (f) {
        document.getElementById("factorTemp").textContent = `${f["Temperature Impact"]}%`;
        document.getElementById("barTemp").style.width    = `${f["Temperature Impact"]}%`;
        document.getElementById("factorDry").textContent  = `${f["Dryness (Low Humidity)"]}%`;
        document.getElementById("barDry").style.width     = `${f["Dryness (Low Humidity)"]}%`;
        document.getElementById("factorWind").textContent = `${f["Wind Spread Potential"]}%`;
        document.getElementById("barWind").style.width    = `${f["Wind Spread Potential"]}%`;
      }
    }
  } catch (err) {
    console.error("Prediction error:", err);
  }
}

/* ── Test Cases Modal ────────────────────────────── */
function initTestModal() {
  const modal    = document.getElementById("testModal");
  const openBtn  = document.getElementById("openTestsBtn");
  const closeBtn = document.getElementById("closeTestsBtn");

  openBtn.addEventListener("click",  () => modal.classList.add("active"));
  closeBtn.addEventListener("click", () => modal.classList.remove("active"));
  modal.addEventListener("click", e => { if (e.target === modal) modal.classList.remove("active"); });
}

async function fetchTestResults() {
  try {
    const res  = await fetch("/api/test-cases");
    const data = await res.json();

    document.getElementById("modalPassedCount").textContent = data.passed;
    document.getElementById("modalFailedCount").textContent = data.failed;

    const list = document.getElementById("modalTestList");
    list.innerHTML = data.test_results.map(tc => `
      <div class="modal-test-item">
        <div class="mtest-top">
          <span><strong>${tc.test_id}:</strong> ${tc.name}</span>
          <span style="color:${tc.status === 'PASSED' ? '#10b981' : '#ef4444'};font-weight:800;">
            ${tc.status === "PASSED" ? "✓ PASSED" : "✗ FAILED"}
          </span>
        </div>
        <p class="mtest-desc">${tc.details}</p>
      </div>
    `).join("");
  } catch (err) {
    console.error("Test fetch error:", err);
    document.getElementById("modalTestList").innerHTML =
      '<p style="font-size:0.78rem;color:#ef4444;text-align:center;padding:1rem 0;">Could not load test results.</p>';
  }
}
