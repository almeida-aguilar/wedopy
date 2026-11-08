---
layout: default
title: Arquitectura y Seguridad
description: Diseño interno de wedopy, coordinador de un solo escritor, watchdog y gestión de fallos
prev:
  title: Tiempo
  url: /api/tiempo.html
next:
  title: Ejemplos Prácticos
  url: /ejemplos.html
---

# Arquitectura y Seguridad

La arquitectura de **`wedopy`** está diseñada para proporcionar una experiencia de programación sencilla y educativa sin comprometer la fiabilidad y seguridad física del hardware.

---

## 🏛️ Las 4 Capas del Sistema

```
┌────────────────────────────────────────────────────────┐
│ 1. Capa de Usuario (Python)                           │
│    Tus scripts, cuadernos Jupyter, ejemplos            │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 2. API Pública (src/wedopy/)                           │
│    Hub · Motor · Sensors · LED · Button · Tasks        │
│    Validación de tipos, rangos y context managers      │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 3. Núcleo Compilado (wedopy_core/_wedopy.pyx - Cython) │
│    • Coordinador Single-Writer (Cola Normal y Urgente) │
│    • Máquina de Estados (DISCONNECTED, READY, ERROR)   │
│    • Watchdog y Heartbeat en hilo independiente        │
│    • Serialización y decodificación binaria de paquetes│
│    • Capa de Transporte (BleakTransport / Simulated)   │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 4. Hardware Físico                                     │
│    LEGO WeDo 2.0 Smart Hub (BLE GATT)                  │
└────────────────────────────────────────────────────────┘
```

---

## 🧵 El Coordinador de un Solo Escritor (*Single-Writer*)

Las pilas Bluetooth (y en particular el firmware del chip BLE del Smart Hub WeDo 2.0) sufren de corrupción de estado o pérdida de paquetes si múltiples operaciones de escritura GATT se envían concurrentemente o sin esperar la respuesta previa.

Para resolver esto de raíz:
1. **Un único hilo escritor**: Todas las órdenes que salen hacia el hardware pasan por una cola coordinada central en un hilo dedicado.
2. **Escrituras con respuesta (*with response*)**: Nunca se recurre a escrituras ciegas sin confirmación (*write-without-response*). Cada comando debe recibir un acuse de recibo del microcontrolador antes de despachar el siguiente.
3. **Canal de Emergencia**: El coordinador dispone de dos colas de prioridad:
   - **Cola normal**: Lecturas periódicas de sensores, cambios de color del LED y ajustes de velocidad de motores.
   - **Cola de emergencia**: Solicitudes de parada crítica del watchdog, que adelantan a cualquier operación pendiente de la cola normal.

---

## ⏱️ Sistema de Seguridad: Heartbeat y Watchdog

Uno de los riesgos principales en robótica educativa es que un vehículo o mecanismo motorizado continúe en movimiento descontrolado si el ordenador se bloquea, el proceso en Python se congela o se pierde la señal de radio.

```
       [ Motor en marcha ]
               │
               ▼
┌─────────────────────────────┐
│    Heartbeat (cada 0.5 s)   │
│  Lee nivel de Batería (GATT)│
└──────────────┬──────────────┘
               │
               ├── ¿ACK recibido en < 2.0 s? ──► Continúa normal
               │
               └── ¿Sin respuesta > 2.0 s?
                       │
                       ▼
         ┌───────────────────────────┐
         │     WATCHDOG DISPARADO    │
         │  1. Parada de emergencia  │
         │     (2 intentos inmediatos)│
         │  2. Hub pasa a 'ERROR'    │
         │  3. Log en wedopy.watchdog│
         └───────────────────────────┘
```

### Funcionamiento detallado:

- **Activación automática**: En cuanto cualquier motor del hub adquiere una velocidad distinta de cero, el hilo de supervisión activa el *heartbeat*.
- **Latido (Heartbeat)**: Solicita la lectura de la característica de batería cada **0.5 segundos**.
- **Perro guardián (Watchdog)**: Si no se recibe una confirmación válida en **2.0 segundos**, el watchdog toma el control:
  1. Emite una orden de parada de emergencia con prioridad máxima (hasta 2 intentos).
  2. Registra el evento crítico en el logger estándar `wedopy.watchdog`.
  3. Transiciona el estado del hub a `ERROR` para evitar nuevas escrituras que puedan comprometer el sistema.
- **Independencia de hilos**: El watchdog y el heartbeat corren en su propio hilo del sistema operativo. Por lo tanto, si tu script de usuario entra en un bucle infinito `while True: pass` o el planificador de tareas se suspende, **el watchdog continuará activo y protegerá el hardware**.

---

## 🎛️ Parámetros de Tiempos (*Timing*)

La biblioteca utiliza parámetros de temporización definidos en `wedopy_core.runtime.Timing`:

| Parámetro | Valor por defecto | Descripción |
| :--- | :---: | :--- |
| `connect_timeout` | `15.0 s` | Tiempo máximo para escanear y conectar con el Smart Hub. |
| `op_timeout` | `1.0 s` | Tiempo límite para recibir acuse de recibo de una orden individual. |
| `retry_max` | `2` | Número máximo de reintentos para órdenes de parada de emergencia. |
| `retry_delay` | `0.05 s` | Pausa entre reintentos en milisegundos. |
| `heartbeat_interval`| `0.5 s` | Intervalo entre latidos de supervisión. |
| `watchdog_interval` | `2.0 s` | Umbral de pérdida de enlace antes del paro de emergencia. |
