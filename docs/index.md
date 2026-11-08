---
layout: default
title: Introducción a wedopy
description: Biblioteca Python para el LEGO WeDo 2.0 Smart Hub sobre Bluetooth Low Energy (BLE)
next:
  title: Instalación
  url: /instalacion.html
---

# wedopy

**`wedopy`** es una biblioteca moderna en Python para controlar el **LEGO® WeDo 2.0 Smart Hub** a través de Bluetooth Low Energy (BLE). Diseñada para educación, robótica y prototipado, combina una API de alto nivel intuitiva en Python con un núcleo de ejecución de bajo nivel ultra fiable implementado en **Cython**.

```python
from wedopy import Hub, task

with Hub() as hub:
    # Encender el LED en color azul
    hub.led.index(3)

    # Girar el motor conectado al puerto A
    motor = hub.motor("A")
    motor.run(75)

    print("Dispositivos conectados:", hub.ports)
```

---

## 🚀 Características principales

- **API Pythonic y sencilla**: Diseñada para ser legible, accesible y didáctica, respetando las mejores prácticas de Python (`with Hub() as hub:`).
- **Seguridad industrial y watchdog**:
  - **Single-Writer Coordinator**: Todas las operaciones BLE se ejecutan en un único hilo secuencial y determinista, garantizando respuestas con acuse de recibo (*with response*).
  - **Heartbeat & Watchdog**: Si los motores están encendidos, se envía un latido (*heartbeat*) cada 0.5 s. Si la comunicación se corta durante más de 2 s, el *watchdog* ejecuta una parada de emergencia en un hilo independiente.
- **Tareas cooperativas integradas**: Concurrencia ligera educativa con generadores (`hub.tasks.add()`, `yield task.sleep(segundos)`), sin lidiar con bloqueos de hilos ni la complejidad sintáctica de `asyncio`.
- **Validado en hardware real**: Probado y calibrado con el Smart Hub WeDo 2.0 real y sus sensores:
  - **Motores**: Control de potencia (-100 a +100) y grupos coordinados (`MotorGroup`).
  - **Sensor de inclinación (Tilt)**: Modos Dirección (`neutral`, `back`, `right`, `left`, `forward`) y Ángulo 2D `(x, y)` calibrados.
  - **Sensor de distancia**: Lectura normalizada (0 a 10) y métodos `is_near()` e `is_far()`.
  - **LED RGB**: Modos indexados (0 a 10) y color verdadero RGB 24-bit.
  - **Botón integrado**: Detección reactiva de pulsación y liberación.

---

## 🏛️ Estructura de dos niveles

La arquitectura de `wedopy` separa estrictamente las responsabilidades:

| Componente | Lenguaje | Responsabilidad |
| :--- | :--- | :--- |
| **API Pública** (`src/wedopy/`) | Python | `Hub`, `Motor`, `DistanceSensor`, `TiltSensor`, `LED`, `Button`, `tasks`, excepciones y context managers. |
| **Núcleo Interno** (`wedopy_core/`) | Cython (`_wedopy`) | Codecs del protocolo WeDo 2.0, coordinador de cola única BLE, watchdog, máquina de estados y backend `Bleak`. |

El usuario final simplemente instala e importa `wedopy` como cualquier paquete estándar de Python, sin requerir conocimientos de Cython ni manipular extensiones nativas.

---

## ⚡ Vista previa de tareas cooperativas

Permite coordinar múltiples acciones a la vez de forma limpia:

```python
from wedopy import Hub, task

with Hub() as hub:
    def parpadear():
        while True:
            hub.led.index(6)       # Amarillo
            yield task.sleep(0.3)
            hub.led.index(8)       # Rojo
            yield task.sleep(0.3)

    def mover():
        motor = hub.motor("A")
        try:
            motor.run(80)
            yield task.sleep(2.0)
        finally:
            motor.stop()

    # Añadir tarea de fondo (se cancela al terminar las normales)
    hub.tasks.add(parpadear, background=True)
    # Añadir tarea principal
    hub.tasks.add(mover)

    # Ejecutar hasta que la tarea principal termine
    hub.tasks.wait()
```

---

## 📚 Secciones de la documentación

1. [**Instalación**](instalacion.md): Requisitos del sistema, dependencias y configuración Bluetooth en Linux.
2. [**Guía de Inicio Rápido**](guia-rapida.md): Tu primer script en 5 minutos.
3. [**Hardware WeDo 2.0**](hardware.md): Particularidades del firmware oficial, sensores y puertos.
4. [**Referencia de la API**](api/index.md): Documentación exhaustiva de todas las clases y funciones.
5. [**Arquitectura y Seguridad**](arquitectura.md): Explicación del coordinador de hilos, watchdog y protocolos.
6. [**Ejemplos Prácticos**](ejemplos.md): Colección de scripts listos para ejecutar.
7. [**Solución de Problemas**](solucion-problemas.md): Respuestas a errores comunes y diagnóstico.
