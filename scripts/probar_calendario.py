from datetime import date
from pathlib import Path

from calendar_reader import leer_eventos

RUTA = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "calendario_test.ics"

for evento in leer_eventos(RUTA, date(2026, 9, 1), date(2026, 10, 31)):
    print(f"{evento['fecha']} {evento['inicio']}-{evento['fin'].time()} ({evento['duracion_horas']}h) {evento['nombre']}")
