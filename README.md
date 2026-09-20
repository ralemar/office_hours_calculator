# calendar-reader

Lee los eventos de un calendario en formato ICS comprendidos entre dos fechas.

## Uso

```python
from datetime import date
from calendar_reader import leer_eventos

eventos = leer_eventos("agenda.ics", date(2026, 9, 1), date(2026, 9, 30))

for evento in eventos:
    print(evento["nombre"], evento["fecha"], evento["inicio"], evento["fin"], evento["duracion_horas"])
```

`leer_eventos(ruta, desde, hasta)` devuelve una lista de `dict` ordenada por
fecha y hora de inicio, con las claves:

| clave | tipo | descripcion |
|---|---|---|
| `nombre` | `str` | `SUMMARY` del evento |
| `fecha` | `datetime.date` | fecha de inicio |
| `inicio` | `datetime.time` | hora de inicio |
| `fin` | `datetime.datetime` | fecha y hora finales (con zona) |
| `duracion_horas` | `float` | duracion en horas |

El rango es inclusivo: de las 00:00 de `desde` a las 23:59 de `hasta`, y se
filtra por la fecha de inicio del evento. Las horas se devuelven convertidas a
`Europe/Madrid`.

## Script de prueba

Hay un calendario de prueba en `tests/fixtures/calendario_test.ics` y un script
manual para volcarlo:

```powershell
uv run python scripts/probar_calendario.py
```

## Limitaciones

- No expande eventos recurrentes (`RRULE`).
- No contempla eventos de dia completo.
- Las horas se convierten a `Europe/Madrid`; en Windows esto requiere `tzdata`
  (ya entra como dependencia de `icalendar`).
- Si un evento no tiene `DTEND` ni `DURATION`, se asume duracion 0 y se emite un
  aviso (`warnings.warn`).
