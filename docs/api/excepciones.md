---
layout: default
title: "API: Excepciones"
description: Jerarquía de excepciones y gestión de errores en wedopy
prev:
  title: Tareas Cooperativas
  url: /api/tareas.html
next:
  title: Tiempo
  url: /api/tiempo.html
---

# Jerarquía de Excepciones

`wedopy` proporciona una jerarquía de excepciones estructurada y explícita para que puedas capturar y gestionar cualquier fallo de hardware o comunicación de forma precisa.

Todas las excepciones pueden importarse desde `wedopy` o desde `wedopy.exceptions`:

```python
from wedopy.exceptions import (
    WedoError,
    BLEError,
    HubConnectionError,
    HubDisconnectedError,
    OperationTimeout,
    HubBusyError,
    DeviceNotFoundError,
    DeviceTypeError,
    AmbiguousDeviceError,
    InvalidStateError,
    UnsupportedFeatureError,
)
```

---

## 🌳 Árbol Jerárquico

```
Exception
└── WedoError (Base para todas las excepciones de wedopy)
    ├── BLEError (Fallos de bajo nivel en transporte y Bluetooth)
    │   ├── HubConnectionError (No se encontró el Hub o falló el emparejamiento)
    │   ├── HubDisconnectedError (Pérdida inesperada de conexión BLE)
    │   ├── OperationTimeout (Expiró el tiempo de espera de una operación)
    │   └── HubBusyError (El bus BLE no pudo admitir la solicitud en este momento)
    ├── DeviceNotFoundError (No hay dispositivo conectado en el puerto especificado)
    ├── DeviceTypeError (El tipo de dispositivo en el puerto no coincide con el solicitado)
    ├── AmbiguousDeviceError (Múltiples dispositivos del mismo tipo sin indicar puerto)
    ├── InvalidStateError (Operación no válida en el estado actual del hub o planificador)
    └── UnsupportedFeatureError (Característica no soportada por el firmware)
```

---

## 📋 Descripción Detallada

### `WedoError`
Excepción base para todos los errores generados por la biblioteca. Si deseas capturar cualquier problema originado por `wedopy`, captura esta clase.

### `BLEError`
Representa anomalías en la capa Bluetooth Low Energy (D-Bus, BlueZ o fallos de GATT).

### `HubConnectionError`
Se lanza cuando `hub.connect()` o `with Hub()` no consigue encontrar ningún Smart Hub en modo anuncio (*advertising*) tras el tiempo límite de búsqueda (15 segundos por defecto), o si la negociación inicial de servicios GATT falla.

### `HubDisconnectedError`
Se produce cuando el Smart Hub pierde el enlace de radio de forma involuntaria (por ejemplo, al agotarse las pilas o al alejarse demasiado del ordenador).

### `OperationTimeout`
Se emite cuando una lectura o escritura BLE no recibe confirmación (ACK) dentro del tiempo de espera estipulado (por defecto 1.0 segundo).

### `HubBusyError`
Se genera si la cola interna del coordinador BLE está saturada o si una operación colisiona con una orden de emergencia en curso.

### `DeviceNotFoundError`
Se produce al invocar `hub.motor()`, `hub.distance_sensor()` o `hub.tilt_sensor()` sobre un puerto donde no hay ningún periférico conectado, o si se omite el puerto y no existe ningún dispositivo de ese tipo en todo el hub.

### `DeviceTypeError`
Se produce cuando intentas acceder a un puerto que contiene un dispositivo distinto al esperado. Por ejemplo, llamar a `hub.motor("A")` cuando en el puerto A está conectado un sensor de inclinación.

### `AmbiguousDeviceError`
Se produce cuando solicitas un dispositivo sin especificar puerto (por ejemplo, `hub.motor()`), pero hay dos dispositivos de ese mismo tipo conectados en A y en B simultáneamente. La biblioteca te obliga a especificar el puerto explícitamente (`"A"` o `"B"`).

### `InvalidStateError`
Se lanza ante secuencias de operaciones inconsistentes, como intentar llamar a `hub.tasks.wait()` dentro de una tarea en ejecución, o solicitar operaciones a un hub que ya ha sido desconectado o apagado.

### `UnsupportedFeatureError`
Se lanza al intentar utilizar funciones no admitidas por el hardware o por la versión del firmware WeDo 2.0.

---

## 💡 Ejemplo de manejo de excepciones

```python
from wedopy import Hub
from wedopy.exceptions import (
    HubConnectionError,
    DeviceNotFoundError,
    OperationTimeout,
    WedoError,
)

try:
    with Hub() as hub:
        motor = hub.motor("A")
        sensor = hub.distance_sensor("B")
        motor.run(80)

        # Esperar lectura
        distancia = sensor.read()
        print("Distancia:", distancia)

except HubConnectionError:
    print("Error: No se encontró ningún Smart Hub. ¿Está encendido el botón y parpadea el LED?")
except DeviceNotFoundError as e:
    print(f"Error de puertos: {e}")
except OperationTimeout:
    print("Tiempo de espera agotado al comunicar con el sensor.")
except WedoError as e:
    print(f"Ocurrió un error en wedopy: {e}")
```
