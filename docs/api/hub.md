---
layout: default
title: "API: Hub"
description: Referencia completa de la clase Hub en wedopy
prev:
  title: Resumen de la API
  url: /api/
next:
  title: Motores
  url: /api/motores.html
---

# Clase `Hub`

La clase `Hub` representa el Smart Hub físico de LEGO WeDo 2.0 y constituye el punto de entrada principal para interactuar con todos los motores, sensores y funciones del dispositivo.

```python
from wedopy import Hub
```

---

## 🏗️ Constructor

```python
Hub(*, transport=None, timing=None)
```

Crea una instancia de control del Hub.

- **Parámetros:**
  - `transport` *(opcional)*: Implementación del transporte BLE. Por defecto utiliza `BleakTransport` (comunicación real por Bluetooth). Para pruebas unitarias sin hardware físico se puede proporcionar `SimulatedHub`.
  - `timing` *(opcional)*: Instancia de `Timing` con parámetros de tiempos de espera y reintentos (usado principalmente en pruebas y entornos de alta latencia).
- **Ejemplo:**
  ```python
  # Uso estándar con hardware real
  hub = Hub()
  ```

---

## 🔄 Ciclo de vida y conexión

### `connect()`
```python
hub.connect() -> Hub
```
Inicia la búsqueda BLE, conecta con el primer WeDo 2.0 Smart Hub detectado, descubre sus puertos y devuelve la propia instancia de `Hub`.

### `disconnect()`
```python
hub.disconnect() -> None
```
Cancela todas las tareas cooperativas en ejecución, solicita la parada de los motores (`nobarrier`) y cierra limpiamente la conexión BLE. Es seguro llamarlo múltiples veces consecutivas.

### `shutdown()`
```python
hub.shutdown() -> None
```
Envía la orden de apagado total de energía al hardware. El Smart Hub se apagará y requerirá presionar manualmente su botón físico para volver a encenderse.

### `stop_all()`
```python
hub.stop_all() -> None
```
Envía una orden inmediata de parada (`run(0)`) a todos los puertos de motor conocidos.

### `is_connected`
```python
hub.is_connected -> bool
```
Propiedad que devuelve `True` si el Hub mantiene una conexión activa, o `False` en caso contrario.

### Uso con Context Manager *(Recomendado)*
```python
with Hub() as hub:
    # El hub se conecta automáticamente al entrar.
    hub.motor("A").run(50)
    # Al salir del bloque (incluso si ocurre una excepción),
    # se garantiza la llamada a disconnect().
```

---

## 🔌 Detección de Puertos y Dispositivos

### `ports`
```python
hub.ports -> dict[str, str]
```
Propiedad de solo lectura que devuelve una instantánea de los dispositivos externos conectados a los puertos `"A"` y `"B"`.

**Ejemplo de retorno:**
```python
{"A": "motor", "B": "distance"}
```
Valores posibles según el dispositivo: `"motor"`, `"motion"` (sensor de distancia), `"tilt"` (sensor de inclinación).

### `refresh_ports()`
```python
hub.refresh_ports() -> dict[str, str]
```
Solicita al hardware del Hub un nuevo reporte del estado de los puertos y devuelve el diccionario actualizado.

---

## ⚙️ Métodos para obtener Dispositivos

### `motor(port=None)`
```python
hub.motor(port=None) -> Motor
```
Obtiene el objeto controlador del motor.
- **Parámetros:**
  - `port` *(str, opcional)*: Puerto físico (`"A"` o `"B"`, sin distinción de mayúsculas/minúsculas).
- **Comportamiento automático:**
  - Si se omite `port` y hay exactamente un motor conectado, se detecta y devuelve automáticamente.
  - Lanza `DeviceNotFoundError` si no hay motor conectado.
  - Lanza `DeviceTypeError` si el dispositivo conectado en el puerto especificado no es un motor.
  - Lanza `AmbiguousDeviceError` si se omite `port` pero hay dos motores conectados a la vez.

### `motors(ports)`
```python
hub.motors(ports) -> MotorGroup
```
Crea un grupo de motores sincronizado.
- **Parámetros:**
  - `ports` *(secuencia)*: Tupla o lista de puertos, por ejemplo `("A", "B")`.

### `distance_sensor(port=None)`
```python
hub.distance_sensor(port=None) -> DistanceSensor
```
Obtiene el sensor de distancia conectado al puerto indicado (o lo autodetecta si solo hay uno).

### `tilt_sensor(port=None)`
```python
hub.tilt_sensor(port=None) -> TiltSensor
```
Obtiene el sensor de inclinación conectado al puerto indicado (o lo autodetecta si solo hay uno).

---

## 💡 Periféricos Integrados

### `led`
```python
hub.led -> LED
```
Devuelve el objeto para controlar el LED RGB integrado.

### `button`
```python
hub.button -> Button
```
Devuelve el objeto para consultar el botón físico integrado.

### `tasks`
```python
hub.tasks -> TaskManager
```
Devuelve el gestor de tareas cooperativas asociado a la sesión de este Hub.
