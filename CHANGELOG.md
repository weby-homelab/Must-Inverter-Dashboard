# Changelog

All notable changes to **MUST Power Desk** are documented in this file.

## [v0.3.0] - 2026-11-26

- Added opt-in safe inverter control (`MUST_ENABLE_WRITE=false` by default) using Modbus Function `06` with allowlisted Tier 1/Tier 2 parameters, 24V threshold cross-validation, EEPROM no-op skipping, cooldown/hourly limits, and read-after-write verification.
- Added control safety UX: session unlock timer, Before→After diff preview, Hold-to-Confirm interlock, quick presets, and SQLite configuration audit trail with one-click rollback.
- Added animated SVG power flow schematic, human-readable `UKR | ENG` decoding of modes and error/warning bitmasks, battery autonomy estimate, and grid outage timeline (`/api/outages`).
- Added range summary analytics (`/api/summary`) and PV1800 decimal high/low accumulated energy decoding.
- Added pointer/touch chart tooltips for mobile devices and Dark/Light theme toggle.
- Added opt-in Telegram alerts (`MUST_TELEGRAM_ENABLED`) for grid outages/restoration, low battery voltage, critical faults, and telemetry loss.

## [v0.2.1] - 2026-09-11

- Added pointer tooltips to the history, power-flow, battery-voltage, and temperature charts.
- Added nearest-sample timestamps, localized series labels, units, and unavailable-value handling to chart tooltips.
- Documented and deployed an opt-in Tailscale-only bind without exposing the dashboard on `0.0.0.0`.
- Updated the installer and health/server version metadata for the release.

## [v0.2.0] - 2026-09-11

- Added one-hour and six-hour dashboard history ranges with minute defaults.
- Added live operational charts for power flow, battery voltage thresholds, and temperatures.
- Reduced the default telemetry cycle and dashboard refresh cadence from 15 seconds to 10 seconds.
- Kept SQLite persistence at one sample per minute to avoid unnecessary database growth.

## [v0.1.1] - 2026-09-02

- Added one-minute and 30-minute history aggregation.
- Added automatic fine-resolution selection for short ranges.
- Added `UKR | ENG` language switching with browser persistence.
- Extended localization across current, history, diagnostics, and configuration views.
- Added version reporting to health responses.
- Documented the supported decoder model families and the read-only security boundary.
