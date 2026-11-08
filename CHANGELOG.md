# Changelog

## 0.1.0.dev0

First implementation of design spec 1.2.0 (`WeDo_2_0_con_Cython.md`).

- Cython core `wedopy_core._wedopy`: protocol codecs, state machine, single-writer coordinator
  (normal/emergency queues), heartbeat and watchdog.
- Public API: `Hub`, `Motor`, `MotorGroup`, `DistanceSensor`, `TiltSensor`, `LED`, `Button`,
  cooperative tasks (`hub.tasks`, `task.sleep`, `task.yield_now`), `running_time`.
- BLE backend `BleakTransport` (Linux/BlueZ first) and `SimulatedHub` transport for tests.
- Validated on real WeDo 2.0 hardware (Nov 2026): compiled build, `BleakTransport`
  (Linux/BlueZ), port discovery, tilt sensor (direction and angle), distance, LED,
  motor, battery, button.
- Tilt sensor: angle mode uses `UNIT_RAW` with `expected_len=2` (`int8` pairs).
  `UNIT_SI` makes the hub silently ignore the configuration and never notify.
- Tilt bump mode (2) is not implemented by the hub firmware; documented as a spec
  artifact, not a wedopy bug.
- Not yet validated on hardware: watchdog timings under a real BLE stall,
  `refresh_ports()` replay, behaviour when the process is killed with the link
  open, and the `strong` stop profile (not implemented).

## 0.1.2

- Soporte documentado para Windows (instalación, solución de problemas).
- Actualización de la documentación.
- Constantes de color en `LED`
