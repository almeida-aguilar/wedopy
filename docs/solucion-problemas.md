---
layout: default
title: Solución de Problemas
description: Guía de diagnóstico y resolución de errores comunes con wedopy y WeDo 2.0
prev:
  title: Ejemplos Prácticos
  url: /ejemplos.html
---

# Solución de Problemas y Preguntas Frecuentes

Esta guía recopila las dudas, errores frecuentes y procedimientos de diagnóstico para resolver incidencias de comunicación y hardware.

---

## ❓ Errores frecuentes y soluciones

### 1. `HubConnectionError`: No se encuentra ningún Smart Hub

**Causa probable:** El ordenador no detecta el paquete de anuncio BLE emitido por el Smart Hub.

**Comprobaciones recomendadas:**

1. **Estado del botón y LED:** Verifica que hayas presionado el botón central del Smart Hub. El LED debe parpadear suavemente en blanco. Si no parpadea o se apaga inmediatamente, las pilas están agotadas.
2. **Conexión previa:** El Smart Hub WeDo 2.0 **solo admite un único dispositivo conectado a la vez**. Si el hub está conectado a otra aplicación (por ejemplo, Scratch Desktop o la app oficial de LEGO), ninguna otra conexión BLE podrá establecerse. Cierra esas aplicaciones o apaga y vuelve a encender el Hub.
3. **Adaptador Bluetooth activo:** Comprueba en tu terminal:
   ```bash
   bluetoothctl power on
   bluetoothctl scan on
   ```
   Deberías ver aparecer un dispositivo con nombre similar a `LPF2 Smart Hub` o `WeDo 2.0`.
4. **Permisos en Linux:** Asegúrate de que tu usuario pertenezca al grupo `bluetooth`:
   ```bash
   sudo usermod -aG bluetooth $USER
   ```
   Reinicia la sesión si acabas de agregarlo.

---

### 2. `OperationTimeout`: Tiempo de espera agotado al leer un sensor

**Causa:** El firmware del sensor WeDo 2.0 opera por **notificación ante cambios** (_delta_).

**Solución:**

- Si el sensor de inclinación o distancia permanece completamente inmóvil, el Smart Hub no genera paquetes BLE repetidos. Mueve el sensor con la mano o coloca un objeto frente al sensor de distancia para provocar una nueva lectura.
- Si el problema persiste, comprueba que el conector LPF2 esté firmemente encajado en el puerto.

---

### 3. `DeviceNotFoundError` o `DeviceTypeError`

**Causa:** Se intenta acceder a un dispositivo no detectado o conectado en el puerto incorrecto.

**Diagnóstico rápido:**
Ejecuta este código para comprobar qué reconoce el hub:

```python
from wedopy import Hub

with Hub() as hub:
    print("Puertos detectados:", hub.ports)
    print("Actualizando reporte de puertos...")
    print("Reporte actualizado:", hub.refresh_ports())
```

- Si un puerto aparece vacío a pesar de tener un sensor conectado, desconecta el cable LPF2 y vuelve a conectarlo firmemente.
- Si llamaste a `hub.motor("A")`, pero el motor está en el puerto B, ajusta el puerto a `"B"` o usa `hub.motor()` sin argumentos para autodetectarlo.

---

### 4. `AmbiguousDeviceError`

**Causa:** Llamaste a `hub.motor()`, `hub.distance_sensor()` o `hub.tilt_sensor()` sin especificar el puerto, pero tienes **dos dispositivos del mismo tipo conectados simultáneamente** (por ejemplo, dos motores en los puertos A y B).

**Solución:**
Pasa el puerto explícitamente:

```python
motor_a = hub.motor("A")
motor_b = hub.motor("B")
```

O si deseas accionarlos juntos:

```python
motores = hub.motors(("A", "B"))
```

---

### 5. El motor continúa girando tras cancelar una tarea o presionar `Ctrl+C`

**Causa:** La cancelación cooperativa de tareas (`hub.tasks.cancel()`) únicamente detiene el planificador lógico, pero no envía órdenes de parada de motores para permitir limpiezas personalizadas.

**Solución:**

1. Utiliza siempre el gestor de contexto `with Hub() as hub:`, el cual garantiza que al salir del bloque se detendrán todos los motores (`stop_all()`) y se cerrará la conexión BLE.
2. Si controlas motores dentro de tareas cooperativas, utiliza la estructura `try ... finally`:
   ```python
   def mover():
       motor = hub.motor("A")
       try:
           motor.run(80)
           yield task.sleep(2)
       finally:
           motor.stop() # Se ejecuta incluso si la tarea es cancelada
   ```

