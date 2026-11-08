---
layout: default
title: "API: Motores"
description: Referencia de las clases Motor y MotorGroup en wedopy
prev:
  title: Hub
  url: /api/hub.html
next:
  title: Sensores
  url: /api/sensores.html
---

# Motores (`Motor` y `MotorGroup`)

El módulo de motores permite accionar y regular la velocidad y dirección de los motores LEGO Power Functions conectados a los puertos del Smart Hub.

```python
from wedopy import Motor, MotorGroup
```

---

## Clase `Motor`

Representa un motor individual conectado al puerto `"A"` o `"B"`. Se obtiene a través de `hub.motor()`.

### Atributos

- **`port`** *(str)*: Nombre del puerto al que está conectado (`"A"` o `"B"`).

### Métodos

#### `run(speed)`
```python
motor.run(speed: int) -> None
```
Establece la potencia y sentido de giro del motor.

- **Parámetros:**
  - `speed` *(int)*: Entero en el rango de `-100` a `100`.
    - Valores positivos (`1` a `100`): Giro en sentido horario / avance.
    - Valores negativos (`-1` a `-100`): Giro en sentido antihorario / retroceso.
    - `0`: Detiene el motor (equivalente a `stop()`).
- **Excepciones:**
  - `TypeError`: Si `speed` no es un número entero.
  - `ValueError`: Si `speed` está fuera del rango `[-100, 100]`.

```python
# Girar a máxima potencia hacia adelante
motor.run(100)

# Marcha lenta en retroceso
motor.run(-30)
```

#### `stop()`
```python
motor.stop() -> None
```
Detiene el motor enviando la orden de potencia `0`.

> **Nota técnica sobre parada:** El Smart Hub implementa el perfil de parada `nobarrier` (*coast*), donde la corriente del motor se corta y el rotor desacelera libremente. El acuse de recibo (ACK) de BLE confirma que la orden fue procesada por el microcontrolador, no que el eje haya dejado de rotar físicamente.

---

## Clase `MotorGroup`

Permite controlar varios motores de manera simultánea y coordinada con un orden determinista (puerto A primero, luego puerto B). Se obtiene a través de `hub.motors(("A", "B"))`.

### Métodos

#### `run(speed)`
```python
group.run(speed: int) -> None
```
Aplica la misma velocidad a todos los motores del grupo en orden determinista.

#### `stop()`
```python
group.stop() -> None
```
Detiene todos los motores del grupo. Si la parada de uno de los motores falla, `MotorGroup` intenta detener los motores restantes antes de propagar la excepción original.

---

## 💡 Ejemplos de uso

### Control básico con detención segura

```python
import time
from wedopy import Hub

with Hub() as hub:
    motor = hub.motor("A")
    try:
        motor.run(75)
        time.sleep(2)
    finally:
        motor.stop()
```

### Control de un robot diferencial con dos motores

```python
import time
from wedopy import Hub

with Hub() as hub:
    izq = hub.motor("A")
    der = hub.motor("B")
    ambos = hub.motors(("A", "B"))

    # Avanzar recto con ambos motores
    ambos.run(60)
    time.sleep(2)

    # Girar sobre su propio eje (rotación diferencial)
    izq.run(50)
    der.run(-50)
    time.sleep(1)

    ambos.stop()
```
