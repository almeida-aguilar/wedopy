---
layout: default
title: Guía de Inicio Rápido
description: Primeros pasos y ejemplos prácticos para controlar WeDo 2.0 con wedopy
prev:
  title: Instalación
  url: /instalacion.html
next:
  title: Hardware WeDo 2.0
  url: /hardware.html
---

# Guía de Inicio Rápido

¡Bienvenido a `wedopy`! En pocos minutos tendrás tu primer programa comunicándose con el LEGO WeDo 2.0 Smart Hub.

---

## 1. Encender el Smart Hub

1. Inserta dos pilas AA o la batería recargable en el Smart Hub.
2. Pulsa el botón físico central. El LED comenzará a parpadear en blanco suave, indicando que el dispositivo está anunciándose por BLE (*advertising*).
3. Asegúrate de que el Bluetooth de tu ordenador esté activo.

---

## 2. El Context Manager `with Hub()`

La forma recomendada de usar `wedopy` es mediante un bloque `with Hub() as hub:`. Este se encarga de:
- Descubrir el primer Smart Hub cercano y conectarse a él.
- Descubrir automáticamente los dispositivos conectados en los puertos A y B.
- Al salir (por fin de programa o por excepción), cancelar tareas pendientes, detener todos los motores y cerrar la conexión BLE de forma limpia.

```python
from wedopy import Hub

with Hub() as hub:
    print("¡Conectado al Smart Hub!")
    print("Dispositivos detectados:", hub.ports)
```

Salida típica:
```text
¡Conectado al Smart Hub!
Dispositivos detectados: {'A': 'motor', 'B': 'tilt'}
```

---

## 3. Controlar un Motor

Conecta un motor en el puerto **A** o **B**. Puedes seleccionarlo explícitamente indicando el puerto, o dejar que `wedopy` lo detecte automáticamente si solo hay uno conectado.

```python
import time
from wedopy import Hub

with Hub() as hub:
    # Obtener el motor en el puerto A
    motor = hub.motor("A")

    # Girar hacia adelante a 70% de potencia
    print("Girando hacia adelante...")
    motor.run(70)
    time.sleep(2)

    # Invertir la dirección (-70%)
    print("Invirtiendo marcha...")
    motor.run(-70)
    time.sleep(2)

    # Detener el motor
    motor.stop()
```

> **Consejo:** Si solo tienes un motor conectado al hub, puedes escribir simplemente `motor = hub.motor()` sin pasar el puerto.

---

## 4. Cambiar el color del LED

El Smart Hub incluye un LED RGB que puede configurarse por índice de color (0 a 10) o mediante valores RGB directos (0 a 255):

```python
import time
from wedopy import Hub

with Hub() as hub:
    # Colores indexados
    print("Color azul...")
    hub.led.index(3)      # 3 = Azul
    time.sleep(1)

    print("Color verde...")
    hub.led.index(5)      # 5 = Verde
    time.sleep(1)

    # Color RGB personalizado (Naranja brillante)
    print("Color RGB naranja...")
    hub.led.rgb(255, 100, 0)
    time.sleep(1)

    # Apagar el LED
    hub.led.off()
```

---

## 5. Leer el Sensor de Distancia

El sensor de distancia mide proximidad en una escala entera calibrada de **0** (objeto muy cerca) a **10** (despejado).

```python
import time
from wedopy import Hub, OperationTimeout

with Hub() as hub:
    sensor = hub.distance_sensor("B")

    print("Acerca tu mano al sensor de distancia...")
    for _ in range(10):
        try:
            dist = sensor.read()
            print(f"Distancia: {dist} | ¿Cerca?: {sensor.is_near(4)}")
        except OperationTimeout:
            print("Esperando nuevo movimiento...")
        time.sleep(0.5)
```

---

## 6. Leer el Sensor de Inclinación (Tilt)

El sensor de inclinación WeDo 2.0 detecta cinco orientaciones físicas: `neutral`, `back` (atrás), `right` (derecha), `left` (izquierda) y `forward` (adelante), además de los ángulos en grados `(x, y)`:

```python
import time
from wedopy import Hub

with Hub() as hub:
    tilt = hub.tilt_sensor()

    print("Inclina el sensor en diferentes direcciones...")
    for _ in range(10):
        direccion = tilt.read_direction()
        angulo = tilt.read_angle()
        print(f"Dirección: {direccion:<8} | Ángulo (x, y): {angulo}")
        time.sleep(0.5)
```

> **Importante:** Por diseño del firmware WeDo 2.0, los sensores solo transmiten datos por BLE cuando detectan un cambio físico. Si el sensor está completamente inmóvil, `read()` devolverá la última muestra conocida o esperará hasta que ocurra un movimiento físico.

---

## 7. Leer el Botón del Hub

El botón físico central puede consultarse en cualquier momento sin bloquear:

```python
import time
from wedopy import Hub

with Hub() as hub:
    print("Pulsa y suelta el botón central del Smart Hub...")
    for _ in range(20):
        if hub.button.is_pressed:
            print("¡Botón presionado!")
            hub.led.index(8) # Rojo
        else:
            hub.led.index(5) # Verde
        time.sleep(0.2)
```

---

## Siguiente paso

Ahora que conoces los componentes básicos, revisa la sección de [**Hardware WeDo 2.0**](hardware.md) para comprender en detalle los modos de los sensores y el comportamiento real del firmware.
