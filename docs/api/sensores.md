---
layout: default
title: "API: Sensores"
description: Referencia de DistanceSensor y TiltSensor en wedopy
prev:
  title: Motores
  url: /api/motores.html
next:
  title: Periféricos Integrados
  url: /api/perifericos.html
---

# Sensores (`DistanceSensor` y `TiltSensor`)

Los sensores WeDo 2.0 permiten interactuar con el entorno físico mediante medición de proximidad infrarroja e inclinación espacial.

```python
from wedopy import DistanceSensor, TiltSensor
```

---

## Clase `DistanceSensor`

El sensor de distancia utiliza un emisor y receptor infrarrojo para estimar la proximidad a un obstáculo. Se obtiene mediante `hub.distance_sensor("A" | "B")`.

### Atributos

- **`port`** *(str)*: Puerto asignado (`"A"` o `"B"`).

### Métodos

#### `read()`
```python
sensor.read() -> int
```
Devuelve una lectura normalizada de distancia como un número entero entre `0` y `10`.

- `0`: Obstáculo inmediatamente frente al sensor (muy cerca).
- `10`: Espacio despejado o sin objeto en el rango de detección.

#### `is_near(threshold)`
```python
sensor.is_near(threshold: int | float) -> bool
```
Evalúa si la distancia actual es estrictamente menor que el umbral (`read() < threshold`).

- **Parámetros:**
  - `threshold` *(número)*: Umbral entre `0` y `10`.

```python
if sensor.is_near(3):
    print("¡Obstáculo detectado a menos de nivel 3!")
```

#### `is_far(threshold)`
```python
sensor.is_far(threshold: int | float) -> bool
```
Evalúa si la distancia actual es estrictamente mayor que el umbral (`read() > threshold`).

- **Parámetros:**
  - `threshold` *(número)*: Umbral entre `0` y `10`.

---

## Clase `TiltSensor`

El sensor de inclinación WeDo 2.0 es un interruptor electromecánico de 4 posiciones que detecta la orientación respecto a la gravedad. Con el logotipo de LEGO hacia arriba y el conector apuntando hacia el usuario:
- El eje `+x` apunta hacia la derecha.
- El eje `+y` apunta hacia adelante.

Se obtiene mediante `hub.tilt_sensor("A" | "B")`.

### Atributos

- **`port`** *(str)*: Puerto asignado (`"A"` o `"B"`).

### Métodos

#### `read_direction()`
```python
tilt.read_direction() -> str
```
Devuelve una cadena que describe la dirección de inclinación predominante:

| Valor devuelto | Significado físico |
| :--- | :--- |
| `"neutral"` | Sensor nivelado horizontalmente. |
| `"back"` | Inclinado hacia atrás (conector elevado). |
| `"forward"` | Inclinado hacia adelante (conector descendido). |
| `"left"` | Inclinado hacia la izquierda. |
| `"right"` | Inclinado hacia la derecha. |

#### `read_angle()`
```python
tilt.read_angle() -> tuple[int, int]
```
Devuelve una tupla `(x, y)` con las componentes angulares en grados (típicamente en el rango nominal de `-45` a `+45` grados).

> **Detalle del protocolo:** Utiliza el modo raw (`UNIT_RAW`, enteros con signo de 8 bits) comprobado en hardware, evitando el fallo de firmware donde `UNIT_SI` provoca que el hub no notifique.

---

## ⚠️ Comportamiento de notificaciones por cambio (*Delta*)

> [!IMPORTANT]
> Los sensores WeDo 2.0 operan bajo el modelo **notificación por cambio físico**:
> 1. Si el sensor permanece inmóvil o ante una distancia constante, el Smart Hub **no emite nuevas muestras por BLE**.
> 2. `read()`, `read_angle()` y `read_direction()` devuelven la última muestra recibida. Si el enlace se acaba de inicializar o se requiere una muestra fresca, el método esperará hasta que ocurra un cambio físico o expire el tiempo límite (`OperationTimeout`).
> 3. Al probar tus programas, mueve el sensor o varía la distancia frente a él para generar lecturas continuas.
