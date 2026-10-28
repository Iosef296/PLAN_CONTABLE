# Contexto del proyecto — Buscador PCGE 2026

## Qué es

App web (y versión .exe de escritorio) para buscar cuentas del **Plan Contable General
Empresarial del Perú, edición 2026**, por código o por descripción, con tolerancia a
errores de tipeo y sinónimos de jerga contable común.

## Origen de los datos

- Fuente: PDF oficial `8559200-plan-contable-general-empresarial-pcge-2026.pdf`
  (subido por el usuario), 203 páginas.
- Se extrajo el texto de las páginas 19 a 52 (sección "CATÁLOGO DE CUENTAS") con
  `pdfplumber`.
- El texto se parseó con un script (`parse.py`, usado una sola vez, no forma parte de
  la app) para separar código + descripción de cada cuenta, resolviendo:
  - Números de página sueltos (descartados).
  - Descripciones que el PDF partió en 2-3 líneas por el salto de columna/página
    (reconstruidas).
  - 1 error real de lectura del PDF (código `70992` debía ser `70902`, corregido a
    mano comparando con el patrón Terceros/Relacionadas del resto del catálogo).
- Resultado: `pcge_data.json`, **1616 cuentas** (niveles 2 a 5 dígitos), cada una con
  `codigo`, `descripcion`, `nivel`, `elemento` (1-9) y `elemento_nombre`.
- Validado: sin códigos duplicados, todo código tiene su padre inmediato en el catálogo.

## Arquitectura de la app

- **Backend**: Flask (`app.py`), single-file, sin base de datos real — el catálogo
  (1616 filas) se carga completo en memoria al arrancar desde `pcge_data.json`. No hace
  falta Postgres/SQLite persistente: es un catálogo de solo lectura que no cambia entre
  despliegues.
- **Frontend**: una sola plantilla (`templates/index.html`), sin frameworks JS, con
  `fetch` a `/buscar` y debounce de 200ms para filtrar en vivo mientras se escribe
  (sin recargar la página).
- **Búsqueda** (`buscar_cuentas` en `app.py`), en este orden:
  1. **Sinónimos**: si el texto escrito coincide con una entrada del diccionario
     `SINONIMOS` (p. ej. `luz` → `energia electrica`, `afp` → `administradoras de
     fondos de pensiones`, `planilla` → `remuneraciones`), se busca también por el
     término técnico mapeado.
  2. **Coincidencia exacta** (substring, sin distinguir mayúsculas/acentos) sobre
     código o descripción. Si hay resultados exactos, se muestran *solo* esos (no se
     mezcla con resultados aproximados).
  3. **Búsqueda difusa** (fuzzy, con `rapidfuzz.fuzz.partial_ratio`, umbral 65) — entra
     únicamente cuando no hubo ningún resultado exacto, para tolerar errores de tipeo
     (ej. "vnetas" encuentra "VENTAS").
  - Filtro adicional por elemento (1-9) combinable con el texto.
- **Versión de escritorio** (`desktop.py`): levanta el mismo Flask en un hilo y abre el
  navegador en `http://127.0.0.1:5000`. Se empaqueta a `.exe` con PyInstaller:
  ```
  pyinstaller --onefile --add-data "pcge_data.json;." --add-data "templates;templates" desktop.py
  ```

## Archivos del repo

| Archivo | Rol |
|---|---|
| `app.py` | App Flask (web + lógica de búsqueda) |
| `templates/index.html` | UI (formulario + tabla + JS de búsqueda en vivo) |
| `pcge_data.json` | Catálogo completo (1616 cuentas) |
| `desktop.py` | Entry point para la versión `.exe` |
| `requirements.txt` | `flask`, `gunicorn`, `rapidfuzz` |
| `Procfile` | `web: gunicorn app:app` (para Railway) |
| `.gitignore` | Excluye `__pycache__`, `venv`, `build/`, `dist/`, `*.spec` |

## Dónde quedó cada cosa

- **Repo**: https://github.com/Iosef296/PLAN_CONTABLE (push hecho a `main`, sin
  atribución de Claude en los commits).
- **Railway**: proyecto `carefree-tenderness`, servicio `web`, conectado al repo de
  GitHub (auto-deploy). Dominio generado: `web-production-61580.up.railway.app`.
  - Al momento de desplegar, Railway tenía un **incidente activo de plataforma**
    ("Deployments stuck in initializing", identificado 28-oct 17:49 UTC, ver
    status.railway.com) que dejó el primer deploy en estado "Queued" sin avanzar.
    No es un problema del código ni de la configuración del proyecto — hay que
    reintentar/esperar a que Railway lo resuelva.

## Cómo correr local

```
pip install -r requirements.txt
python app.py
```
Abre `http://localhost:5000`.

## Pendiente / posibles mejoras futuras

- Confirmar que el deploy en Railway termine de arrancar una vez pase el incidente.
- Ampliar el diccionario `SINONIMOS` con más jerga según lo que el usuario necesite
  buscar seguido.
- Empaquetar y probar el `.exe` con PyInstaller.
