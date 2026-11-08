---
layout: default
title: Ejemplos Prácticos
description: Scripts y ejemplos listos para ejecutar con wedopy
prev:
  title: Arquitectura y Seguridad
  url: /arquitectura.html
next:
  title: Solución de Problemas
  url: /solucion-problemas.html
---

# Ejemplos Prácticos

Esta sección contiene programas completos probados en hardware real, listos para copiar, ejecutar y adaptar a tus propios modelos de LEGO WeDo 2.0.

Los archivos fuente de estos ejemplos se encuentran disponibles en la carpeta [`examples/`](https://github.com/almeida-aguilar/wedopy/tree/main/examples) del repositorio.

---

## 1. Concurrencia con Tareas: Luces y Movimiento

`examples/blink_and_move.py` demuestra cómo hacer parpadear el LED en bucle continuo mientras un motor gira durante 3 segundos, utilizando tareas cooperativas sin bloquear el programa ni recurrir a hilos.

```python
"""Blink the LED while a motor runs, using cooperative tasks (no threads, no asyncio)."""
from wedopy import Hub, task

with Hub() as hub:
    def blink():
        while True:
            hub.led.index(6)   # Amarillo
            yield task.sleep(0.3)
            hub.led.index(9)   # Blanco
            yield task.sleep(0.3)

    def move():
        motor = hub.motor("A")
        try:
            motor.run(75)
            yield task.sleep(3)
        finally:
            motor.stop()

    # La tarea de fondo se cancela automáticamente al terminar 'move'
    hub.tasks.add(blink, background=True)
    hub.tasks.add(move)
    hub.tasks.wait()
```

---

## 2. Vehículo Evasor de Obstáculos

`examples/distance_sensor.py` acciona el motor al 70% de potencia y supervisa el sensor de proximidad en tiempo real. Cuando un obstáculo se encuentra a menos de nivel 3 (muy cerca), el vehículo frena inmediatamente.

```python
"""Drive until the distance sensor reports something nearer than 3 (scale 0..10)."""
import time
from wedopy import Hub, OperationTimeout

with Hub() as hub:
    sensor = hub.distance_sensor("B")
    motor = hub.motor("A")

    motor.run(70)
    print("Avanzando... esperando obstáculo frente al sensor B")

    while True:
        try:
            if sensor.is_near(3):
                print("¡Obstáculo detectado a menos de nivel 3!")
                break
        except OperationTimeout:
            print("Sin respuesta del sensor; deteniendo por seguridad")
            break
        time.sleep(0.05)

    motor.stop()
```

---

## 3. Robot de Dos Motores (`MotorGroup`)

`examples/two_motors.py` controla simultáneamente dos motores conectados a los puertos A y B (por ejemplo, las dos ruedas motrices de un vehículo), garantizando que ambos se detengan incluso si ocurre un error en uno de ellos.

```python
"""Drive two motors together (A first, then B; not atomic), then stop."""
import time
from wedopy import Hub

with Hub() as hub:
    motors = hub.motors(("A", "B"))

    print("Iniciando tracción doble...")
    motors.run(75)
    time.sleep(2)

    print("Deteniendo motores...")
    motors.stop()
```

---

## 4. Monitor de Orientación con Sensor de Inclinación

`examples/tilt_sensor.py` toma 20 muestras periódicas reportando el ángulo 2D y la dirección física (`neutral`, `forward`, `back`, `left`, `right`).

```python
"""Print the tilt angle and direction."""
import time
from wedopy import Hub

with Hub() as hub:
    tilt = hub.tilt_sensor("A")

    print("Mueve el sensor de inclinación en el puerto A:")
    for _ in range(20):
        print(f"Ángulo: {tilt.read_angle()} | Dirección: {tilt.read_direction()}")
        time.sleep(0.25)
```

---

## 5. Espectro y Ciclo de Colores LED

`examples/led.py` recorre uno a uno todos los colores indexados de la paleta oficial de LEGO WeDo 2.0 y finaliza encendiendo un color RGB personalizado.

```python
"""Cycle through the indexed LED colours, then show an RGB colour."""
import time
from wedopy import Hub

with Hub() as hub:
    # Recorrer colores oficiales del 1 al 10
    for i in range(1, 11):
        hub.led.index(i)
        time.sleep(0.3)

    # Establecer color RGB naranja brillante
    hub.led.rgb(255, 80, 0)
    time.sleep(1)

    hub.led.off()
```
