---
layout: default
title: Instalación y Requisitos
description: Requisitos del sistema, configuración Bluetooth en Linux e instalación de wedopy
prev:
  title: Introducción
  url: /
next:
  title: Guía Rápida
  url: /guia-rapida.html
---

# Instalación y Requisitos

En esta guía aprenderás a preparar tu entorno e instalar **`wedopy`** en tu sistema.

---

## 💻 Requisitos del sistema

- **Python**: Versiones `3.9`, `3.10`, `3.11`, `3.12` o `3.13`.
- **Sistema Operativo**: Linux con stack **BlueZ** (probado en Ubuntu, Debian, Fedora, Arch Linux).
- **Adaptador Bluetooth**: Adaptador Bluetooth 4.0 o superior compatible con **Bluetooth Low Energy (BLE)**.
- **Compilador C / Cython** (únicamente si compilas desde las fuentes o paquete de desarrollo).

---

## 📦 Instalación estándar

### Usando pip

Para instalar la versión publicada más reciente desde PyPI:

```bash
pip install wedopy
```

O en un entorno virtual recomendado:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install wedopy
```

### Usando uv

Si utilizas [uv](https://github.com/astral-sh/uv) como gestor de paquetes ultrarrápido:

```bash
uv add wedopy
```

---

## 🛠️ Instalación desde código fuente (Desarrollo)

Si deseas clonar el repositorio y compilar la extensión en Cython para contribuir o probar los últimos cambios:

### Con uv (recomendado)

```bash
git clone https://github.com/almeida-aguilar/wedopy.git
cd wedopy

# Instalar dependencias y compilar extensiones
uv sync

# Ejecutar la suite de pruebas unitarias
uv run pytest
```

### Con venv y pip

```bash
git clone https://github.com/almeida-aguilar/wedopy.git
cd wedopy

python3 -m venv .venv
source .venv/bin/activate

# Instalar en modo editable con herramientas de desarrollo
python -m pip install -e ".[dev]"

# Ejecutar las pruebas
pytest
```

> **Nota sobre Cython:** El archivo `wedopy_core/_wedopy.pyx` está redactado en un subconjunto de Cython compatible con sintaxis pura de Python. Si el módulo nativo compilado aún no está presente, las pruebas en `tests/conftest.py` pueden ejecutarse usando la versión interpretada emitiendo una advertencia.

---

## 📶 Configuración de Bluetooth en Linux

La comunicación con el LEGO WeDo 2.0 Smart Hub utiliza la biblioteca `bleak`, que interactúa con el demonio `bluetoothd` (BlueZ) a través de D-Bus.

### 1. Comprobar el servicio Bluetooth

Asegúrate de que el servicio Bluetooth esté activo:

```bash
sudo systemctl status bluetooth
```

Si no está activo, inícialo:

```bash
sudo systemctl start bluetooth
sudo systemctl enable bluetooth
```

### 2. Verificar el adaptador Bluetooth

Asegúrate de que el adaptador no esté bloqueado por `rfkill`:

```bash
rfkill list bluetooth
```

Si aparece bloqueado (*Soft blocked: yes*), desbloquéalo:

```bash
sudo rfkill unblock bluetooth
```

Comprueba que el adaptador esté encendido:

```bash
bluetoothctl power on
```

### 3. Permisos de usuario

Para evitar ejecutar scripts con `sudo`, asegúrate de que tu usuario tenga permisos para interactuar con los adaptadores Bluetooth:

```bash
sudo usermod -aG bluetooth $USER
```

> Reinicia la sesión o ejecuta `newgrp bluetooth` para que los cambios de grupo surtan efecto.

---

## 🧪 Verificación de la instalación

Puedes verificar que la biblioteca está correctamente instalada y que el simulador interno pasa todas las pruebas con:

```bash
python3 -c "import wedopy; print('wedopy versión:', wedopy.__version__)"
pytest
```

Si las 98 pruebas pasan correctamente, ¡tu entorno está listo para conectarse al Smart Hub!
