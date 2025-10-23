import re
from datetime import datetime
import dateparser

tz = None  # ajustar zona si es necesario

def clean_text(text: str) -> str:
    # Quita caracteres OCR erróneos
    text = re.sub(r"[^\w\s\,\:\-]", '', text)
    # Quita líneas vacías
    lineas = text.splitlines()
    lineas_no_vacias = [linea.strip() for linea in lineas if linea.strip()]
    return '\n'.join(lineas_no_vacias)


def parse_fecha00(text: str) -> datetime:
    # Acepta formatos dd MMMM yyyy (es) o dddd, dd MMMM yyyy (en)
    formatos = ['%A, %d %B %Y', '%d %B %Y', '%A, %d %B %Y', '%A, %d %B %Y']
    for fmt in formatos:
        try:
            return datetime.strptime(text.strip(), fmt)
        except ValueError:
            continue
    raise ValueError(f'Formato fecha no reconocido: {text}')

def parse_fecha(text: str) -> datetime:
    if re.search(r'\b\d{1,2}:\d{2}\b', text):
        raise ValueError(f'Formate de fecha no reconocido: {text}')

    fecha = dateparser.parse(text, languages=['es', 'en'])
    if fecha:
        return fecha
    raise ValueError(f'Formato fecha no reconocido: {text}')

def diff_days(d1: datetime, d2: datetime) -> int:
    diff = d1 - d2
    return diff.days