---

## 🪟 Problemas específicos de Windows

### 1. `HubConnectionError`: no se encuentra el hub en Windows

**Causas y soluciones:**

1. **Bluetooth desactivado o adaptador bloqueado.** Comprueba en _Configuración → Bluetooth y dispositivos_ que el Bluetooth está activado. En PowerShell:
   ```powershell
   Get-PnpDevice -Class Bluetooth
   ```
   Debe aparecer tu adaptador (por ejemplo, _Intel(R) Wireless Bluetooth_). Si no aparece o el Bluetooth está deshabilitado, actualiza los drivers del fabricante.
2. **Falta de emparejamiento.** Algunos adaptadores Windows no exponen dispositivos BLE no emparejados a `bleak`. Abre _Configuración → Bluetooth y dispositivos → Agregar dispositivo_ y empareja el "LPF2 Smart Hub" antes de ejecutar `wedopy`.
3. **Otro cliente BLE conectado.** El hub solo admite una conexión. Cierra la app oficial de LEGO, Scratch o cualquier otra aplicación que use el hub.
4. **Adaptador incompatible o driver antiguo.** Los adaptadores Bluetooth 4.0 antiguos pueden no soportar GATT correctamente. Actualiza el driver del fabricante (Intel, Realtek, Broadcom…).

---

### 2. `OperationTimeout` intermitente en Windows

El backend WinRT de `bleak` puede introducir latencias mayores que BlueZ. Si los timeouts son frecuentes:

- Ajusta los parámetros de `Timing` al construir el hub:
  ```python
  from wedopy import Hub
  from wedopy_core.runtime.timing import Timing

  timing = Timing(op_timeout=2.0, connect_timeout=30.0)
  with Hub(timing=timing) as hub:
      motor = hub.motor("A")
      motor.run(80)
  ```
- Aleja el hub de fuentes de interferencia Wi-Fi (2.4 GHz) o USB 3.0.
- Si el problema persiste, comprueba la distancia entre el adaptador y el hub (recomendado < 5 m sin obstáculos).

---

### 3. Error al compilar `_wedopy.pyx` en Windows

Si `pip install -e ".[dev]"` falla con errores de compilación:

- Instala **Build Tools for Visual Studio** desde [visualstudio.microsoft.com/visual-cpp-build-tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/), seleccionando la carga de trabajo **"Desarrollo para el escritorio con C++"**.
- Asegúrate de usar la versión de Python para la que tienes el compilador (Visual Studio 2019/2022 soporta Python 3.9–3.13).
- Como alternativa, usa `uv sync` (descarga wheels precompilados cuando existen).
- Si no necesitas la extensión compilada, `tests/conftest.py` ejecutará `_wedopy.pyx` como Python puro (con una advertencia). Esto es útil para desarrollo, pero **no recomendado para producción** por el rendimiento.

---

### 4. PowerShell bloquea la activación del entorno virtual

Error típico:

```text
File .\.venv\Scripts\Activate.ps1 cannot be loaded because running scripts is disabled on this system.
```

**Solución (una sola vez por usuario):**

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Después, vuelve a intentar la activación:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

### 5. `ModuleNotFoundError: No module named 'wedopy'` tras instalar en Windows

**Causa:** Es probable que estés ejecutando Python desde fuera del entorno virtual, o que la instalación haya fallado.

**Solución:**

1. Confirma que el entorno virtual está activado (el prompt debe mostrar `(.venv)` al inicio).
2. Verifica la instalación:
   ```powershell
   python -c "import wedopy; print(wedopy.__version__)"
   ```
3. Si el comando falla, revisa la salida de `pip install` para identificar el error de compilación (ver problema 3).

---

## 🔍 Activación de Registros Detallados (Logging)

`wedopy` utiliza el módulo estándar `logging` de Python. Para visualizar todas las tramas enviadas, respuestas recibidas y el latido del watchdog en tu terminal:

```python
import logging
from wedopy import Hub

# Activar registro en nivel DEBUG
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

with Hub() as hub:
    hub.led.index(3)
    hub.motor("A").run(50)
```

**Loggers disponibles:**

- `wedopy`: Flujo de operaciones de alto nivel y conexión.
- `wedopy.watchdog`: Eventos del supervisor de latidos y paradas de emergencia.
- `wedopy.tasks`: Planificación, tiempos de espera y cancelación de tareas cooperativas.

En **Windows**, si los logs no aparecen en la consola de PowerShell, asegúrate de que la codificación sea UTF-8:

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```
