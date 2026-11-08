---
layout: default
title: Resumen de la API
description: Índice general y estructura de la API pública de wedopy
prev:
  title: Hardware WeDo 2.0
  url: /hardware.html
next:
  title: Hub
  url: /api/hub.html
---

# Resumen de la API

La API pública de **`wedopy`** está diseñada bajo principios de consistencia, claridad didáctica y seguridad. Todos los símbolos esenciales pueden importarse directamente desde el paquete raíz:

```python
from wedopy import (
    Hub,
    Motor,
    MotorGroup,
    DistanceSensor,
    TiltSensor,
    LED,
    Button,
    task,
    running_time,
)
```

---

## 📑 Módulos y Clases

| Módulo / Clase | Descripción | Documentación |
| :--- | :--- | :--- |
| **[`Hub`](hub.md)** | Punto de entrada principal. Administra la conexión BLE, ciclo de vida, descubrimiento de puertos y acceso a dispositivos. | [Ver API de Hub](hub.md) |
| **[`Motor`](motores.md)** | Control de velocidad (-100 a 100), arranque y frenado en un puerto específico. | [Ver API de Motores](motores.md) |
| **[`MotorGroup`](motores.md)** | Control sincronizado de dos motores (A y B) con orden determinista. | [Ver API de Motores](motores.md) |
| **[`DistanceSensor`](sensores.md)** | Lectura de distancia (0..10) y métodos de umbral `is_near()` e `is_far()`. | [Ver API de Sensores](sensores.md) |
| **[`TiltSensor`](sensores.md)** | Sensor de inclinación: lectura de dirección (`read_direction()`) y ángulo 2D (`read_angle()`). | [Ver API de Sensores](sensores.md) |
| **[`LED`](perifericos.md)** | Control del LED RGB integrado (colores indexados 0..10 o RGB directo). | [Ver API de Periféricos](perifericos.md) |
| **[`Button`](perifericos.md)** | Consulta de estado del botón físico integrado (`is_pressed`, `is_released`). | [Ver API de Periféricos](perifericos.md) |
| **[`task` y `tasks`](tareas.md)** | Sistema de multitarea cooperativa ligera (`task.sleep`, `task.yield_now`, `hub.tasks.wait`). | [Ver API de Tareas](tareas.md) |
| **[`Excepciones`](excepciones.md)** | Jerarquía completa de errores de comunicación, conexión y estado. | [Ver Excepciones](excepciones.md) |
| **[`running_time`](tiempo.md)** | Utilidad sencilla para medir milisegundos transcurridos desde el inicio del programa. | [Ver API de Tiempo](tiempo.md) |

---

## 💡 Patrón de uso fundamental

```python
from wedopy import Hub

# Conexión automática mediante context manager
with Hub() as hub:
    # Obtener dispositivos
    motor = hub.motor("A")
    distancia = hub.distance_sensor("B")

    # Operaciones
    hub.led.index(5) # Verde
    motor.run(80)

    while not distancia.is_near(3):
        pass

    motor.stop()
```
