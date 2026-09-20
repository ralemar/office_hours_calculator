import warnings
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

from icalendar import Calendar

MADRID = ZoneInfo("Europe/Madrid")


def leer_eventos(ruta: str | Path, desde: date, hasta: date) -> list[dict]:
    contenido = Path(ruta).read_bytes()
    calendario = Calendar.from_ical(contenido)

    eventos = []
    for componente in calendario.walk("VEVENT"):
        inicio = componente["DTSTART"].dt.astimezone(MADRID)
        if inicio.date() < desde or inicio.date() > hasta:
            continue

        if "DTEND" in componente:
            fin = componente["DTEND"].dt.astimezone(MADRID)
        elif "DURATION" in componente:
            fin = inicio + componente["DURATION"].dt
        else:
            warnings.warn(f"El evento '{componente.get('SUMMARY', '')}' no tiene DTEND ni DURATION; se asume duracion 0")
            fin = inicio

        eventos.append(
            {
                "nombre": str(componente.get("SUMMARY", "")),
                "fecha": inicio.date(),
                "inicio": inicio.time(),
                "fin": fin,
                "duracion_horas": (fin - inicio).total_seconds() / 3600,
            }
        )

    eventos.sort(key=lambda evento: (evento["fecha"], evento["inicio"]))
    return eventos
