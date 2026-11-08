---
layout: default
title: "API: Periféricos Integrados"
description: Referencia del LED RGB y el Botón físico del Smart Hub en wedopy
prev:
  title: Sensores
  url: /api/sensores.html
next:
  title: Tareas Cooperativas
  url: /api/tareas.html
---

# Periféricos Integrados (`LED` y `Button`)

El LEGO WeDo 2.0 Smart Hub incorpora un LED multicolor y un botón pulsador integrados directamente en la placa principal, accesibles a través de `hub.led` y `hub.button`.

```python
from wedopy import LED, Button
```

---

## Clase `LED`

Controla el diodo emisor de luz multicolor del Hub. Permite seleccionar colores predefinidos mediante índices o colores personalizados mediante componentes RGB (rojo, verde y azul).

### Métodos

#### `on()`
```python
hub.led.on() -> None
```
Enciende el LED en color blanco a máxima intensidad (equivalente a `rgb(255, 255, 255)`).

#### `off()`
```python
hub.led.off() -> None
```
Apaga el LED (equivalente a `rgb(0, 0, 0)`).

#### `index(index)`
```python
hub.led.index(index: int) -> None
```
Aplica uno de los colores predefinidos de la paleta oficial de WeDo 2.0 (enteros entre `0` y `10`).

| Índice | Color visual |
| :---: | :--- |
| `0` | **Apagado** |
| `1` | **Rosa** |
| `2` | **Morado** |
| `3` | **Azul** |
| `4` | **Celeste / Cian** |
| `5` | **Verde** |
| `6` | **Amarillo** |
| `7` | **Naranja** |
| `8` | **Rojo** |
| `9` | **Blanco brillante** |
| `10` | **Blanco tenue** |

```python
hub.led.index(5)  # Enciende en verde
```

#### `rgb(red, green, blue)`
```python
hub.led.rgb(red: int, green: int, blue: int) -> None
```
Establece un color personalizado mediante canales de 8 bits (0 a 255).

- **Parámetros:**
  - `red` *(int)*: Intensidad del canal rojo (`0..255`).
  - `green` *(int)*: Intensidad del canal verde (`0..255`).
  - `blue` *(int)*: Intensidad del canal azul (`0..255`).

```python
# Color turquesa personalizado
hub.led.rgb(0, 200, 180)
```

---

## Clase `Button`

Permite consultar el estado actual del botón pulsador central del Smart Hub.

### Propiedades

#### `is_pressed`
```python
hub.button.is_pressed -> bool
```
Devuelve `True` si el botón físico está siendo presionado en este instante, o `False` si está libre.

#### `is_released`
```python
hub.button.is_released -> bool
```
Devuelve `True` si el botón físico no está presionado (inverso de `is_pressed`).

---

## 💡 Ejemplo interactivo: Botón de cambio de color

```python
import time
from wedopy import Hub

with Hub() as hub:
    color = 1
    print("Pulsa el botón central para cambiar el color del LED (Ctrl+C para salir)")

    while True:
        if hub.button.is_pressed:
            hub.led.index(color)
            color = (color % 10) + 1
            # Esperar a que se libere el botón (evita rebotes)
            while hub.button.is_pressed:
                time.sleep(0.05)
        time.sleep(0.05)
```
