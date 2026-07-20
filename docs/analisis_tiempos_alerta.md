# Análisis y Validación Metrológica de Tiempos de Alerta (Pre-Aviso)
## Programa de Aseguramiento Metrológico (PAME) — Laboratorios Laproff S.A.S.

Este documento presenta el análisis técnico y logístico para justificar y validar los tiempos de pre-aviso y los umbrales de alerta del módulo complementario del PAME, en respuesta a los requerimientos de la auditoría de metrología y aseguramiento de calidad (INVIMA).

---

## 1. Planteamiento del Problema Logístico y Metrológico

En la industria farmacéutica bajo la regulación de las Buenas Prácticas de Manufactura (BPM), el estado de calibración o calificación de un equipo tiene una vigencia definida por su frecuencia. Tomemos como base el siguiente caso típico de la planta:

* **Fecha de ejecución del servicio anterior:** 25 de junio de 2025.
* **Frecuencia:** Anual.
* **Vigencia metrológica:** Junio de 2026 completo (hasta el 30 de junio de 2026).
* **Fecha límite de ejecución (Overdue / Vencido):** 1 de julio de 2026.

### El Dilema de la Ventana de Ejecución
Aunque el equipo es técnicamente válido hasta el 30 de junio de 2026, la calibración de reemplazo **debe ejecutarse y verificarse dentro del mes de junio**. Si se permite que llegue el 1 de julio sin ejecutar el servicio, el equipo entra inmediatamente en estado **Vencido**, obligando a su retiro preventivo de las líneas productivas y bloqueando cualquier lote de medicamentos procesado por dicho activo.

Por lo tanto, la ventana efectiva de programación y ejecución es del **1 de junio al 30 de junio**. Para que el servicio se lleve a cabo exitosamente dentro de esta ventana, las alertas deben dispararse de forma proactiva semanas antes de que inicie la ventana.

---

## 2. Cronograma de Gestión de un Servicio Metrológico (Logística Real)

La ejecución de una calibración o calificación externa en Laboratorios Laproff S.A.S. no es inmediata; involucra un ciclo administrativo y técnico que toma, en promedio, **30 a 45 días**:

```
[Día 0: Alerta Media/Programar] 
       │
       ▼ (7-10 días)
[Fase 1: Cotización y Aprobación] ── Solicitar ofertas a laboratorios acreditados (ISO/IEC 17025)
       │                           y emitir Orden de Compra (OC).
       ▼ (10-15 días)
[Fase 2: Agendamiento y Parada]   ── Coordinar fecha con el proveedor y planificar parada de planta
       │                           con el área de Producción para no afectar manufactura.
       ▼ (1-3 días)
[Fase 3: Preparación y Ejecución] ── Limpieza, despeje de área y ejecución de las mediciones por el técnico.
       │
       ▼ (5-10 días)
[Fase 4: Emisión y Confirmación]  ── Recepción del certificado metrológico, cálculo de error vs tolerancia (MPE),
                                   emisión de etiqueta de aptitud y actualización en el aplicativo.
```

---

## 3. Umbrales de Alerta Propuestos y su Justificación

Basándonos en el ciclo de 30-45 días de gestión metrológica, se definen los siguientes umbrales dinámicos (calculados en días restantes hasta la fecha límite de vencimiento, por ejemplo, el 30 de junio):

### A. Alerta de Prioridad Media (Programar): **45 días antes de la fecha límite**
* **Justificación:** Se dispara aproximadamente 15 días antes de que comience el mes de ejecución (ej. **15 de mayo** para vencimientos en junio). Proporciona a los metrólogos una ventana de 15 días para la fase administrativa (cotizaciones, aprobación de presupuestos y generación de la orden de compra). Cuando inicia el mes de ejecución, el contrato y el proveedor ya deben estar listos.

### B. Alerta de Prioridad Alta: **30 días antes de la fecha límite**
* **Justificación:** Se dispara al inicio del mes de ejecución (ej. **1 de junio**). Indica que el equipo ha ingresado a su mes crítico de vigencia y que el servicio debe ser agendado en el transcurso de los siguientes 15 días, coordinando la parada de planta para evitar retrasos de último momento.

### C. Alerta de Prioridad Crítica (Acción Inmediata): **15 días antes de la fecha límite**
* **Justificación:** Se dispara a mitad del mes de ejecución (ej. **15 de junio**). Representa la última oportunidad para realizar la calibración antes del vencimiento regulatorio. Si el servicio no está programado, requiere escalamiento prioritario a la jefatura de Validaciones y Metrología debido al riesgo inminente de parada de línea.

---

## 4. Adaptación del Sistema de Alertas

Para materializar esta validación, el software del PAME implementa estos umbrales ajustándolos dinámicamente según la **frecuencia de uso del equipo**, reconociendo que los equipos con frecuencias más cortas (semestrales, trimestrales o mensuales) tienen ventanas de agendamiento proporcionalmente más reducidas:

| Frecuencia del Servicio | Alerta Media (Programar) | Alerta Alta | Alerta Crítica |
| :--- | :---: | :---: | :---: |
| **Bienal / Trienal / Anual** | 45 días | 30 días | 15 días |
| **Semestral** | 30 días | 20 días | 10 días |
| **Trimestral / Mensual** | 15 días | 10. días | 5 días |

*Esta lógica adaptativa optimiza el flujo de bandejas de entrada del personal técnico, previniendo la fatiga por alertas tempranas en equipos de alta rotación, mientras otorga el tiempo logístico necesario a los activos de gran envergadura.*
