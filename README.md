# WorkJourney AI

Sistema completo de productividad personal construido con **Python + Streamlit**,
usando **Google Sheets** como base de datos (sin SQL).

## Arquitectura

```
app.py                  # Punto de entrada (login, routing, layout)
components/              # UI reutilizable (sidebar, cards, charts, timeline, command palette, quick add...)
pages/                   # Una página por módulo (prefijo "_" para que Streamlit no las trate como multipage)
services/                # Lógica de negocio por módulo (Journey, Activities, Time, Finance, Goals, Clients, Projects, Insights...)
database/                # Cliente de gspread + repositorio genérico de CRUD
utils/                   # Formateo, validaciones y helpers genéricos
helpers/                 # Logging y cache
config/                  # Configuración central, paleta de colores, esquemas de hojas
assets/                  # style.css con el tema visual SaaS
.streamlit/config.toml   # Tema nativo de Streamlit
```

## 1. Instalación

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## 2. Configuración de Google Sheets (base de datos)

### 2.1 Crear el proyecto en Google Cloud

1. Ve a [Google Cloud Console](https://console.cloud.google.com/) y crea un proyecto nuevo.
2. Habilita las APIs **Google Sheets API** y **Google Drive API**.
3. Ve a **APIs & Services → Credentials → Create Credentials → Service Account**.
4. Crea la cuenta de servicio (no necesita roles de proyecto adicionales).
5. Entra a la cuenta de servicio creada → pestaña **Keys** → **Add Key → Create new key → JSON**.
6. Se descargará un archivo `.json`. Renómbralo (o no) y colócalo en:
   `config/service_account.json`
   (o la ruta que definas en `GOOGLE_SERVICE_ACCOUNT_FILE`).

### 2.2 Crear el spreadsheet

1. Crea una Google Sheet en blanco (puede llamarse "WorkJourney AI DB").
2. Copia el ID desde la URL:
   `https://docs.google.com/spreadsheets/d/ESTE_ES_EL_ID/edit`
3. Comparte la hoja con el **email de la cuenta de servicio** (lo encuentras
   dentro del archivo `.json`, campo `client_email`) con permisos de **Editor**.

La app crea automáticamente todas las hojas necesarias (Journey, Activities,
Time, Finance, Clients, Projects, Goals, Tags, Notifications, Settings, Users)
la primera vez que se conecta.

### 2.3 Variables de entorno

Copia `.env.example` como `.env` y completa:

```
GOOGLE_SHEET_ID=tu_id_de_spreadsheet
GOOGLE_SERVICE_ACCOUNT_FILE=config/service_account.json
AUTH_COOKIE_KEY=una_clave_secreta_larga_y_unica
```

## 3. Ejecutar la aplicación

```bash
streamlit run app.py
```

La primera vez que abras la app, como no hay usuarios registrados, se te
pedirá crear la cuenta de administrador (multiusuario vía la hoja `Users`,
contraseñas con hash mediante `streamlit-authenticator`).

## 4. Funcionalidades incluidas

- **CRUD completo** (crear/editar/eliminar/duplicar) en Journey, Actividades,
  Tiempo, Finanzas, Objetivos, Clientes y Proyectos — persistido en Google Sheets.
- **Dashboard** con KPIs, sparklines, heatmap de productividad, distribución de
  tiempo y panel lateral "Hoy" con progreso circular.
- **Journey**: diario profesional con timeline estilo Notion.
- **Actividades**: data entry + tabla filtrable/exportable + vista Kanban.
- **Tiempo**: temporizador start/pausa/reanudar/detener, registro manual,
  vista de calendario mensual, vista semanal y por lista.
- **Finanzas**: ingresos/gastos, forecast, comparativa mensual, meta mensual.
- **Objetivos**: progreso visual, proyección de cumplimiento.
- **Clientes / Proyectos**: rentabilidad, ROI, tiempo invertido.
- **Insights AI**: 100% generados con Python/Pandas (sin llamadas a APIs externas).
- **Analítica**: filtros de rango de fechas, comparativas y métricas avanzadas
  (valor/hora, horas facturables vs no facturables, racha de productividad,
  cumplimiento de objetivos).
- **Command Palette (Ctrl+K)**: búsqueda global y navegación rápida.
- **Quick Add (+)**: registrar actividad / iniciar timer / registrar ingreso en un clic.
- **Centro de notificaciones**: recordatorios de objetivos y seguimiento de clientes.
- **Exportación** a CSV, Excel y PDF; **importación** desde Excel/CSV.

## 5. Notas y limitaciones conocidas

- **Calendario**: se implementó como una vista de calendario mensual con
  intensidad de color por horas trabajadas (similar a un heatmap). Streamlit no
  soporta de forma nativa el *drag & drop* real de eventos sin un componente
  JavaScript personalizado fuera del stack solicitado; la reprogramación de
  registros se hace editando la fecha/hora desde el formulario correspondiente.
- **Ctrl+K**: el atajo de teclado se implementa inyectando JavaScript que
  enfoca el campo de búsqueda superior. Si tu navegador bloquea scripts en
  iframes de terceros, usa el campo de búsqueda directamente con el mouse.
- **Cache**: las lecturas de Google Sheets se cachean 20-30 segundos para no
  exceder las cuotas de la API; usa "Limpiar caché" en Configuración si
  necesitas forzar una relectura inmediata.
- **Dark mode**: la preferencia se guarda en el perfil del usuario; el tema
  visual activo se controla desde `.streamlit/config.toml`.

## 6. Estructura de datos (hojas)

Cada módulo tiene su propia hoja con columnas fijas definidas en
`config/settings.py → SCHEMAS`. Si necesitas agregar un campo nuevo, agrégalo
ahí y la app lo tomará en cuenta automáticamente en el CRUD genérico
(`database/repository.py`).
