# Informe de avance parcial: Módulo metrológico (PAME)

**Proyecto de grado**  
**Autor:** Juliana Gómez  
**Fecha:** 30 de julio de 2026  
**Presentado a:** Asesor interno del proyecto de grado  

---

## 1. Resumen ejecutivo

Este informe resume las actividades desarrolladas en el módulo de aseguramiento metrológico (PAME) para Laboratorios Laproff S.A.S. En las últimas semanas, nos enfocamos en trasladar el control del cronograma de calibración a una plataforma web centralizada y funcional. Los cambios principales abarcan la optimización del rendimiento al cargar bases de datos reales y la integración del sistema de envío de correos para las alertas de vencimiento.

---

## 2. Comparación de avances respecto al estado inicial

A continuación se detallen las mejoras realizadas en el aplicativo en comparación con el punto de partida:

| Aspecto | Estado inicial | Estado actual |
| :--- | :--- | :--- |
| **Rendimiento del aplicativo** | La pantalla se congelaba por unos 3 minutos al cambiar de pestaña cuando se cargaba la base de datos completa de los equipos. | Se modificó el código para consultar los datos en un solo bloque y agruparlos en memoria. El cambio de pestaña ahora es inmediato. |
| **Envío de correos** | Las alertas no se enviaban debido a problemas de configuración y sincronización con el servidor de Brevo. | Se configuraron las credenciales correctas en el archivo de entorno y el envío de correos funciona correctamente. |
| **Alertas automáticas** | No existían avisos automáticos de vencimiento; solo se podían consultar los datos de forma manual. | Se programó una tarea que revisa diariamente el inventario y envía alertas automáticas según las reglas del laboratorio. |
| **Indicadores de control** | No se contaba con KPIs consolidados en el inicio de la pantalla. | Se incluyó una tarjeta resumen en el dashboard que muestra el porcentaje de equipos al día, equipos conformes y vencidos. |

---

## 3. Explicación de las decisiones tomadas

### Optimización del tiempo de carga en la base de datos
Al integrar los datos reales del laboratorio, notamos que el cambio de pestañas era demasiado lento. Al revisar el código, encontramos que el programa realizaba consultas individuales a la base de datos por cada equipo de forma consecutiva (problema conocido como N+1). Para solucionarlo, reescribimos el repositorio para que traiga toda la información necesaria en una sola consulta y haga el cruce de datos en la memoria del servidor. Además, añadimos un sistema de caché local que evita consultar la base de datos repetidamente a menos que se cargue un nuevo archivo de datos.

### Configuración del envío de correos por lotes
Para evitar saturar al metrólogo con correos diarios individuales por cada equipo que venza, establecimos que las alertas rutinarias (equipos que vencen el próximo mes) se agrupen y se envíen en un solo correo consolidado cuando se acumulen 5 o más equipos. Sin embargo, si un equipo está a menos de 15 días de vencerse, se considera una alerta crítica y el correo se envía de inmediato, asegurando que los casos urgentes no queden en espera.

---

## 4. Justificación del plazo de 30 días para alertas preventivas

Se decidió que las alertas preventivas se emitan con un mes (30 días) de anticipación. Esta ventana de tiempo responde a la logística y los procesos operativos necesarios en el laboratorio:

*   **Cotización con proveedores autorizados:** Muchas magnitudes requieren calibración por laboratorios externos acreditados. El proceso de solicitar cotizaciones, comparar ofertas y tramitar la orden de compra interna toma aproximadamente entre 1 y 12 días.
*   **Programación del servicio:** Es necesario coordinar con el área de producción para programar la calibración en fechas que no afecten los lotes de fabricación activos. Esta planeación toma entre 3 y 5 días adicionales.
*   **Ejecución y traslado:** El tiempo que tarda el proveedor en realizar el servicio técnico, emitir el informe de calibración y entregar el equipo calibrado toma aproximadamente una semana.
*   **Verificación del certificado de conformidad:** Una vez entregado el equipo, el metrólogo debe revisar el informe, contrastar los datos contra las tolerancias permitidas por el método y dictaminar si el equipo es apto para volver a usarse en planta.

**Conclusión:** Por estas razones, un plazo menor a un mes no daría margen suficiente para realizar las gestiones, obligando a detener la operación del equipo o a usarlo con la calibración ya vencida.

---

## 5. Estado de las pruebas y validación

El funcionamiento lógico del aplicativo se validó mediante una serie de pruebas unitarias locales (`pytest`). Estas pruebas verifican que el cálculo de los días restantes sea correcto, que las alertas se agrupen de forma adecuada por área y prioridad, y que el formato HTML de los correos no presente fallas de visualización. Actualmente, todas las pruebas del sistema pasan correctamente.

---

## 6. Siguientes pasos y temas para la reunión

Para finalizar el proyecto, se tienen programadas las siguientes tareas:

*   **Detalles de la visualización:** Ajustar las leyendas y títulos de los ejes de los gráficos en el dashboard para evitar que los textos largos de las áreas del laboratorio se vean cortados.
*   **Prueba piloto:** Iniciar una prueba de campo de 1 a 2 semanas utilizando datos diarios reales del laboratorio para verificar el flujo de correos automáticos en el entorno de trabajo.
*   **Escrito final:** Iniciar la redacción formal del documento de tesis basándonos en la estructura aprobada por el asesor.
