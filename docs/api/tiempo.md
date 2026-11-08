---
layout: default
title: "API: Tiempo"
description: Función educativa running_time() en wedopy
prev:
  title: Excepciones
  url: /api/excepciones.html
next:
  title: Arquitectura y Seguridad
  url: /arquitectura.html
---

# Módulo de Tiempo (`running_time`)

Para proyectos didácticos y robótica escolar, `wedopy` proporciona una función simple inspirada en el ecosistema educativo (como micro:bit) para medir el tiempo transcurrido sin necesidad de importar librerías externas o calcular diferencias manuales.

```python
from wedopy import running_time
```

---

## Función `running_time()`

```python
running_time() -> int
```

Devuelve el número de **milisegundos** (enteros) transcurridos desde que se importó el paquete `wedopy` en el proceso actual (en la práctica, desde el arranque del programa).

- **Retorno:** `int` con el tiempo en milisegundos.
- **Reloj base:** Utiliza `time.monotonic()` internamente, por lo que no se ve afectado por cambios de hora en el sistema operativo.

---

## 💡 Ejemplos de uso

### Medición de duración de un trayecto

```python
import time
from wedopy import Hub, running_time

with Hub() as hub:
    motor = hub.motor("A")

    inicio = running_time()
    motor.run(75)

    time.sleep(2.5)

    motor.stop()
    fin = running_time()

    print(f"El motor estuvo activo durante {fin - inicio} ms (aprox. {(fin - inicio)/1000:.2f} s)")
```

### Temporizador sin bloqueo

```python
import time
from wedopy import Hub, running_time

with Hub() as hub:
    # Cambiar de color cada 500 ms
    siguiente_cambio = running_time() + 500
    color = 1

    for _ in range(100):
        if running_time() >= siguiente_cambio:
            hub.led.index(color)
            color = (color % 10) + 1
            siguiente_cambio = running_time() + 500
        time.sleep(0.01)
```

> **Nota:** Para operaciones avanzadas de sincronización o retardos en tareas cooperativas, utiliza siempre [`yield task.sleep(segundos)`](tareas.md).
