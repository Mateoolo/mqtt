"""
subscriber_reto.py
==================
Suscriptor MQTT inteligente que valúa datos con Pydantic, genera
alertas en tiempo real si se supera el umbral de cadena de frío y
registra fallos de validación en un archivo de log.
"""

import json
import time
from datetime import datetime

import paho.mqtt.client as mqtt
from pydantic import BaseModel, Field, ValidationError

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
BROKER = "broker.emqx.io"
PUERTO = 1883
TOPICO_SUSCRIPCION = "unmsm/callao/camara/+/telemetria"
UMBRAL_PELIGRO = 30.0  # °C
LOG_ERRORES = "log_errores.txt"


# ---------------------------------------------------------------------------
# Esquema de validación con Pydantic
# ---------------------------------------------------------------------------
class LecturaSensor(BaseModel):
    """Modelo de datos esperado para una lectura de sensor.

    Se usa alias para mapear el campo 'sensor_id' del JSON a 'camara_id'.
    """
    camara_id: str = Field(..., alias="sensor_id")
    timestamp: float
    valor: float = Field(..., ge=-50.0, le=100.0)
    unidad: str


# ---------------------------------------------------------------------------
# Registro de errores en archivo
# ---------------------------------------------------------------------------
def registrar_error(topico: str, payload_raw: str, mensaje_error: str):
    """Append al archivo log_errores.txt con timestamp."""
    timestamp = datetime.now().isoformat()
    linea = (
        f"[{timestamp}] Tópico: {topico}\n"
        f"  Payload: {payload_raw}\n"
        f"  Error:   {mensaje_error}\n"
        f"{'-' * 70}\n"
    )
    with open(LOG_ERRORES, "a", encoding="utf-8") as f:
        f.write(linea)


# ---------------------------------------------------------------------------
# Callbacks MQTT
# ---------------------------------------------------------------------------
def on_connect(client, userdata, flags, rc, properties):
    if rc == 0:
        print("Conectado al broker MQTT exitosamente.")
        client.subscribe(TOPICO_SUSCRIPCION)
        print(f"Suscrito a: {TOPICO_SUSCRIPCION}")
    else:
        print(f"Error de conexión. Código de retorno: {rc}")


def on_message(client, userdata, msg):
    raw_payload = msg.payload.decode(errors="replace")
    print(f"\n[SUSCRIPTOR] Mensaje recibido en: {msg.topic}")
    print(f"  Payload: {raw_payload[:80]}...") if len(raw_payload) > 80 else print(f"  Payload: {raw_payload}")

    # --- 1. Intentar decodificar JSON ------------------------------------
    try:
        datos_json = json.loads(raw_payload)
    except json.JSONDecodeError as e:
        registrar_error(msg.topic, raw_payload, f"JSON inválido: {e}")
        print(f"  -> Error: JSON invalido - registrado en {LOG_ERRORES}")
        return

    # --- 2. Validar contra el esquema Pydantic ---------------------------
    try:
        lectura = LecturaSensor(**datos_json)
    except ValidationError as e:
        registrar_error(msg.topic, raw_payload, f"Validación Pydantic: {e}")
        print(f"  -> Error: violacion de esquema - registrado en {LOG_ERRORES}")
        return

    # --- 3. Datos válidos — comprobar umbral ----------------------------
    temp = lectura.valor
    print(f"  + Datos validados - Camara: {lectura.camara_id}, "
          f"Temperatura: {temp} {lectura.unidad}")

    if temp > UMBRAL_PELIGRO:
        print(f"  ! [PELIGRO] Perdida de cadena de frio en Camara "
              f"{lectura.camara_id}!")
    else:
        print(f"  -> Temperatura dentro del rango seguro "
              f"(<= {UMBRAL_PELIGRO} C).")


# ---------------------------------------------------------------------------
# Bucle principal
# ---------------------------------------------------------------------------
def main():
    cliente = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

    cliente.on_connect = on_connect
    cliente.on_message = on_message

    print(f"Conectando al broker {BROKER}:{PUERTO} ...")
    cliente.connect(BROKER, PUERTO, keepalive=60)

    # Bucle síncrono infinito (bloqueante)
    cliente.loop_forever()


if __name__ == "__main__":
    main()
