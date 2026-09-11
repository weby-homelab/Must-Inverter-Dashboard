(() => {
  "use strict";

  const translations = {
    uk: {
      "page.title": "MUST Power Desk",
      "page.description": "Локальний read-only моніторинг MUST PV18-3224 VPM II",
      "language.label": "Мова",
      "common.refresh": "Оновити дані",
      "common.waiting": "очікування...",
      "common.source_usb": "USB serial",
      "common.error": "Помилка",
      "common.code": "код",
      "common.none": "немає",
      "common.registers": "регістрів",
      "common.state": "стан",
      "common.not_available": "--",
      "hero.device": "PV18-3224 VPM II",
      "hero.live": "LIVE TELEMETRY",
      "hero.title": "Енергія",
      "hero.title2": "під контролем.",
      "hero.description": "Локальний read-only моніторинг інвертора. Жодних команд керування, лише точні дані з вашого USB Modbus-каналу.",
      "hero.last": "Останній знімок",
      "hero.source": "Джерело",
      "hero.nominal": "VA NOMINAL",
      "snapshot.note": "Дані оновлюються автоматично кожні 10 секунд",
      "section.now": "01 / ЗАРАЗ",
      "section.flow": "Потік енергії",
      "metric.pv.label": "PV input",
      "metric.pv.unit": "сонячна генерація",
      "metric.load.label": "Навантаження",
      "metric.load.unit": "поточне навантаження",
      "metric.grid.label": "Grid",
      "metric.grid.unit": "потік мережі",
      "metric.battery.label": "Battery",
      "metric.battery.unit": "напруга батареї",
      "metric.live": "LIVE",
      "metric.group_power": "Потік потужності",
      "metric.group_voltage": "Напруга",
      "metric.group_current": "Струм / частота",
      "metric.group_temperature": "Температура",
      "metric.option_load_power": "Навантаження, W",
      "metric.option_pv_power": "PV генерація, W",
      "metric.option_grid_power": "Потік мережі, W",
      "metric.option_battery_power": "Потужність батареї, W",
      "metric.option_load_percent": "Навантаження, %",
      "metric.option_battery_voltage": "Батарея, V",
      "metric.option_pv_voltage": "PV voltage, V",
      "metric.option_inverter_voltage": "AC output, V",
      "metric.option_grid_voltage": "Grid, V",
      "metric.option_bus_voltage": "DC bus, V",
      "metric.option_pv_current": "PV current, A",
      "metric.option_inverter_current": "AC output current, A",
      "metric.option_grid_current": "Grid current, A",
      "metric.option_load_current": "Load current, A",
      "metric.option_inverter_frequency": "Inverter frequency, Hz",
      "metric.option_grid_frequency": "Grid frequency, Hz",
      "metric.option_ac_temp": "AC radiator, °C",
      "metric.option_transformer_temp": "Transformer, °C",
      "metric.option_dc_temp": "DC radiator, °C",
      "operations.kicker": "02 / ОПЕРАТИВНО",
      "operations.title": "Оперативні графіки",
      "operations.note": "Вибраний період · live-дані кожні 10 секунд",
      "operations.aria_label": "Оперативні графіки моніторингу",
      "operations.live": "LIVE · 10 S",
      "operations.power.kicker": "POWER FLOW",
      "operations.power.title": "Потік потужності",
      "operations.power.aria_label": "Графік потоку потужності",
      "operations.battery.kicker": "BATTERY",
      "operations.battery.title": "Напруга батареї",
      "operations.battery.aria_label": "Графік напруги батареї",
      "operations.battery.caption": "Порогові значення з read-only конфігурації",
      "operations.battery.low": "MIN",
      "operations.battery.high": "MAX",
      "operations.thermal.kicker": "THERMAL",
      "operations.thermal.title": "Температури",
      "operations.thermal.aria_label": "Графік температур",
      "operations.legend.pv": "PV",
      "operations.legend.load": "Навантаження",
      "operations.legend.grid": "Grid",
      "operations.legend.battery": "Battery",
      "operations.legend.ac": "AC radiator",
      "operations.legend.transformer": "Transformer",
      "operations.legend.dc": "DC radiator",
      "history.kicker": "03 / ІСТОРІЯ",
      "history.title": "Поведінка системи",
      "history.range_aria": "Період історії",
      "history.chart_aria": "Графік історичних показників",
      "range.1h": "1 год",
      "range.6h": "6 год",
      "range.24h": "24 год",
      "range.7d": "7 днів",
      "range.30d": "30 днів",
      "range.1y": "1 рік",
      "range.all": "Усе",
      "history.metric": "Показник",
      "history.resolution": "Роздільність",
      "period.minute": "1 хв",
      "period.30m": "30 хв",
      "period.hour": "Година",
      "period.day": "День",
      "period.week": "Тиждень",
      "period.month": "Місяць",
      "period.raw": "Raw samples",
      "history.export": "CSV export",
      "history.empty": "Історія з'явиться після перших збережених samples",
      "history.no_data": "Немає збережених даних",
      "history.points_one": "точка",
      "history.points_many": "точок",
      "history.shown_limit": "показано ліміт raw points",
      "status.kicker": "04 / СТАН",
      "status.title": "Система",
      "status.model": "Модель",
      "status.nominal": "Номінал",
      "status.serial": "Serial number",
      "status.firmware": "Firmware",
      "status.poll": "Останній poll",
      "system.waiting": "Очікування",
      "system.connecting": "Підключення до інвертора",
      "system.connected": "Підключено",
      "system.ok": "Система в нормі",
      "system.channel_ok": "Канал відповідає",
      "system.partial": "Часткові дані",
      "system.degraded": "Деградований режим",
      "system.partial_detail": "Окремі блоки не відповідають",
      "system.offline": "Немає зв'язку",
      "system.offline_detail": "Очікування відповіді від порту",
      "system.starting": "Запуск сервісу",
      "system.starting_detail": "Перший poll ще не завершено",
      "system.stale": "Дані застаріли",
      "system.stale_detail": "Останній sample надто старий",
      "health.active": "Read-only канал активний",
      "health.stale_age": "Останній sample",
      "telemetry.kicker": "05 / TELEMETRY",
      "telemetry.title": "Деталі сигналу",
      "telemetry.ac": "AC output",
      "telemetry.dc": "DC / bus",
      "telemetry.temperatures": "Температури",
      "telemetry.accumulated": "Накопичені показники",
      "telemetry.current": "Струм",
      "telemetry.frequency": "Частота",
      "telemetry.reactive": "Reactive",
      "telemetry.battery_current": "Battery current",
      "telemetry.pv_voltage": "PV voltage",
      "telemetry.pv_current": "PV current",
      "telemetry.ac_radiator": "AC radiator",
      "telemetry.dc_radiator": "DC radiator",
      "telemetry.transformer": "Transformer",
      "telemetry.charger_radiator": "Charger radiator",
      "telemetry.charged": "Charged",
      "telemetry.discharged": "Discharged",
      "telemetry.uptime": "Charger uptime",
      "config.kicker": "06 / CONFIG",
      "config.title": "Параметри",
      "config.readonly": "READ ONLY",
      "config.charger": "Зарядний контур",
      "config.inverter": "Інверторний контур",
      "config.charger_work": "Charger",
      "config.absorb_voltage": "Absorb voltage",
      "config.float_voltage": "Float voltage",
      "config.battery_low": "Battery low",
      "config.battery_high": "Battery high",
      "config.max_current": "Max current",
      "config.capacity": "Battery capacity",
      "config.equalization": "Equalization",
      "config.offgrid": "Off-grid",
      "config.output": "Output",
      "config.frequency": "Frequency",
      "config.search_mode": "Search mode",
      "config.energy_mode": "Energy mode",
      "config.max_discharge": "Max discharge",
      "config.grid_charge": "Grid charge",
      "config.source_priority": "Source priority",
      "diagnostics.kicker": "07 / DIAGNOSTICS",
      "diagnostics.title": "Діагностика",
      "diagnostics.nominal": "NOMINAL",
      "diagnostics.channel": "Serial channel",
      "diagnostics.latency": "Response latency",
      "diagnostics.charger_error": "Charger error code",
      "diagnostics.charger_warning": "Charger warning code",
      "diagnostics.frames": "Frames",
      "diagnostics.section_errors": "Section errors",
      "diagnostics.raw": "Raw register frames",
      "diagnostics.expand": "розгорнути",
      "footer": "Local service · read-only Modbus RTU · UTC storage",
    },
    en: {
      "page.title": "MUST Power Desk",
      "page.description": "Local read-only monitoring for the MUST PV18-3224 VPM II",
      "language.label": "Language",
      "common.refresh": "Refresh data",
      "common.waiting": "waiting...",
      "common.source_usb": "USB serial",
      "common.error": "Error",
      "common.code": "code",
      "common.none": "none",
      "common.registers": "registers",
      "common.state": "state",
      "common.not_available": "--",
      "hero.device": "PV18-3224 VPM II",
      "hero.live": "LIVE TELEMETRY",
      "hero.title": "Energy",
      "hero.title2": "under control.",
      "hero.description": "Local read-only inverter monitoring. No control commands, only precise data from your USB Modbus channel.",
      "hero.last": "Last snapshot",
      "hero.source": "Source",
      "hero.nominal": "VA NOMINAL",
      "snapshot.note": "Data refresh automatically every 10 seconds",
      "section.now": "01 / NOW",
      "section.flow": "Energy flow",
      "metric.pv.label": "PV input",
      "metric.pv.unit": "solar generation",
      "metric.load.label": "Load",
      "metric.load.unit": "current demand",
      "metric.grid.label": "Grid",
      "metric.grid.unit": "grid flow",
      "metric.battery.label": "Battery",
      "metric.battery.unit": "battery voltage",
      "metric.live": "LIVE",
      "metric.group_power": "Power flow",
      "metric.group_voltage": "Voltage",
      "metric.group_current": "Current / frequency",
      "metric.group_temperature": "Temperature",
      "metric.option_load_power": "Load, W",
      "metric.option_pv_power": "PV generation, W",
      "metric.option_grid_power": "Grid flow, W",
      "metric.option_battery_power": "Battery power, W",
      "metric.option_load_percent": "Load, %",
      "metric.option_battery_voltage": "Battery, V",
      "metric.option_pv_voltage": "PV voltage, V",
      "metric.option_inverter_voltage": "AC output, V",
      "metric.option_grid_voltage": "Grid, V",
      "metric.option_bus_voltage": "DC bus, V",
      "metric.option_pv_current": "PV current, A",
      "metric.option_inverter_current": "AC output current, A",
      "metric.option_grid_current": "Grid current, A",
      "metric.option_load_current": "Load current, A",
      "metric.option_inverter_frequency": "Inverter frequency, Hz",
      "metric.option_grid_frequency": "Grid frequency, Hz",
      "metric.option_ac_temp": "AC radiator, °C",
      "metric.option_transformer_temp": "Transformer, °C",
      "metric.option_dc_temp": "DC radiator, °C",
      "operations.kicker": "02 / OPERATIONS",
      "operations.title": "Operational charts",
      "operations.note": "Selected range · live data every 10 seconds",
      "operations.aria_label": "Operational monitoring charts",
      "operations.live": "LIVE · 10 S",
      "operations.power.kicker": "POWER FLOW",
      "operations.power.title": "Power flow",
      "operations.power.aria_label": "Power flow chart",
      "operations.battery.kicker": "BATTERY",
      "operations.battery.title": "Battery voltage",
      "operations.battery.aria_label": "Battery voltage chart",
      "operations.battery.caption": "Thresholds from read-only configuration",
      "operations.battery.low": "LOW",
      "operations.battery.high": "HIGH",
      "operations.thermal.kicker": "THERMAL",
      "operations.thermal.title": "Temperatures",
      "operations.thermal.aria_label": "Temperature chart",
      "operations.legend.pv": "PV",
      "operations.legend.load": "Load",
      "operations.legend.grid": "Grid",
      "operations.legend.battery": "Battery",
      "operations.legend.ac": "AC radiator",
      "operations.legend.transformer": "Transformer",
      "operations.legend.dc": "DC radiator",
      "history.kicker": "03 / HISTORY",
      "history.title": "System behavior",
      "history.range_aria": "History range",
      "history.chart_aria": "Historical metrics chart",
      "range.1h": "1 hr",
      "range.6h": "6 hrs",
      "range.24h": "24 hrs",
      "range.7d": "7 days",
      "range.30d": "30 days",
      "range.1y": "1 year",
      "range.all": "All",
      "history.metric": "Metric",
      "history.resolution": "Resolution",
      "period.minute": "1 min",
      "period.30m": "30 min",
      "period.hour": "Hour",
      "period.day": "Day",
      "period.week": "Week",
      "period.month": "Month",
      "period.raw": "Raw samples",
      "history.export": "CSV export",
      "history.empty": "History will appear after the first saved samples",
      "history.no_data": "No saved data",
      "history.points_one": "point",
      "history.points_many": "points",
      "history.shown_limit": "raw point limit shown",
      "status.kicker": "04 / STATUS",
      "status.title": "System",
      "status.model": "Model",
      "status.nominal": "Rated",
      "status.serial": "Serial number",
      "status.firmware": "Firmware",
      "status.poll": "Last poll",
      "system.waiting": "Waiting",
      "system.connecting": "Connecting to inverter",
      "system.connected": "Connected",
      "system.ok": "System nominal",
      "system.channel_ok": "Channel responding",
      "system.partial": "Partial data",
      "system.degraded": "Degraded mode",
      "system.partial_detail": "Some sections are not responding",
      "system.offline": "No connection",
      "system.offline_detail": "Waiting for a port response",
      "system.starting": "Starting service",
      "system.starting_detail": "First poll is not complete",
      "system.stale": "Data is stale",
      "system.stale_detail": "The last sample is too old",
      "health.active": "Read-only channel active",
      "health.stale_age": "Last sample",
      "telemetry.kicker": "05 / TELEMETRY",
      "telemetry.title": "Signal details",
      "telemetry.ac": "AC output",
      "telemetry.dc": "DC / bus",
      "telemetry.temperatures": "Temperatures",
      "telemetry.accumulated": "Accumulated",
      "telemetry.current": "Current",
      "telemetry.frequency": "Frequency",
      "telemetry.reactive": "Reactive",
      "telemetry.battery_current": "Battery current",
      "telemetry.pv_voltage": "PV voltage",
      "telemetry.pv_current": "PV current",
      "telemetry.ac_radiator": "AC radiator",
      "telemetry.dc_radiator": "DC radiator",
      "telemetry.transformer": "Transformer",
      "telemetry.charger_radiator": "Charger radiator",
      "telemetry.charged": "Charged",
      "telemetry.discharged": "Discharged",
      "telemetry.uptime": "Charger uptime",
      "config.kicker": "06 / CONFIG",
      "config.title": "Configuration",
      "config.readonly": "READ ONLY",
      "config.charger": "Charger circuit",
      "config.inverter": "Inverter circuit",
      "config.charger_work": "Charger",
      "config.absorb_voltage": "Absorb voltage",
      "config.float_voltage": "Float voltage",
      "config.battery_low": "Battery low",
      "config.battery_high": "Battery high",
      "config.max_current": "Max current",
      "config.capacity": "Battery capacity",
      "config.equalization": "Equalization",
      "config.offgrid": "Off-grid",
      "config.output": "Output",
      "config.frequency": "Frequency",
      "config.search_mode": "Search mode",
      "config.energy_mode": "Energy mode",
      "config.max_discharge": "Max discharge",
      "config.grid_charge": "Grid charge",
      "config.source_priority": "Source priority",
      "diagnostics.kicker": "07 / DIAGNOSTICS",
      "diagnostics.title": "Diagnostics",
      "diagnostics.nominal": "NOMINAL",
      "diagnostics.channel": "Serial channel",
      "diagnostics.latency": "Response latency",
      "diagnostics.charger_error": "Charger error code",
      "diagnostics.charger_warning": "Charger warning code",
      "diagnostics.frames": "Frames",
      "diagnostics.section_errors": "Section errors",
      "diagnostics.raw": "Raw register frames",
      "diagnostics.expand": "expand",
      "footer": "Local service · read-only Modbus RTU · UTC storage",
    },
  };

  const state = {
    range: "24h",
    period: "30m",
    metric: "load_power_w",
    language: readLanguage(),
    current: null,
    health: null,
    history: null,
    historyRequest: 0,
    livePoints: [],
    refreshTimer: null,
    chartModels: new Map(),
    chartPointers: new Map(),
    activeChartId: null,
  };

  const REFRESH_INTERVAL_MS = 10_000;
  const LIVE_BUFFER_MS = 6 * 60 * 60 * 1000;
  const MAX_OPERATIONAL_POINTS = 2400;

  const metricMeta = {
    load_power_w: { labelKey: "metric.load.label", unit: "W", color: "#efb35b", decimals: 0 },
    pv_power_w: { labelKey: "metric.pv.label", unit: "W", color: "#56d8db", decimals: 0 },
    grid_power_w: { labelKey: "metric.grid.label", unit: "W", color: "#91a8ff", decimals: 0 },
    battery_power_w: { labelKey: "metric.battery.label", unit: "W", color: "#71d39a", decimals: 0 },
    pv_voltage_v: { labelKey: "telemetry.pv_voltage", unit: "V", color: "#56d8db", decimals: 1 },
    battery_voltage_v: { labelKey: "metric.battery.label", unit: "V", color: "#71d39a", decimals: 2 },
    inverter_voltage_v: { labelKey: "telemetry.ac", unit: "V", color: "#91a8ff", decimals: 1 },
    grid_voltage_v: { labelKey: "metric.grid.label", unit: "V", color: "#91a8ff", decimals: 1 },
    bus_voltage_v: { labelKey: "telemetry.dc", unit: "V", color: "#c18bff", decimals: 1 },
    pv_current_a: { labelKey: "telemetry.pv_current", unit: "A", color: "#56d8db", decimals: 1 },
    inverter_current_a: { labelKey: "telemetry.ac", unit: "A", color: "#91a8ff", decimals: 1 },
    grid_current_a: { labelKey: "metric.grid.label", unit: "A", color: "#91a8ff", decimals: 1 },
    load_current_a: { labelKey: "metric.load.label", unit: "A", color: "#efb35b", decimals: 1 },
    inverter_frequency_hz: { labelKey: "telemetry.frequency", unit: "Hz", color: "#c18bff", decimals: 2 },
    grid_frequency_hz: { labelKey: "telemetry.frequency", unit: "Hz", color: "#c18bff", decimals: 2 },
    load_percent: { labelKey: "metric.load.label", unit: "%", color: "#efb35b", decimals: 0 },
    ac_radiator_temperature_c: { labelKey: "telemetry.ac_radiator", unit: "°C", color: "#efb35b", decimals: 0 },
    transformer_temperature_c: { labelKey: "telemetry.transformer", unit: "°C", color: "#efb35b", decimals: 0 },
    dc_radiator_temperature_c: { labelKey: "telemetry.dc_radiator", unit: "°C", color: "#efb35b", decimals: 0 },
  };

  const operationalChartSpecs = [
    {
      canvasId: "powerChart",
      emptyId: "powerChartEmpty",
      unit: "W",
      decimals: 0,
      zeroLine: true,
      series: [
        { metric: "pv_power_w", labelKey: "operations.legend.pv", color: "#56d8db" },
        { metric: "load_power_w", labelKey: "operations.legend.load", color: "#efb35b" },
        { metric: "grid_power_w", labelKey: "operations.legend.grid", color: "#91a8ff" },
        { metric: "battery_power_w", labelKey: "operations.legend.battery", color: "#71d39a" },
      ],
    },
    {
      canvasId: "batteryChart",
      emptyId: "batteryChartEmpty",
      unit: "V",
      decimals: 2,
      references: "battery",
      series: [
        { metric: "battery_voltage_v", labelKey: "metric.battery.label", color: "#71d39a" },
      ],
    },
    {
      canvasId: "thermalChart",
      emptyId: "thermalChartEmpty",
      unit: "°C",
      decimals: 0,
      series: [
        { metric: "ac_radiator_temperature_c", labelKey: "operations.legend.ac", color: "#efb35b" },
        { metric: "transformer_temperature_c", labelKey: "operations.legend.transformer", color: "#ef7272" },
        { metric: "dc_radiator_temperature_c", labelKey: "operations.legend.dc", color: "#c18bff" },
      ],
    },
  ];

  const $ = (id) => document.getElementById(id);
  const setText = (id, value) => { const node = $(id); if (node) node.textContent = value; };
  const safeNumber = (value) => typeof value === "number" && Number.isFinite(value);

  function readLanguage() {
    try {
      return localStorage.getItem("must-power-desk-language") === "en" ? "en" : "uk";
    } catch (error) {
      return "uk";
    }
  }

  function t(key) {
    return translations[state.language][key] || translations.uk[key] || key;
  }

  function applyLanguage() {
    document.documentElement.lang = state.language === "en" ? "en" : "uk";
    document.title = t("page.title");
    const description = document.querySelector('meta[name="description"]');
    if (description) description.content = t("page.description");
    document.querySelectorAll("[data-i18n]").forEach((node) => { node.textContent = t(node.dataset.i18n); });
    document.querySelectorAll("[data-i18n-label]").forEach((node) => { node.label = t(node.dataset.i18nLabel); });
    document.querySelectorAll("[data-i18n-title]").forEach((node) => { node.title = t(node.dataset.i18nTitle); });
    document.querySelectorAll("[data-i18n-aria-label]").forEach((node) => { node.setAttribute("aria-label", t(node.dataset.i18nAriaLabel)); });
    document.querySelectorAll("[data-lang]").forEach((button) => {
      const active = button.dataset.lang === state.language;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", String(active));
    });
    if (state.health) renderHealth(state.health);
    if (state.current) renderCurrent(state.current);
    if (state.history) renderHistory(state.history);
  }

  function locale() { return state.language === "en" ? "en-GB" : "uk-UA"; }

  function number(value, decimals = 0) {
    if (!safeNumber(value)) return "--";
    return new Intl.NumberFormat(locale(), { maximumFractionDigits: decimals, minimumFractionDigits: decimals }).format(value);
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
    if (!iso) return t("common.waiting");
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return "--";
    return new Intl.DateTimeFormat(locale(), { dateStyle: "short", timeStyle: "medium" }).format(date);
  }

  function shortTime(iso, period = state.period) {
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return "";
    if (period === "month" || period === "week" || period === "day") return new Intl.DateTimeFormat(locale(), { month: "short", day: "numeric" }).format(date);
    return new Intl.DateTimeFormat(locale(), { hour: "2-digit", minute: "2-digit" }).format(date);
  }

  function statusMeta(status) {
    return {
      online: [t("system.connected"), t("system.ok"), t("system.channel_ok")],
      degraded: [t("system.partial"), t("system.degraded"), t("system.partial_detail")],
      offline: [t("system.offline"), t("system.offline"), t("system.offline_detail")],
      starting: [t("system.starting"), t("system.waiting"), t("system.starting_detail")],
      stale: [t("system.stale"), t("system.stale"), t("system.stale_detail")],
    }[status] || [t("common.not_available"), t("common.not_available"), t("common.not_available")];
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
    document.querySelectorAll(".operational-live").forEach((node) => { node.dataset.state = status; });
    setText("connectionLabel", badge);
    setText("systemStateTitle", title);
    setText("systemStateText", detail);
    setText("pollLatency", safeNumber(health.latency_ms) ? `${number(health.latency_ms, 0)} ms` : "--");
    const error = health.last_error ? `${t("common.error")}: ${health.last_error}` : t("health.active");
    const staleAge = safeNumber(health.sample_age_seconds) ? ` · ${number(health.sample_age_seconds, 0)} s` : "";
    setText("healthMessage", status === "online" ? t("health.active") : status === "stale" ? `${t("health.stale_age")}${staleAge}` : error);
    const diagnostic = $("diagnosticBadge");
    if (diagnostic) {
      diagnostic.dataset.state = status;
      diagnostic.textContent = status === "online" ? t("diagnostics.nominal") : status.toUpperCase();
    }
  }

  function renderCurrent(snapshot) {
    if (!snapshot) return;
    state.current = snapshot;
    rememberLivePoint(snapshot);
    const metrics = snapshot.metrics || {};
    const identity = snapshot.identity || {};
    const inverter = (snapshot.status && snapshot.status.inverter) || {};
    const charger = (snapshot.status && snapshot.status.charger) || {};
    setText("lastUpdated", timeLabel(snapshot.captured_at));
    setText("sourcePort", snapshot.source ? `${snapshot.source.port} · ID ${snapshot.source.slave_id}` : t("common.source_usb"));
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
    setText("batteryState", `${t("common.state")} ${stateLabel(inverter.work_state_code)}`);
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
    renderOperationalCharts();
  }

  function stateLabel(code) {
    if (code == null) return t("common.not_available");
    const labels = {
      0: state.language === "en" ? "standby" : "очікування",
      1: state.language === "en" ? "charging" : "заряджання",
      2: state.language === "en" ? "inverting" : "інвертування",
      3: state.language === "en" ? "fault" : "помилка",
    };
    return labels[code] || `${t("common.code")} ${code}`;
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
      [t("config.charger_work"), yesNo(charger && charger.charger_work_enabled)],
      [t("config.absorb_voltage"), valueWithUnit(charger && charger.absorb_voltage_v, "V", 1)],
      [t("config.float_voltage"), valueWithUnit(charger && charger.float_voltage_v, "V", 1)],
      [t("config.battery_low"), valueWithUnit(charger && charger.battery_low_voltage_v, "V", 1)],
      [t("config.battery_high"), valueWithUnit(charger && charger.battery_high_voltage_v, "V", 1)],
      [t("config.max_current"), valueWithUnit(charger && charger.max_charger_current_a, "A", 1)],
      [t("config.capacity"), valueWithUnit(charger && charger.battery_capacity_ah, "Ah", 0)],
      [t("config.equalization"), yesNo(charger && charger.equalization_enabled)],
    ];
    const inverterRows = [
      [t("config.offgrid"), yesNo(inverter && inverter.offgrid_work_enabled)],
      [t("config.output"), valueWithUnit(inverter && inverter.output_voltage_v, "V", 1)],
      [t("config.frequency"), valueWithUnit(inverter && inverter.output_frequency_hz, "Hz", 2)],
      [t("config.search_mode"), yesNo(inverter && inverter.search_mode_enabled)],
      [t("config.energy_mode"), code(inverter && inverter.energy_use_mode_code)],
      [t("config.max_discharge"), valueWithUnit(inverter && inverter.max_discharger_current_a, "A", 1)],
      [t("config.grid_charge"), valueWithUnit(inverter && inverter.grid_max_charger_current_a, "A", 1)],
      [t("config.source_priority"), code(inverter && inverter.charger_source_priority_code)],
    ];
    renderKeyValues("chargerConfig", chargerRows);
    renderKeyValues("inverterConfig", inverterRows);
  }

  function yesNo(value) {
    if (typeof value !== "boolean") return "--";
    return value ? (state.language === "en" ? "Yes" : "Так") : (state.language === "en" ? "No" : "Ні");
  }

  function code(value) { return value == null ? t("common.not_available") : `${t("common.code")} ${value}`; }

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
      [t("diagnostics.channel"), connection.status || t("common.not_available")],
      [t("diagnostics.latency"), valueWithUnit(connection.latency_ms, "ms", 0)],
      [t("diagnostics.charger_error"), code(snapshot.status && snapshot.status.charger && snapshot.status.charger.error_code)],
      [t("diagnostics.charger_warning"), code(snapshot.status && snapshot.status.charger && snapshot.status.charger.warning_code)],
      [t("diagnostics.frames"), `${Object.keys(raw).length} / ${Object.keys(raw).length + Object.keys(errors).length}`],
      [t("diagnostics.section_errors"), Object.keys(errors).length ? Object.keys(errors).join(", ") : t("common.none")],
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
      title.textContent = `${section} · ${registers.length} ${t("common.registers")}`;
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
      setText("historySummary", `${t("common.error")}: ${error.message}`);
      renderChart();
      renderOperationalCharts();
    }
  }

  function renderHistory(history) {
    const count = history.points ? history.points.length : 0;
    const suffix = history.truncated ? ` · ${t("history.shown_limit")}` : "";
    const pointWord = count === 1 ? t("history.points_one") : t("history.points_many");
    const periodLabel = t(`period.${history.period || state.period}`);
    setText("historySummary", `${count} ${pointWord} · ${periodLabel}${suffix}`);
    setText("legendLabel", t((metricMeta[state.metric] || metricMeta.load_power_w).labelKey));
    renderChart();
    renderOperationalCharts();
  }

  function renderChart() {
    const canvas = $("historyChart");
    const empty = $("chartEmpty");
    if (!canvas) return;
    state.chartModels.delete(canvas.id);
    hideChartTooltip(canvas.id);
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
    if (!values.length) {
      if (empty) empty.classList.remove("is-hidden");
      return;
    }
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
    state.chartModels.set(canvas.id, {
      canvasId: canvas.id,
      points,
      series: [{ metric: state.metric, label: t(meta.labelKey), unit: meta.unit, decimals: meta.decimals, color: meta.color }],
      x,
      y,
      padding,
      chartWidth,
      chartHeight,
      width,
      height,
    });
    refreshChartTooltip(canvas.id);
  }

  function rememberLivePoint(snapshot) {
    if (!snapshot || !snapshot.captured_at) return;
    const point = { captured_at: snapshot.captured_at, ...(snapshot.metrics || {}) };
    const existing = state.livePoints.findIndex((item) => item.captured_at === point.captured_at);
    if (existing >= 0) state.livePoints[existing] = point;
    else state.livePoints.push(point);
    const cutoff = Date.now() - LIVE_BUFFER_MS;
    state.livePoints = state.livePoints.filter((item) => {
      const timestamp = Date.parse(item.captured_at);
      return Number.isFinite(timestamp) && timestamp >= cutoff;
    });
  }

  function operationalPoints() {
    const historyPoints = state.history && Array.isArray(state.history.points) ? state.history.points : [];
    const from = state.history && state.history.from ? Date.parse(state.history.from) : NaN;
    const points = new Map();
    [...historyPoints, ...state.livePoints].forEach((point) => {
      const timestamp = Date.parse(point.captured_at);
      if (!Number.isFinite(timestamp) || (Number.isFinite(from) && timestamp < from)) return;
      points.set(point.captured_at, point);
    });
    return limitOperationalPoints([...points.values()].sort((left, right) => (
      Date.parse(left.captured_at) - Date.parse(right.captured_at)
    )));
  }

  function limitOperationalPoints(points) {
    if (points.length <= MAX_OPERATIONAL_POINTS) return points;
    return Array.from({ length: MAX_OPERATIONAL_POINTS }, (_, index) => (
      points[Math.round(index * (points.length - 1) / (MAX_OPERATIONAL_POINTS - 1))]
    ));
  }

  function batteryReferenceLines() {
    const configuration = state.current && state.current.configuration;
    const charger = configuration && configuration.charger;
    const inverter = configuration && configuration.inverter;
    const low = safeNumber(inverter && inverter.battery_low_voltage_v)
      ? inverter.battery_low_voltage_v
      : charger && charger.battery_low_voltage_v;
    const high = safeNumber(inverter && inverter.battery_high_voltage_v)
      ? inverter.battery_high_voltage_v
      : charger && charger.battery_high_voltage_v;
    return [
      safeNumber(low) ? { value: low, label: t("operations.battery.low"), color: "#ef7272" } : null,
      safeNumber(high) ? { value: high, label: t("operations.battery.high"), color: "#56d8db" } : null,
    ].filter(Boolean);
  }

  function renderOperationalCharts() {
    const points = operationalPoints();
    operationalChartSpecs.forEach((spec) => drawOperationalChart(spec, points));
  }

  function drawOperationalChart(spec, points) {
    const canvas = $(spec.canvasId);
    const empty = $(spec.emptyId);
    if (!canvas) return;
    state.chartModels.delete(canvas.id);
    hideChartTooltip(canvas.id);
    const rect = canvas.getBoundingClientRect();
    const width = Math.max(1, rect.width);
    const height = Math.max(1, rect.height);
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.max(1, Math.floor(width * ratio));
    canvas.height = Math.max(1, Math.floor(height * ratio));
    const ctx = canvas.getContext("2d");
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    ctx.clearRect(0, 0, width, height);
    if (!points.length) {
      if (empty) empty.classList.remove("is-hidden");
      return;
    }

    const padding = { top: 14, right: 12, bottom: 27, left: 48 };
    const chartWidth = Math.max(1, width - padding.left - padding.right);
    const chartHeight = Math.max(1, height - padding.top - padding.bottom);
    const references = spec.references === "battery" ? batteryReferenceLines() : [];
    const seriesValues = spec.series.flatMap((series) => points.map((point) => point[series.metric]).filter(safeNumber));
    if (!seriesValues.length) {
      if (empty) empty.classList.remove("is-hidden");
      return;
    }
    if (empty) empty.classList.add("is-hidden");
    const values = [...seriesValues, ...references.map((reference) => reference.value)];
    let min = Math.min(...values);
    let max = Math.max(...values);
    if (min === max) { min -= 1; max += 1; }
    const paddingValue = (max - min) * 0.12;
    min -= paddingValue;
    max += paddingValue;
    const x = (index) => padding.left + (points.length === 1
      ? chartWidth / 2
      : index / (points.length - 1) * chartWidth);
    const y = (value) => padding.top + chartHeight - ((value - min) / (max - min)) * chartHeight;

    ctx.font = "9px IBM Plex Mono, monospace";
    ctx.lineWidth = 1;
    for (let index = 0; index <= 3; index += 1) {
      const lineY = padding.top + chartHeight * index / 3;
      ctx.strokeStyle = "rgba(173, 194, 208, .10)";
      ctx.beginPath();
      ctx.moveTo(padding.left, lineY);
      ctx.lineTo(width - padding.right, lineY);
      ctx.stroke();
      ctx.fillStyle = "#52616d";
      ctx.fillText(formatAxis(max - (max - min) * index / 3, spec), 4, lineY + 3);
    }

    if (spec.zeroLine && min < 0 && max > 0) {
      const zeroY = y(0);
      ctx.strokeStyle = "rgba(232, 237, 240, .26)";
      ctx.beginPath();
      ctx.moveTo(padding.left, zeroY);
      ctx.lineTo(width - padding.right, zeroY);
      ctx.stroke();
    }

    references.forEach((reference) => {
      const lineY = y(reference.value);
      ctx.setLineDash([4, 4]);
      ctx.strokeStyle = reference.color;
      ctx.globalAlpha = 0.55;
      ctx.beginPath();
      ctx.moveTo(padding.left, lineY);
      ctx.lineTo(width - padding.right, lineY);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.globalAlpha = 1;
      ctx.fillStyle = reference.color;
      ctx.fillText(`${reference.label} ${number(reference.value, spec.decimals)} ${spec.unit}`, padding.left + 5, lineY - 4);
    });

    spec.series.forEach((series) => {
      let lastPoint = null;
      let drawing = false;
      ctx.beginPath();
      points.forEach((point, index) => {
        const value = point[series.metric];
        if (!safeNumber(value)) {
          drawing = false;
          return;
        }
        const pointX = x(index);
        const pointY = y(value);
        if (drawing) ctx.lineTo(pointX, pointY);
        else ctx.moveTo(pointX, pointY);
        drawing = true;
        lastPoint = [pointX, pointY];
      });
      ctx.strokeStyle = series.color;
      ctx.lineWidth = 1.7;
      ctx.lineJoin = "round";
      ctx.lineCap = "round";
      ctx.stroke();
      if (lastPoint) {
        ctx.fillStyle = series.color;
        ctx.beginPath();
        ctx.arc(lastPoint[0], lastPoint[1], 2.5, 0, Math.PI * 2);
        ctx.fill();
      }
    });

    ctx.fillStyle = "#52616d";
    const labels = Math.min(4, points.length);
    for (let index = 0; index < labels; index += 1) {
      const pointIndex = Math.round(index * (points.length - 1) / Math.max(1, labels - 1));
      ctx.fillText(shortTime(points[pointIndex].captured_at), x(pointIndex) - 18, height - 7);
    }
    state.chartModels.set(canvas.id, {
      canvasId: canvas.id,
      points,
      series: spec.series.map((series) => ({
        metric: series.metric,
        label: t(series.labelKey),
        unit: spec.unit,
        decimals: spec.decimals,
        color: series.color,
      })),
      x,
      y,
      padding,
      chartWidth,
      chartHeight,
      width,
      height,
    });
    refreshChartTooltip(canvas.id);
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

  function bindChartHover() {
    document.querySelectorAll("#historyChart, .operational-chart-wrap canvas").forEach((canvas) => {
      canvas.addEventListener("mousemove", handleChartMove);
      canvas.addEventListener("mouseleave", () => {
        state.chartPointers.delete(canvas.id);
        hideChartTooltip(canvas.id);
      });
    });
  }

  function handleChartMove(event) {
    const canvas = event.currentTarget;
    const model = state.chartModels.get(canvas.id);
    if (!model || !model.points.length) {
      hideChartTooltip(canvas.id);
      return;
    }
    const pointer = { clientX: event.clientX, clientY: event.clientY };
    state.chartPointers.set(canvas.id, pointer);
    const rect = canvas.getBoundingClientRect();
    const chartX = Math.max(0, Math.min(model.chartWidth, event.clientX - rect.left - model.padding.left));
    const position = model.points.length === 1 ? 0 : chartX / model.chartWidth * (model.points.length - 1);
    const index = Math.max(0, Math.min(model.points.length - 1, Math.round(position)));
    showChartTooltip(model, index, pointer.clientX, pointer.clientY);
  }

  function showChartTooltip(model, index, clientX, clientY) {
    const tooltip = $("chartTooltip");
    const time = $("chartTooltipTime");
    const values = $("chartTooltipValues");
    const point = model.points[index];
    if (!tooltip || !time || !values || !point) return;
    time.textContent = timeLabel(point.captured_at);
    values.replaceChildren();
    model.series.forEach((series) => {
      const row = document.createElement("div");
      row.className = "chart-tooltip-row";
      const label = document.createElement("span");
      const swatch = document.createElement("i");
      const result = document.createElement("span");
      swatch.style.background = series.color;
      label.append(swatch, document.createTextNode(series.label));
      result.textContent = safeNumber(point[series.metric])
        ? `${number(point[series.metric], series.decimals)} ${series.unit}`
        : t("common.not_available");
      row.append(label, result);
      values.append(row);
    });
    state.activeChartId = model.canvasId;
    tooltip.setAttribute("aria-hidden", "false");
    tooltip.classList.add("is-visible");
    tooltip.style.left = `${clientX + 14}px`;
    tooltip.style.top = `${clientY + 14}px`;
    const bounds = tooltip.getBoundingClientRect();
    const margin = 8;
    const left = Math.max(margin, Math.min(clientX + 14, window.innerWidth - bounds.width - margin));
    const top = Math.max(margin, Math.min(clientY + 14, window.innerHeight - bounds.height - margin));
    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${top}px`;
  }

  function refreshChartTooltip(chartId) {
    const pointer = state.chartPointers.get(chartId);
    const model = state.chartModels.get(chartId);
    if (!pointer || !model) return;
    showChartTooltip(model, nearestChartIndex(model, pointer.clientX), pointer.clientX, pointer.clientY);
  }

  function nearestChartIndex(model, clientX) {
    const canvas = $(model.canvasId);
    if (!canvas) return 0;
    const rect = canvas.getBoundingClientRect();
    const chartX = Math.max(0, Math.min(model.chartWidth, clientX - rect.left - model.padding.left));
    const position = model.points.length === 1 ? 0 : chartX / model.chartWidth * (model.points.length - 1);
    return Math.max(0, Math.min(model.points.length - 1, Math.round(position)));
  }

  function hideChartTooltip(chartId = null) {
    if (chartId && state.activeChartId !== chartId) return;
    const tooltip = $("chartTooltip");
    if (tooltip) {
      tooltip.classList.remove("is-visible");
      tooltip.setAttribute("aria-hidden", "true");
    }
    state.activeChartId = null;
  }

  function connectEvents() {
    if (!("EventSource" in window)) return;
    const events = new EventSource("/api/events");
    events.addEventListener("snapshot", (event) => {
      try {
        const payload = JSON.parse(event.data);
        renderHealth(payload.health);
        renderCurrent(payload.data);
      } catch (error) { console.warn("Invalid snapshot event", error); }
    });
    events.addEventListener("health", (event) => {
      try { renderHealth(JSON.parse(event.data).health); } catch (error) { console.warn("Invalid health event", error); }
    });
    events.onerror = () => {
      if (!state.health || state.health.status === "online") renderHealth({ status: "offline", last_error: "SSE connection lost" });
    };
  }

  function startRefreshLoop() {
    if (state.refreshTimer) window.clearInterval(state.refreshTimer);
    state.refreshTimer = window.setInterval(() => {
      loadCurrent();
      loadHistory();
    }, REFRESH_INTERVAL_MS);
  }

  function bindControls() {
    document.querySelectorAll("[data-lang]").forEach((button) => button.addEventListener("click", () => {
      state.language = button.dataset.lang === "en" ? "en" : "uk";
      try { localStorage.setItem("must-power-desk-language", state.language); } catch (error) { /* storage can be unavailable */ }
      applyLanguage();
    }));
    const defaultPeriods = { "1h": "minute", "6h": "minute", "24h": "30m", "7d": "day", "30d": "day", "1y": "month", all: "month" };
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
    bindChartHover();
    window.addEventListener("resize", () => { renderChart(); renderOperationalCharts(); });
    window.addEventListener("blur", () => hideChartTooltip());
  }

  async function boot() {
    applyLanguage();
    bindControls();
    await Promise.all([loadCurrent(), loadHistory()]);
    connectEvents();
    startRefreshLoop();
  }

  boot();
})();
