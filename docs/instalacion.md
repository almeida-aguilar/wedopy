---
layout: default
title: Instalación y Requisitos
description: Requisitos del sistema, configuración Bluetooth en Linux y Windows e instalación de wedopy
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
- **Sistema Operativo**:
  - **Linux** con stack **BlueZ** (probado en Ubuntu, Debian, Fedora, Arch Linux). Plataforma oficial y validada en hardware.
  - **Windows 10 (1809+) o Windows 11** con Bluetooth 4.0+ (backend WinRT a través de `bleak`). Soporte documentado, no validado oficialmente con hardware.
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

Si aparece bloqueado (_Soft blocked: yes_), desbloquéalo:

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

## 🪟 Windows

`wedopy` funciona en Windows a través de `bleak`, que utiliza **WinRT** como backend BLE. La plataforma **no está validada oficialmente con hardware real** (la validación se ha realizado en Linux/BlueZ), pero el código no contiene ninguna dependencia específica de Linux y la instalación está documentada y soportada.

### Requisitos

- **Windows 10 (versión 1809 o superior) o Windows 11.**
- **Python 3.9–3.13** (recomendado Python 3.12).
- **Bluetooth 4.0+** activo y adaptador habilitado.
- **Microsoft Visual C++ Build Tools** (solo si compilas la extensión Cython desde fuente; si instalas un wheel precompilado no es necesario).

### Instalación con pip

Abre **PowerShell** (no es necesario ejecutarlo como administrador):

```powershell
# Crear y activar el entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Actualizar pip e instalar
python -m pip install --upgrade pip
python -m pip install wedopy
```

> Si PowerShell bloquea la activación del entorno virtual con un error de _execution policy_, ejecuta una vez:
>
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```

### Instalación desde código fuente

```powershell
git clone https://github.com/almeida-aguilar/wedopy.git
cd wedopy

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

pytest
```

Si la compilación de Cython falla por falta de compilador, instala las **Build Tools for Visual Studio** desde [visualstudio.microsoft.com/visual-cpp-build-tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/), seleccionando la carga de trabajo **"Desarrollo para el escritorio con C++"**.

> **Nota sobre Cython en Windows:** al igual que en Linux, si la extensión nativa no está compilada, `tests/conftest.py` ejecuta `wedopy_core/_wedopy.pyx` como Python puro y emite una advertencia.

### Instalación con uv

```powershell
uv sync
uv run pytest
```

### Comprobar el adaptador Bluetooth

Antes de ejecutar `wedopy`, verifica que Windows detecta el Bluetooth:

1. **Configuración → Bluetooth y dispositivos** → el interruptor de Bluetooth debe estar activado.
2. En PowerShell:
   ```powershell
   Get-PnpDevice -Class Bluetooth
   ```
   Debe aparecer tu adaptador (por ejemplo, _Intel(R) Wireless Bluetooth_).
3. Si el adaptador no aparece o el Bluetooth está deshabilitado, actualiza los drivers del fabricante.

### Verificación rápida

```powershell
python -c "import wedopy; print('wedopy', wedopy.__version__)"
```

Si el comando imprime la versión sin errores, la instalación está completa.

### Limitaciones conocidas en Windows

- **No validado con hardware real.** El comportamiento de `bleak` sobre WinRT puede diferir de BlueZ en latencias, reconexión y tiempos de ACK. Los tiempos del watchdog (2 s) y del heartbeat (0.5 s) están calibrados para Linux; en Windows podrían necesitar ajustes.
- **Requisito de un único cliente BLE.** El hub WeDo 2.0 solo admite una conexión BLE a la vez. Cierra aplicaciones como la app oficial de LEGO o Scratch antes de conectar con `wedopy`.
- **Emparejamiento.** En algunos adaptadores Windows es necesario emparejar primero el hub desde _Configuración → Bluetooth y dispositivos → Agregar dispositivo_ antes de que `bleak` lo detecte. Si `HubConnectionError` persiste, prueba a emparejar manualmente el dispositivo "LPF2 Smart Hub" y vuelve a ejecutar.

### Alternativa: WSL2

Si necesitas el stack BlueZ (por ejemplo, para reproducir exactamente el entorno validado), puedes usar **WSL2 con Ubuntu**. Ten en cuenta que WSL2 **no tiene acceso directo al adaptador Bluetooth del host** de forma predeterminada; es posible pasar el adaptador USB a WSL2 mediante `usbipd-win`, pero la configuración es avanzada y no está cubierta por esta guía. Para la mayoría de usuarios, la instalación nativa en Windows descrita arriba es suficiente.

---

## 🧪 Verificación de la instalación

Puedes verificar que la biblioteca está correctamente instalada y que el simulador interno pasa todas las pruebas con:

```bash
python3 -c "import wedopy; print('wedopy versión:', wedopy.__version__)"
pytest
```

Si las 98 pruebas pasan correctamente, ¡tu entorno está listo para conectarse al Smart Hub!
