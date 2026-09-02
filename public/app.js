(() => {
  "use strict";

  const state = {
    range: "24h",
    period: "hour",
    metric: "load_power_w",
    current: null,
    health: null,
    history: null,
    historyRequest: 0,
  };

  const metricMeta = {
    load_power_w: { label: "Навантаження", unit: "W", color: "#efb35b", decimals: 0 },
    pv_power_w: { label: "PV генерація", unit: "W", color: "#56d8db", decimals: 0 },
    grid_power_w: { label: "Потік мережі", unit: "W", color: "#91a8ff", decimals: 0 },
    battery_power_w: { label: "Потужність батареї", unit: "W", color: "#71d39a", decimals: 0 },
    pv_voltage_v: { label: "PV voltage", unit: "V", color: "#56d8db", decimals: 1 },
    battery_voltage_v: { label: "Батарея", unit: "V", color: "#71d39a", decimals: 2 },
    inverter_voltage_v: { label: "AC output", unit: "V", color: "#91a8ff", decimals: 1 },
    grid_voltage_v: { label: "Grid voltage", unit: "V", color: "#91a8ff", decimals: 1 },
    bus_voltage_v: { label: "DC bus", unit: "V", color: "#c18bff", decimals: 1 },
    pv_current_a: { label: "PV current", unit: "A", color: "#56d8db", decimals: 1 },
    inverter_current_a: { label: "AC output current", unit: "A", color: "#91a8ff", decimals: 1 },
    grid_current_a: { label: "Grid current", unit: "A", color: "#91a8ff", decimals: 1 },
    load_current_a: { label: "Load current", unit: "A", color: "#efb35b", decimals: 1 },
    inverter_frequency_hz: { label: "Inverter frequency", unit: "Hz", color: "#c18bff", decimals: 2 },
    grid_frequency_hz: { label: "Grid frequency", unit: "Hz", color: "#c18bff", decimals: 2 },
    load_percent: { label: "Навантаження", unit: "%", color: "#efb35b", decimals: 0 },
    ac_radiator_temperature_c: { label: "AC radiator", unit: "°C", color: "#efb35b", decimals: 0 },
    transformer_temperature_c: { label: "Transformer", unit: "°C", color: "#efb35b", decimals: 0 },
    dc_radiator_temperature_c: { label: "DC radiator", unit: "°C", color: "#efb35b", decimals: 0 },
  };

  const $ = (id) => document.getElementById(id);
  const setText = (id, value) => { const node = $(id); if (node) node.textContent = value; };
  const safeNumber = (value) => typeof value === "number" && Number.isFinite(value);

  function number(value, decimals = 0) {
    if (!safeNumber(value)) return "--";
    return new Intl.NumberFormat("uk-UA", { maximumFractionDigits: decimals, minimumFractionDigits: decimals }).format(value);
  }

  function power(value) {
    if (!safeNumber(value)) return "--";
    const absolute = Math.abs(value);
    return absolute >= 1000 ? `${number(value / 1000, 2)} kW` : `${number(value, 0)} W`;
  }

  function valueWithUnit(value, unit, decimals = 1) {
    return safeNumber(value) ? `${number(value, decimals)} ${unit}` : `-- ${unit}`;
  }

  function timeLabel(iso) {
    if (!iso) return "очікування...";
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return "--";
    return new Intl.DateTimeFormat("uk-UA", { dateStyle: "short", timeStyle: "medium" }).format(date);
  }

  function shortTime(iso, period = state.period) {
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return "";
    if (period === "month" || period === "week") return new Intl.DateTimeFormat("uk-UA", { month: "short", day: "numeric" }).format(date);
    if (period === "day") return new Intl.DateTimeFormat("uk-UA", { month: "short", day: "numeric" }).format(date);
    return new Intl.DateTimeFormat("uk-UA", { hour: "2-digit", minute: "2-digit" }).format(date);
  }

  function statusMeta(status) {
    return {
      online: ["Підключено", "Система в нормі", "Канал відповідає"],
      degraded: ["Часткові дані", "Деградований режим", "Окремі блоки не відповідають"],
      offline: ["Немає зв'язку", "Offline", "Очікування відповіді від порту"],
      starting: ["Запуск сервісу", "Запуск", "Перший poll ще не завершено"],
      stale: ["Дані застаріли", "Stale", "Останній sample надто старий"],
    }[status] || ["Невідомо", "Невідомий стан", "Перевірте health endpoint"];
  }

  async function getJson(url) {
    const response = await fetch(url, { headers: { Accept: "application/json" }, cache: "no-store" });
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || `HTTP ${response.status}`);
    return body;
  }

  function renderHealth(health) {
    if (!health) return;
    state.health = health;
    const status = health.status || "starting";
    const [badge, title, detail] = statusMeta(status);
    const badgeNode = $("connectionBadge");
    const systemNode = $("systemState");
    if (badgeNode) { badgeNode.dataset.state = status; }
    if (systemNode) { systemNode.dataset.state = status; }
    setText("connectionLabel", badge);
    setText("systemStateTitle", title);
    setText("systemStateText", detail);
    setText("pollLatency", safeNumber(health.latency_ms) ? `${number(health.latency_ms, 0)} ms` : "--");
    const error = health.last_error ? `Помилка: ${health.last_error}` : "Read-only канал активний";
    setText("healthMessage", status === "online" ? "Read-only канал активний" : error);
    const diagnostic = $("diagnosticBadge");
    if (diagnostic) {
      diagnostic.dataset.state = status;
      diagnostic.textContent = status === "online" ? "NOMINAL" : status.toUpperCase();
    }
  }

  function renderCurrent(snapshot) {
    if (!snapshot) return;
    state.current = snapshot;
    const metrics = snapshot.metrics || {};
    const identity = snapshot.identity || {};
    const inverter = (snapshot.status && snapshot.status.inverter) || {};
    const charger = (snapshot.status && snapshot.status.charger) || {};
    setText("lastUpdated", timeLabel(snapshot.captured_at));
    setText("sourcePort", snapshot.source ? `${snapshot.source.port} · ID ${snapshot.source.slave_id}` : "USB serial");
    setText("pvPower", power(metrics.pv_power_w));
    setText("pvVoltage", valueWithUnit(metrics.pv_voltage_v, "V", 1));
    setText("pvCurrent", valueWithUnit(metrics.pv_current_a, "A", 1));
    setText("loadPower", power(metrics.load_power_w));
    setText("loadPercent", `${number(metrics.load_percent, 0)}%`);
    setText("loadCurrent", valueWithUnit(metrics.load_current_a, "A", 1));
    setText("gridPower", power(metrics.grid_power_w));
    setText("gridVoltage", valueWithUnit(metrics.grid_voltage_v, "V", 1));
    setText("gridFrequency", valueWithUnit(metrics.grid_frequency_hz, "Hz", 2));
    setText("batteryVoltage", valueWithUnit(metrics.battery_voltage_v, "V", 2));
    setText("batteryPower", valueWithUnit(metrics.battery_power_w, "W", 0));
    setText("batteryState", `стан ${stateLabel(inverter.work_state_code)}`);
    const loadBar = $("loadBar");
    if (loadBar) loadBar.style.width = `${Math.max(0, Math.min(100, metrics.load_percent || 0))}%`;
    const batteryBar = $("batteryBar");
    if (batteryBar) batteryBar.style.width = `${batteryVoltagePosition(metrics.battery_voltage_v, snapshot.configuration)}%`;

    setText("identityModel", identity.model || "PV1800");
    setText("ratedPower", safeNumber(metrics.rated_power_w) ? `${number(metrics.rated_power_w, 0)} W` : "--");
    setText("identitySerial", identity.serial_number || inverter.serial_number || "--");
    setText("identityFirmware", [identity.hardware_version, identity.software_version].filter(Boolean).join(" / ") || "--");
    setText("workState", inverter.work_state_code == null ? "--" : `CODE ${inverter.work_state_code}`);
    setText("inverterVoltage", valueWithUnit(metrics.inverter_voltage_v, "V", 1));
    setText("inverterCurrent", valueWithUnit(metrics.inverter_current_a, "A", 1));
    setText("inverterFrequency", valueWithUnit(metrics.inverter_frequency_hz, "Hz", 2));
    setText("inverterReactive", valueWithUnit(inverter.inverter_reactive_power_var, "var", 0));
    setText("busVoltage", valueWithUnit(metrics.bus_voltage_v, "V", 1));
    setText("batteryCurrent", safeNumber(inverter.battery_current_raw) ? `${number(inverter.battery_current_raw, 0)} raw` : "-- raw");
    setText("pvVoltageDetail", valueWithUnit(metrics.pv_voltage_v, "V", 1));
    setText("pvCurrentDetail", valueWithUnit(metrics.pv_current_a, "A", 1));
    setText("tempAc", valueWithUnit(metrics.ac_radiator_temperature_c, "°C", 0));
    setText("tempDc", valueWithUnit(metrics.dc_radiator_temperature_c, "°C", 0));
    setText("tempTransformer", valueWithUnit(metrics.transformer_temperature_c, "°C", 0));
    setText("tempCharger", valueWithUnit(charger.radiator_temperature_c, "°C", 0));
    setText("accumulatedLoad", energy(inverter.accumulated_load_power_wh));
    setText("accumulatedCharge", energy(inverter.accumulated_charger_power_wh));
    setText("accumulatedDischarge", energy(inverter.accumulated_discharger_power_wh));
    setText("chargerUptime", charger.accumulated_time || "--");
    renderConfiguration(snapshot.configuration);
    renderDiagnostics(snapshot);
    renderRaw(snapshot.raw);
  }

  function stateLabel(code) {
    if (code == null) return "--";
    return ({ 0: "standby", 1: "charging", 2: "inverting", 3: "fault" })[code] || `code ${code}`;
  }

  function batteryVoltagePosition(voltage, configuration) {
    if (!safeNumber(voltage)) return 0;
    const inverter = configuration && configuration.inverter;
    const low = safeNumber(inverter && inverter.battery_low_voltage_v) ? inverter.battery_low_voltage_v : 24;
    const high = safeNumber(inverter && inverter.battery_high_voltage_v) ? inverter.battery_high_voltage_v : 30;
    return Math.max(0, Math.min(100, ((voltage - low) / Math.max(.1, high - low)) * 100));
  }

  function energy(wh) {
    return safeNumber(wh) ? `${number(wh / 1000, 2)} kWh` : "-- kWh";
  }

  function renderConfiguration(configuration) {
    const charger = configuration && configuration.charger;
    const inverter = configuration && configuration.inverter;
    const chargerRows = [
      ["Charger", yesNo(charger && charger.charger_work_enabled)],
      ["Absorb voltage", valueWithUnit(charger && charger.absorb_voltage_v, "V", 1)],
      ["Float voltage", valueWithUnit(charger && charger.float_voltage_v, "V", 1)],
      ["Battery low", valueWithUnit(charger && charger.battery_low_voltage_v, "V", 1)],
      ["Battery high", valueWithUnit(charger && charger.battery_high_voltage_v, "V", 1)],
      ["Max current", valueWithUnit(charger && charger.max_charger_current_a, "A", 1)],
      ["Battery capacity", valueWithUnit(charger && charger.battery_capacity_ah, "Ah", 0)],
      ["Equalization", yesNo(charger && charger.equalization_enabled)],
    ];
    const inverterRows = [
      ["Off-grid", yesNo(inverter && inverter.offgrid_work_enabled)],
      ["Output", valueWithUnit(inverter && inverter.output_voltage_v, "V", 1)],
      ["Frequency", valueWithUnit(inverter && inverter.output_frequency_hz, "Hz", 2)],
      ["Search mode", yesNo(inverter && inverter.search_mode_enabled)],
      ["Energy mode", code(inverter && inverter.energy_use_mode_code)],
      ["Max discharge", valueWithUnit(inverter && inverter.max_discharger_current_a, "A", 1)],
      ["Grid charge", valueWithUnit(inverter && inverter.grid_max_charger_current_a, "A", 1)],
      ["Source priority", code(inverter && inverter.charger_source_priority_code)],
    ];
    renderKeyValues("chargerConfig", chargerRows);
    renderKeyValues("inverterConfig", inverterRows);
  }

  function yesNo(value) {
    if (typeof value !== "boolean") return "--";
    return value ? "Так" : "Ні";
  }

  function code(value) { return value == null ? "--" : `code ${value}`; }

  function renderKeyValues(id, rows) {
    const root = $(id);
    if (!root) return;
    root.replaceChildren();
    rows.forEach(([label, value]) => {
      const row = document.createElement("div");
      row.className = "key-value";
      const name = document.createElement("span");
      const result = document.createElement("span");
      name.textContent = label;
      result.textContent = value;
      row.append(name, result);
      root.append(row);
    });
  }

  function renderDiagnostics(snapshot) {
    const root = $("diagnosticsList");
    if (!root) return;
    const connection = snapshot.connection || {};
    const errors = connection.section_errors || {};
    const raw = snapshot.raw || {};
    const rows = [
      ["Serial channel", connection.status || "unknown"],
      ["Response latency", valueWithUnit(connection.latency_ms, "ms", 0)],
      ["Charger error code", code(snapshot.status && snapshot.status.charger && snapshot.status.charger.error_code)],
      ["Charger warning code", code(snapshot.status && snapshot.status.charger && snapshot.status.charger.warning_code)],
      ["Frames", `${Object.keys(raw).length} / ${Object.keys(raw).length + Object.keys(errors).length}`],
      ["Section errors", Object.keys(errors).length ? Object.keys(errors).join(", ") : "none"],
    ];
    root.replaceChildren();
    rows.forEach(([label, value]) => {
      const row = document.createElement("div");
      const name = document.createElement("span");
      const result = document.createElement("strong");
      name.textContent = label;
      result.textContent = value;
      row.append(name, result);
      root.append(row);
    });
  }

  function renderRaw(raw) {
    const root = $("rawRegisters");
    if (!root) return;
    root.replaceChildren();
    Object.entries(raw || {}).forEach(([section, registers]) => {
      const wrapper = document.createElement("div");
      wrapper.className = "raw-section";
      const title = document.createElement("h4");
      title.textContent = `${section} · ${registers.length} registers`;
      const table = document.createElement("table");
      table.className = "raw-table";
      const body = document.createElement("tbody");
      registers.forEach((register, index) => {
        const row = document.createElement("tr");
        const indexCell = document.createElement("td");
        const valueCell = document.createElement("td");
        indexCell.textContent = String(index);
        valueCell.textContent = `0x${Number(register).toString(16).padStart(4, "0").toUpperCase()} · ${register}`;
        row.append(indexCell, valueCell);
        body.append(row);
      });
      table.append(body);
      wrapper.append(title, table);
      root.append(wrapper);
    });
  }

  async function loadCurrent() {
    try {
      const response = await getJson("/api/current");
      renderHealth(response.health);
      if (response.data) renderCurrent(response.data);
    } catch (error) {
      renderHealth({ status: "offline", last_error: error.message });
    }
  }

  async function loadHistory() {
    const requestId = ++state.historyRequest;
    const url = `/api/history?range=${encodeURIComponent(state.range)}&period=${encodeURIComponent(state.period)}`;
    const exportUrl = `/api/export.csv?range=${encodeURIComponent(state.range)}&period=${encodeURIComponent(state.period)}`;
    const link = $("exportLink");
    if (link) link.href = exportUrl;
    try {
      const history = await getJson(url);
      if (requestId !== state.historyRequest) return;
      state.history = history;
      renderHistory(history);
    } catch (error) {
      if (requestId !== state.historyRequest) return;
      state.history = null;
      setText("historySummary", `Не вдалося завантажити історію: ${error.message}`);
      renderChart();
    }
  }

  function renderHistory(history) {
    const count = history.points ? history.points.length : 0;
    const suffix = history.truncated ? " · показано ліміт raw points" : "";
    setText("historySummary", `${count} ${count === 1 ? "точка" : "точок"} · ${history.period}${suffix}`);
    setText("legendLabel", (metricMeta[state.metric] || metricMeta.load_power_w).label);
    renderChart();
  }

  function renderChart() {
    const canvas = $("historyChart");
    const empty = $("chartEmpty");
    if (!canvas) return;
    const points = (state.history && state.history.points) || [];
    if (!points.length) {
      if (empty) empty.classList.remove("is-hidden");
      const context = canvas.getContext("2d");
      context.clearRect(0, 0, canvas.width, canvas.height);
      return;
    }
    if (empty) empty.classList.add("is-hidden");
    const rect = canvas.getBoundingClientRect();
    const ratio = window.devicePixelRatio || 1;
    canvas.width = Math.max(1, Math.floor(rect.width * ratio));
    canvas.height = Math.max(1, Math.floor(rect.height * ratio));
    const ctx = canvas.getContext("2d");
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    const width = rect.width;
    const height = rect.height;
    const padding = { top: 18, right: 12, bottom: 31, left: 46 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    const meta = metricMeta[state.metric] || metricMeta.load_power_w;
    const values = points.map((point) => point[state.metric]).filter(safeNumber);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!values.length) return;
    let min = Math.min(...values);
    let max = Math.max(...values);
    if (min === max) { min -= 1; max += 1; }
    const pad = (max - min) * .14;
    min -= pad; max += pad;
    const x = (index) => padding.left + (points.length === 1 ? chartWidth / 2 : index / (points.length - 1) * chartWidth);
    const y = (value) => padding.top + chartHeight - ((value - min) / (max - min)) * chartHeight;
    ctx.clearRect(0, 0, width, height);
    ctx.font = "9px IBM Plex Mono, monospace";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i += 1) {
      const lineY = padding.top + chartHeight * i / 4;
      ctx.strokeStyle = "rgba(173, 194, 208, .10)";
      ctx.beginPath(); ctx.moveTo(padding.left, lineY); ctx.lineTo(width - padding.right, lineY); ctx.stroke();
      ctx.fillStyle = "#52616d";
      ctx.fillText(formatAxis(max - (max - min) * i / 4, meta), 4, lineY + 3);
    }
    const valid = points.map((point, index) => safeNumber(point[state.metric]) ? [x(index), y(point[state.metric])] : null).filter(Boolean);
    if (!valid.length) return;
    const gradient = ctx.createLinearGradient(0, padding.top, 0, height - padding.bottom);
    gradient.addColorStop(0, hexToRgba(meta.color, .24));
    gradient.addColorStop(1, hexToRgba(meta.color, 0));
    ctx.beginPath();
    ctx.moveTo(valid[0][0], height - padding.bottom);
    valid.forEach(([pointX, pointY]) => ctx.lineTo(pointX, pointY));
    ctx.lineTo(valid[valid.length - 1][0], height - padding.bottom);
    ctx.closePath(); ctx.fillStyle = gradient; ctx.fill();
    ctx.beginPath();
    valid.forEach(([pointX, pointY], index) => index ? ctx.lineTo(pointX, pointY) : ctx.moveTo(pointX, pointY));
    ctx.strokeStyle = meta.color; ctx.lineWidth = 2; ctx.lineJoin = "round"; ctx.lineCap = "round"; ctx.stroke();
    ctx.fillStyle = "#52616d";
    const labels = Math.min(5, points.length);
    for (let i = 0; i < labels; i += 1) {
      const index = Math.round(i * (points.length - 1) / Math.max(1, labels - 1));
      ctx.fillText(shortTime(points[index].captured_at), x(index) - 18, height - 8);
    }
  }

  function formatAxis(value, meta) {
    if (!safeNumber(value)) return "--";
    return `${number(value, meta.decimals)} ${meta.unit}`;
  }

  function hexToRgba(hex, alpha) {
    const value = hex.replace("#", "");
    const bigint = parseInt(value, 16);
    return `rgba(${(bigint >> 16) & 255}, ${(bigint >> 8) & 255}, ${bigint & 255}, ${alpha})`;
  }

  function connectEvents() {
    if (!("EventSource" in window)) return;
    const events = new EventSource("/api/events");
    events.addEventListener("snapshot", (event) => {
      try {
        const payload = JSON.parse(event.data);
        renderHealth(payload.health);
        renderCurrent(payload.data);
        window.clearTimeout(state.historyTimer);
        state.historyTimer = window.setTimeout(loadHistory, 1000);
      } catch (error) { console.warn("Invalid snapshot event", error); }
    });
    events.addEventListener("health", (event) => {
      try { renderHealth(JSON.parse(event.data).health); } catch (error) { console.warn("Invalid health event", error); }
    });
    events.onerror = () => {
      if (!state.health || state.health.status === "online") renderHealth({ status: "offline", last_error: "SSE connection lost" });
    };
  }

  function bindControls() {
    const defaultPeriods = { "24h": "hour", "7d": "day", "30d": "day", "1y": "month", all: "month" };
    document.querySelectorAll("[data-range]").forEach((button) => button.addEventListener("click", () => {
      document.querySelectorAll("[data-range]").forEach((item) => item.classList.remove("is-active"));
      button.classList.add("is-active");
      state.range = button.dataset.range;
      state.period = defaultPeriods[state.range] || state.period;
      $("periodSelect").value = state.period;
      loadHistory();
    }));
    $("metricSelect").addEventListener("change", (event) => {
      state.metric = event.target.value;
      renderHistory(state.history || { points: [], period: state.period });
    });
    $("periodSelect").addEventListener("change", (event) => { state.period = event.target.value; loadHistory(); });
    $("refreshButton").addEventListener("click", () => { loadCurrent(); loadHistory(); });
    window.addEventListener("resize", () => renderChart());
  }

  async function boot() {
    bindControls();
    await Promise.all([loadCurrent(), loadHistory()]);
    connectEvents();
  }

  boot();
})();
