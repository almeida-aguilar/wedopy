---
layout: default
title: "API: Tareas Cooperativas"
description: Sistema de concurrencia cooperativa con hub.tasks y el módulo task en wedopy
prev:
  title: Periféricos Integrados
  url: /api/perifericos.html
next:
  title: Excepciones
  url: /api/excepciones.html
---

# Tareas Cooperativas (`hub.tasks` y `task`)

`wedopy` incluye un sistema didáctico de **multitarea cooperativa** basado en generadores de Python (`yield`). Permite que múltiples acciones ocurran en paralelo (por ejemplo, parpadear un LED mientras un motor avanza y un sensor supervisa el camino) **sin necesidad de hilos de usuario ni la complejidad sintáctica de `asyncio`**.

```python
from wedopy import Hub, task
```

---

## 📦 Módulo `task`

Proporciona las instrucciones que una tarea devuelve con `yield` para ceder el control al planificador:

### `task.sleep(seconds)`
```python
yield task.sleep(seconds: float)
```
Suspende la ejecución de la tarea actual durante al menos `seconds` segundos, permitiendo que otras tareas avancen mientras tanto.

- Si `seconds == 0`, equivale a `yield task.yield_now()`.
- Si se crea la instrucción sin la palabra `yield`, `wedopy` emitirá una advertencia (`RuntimeWarning`) para prevenir errores comunes de principiantes.

### `task.yield_now()`
```python
yield task.yield_now()
```
Cede inmediatamente el turno al siguiente proceso en la cola de tareas listas sin introducir retraso en tiempo.

---

## 🎛️ Gestor `hub.tasks` (`TaskManager`)

Cada instancia de `Hub` dispone de su propio gestor `hub.tasks`.

### Métodos

#### `add(func, *, background=False)`
```python
hub.tasks.add(func: callable, *, background: bool = False) -> None
```
Registra una función o generador para ser ejecutado.

- **Parámetros:**
  - `func`: Función convencional o función generadora (que use `yield task.sleep(...)`). No admite funciones `async def`.
  - `background` *(bool, por defecto `False`)*:
    - Si es `False` (tarea normal): la tarea mantiene vivo el bucle de `wait()` hasta que finalice.
    - Si es `True` (tarea de fondo): la tarea se ejecuta indefinidamente (ej. animación continua de LED) y **se cancela automáticamente** en cuanto todas las tareas normales hayan finalizado.

#### `wait()`
```python
hub.tasks.wait() -> None
```
Inicia la ejecución de todas las tareas registradas y bloquea el hilo llamante hasta que todas las tareas normales hayan concluido.
- Al terminar las tareas normales, cancela las tareas marcadas como `background=True`.
- Si el usuario interrumpe el programa con `Ctrl+C` (`KeyboardInterrupt`), `wait()` cancela ordenadamente todas las tareas pendientes antes de propagar la interrupción.

#### `cancel()`
```python
hub.tasks.cancel() -> None
```
Cancela de inmediato todas las tareas registradas (normales y de fondo).

> **Aviso de seguridad sobre motores:** Cancelar una tarea **no detiene automáticamente los motores** en movimiento. Para evitar que un motor continúe girando indefinidamente, protégelo siempre dentro de un bloque `try/finally` o utiliza la salida del context manager `with Hub()`.

#### `diagnostics`
```python
hub.tasks.diagnostics -> list[tuple[str, Exception]]
```
Lista de errores secundarios o excepciones capturadas durante la limpieza y cancelación de tareas en la última llamada a `wait()`.

---

## 💡 Ejemplo completo: Luces de emergencia y marcha

```python
from wedopy import Hub, task

with Hub() as hub:
    # Tarea de fondo: destello de LED continuo (amarillo y azul)
    def luces_policia():
        while True:
            hub.led.index(6)       # Amarillo
            yield task.sleep(0.2)
            hub.led.index(3)       # Azul
            yield task.sleep(0.2)

    # Tarea normal: mover el motor durante 3 segundos
    def mover_vehiculo():
        motor = hub.motor("A")
        try:
            motor.run(80)
            yield task.sleep(3.0)
        finally:
            motor.stop()           # Garantiza la parada al finalizar o cancelarse

    # Registrar tareas
    hub.tasks.add(luces_policia, background=True)
    hub.tasks.add(mover_vehiculo)

    print("Iniciando tareas coordinadas...")
    # Ejecuta hasta que mover_vehiculo termine.
    # En ese instante, luces_policia se cancela automáticamente.
    hub.tasks.wait()
    print("¡Finalizado con éxito!")
```
