# Cuestionario de Evaluación — Laboratorio MQTT

## 1. Pregunta Crítica

> ¿Por qué no es viable utilizar una arquitectura síncrona HTTP REST para interconectar sensores industriales que reportan datos cada 1 segundo? Justifique su respuesta basándose en hilos de ejecución de servidor y sobrecarga de paquetes.

**Respuesta:**

La arquitectura HTTP REST no es viable para entornos de sensores industriales con reportes periódicos de 1 segundo por dos razones fundamentales:

**a) Modelo de hilos de ejecución del servidor.**  
HTTP opera bajo el paradigma Cliente-Servidor síncrono: por cada petición entrante, el servidor debe mantener un hilo (o proceso) bloqueado mientras espera la respuesta del recurso. Si un servidor REST recibe N sensores reportando cada 1 segundo, debe mantener al menos N conexiones concurrentes en estado activo. Cuando N escala a cientos o miles de sensores (típico en una planta industrial o cadena farmacéutica), el costo de context-switching, memoria y gestión de hilos del sistema operativo se vuelve prohibitivo. Un servidor web convencional maneja del orden de 10⁴ conexiones simultáneas como máximo; una planta con 10 000 sensores saturaría el servidor en segundos. MQTT, en contraste, es asíncrono y orientado a eventos: un solo hilo en el broker puede manejar millones de conexiones gracias al modelo Pub/Sub y al bucle de red no bloqueante.

**b) Sobrecarga de paquetes (overhead).**  
Cada petición HTTP lleva consigo cabeceras de texto plano de varios cientos de bytes incluso para un payload mínimo. Una petición GET o POST típica excede los 500 bytes solo en cabeceras (User-Agent, Content-Type, Cookies, etc.). Al enviar un payload de, digamos, 50 bytes cada segundo, el overhead de HTTP representa más del 90 % del tráfico total. En una red con 10 000 sensores, esto se traduce en ≈ 5 MB/s únicamente de cabeceras. MQTT reduce la cabecera fija a solo 2 bytes, logrando una eficiencia espectral órdenes de magnitud superior. Esto es crítico cuando los sensores se comunican mediante redes LPWAN, satelitales o celulares con ancho de banda limitado y costoso.

### Conclusión

HTTP REST no escala en número de conexiones ni eficiencia de red para telemetría industrial de alta frecuencia. MQTT, con su modelo asíncrono Pub/Sub y cabecera de 2 bytes, fue diseñado explícitamente para resolver estos problemas.

---

## 2. Pregunta Práctica

> Explique en qué escenarios de desarrollo de software es imperativo utilizar el nivel QoS 2 en lugar de QoS 0.

**Respuesta:**

QoS (Quality of Service) define la garantía de entrega de un mensaje MQTT. Los tres niveles son:

| QoS | Garantía | Duplicados | Overhead |
|-----|----------|------------|----------|
| 0   | A lo sumo una vez (_at most once_) | No | Mínimo |
| 1   | Al menos una vez (_at least once_) | Sí | Medio |
| 2   | Exactamente una vez (_exactly once_) | No | Máximo (4 pasos) |

Es **imperativo usar QoS 2** en los siguientes escenarios:

**a) Sistemas de pago y transacciones financieras.**  
Si un mensaje transporta una orden de compra, transferencia bancaria o autorización de pago, la duplicación (posible en QoS 1) o la pérdida (posible en QoS 0) son inaceptables. El sistema debe garantizar que la transacción se procese exactamente una vez.

**b) Control de dispositivos críticos (actuadores industriales).**  
En una línea de envasado farmacéutico, una orden de "activar pistón" o "abrir válvula" no puede perderse (peligro físico) ni duplicarse (riesgo de sobrepresión o rotura). QoS 2 asegura que el actuador reciba la instrucción una y solo una vez.

**c) Comandos de seguridad y enclavamientos (_interlocks_).**  
En una cámara de refrigeración, el comando "encender respaldo" ante una falla del compresor principal debe llegar con certeza absoluta. Una pérdida de mensaje (QoS 0) podría significar la pérdida total del producto almacenado.

**d) Telemetría con valor legal o regulatorio.**  
En cadenas de frío farmacéuticas, los registros de temperatura deben ser auditables y completos. Si se pierde una lectura (QoS 0) se genera un hueco en la auditoría que puede invalidar un lote entero de vacunas. QoS 2 garantiza la integridad del histórico.

### Cuándo NO usar QoS 2

Para lecturas periódicas de sensores no críticas (temperatura ambiente, humedad) donde una pérdida aislada es tolerable, QoS 0 es preferible por su mínimo overhead y mayor throughput.

---

## 3. Reflexión Ética / RSU

> El uso ineficiente de protocolos de red aumenta el procesamiento en centros de datos, incrementando la huella de carbono. ¿Cómo contribuye el diseño de protocolos eficientes como MQTT a la sostenibilidad tecnológica de las regiones rurales del Perú?

**Respuesta:**

MQTT contribuye a la sostenibilidad tecnológica de las regiones rurales del Perú desde tres dimensiones interconectadas:

**a) Eficiencia energética en dispositivos de campo.**  
Los sensores IoT en zonas rurales (como estaciones meteorológicas en la sierra o boyas de monitoreo en la Amazonía) funcionan con baterías o paneles solares. El overhead mínimo de MQTT (2 bytes de cabecera) permite transmitir más datos con la misma energía, alargando la vida útil de los dispositivos y reduciendo la frecuencia de reemplazo de baterías, lo que disminuye los residuos electrónicos y el impacto logístico en zonas de difícil acceso.

**b) Reducción del ancho de banda satelital y celular.**  
Muchas comunidades rurales del Perú se conectan mediante enlaces satelitales o redes celulares 3G/4G con ancho de banda limitado y costoso por megabyte. MQTT, al minimizar el overhead, permite que proyectos de telesalud, telemedicina y monitoreo ambiental funcionen con planes de datos reducidos, democratizando el acceso a la conectividad. Por ejemplo, un centro de salud en Ayacucho que monitorea la cadena de frío de sus vacunas puede transmitir lecturas cada minuto consumiendo menos de 1 MB al mes.

**c) Menor huella de carbono en centros de datos.**  
Un broker MQTT maneja millones de mensajes con un solo hilo de CPU, mientras que un servidor HTTP REST requiere múltiples procesos y mayor capacidad de cómputo para la misma carga. Esto se traduce en menor consumo eléctrico y menor generación de calor en los centros de datos. Escalado a nivel nacional, la migración de protocolos ineficientes a MQTT puede reducir significativamente la huella de carbono de la infraestructura digital peruana.

### Conclusión

MQTT no es solo una elección técnica; es una decisión de diseño con impacto social y ambiental directo. Su eficiencia permite llevar monitoreo inteligente, telemedicina y cadenas de frío seguras a regiones rurales del Perú que de otro modo quedarían excluidas por los costos de conectividad y energía, alineándose con los Objetivos de Desarrollo Sostenible (ODS 3: Salud y Bienestar; ODS 7: Energía Asequible y No Contaminante; ODS 13: Acción por el Clima).
