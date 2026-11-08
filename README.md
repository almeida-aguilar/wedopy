# wedopy

[![Docs](https://img.shields.io/badge/docs-Dracula%20Theme-bd93f9.svg)](https://almeida-aguilar.github.io/wedopy/)
[![Licencia: MIT](https://img.shields.io/badge/Licencia-MIT-50fa7b.svg)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-8be9fd.svg)](https://www.python.org/)

Biblioteca Python para el **LEGO WeDo 2.0 Smart Hub** a través de Bluetooth Low Energy (BLE).\
API pública en Python, núcleo de ejecución de alto rendimiento en Cython. Implementa la especificación de diseño 1.2.0.

📖 **Documentación online:** [https://almeida-aguilar.github.io/wedopy/](https://almeida-aguilar.github.io/wedopy/)

```python
from wedopy import Hub, task

with Hub() as hub:
    motor = hub.motor("A")
    motor.run(100)
```

---

## Instalación (Desarrollo)

### Con entorno virtual y pip (Linux/macOS)

```bash
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -e ".[dev]"      # compila la extensión en Cython e instala bleak
python -m pytest
```

### Con uv (recomendado)

```bash
uv sync
uv run pytest
```

### En Windows

Se requiere **Python 3.9+** y, si se compila la extensión Cython desde fuente, **Microsoft Visual C++ Build Tools**. Con PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest
```

O con uv:

```powershell
uv sync
uv run pytest
```

> **Requisitos adicionales en Windows:** Bluetooth 4.0+ activo y adaptador habilitado. `bleak` usa WinRT como backend BLE. Consulta la sección de [Instalación](docs/instalacion.md#-windows) para más detalles.

Linux/BlueZ es la plataforma validada en hardware real. Windows funciona a través de `bleak` (WinRT), pero **no está validado oficialmente con hardware**.

---

## Estructura del Repositorio

| Ruta                      | Contenido                                                                                              |
| :------------------------ | :----------------------------------------------------------------------------------------------------- |
| `src/wedopy/`             | API pública: `Hub`, `Motor`, `MotorGroup`, sensores, `LED`, `Button`, `task`, `tasks`, excepciones     |
| `wedopy_core/_wedopy.pyx` | Núcleo Cython: codecs de protocolo, máquina de estados, coordinador single-writer, heartbeat, watchdog |
| `wedopy_core/transport/`  | Interfaz `Transport`, `BleakTransport` (BLE real), `SimulatedHub` (pruebas sin hardware)               |
| `wedopy_core/protocol/`   | UUIDs y constantes del protocolo WeDo 2.0                                                              |
| `wedopy_core/runtime/`    | Parámetros de temporización `Timing`, supervisor del proceso                                           |
| `tests/`, `examples/`     | Suite de pruebas pytest (con hub simulado) y ejemplos ejecutables                                      |
| `docs/`                   | Documentación web oficial compatible con GitHub Pages (Tema Dracula)                                   |

> **Diferencias respecto a la especificación original:** `src/wedo/` es `src/wedopy/` (el nombre de importación es `wedopy`); el módulo compilado es `wedopy_core._wedopy`; los codecs del protocolo residen dentro del núcleo de Cython en lugar de archivos `.py` separados; las excepciones se definen en `wedopy_core/exceptions.py` y se reexportan en `wedopy.exceptions`, garantizando que el núcleo nunca importe el paquete público.

---

## Comportamientos clave del hardware y diseño

- **Coordinador de un solo escritor (_Single Writer_):** Toda operación BLE se canaliza a través de un único hilo coordinador. Las escrituras y el latido (_heartbeat_) son siempre **con respuesta** (_with response_); no existe degradación silenciosa a escrituras sin confirmación.
- **Seguridad activa (Heartbeat & Watchdog):** Mientras algún motor tenga una velocidad distinta de cero, se envía un latido (lectura del nivel de batería) cada **0.5 s**. Si transcurren **2 s** sin un acuse de recibo (ACK) válido, el _watchdog_ detiene los motores con prioridad de emergencia (2 intentos), registra el evento en el logger `wedopy.watchdog` y transiciona el hub al estado `error`. El watchdog y el heartbeat se ejecutan en un hilo independiente, por lo que un bloqueo en el hilo del usuario no puede desactivarlos.
- **Tiempos límite acotados:** Las operaciones normales expiran tras **1 s** (_timeout_), lo que delimita cuánto tiempo puede esperar una solicitud de emergencia detrás de una operación en curso (una llamada BLE en vuelo no puede cancelarse de forma destructiva).
- **Perfil de parada:** La detención de motores utiliza el perfil libre `nobarrier` (_coast_). El hardware no ofrece freno activo (`strong`).
- **Gestión de tareas y motores:** `hub.tasks.cancel()` nunca detiene los motores por sí mismo; protege los motores con bloques `try/finally` o llama explícitamente a `hub.stop_all()`. Al salir de un bloque `with Hub()`, se cancelan primero las tareas y a continuación se detienen los motores.
- **Registro (_Logging_):** Se integra con el módulo estándar `logging` de Python (`wedopy`, `wedopy.watchdog`, `wedopy.tasks`).
- **Notificaciones por cambio (_Delta_):** Los sensores solo emiten datos ante variaciones físicas. `read_angle()`, `read_direction()` y el sensor de distancia devuelven la última muestra conocida; si la magnitud física no ha variado desde la última notificación, la llamada esperará hasta que ocurra un movimiento o expire el tiempo de espera.
- **Sensor de inclinación (Tilt):** Es un interruptor electromecánico de 4 posiciones, no un acelerómetro triaxial. Su modo de dirección (1) utiliza `UNIT_SI` (`float32` de 4 bytes); su modo de ángulo (0) **requiere estrictamente `UNIT_RAW`** (par de `int8` de 2 bytes) — con `UNIT_SI`, el firmware del hub ignora la configuración y nunca emite datos. El modo golpe (_bump_, 2) es aceptado por el firmware pero no está implementado en los sensores comerciales.

---

## Estado de Validación

Validado con el hub simulado y en hardware real LEGO WeDo 2.0 (noviembre de 2026):

- Compilación nativa en Cython (`wedopy_core._wedopy`).
- `BleakTransport` en Linux/BlueZ: escaneo, conexión, descubrimiento de puertos y recepción de notificaciones.
- Sensor de inclinación: modo dirección (1, `UNIT_SI`) y modo ángulo (0, `UNIT_RAW`).
- Batería, botón físico central, LED RGB, motor y sensor de distancia.

**Plataformas:**

- **Linux/BlueZ**: plataforma oficial, validada en hardware real.
- **Windows (WinRT)**: soporte añadido a través de `bleak`; instalación documentada en [`docs/instalacion.md`](docs/instalacion.md#-windows). No validado oficialmente con hardware.

**Pendiente de validación en hardware:** temporizaciones del watchdog ante una desconexión abrupta por interferencia BLE severa, repetición de `refresh_ports()`, comportamiento si el proceso se finaliza forzosamente (`kill -9`) con el enlace abierto, y el perfil de parada `strong` (no implementado en el firmware). En Windows, adicionalmente: latencias del backend WinRT, reconexión tras suspensión del sistema y comportamiento del emparejamiento en adaptadores Intel/Realtek/Broadcom.

`wedopy_core/_wedopy.pyx` está escrito en un subconjunto de Cython compatible con sintaxis pura de Python, por lo que `tests/conftest.py` puede ejecutarlo sin compilar cuando la extensión no está construida (emite una advertencia). Las optimizaciones tipadas `cdef` podrán agregarse en el futuro según los perfiles de rendimiento.
