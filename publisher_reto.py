"""
publisher_reto.py
=================
Publicador MQTT que simula sensores de temperatura para dos cámaras
de refrigeración en la cadena de frío farmacéutica.
Incorpora inyección programada de datos corruptos para probar
la tolerancia a fallos del suscriptor.
"""

import json
import random
import time

import paho.mqtt.client as mqtt

# ---------------------------------------------------------------------------
# Configuración del broker y tópicos
# ---------------------------------------------------------------------------
BROKER = "broker.emqx.io"
PUERTO = 1883
TOPICO_BASE = "unmsm/callao/camara"
CAMARAS = ["01", "02"]
INTERVALO = 2          # segundos entre publicaciones
UMBRAL_PELIGRO = 8.0   # °C — estándar cadena de frío farmacéutica

# ---------------------------------------------------------------------------
# Control de inyección de fallos
# ---------------------------------------------------------------------------
FALLOS = [
    # 1. valor = None (tipo inválido para float)
    lambda c_id: {
        "sensor_id": c_id,
        "timestamp": time.time(),
        "valor": None,
        "unidad": "Celsius",
    },
    # 2. valor = cadena de texto en vez de número
    lambda c_id: {
        "sensor_id": c_id,
        "timestamp": time.time(),
        "valor": "exploto",
        "unidad": "Celsius",
    },
    # 3. payload ni siquiera es JSON válido
    lambda c_id: f"ESTO_NO_ES_JSON_CAMARA_{c_id}",
    # 4. falta el campo obligatorio sensor_id
    lambda c_id: {
        "timestamp": time.time(),
        "valor": 6.5,
        "unidad": "Celsius",
    },
    # 5. valor fuera del rango físico permitido por Pydantic (le=100.0)
    lambda c_id: {
        "sensor_id": c_id,
        "timestamp": time.time(),
        "valor": 120.0,
        "unidad": "Celsius",
    },
]

contador_publicaciones = 0


# ---------------------------------------------------------------------------
# Generación de datos normales del sensor
# ---------------------------------------------------------------------------
def generar_lectura_normal(camara_id: str) -> dict:
    """Genera una lectura de temperatura válida."""
    return {
        "sensor_id": camara_id,
        "timestamp": time.time(),
        "valor": round(random.uniform(2.0, 10.0), 2),
        "unidad": "Celsius",
    }


# ---------------------------------------------------------------------------
# Publicación de un mensaje
# ---------------------------------------------------------------------------
def publicar(cliente: mqtt.Client, topico: str, payload, camara_id: str):
    """Serializa y publica el payload en el tópico indicado."""
    if isinstance(payload, dict):
        mensaje = json.dumps(payload, ensure_ascii=False)
    else:
        mensaje = str(payload)

    info = cliente.publish(topico, mensaje, qos=1)
    info.wait_for_publish()
    print(f"[PUBLICADOR] Cámara {camara_id} → {topico}: {mensaje}")


# ---------------------------------------------------------------------------
# Conexión al broker
# ---------------------------------------------------------------------------
def conectar_mqtt() -> mqtt.Client:
    """Crea y conecta el cliente MQTT usando la API moderna v2."""
    cliente = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    print(f"Conectando al broker {BROKER}:{PUERTO} ...")
    cliente.connect(BROKER, PUERTO, keepalive=60)
    return cliente


# ---------------------------------------------------------------------------
# Bucle principal
# ---------------------------------------------------------------------------
def main():
    global contador_publicaciones

    cliente = conectar_mqtt()
    cliente.loop_start()

    try:
        while True:
            for cam_id in CAMARAS:
                topico = f"{TOPICO_BASE}/{cam_id}/telemetria"
                contador_publicaciones += 1

                # Cada ~10 publicaciones inyectamos un fallo (rotativo)
                if contador_publicaciones % 10 == 0:
                    idx_fallo = (contador_publicaciones // 10 - 1) % len(FALLOS)
                    payload = FALLOS[idx_fallo](cam_id)
                    print(f"  → INYECTANDO FALLO tipo {idx_fallo + 1}")
                else:
                    payload = generar_lectura_normal(cam_id)

                publicar(cliente, topico, payload, cam_id)
                time.sleep(INTERVALO)

    except KeyboardInterrupt:
        print("\nDeteniendo publicador ...")
    finally:
        cliente.loop_stop()
        cliente.disconnect()
        print("Publicador desconectado.")


if __name__ == "__main__":
    main()
