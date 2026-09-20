# PLAN: Herramienta lectora de calendarios ICS

## Objetivo

Crear una CLI que, dado un fichero `.ics` y dos fechas (`desde`, `hasta`), liste
los eventos comprendidos en ese rango y muestre para cada uno:

- Nombre del evento
- Fecha
- Hora de inicio
- Hora final
- Duración (en horas)

Estado de partida: proyecto `uv` con layout `src/`, paquete
`src/0920_calendar_reader/` y entrypoint `0920-calendar-reader` ya declarado en
`pyproject.toml`. Solo contiene un `main()` de ejemplo.

## Decisiones tecnicas

- **Libreria ICS:** `icalendar` para parsear el fichero. Maneja el plegado de
  lineas, propiedades `DTSTART`/`DTEND`/`DURATION`, zonas horarias (`TZID`) y
  fechas de dia completo. Alternativa a considerar: `recurring-ical-events`
  para expandir eventos recurrentes (`RRULE`).
- **Fechas de argumentos:** `datetime.date.fromisoformat` para aceptar
  `YYYY-MM-DD`. Sin dependencias extra de parseo.
- **CLI:** `argparse` de la libreria estandar (no anadir `click`/`typer` salvo
  que se pida).
- **Salida:** tabla legible por defecto y opcion `--csv` para exportar.

## Estructura propuesta

```
src/0920_calendar_reader/
├── __init__.py        # main() -> solo orquesta
├── cli.py             # parseo de argumentos y salida
├── events.py          # lectura del ICS y normalizacion de eventos
└── models.py          # dataclass Evento
tests/
├── test_events.py
└── fixtures/agenda.ics
```

## Modelo de datos

`models.py`

```python
@dataclass(frozen=True)
class Evento:
    nombre: str
    fecha: date
    inicio: datetime | None
    fin: datetime | None
    duracion_horas: float
```

- Eventos de dia completo (`VALUE=DATE`): `inicio`/`fin` a `None`, fecha bruta,
  duracion en dias u horas equivalentes (decidir y documentar).
- Eventos con `DURATION` en vez de `DTEND`: calcular `fin = inicio + duration`.

## Pasos de implementacion

1. **Anadir dependencia**
   - `uv add icalendar`
   - Verificar que se actualiza `pyproject.toml` y `uv.lock`.

2. **Crear `models.py`**
   - Definir la dataclass `Evento` y, si procede, un `__str__`/formato de fila.

3. **Crear `events.py`**
   - `leer_calendario(ruta: Path) -> list[Evento]`
   - Recorrer componentes `VEVENT` con `Calendar.from_ical(...)`.
   - Normalizar:
     - `DTSTART`/`DTEND` a `datetime` con zona (o `date` si dia completo).
     - Si hay fecha+hora, construir `datetime`; si la hora es 00:00 y es
       dia completo, tratar como evento de todo el dia.
     - Resolver `DURATION` cuando falta `DTEND`.
     - Si falta `DTEND`, asumir fin = inicio (duracion 0) y avisar.
   - Filtrar por rango: solape con `[desde 00:00, hasta 23:59:59]`.
   - Calcular `duracion_horas = (fin - inicio).total_seconds() / 3600`.
   - Ordenar por fecha y hora de inicio.
   - Gestionar errores: fichero inexistente, ICS invalido, sin `VEVENT`.

4. **Crear `cli.py`**
   - `argparse`:
     - posicional `ics` (ruta).
     - posicional `desde`, `hasta` (ISO `YYYY-MM-DD`).
     - opcional `--csv` (salida CSV) y `--encoding`.
   - Validar `desde <= hasta`; si no, error claro y `sys.exit(2)`.
   - Formatear la tabla con anchos alineados (sin dependencias) o `csv` stdlib
     para el modo exportacion.
   - Encabezados: `Evento | Fecha | Inicio | Fin | Duracion (h)`.

5. **Recablear `__init__.py`**
   - `main()` llama a `cli.main()` para mantener el entrypoint
     `0920-calendar-reader = "0920_calendar_reader:main"`.

6. **Tests**
   - `tests/fixtures/agenda.ics` con casos: evento normal, evento de dia
     completo, evento con `DURATION`, evento fuera de rango, `TZID` distinto.
   - `test_events.py`: filtrado, calculo de duracion, orden.
   - Probar manualmente:
     `uv run 0920-calendar-reader tests/fixtures/agenda.ics 2026-09-01 2026-09-30`

7. **Documentacion**
   - Rellenar `README.md` con uso, ejemplos y limitaciones (recurrencias no
     expandidas en v1).

8. **Verificacion final**
   - `uv run 0920-calendar-reader --help`
   - Ejecucion real contra un `.ics` de prueba.
   - Si se anaden herramientas de lint/format, registrar el comando en
     `AGENTS.md`.

## Casos limite a cubrir

- Dia completo vs. con hora.
- `DURATION` sin `DTEND`.
- Zonas horarias (`TZID`) y UTC (`Z`).
- Eventos que empiezan antes de `desde` pero terminan dentro del rango.
- Eventos recurrentes (`RRULE`): en v1 se trata solo la primera ocurrencia o se
  documenta como no soportado.
- Ficheros con multiples `VCALENDAR` o `VEVENT` sin `SUMMARY`.

## Fuera de alcance (v1)

- Expansion de recurrencias.
- Exportacion a Excel/JSON.
- Interfaz web o GUI.



## MODIFICACIONES

- Cambia el nombre del proyecto a calendar_reader
- Quiero que el código que escribas sea MÍNIMO. Es decir:
  - No hace falta que te inventes clases de datos si no es necesario, ¿no sirve un diccionario?
  - No añadas dependencias innecesarias.
  - No cubras casos límite sin decírmelo.
- icalendar es suficiente, no habrá eventos recurrentes
- no hay eventos de día completo
- No hace falta crear un CLI, crearemos otro script para hacer tests a mano. En el futuro esto sera una webapp sencilla así que olvida la CLI.
- Por el momento no hagas verificacion ni tests porque no tenemos los archivos.