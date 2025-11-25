# Mouse-Control (Control de Cursor Manual y con Marcadores)

Este repositorio contiene dos utilidades desarrolladas para controlar el cursor del sistema:  
1) una versión **manual** para pruebas rápidas, y  
2) una versión **automática** utilizada en el proyecto final para validar la sincronización entre un marcador físico (capturado por OptiTrack) y la proyección visual.

Ambas herramientas fueron utilizadas durante el desarrollo del sistema de interacción física sobre la mesa del laboratorio Robotat.

---

## Archivos principales

### **1. MouseControl_Manual.py**
Control del cursor **mediante inputs escritos en la terminal**.  
Es una herramienta práctica para pruebas locales sin hardware externo.

- Simula movimiento del ratón.
- No requiere conexión a ningún sistema de visión.
- Implementado con `pyautogui`.

#### Dependencias
```python
import pyautogui
import time
```

#### Características
- Permite introducir valores manuales para mover el cursor.
- Útil para depurar interacciones sin el sistema OptiTrack.
- Se ejecuta desde consola:
```bash
python MouseControl_Manual.py
```

---

### **2. MouseControl_Auto.py** (Versión Final)
Versión completa utilizada en el proyecto para validar la **sincronización entre el marcador físico y la proyección**.  
Es la versión descrita en el trabajo escrito y en el Manual Cliente/Servidor.

- Lee datos de posición provenientes del sistema OptiTrack vía MQTT.
- Convierte esas coordenadas en movimientos reales del cursor.
- Usa llamadas de bajo nivel con `ctypes` para mayor precisión.

#### Dependencias
```python
import numpy as np
import cv2
import json
import paho.mqtt.client as mqtt
import threading
import time
import keyboard
import ctypes
from ctypes import wintypes
```

---

## Requisitos para ejecutar **MouseControl_Auto.py**

Para que la aplicación reciba los datos correctos y pueda mover el cursor según la posición del marcador, se requiere:

### ✔ 1. El sistema OptiTrack / NatNet → MQTT debe estar corriendo  
El servidor del laboratorio debe estar transmitiendo la información del marcador por MQTT.

### ✔ 2. El cliente debe estar conectado a la red del Robotat  
La computadora que ejecuta el script debe estar en la misma red donde se publica el tópico MQTT.

### ✔ 3. Configurar el tópico MQTT correcto dentro del script  
En el código, ajustar la línea:
```python
MQTT_TOPIC = "robotat/tu_topic"
```

---

## Ejecución

### Modo manual
```bash
python MouseControl_Manual.py
```

### Modo automático
```bash
python MouseControl_Auto.py
```

---

## Notas adicionales

- El modo automático utiliza coordenadas en tiempo real provenientes del sistema de captura de movimiento.
- El uso de `ctypes` permite controlar el cursor con precisión milimétrica.
- El script puede ampliarse fácilmente para soportar múltiples marcadores o gestos.

---

