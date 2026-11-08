---
layout: default
title: Hardware WeDo 2.0 y Protocolo
description: Análisis detallado del hardware LEGO WeDo 2.0 Smart Hub, comportamiento del firmware y BLE
prev:
  title: Guía Rápida
  url: /guia-rapida.html
next:
  title: Resumen de la API
  url: /api/
---

# Hardware WeDo 2.0 y Protocolo

El **LEGO® WeDo 2.0 Smart Hub** (número de modelo 45300) es un microcontrolador con conectividad Bluetooth Low Energy (BLE) diseñado para la educación robótica. Esta sección documenta su arquitectura física, protocolo de comunicación y particularidades descubiertas y validadas en el hardware real.

---

## 🔌 Puertos y Dispositivos

El Smart Hub cuenta con dos conectores externos de tipo LEGO Power Functions 2.0 (LPF2) y varios periféricos integrados en la placa:

```
                  ┌──────────────────────┐
                  │    [ Botón Central ] │
                  │                      │
   [ Puerto A ] ──┤    [ LED RGB ]       ├── [ Puerto B ]
   (Conector 1)   │                      │   (Conector 2)
                  │    Compartimento     │
                  │    2x Pilas AA       │
                  └──────────────────────┘
```

| Dispositivo | Identificador interno | Tipo de conexión | Notas |
| :--- | :--- | :--- | :--- |
| **Batería** | `0x00` | Interno | Nivel de batería en porcentaje (usado para el latido/heartbeat). |
| **Puerto A** | `0x01` | Externo LPF2 | Admite Motor, Sensor de Distancia o Sensor de Inclinación. |
| **Puerto B** | `0x02` | Externo LPF2 | Admite Motor, Sensor de Distancia o Sensor de Inclinación. |
| **LED RGB** | `0x06` | Interno | Admite modo indexado (0..10) o color directo (RGB 24-bit). |
| **Botón** | `0x07` | Interno | Estado del botón físico (0 = liberado, 1 = presionado). |

---

## 📡 Protocolo Bluetooth Low Energy (GATT)

El Smart Hub se expone mediante los siguientes servicios y características GATT:

- **Servicio Principal WeDo 2.0**: `00001523-1212-efde-1523-785feabcd123`
- **Característica de Salida / Comandos**: `00001565-1212-efde-1523-785feabcd123` (Escrituras con respuesta para motores y LED).
- **Característica de Notificación de Puertos**: `00001527-1212-efde-1523-785feabcd123` (Reporta conexión/desconexión de dispositivos).
- **Característica de Notificación de Sensores**: `00001560-1212-efde-1523-785feabcd123` (Envío de muestras de sensores).
- **Servicio Estándar de Batería**: `0000180f-0000-1000-8000-00805f9b34fb` (Lectura periódica del nivel de carga).

---

## 🔍 Particularidades del Firmware (Comprobadas en Hardware)

Durante la implementación y validación en hardware real de `wedopy`, se identificaron comportamientos críticos que difieren de la documentación teórica:

### 1. Sensor de inclinación (Tilt): No es un acelerómetro continuo

El sensor de inclinación WeDo 2.0 es en realidad un **interruptor mecánico de 4 posiciones** con amortiguación, no un acelerómetro triaxial IMU.

- **Modo Dirección (Modo 1)**: Configurado con `UNIT_SI`. Emite un número en coma flotante de 4 bytes (`float32`). Los valores válidos son:
  - `0`: Neutro / horizontal (`neutral`)
  - `3`: Inclinado hacia atrás (`back`)
  - `5`: Inclinado a la derecha (`right`)
  - `7`: Inclinado a la izquierda (`left`)
  - `9`: Inclinado hacia adelante (`forward`)
- **Modo Ángulo (Modo 0)**: **Requiere estrictamente `UNIT_RAW`** y emite un par de enteros con signo de 8 bits (`int8`, 2 bytes en total).
  > **Advertencia de compatibilidad:** Si el software envía una solicitud de ángulo con `UNIT_SI` (como indicaba la especificación antigua de LEGO), el firmware del Hub **acepta el comando sin error pero nunca emite ninguna notificación**. `wedopy` maneja esto automáticamente solicitando `UNIT_RAW`.
- **Modo Golpe/Bump (Modo 2)**: Aunque el firmware responde afirmativamente a la orden de configuración del modo 2, los sensores de inclinación comerciales nunca emiten notificaciones de golpe. Este modo no está implementado en el firmware físico.

### 2. Notificaciones por cambio (Delta-Only)

Los sensores WeDo 2.0 funcionan en modo *notificación por cambio*:
- Cuando un sensor está en reposo absoluto, **el firmware no envía paquetes BLE repetidos**.
- Si invocas `sensor.read()` y no ha habido cambio físico desde la última muestra, la función devolverá el último valor almacenado en caché. Si se requiere una muestra fresca tras una reconexión, es necesario que haya movimiento físico o la operación esperará hasta el tiempo límite (*timeout*).

### 3. Sensor de distancia

- El sensor infrarrojo mide proximidad por intensidad reflejada en una escala de **0 a 10**, no en centímetros reales.
- El valor `0` representa proximidad inmediata (menos de 3-5 cm), mientras que `10` representa ausencia de obstáculo detectable.

### 4. Motores y parada `nobarrier`

- El comando de potencia acepta enteros en el rango `-100` a `+100`.
- El Smart Hub implementa una parada tipo *coast/float* sin freno activo (*brake/barrier*). Cuando se ordena `motor.stop()`, el motor deja de recibir energía y desacelera libremente.
- Los acuses de recibo (ACK) confirman la recepción y procesamiento de la orden en el microcontrolador, pero no que el eje mecánico se haya detenido por completo.

---

## 🛡️ Hilo Coordinador y Seguridad

Debido a que el chip BLE del Smart Hub no soporta operaciones de escritura concurrentes desordenadas:
1. `wedopy` utiliza un **hilo coordinador único** (*Single-Writer Coordinator*).
2. Todas las escrituras se realizan estrictamente **con respuesta** (*with response*), garantizando que el paquete anterior fue recibido y validado por el hub antes de emitir el siguiente.
3. El *Watchdog* de seguridad supervisa el latido continuo de batería (Heartbeat cada 0.5 s) mientras los motores estén encendidos. Ante cualquier fallo de enlace superior a 2 segundos, se lanzan 2 intentos de parada de emergencia en un canal prioritario.
