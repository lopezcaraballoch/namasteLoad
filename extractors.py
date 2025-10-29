#
# CHLC
import re
from typing import List, Optional
from datetime import datetime
from .classes_models import CentroMedico, Registro, Cita, Main, AppointmentImagen, Paciente
from .utils import clean_text, parse_fecha, diff_days

from PIL import Image
import pytesseract
import unicodedata
from difflib import SequenceMatcher

## Regular expressions to read all
re_line_time = re.compile(r'\b(\d{1,2}:\d{2})\b')  # format: "11:33"
re_line_patient = re.compile(
    r'^(?!.*\b(CS|CENTRO|CITA|MEDICAL)\b)[A-ZÁÉÍÓÚÜÑ\s.\-]+$',
    re.MULTILINE
)

re_line_date = re.compile(
    r'^(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo|monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
    re.IGNORECASE
) # format: starts with ...

#re_line_type_appointment = re.compile(r'^(medicina|medical|cita|appointment|phone|enfermeria|telef)',re.IGNORECASE) # format: starts with ...
re_line_type_appointment = re.compile(
    r'^(medicina|medical|cita|appointment|phone|telefono|tel[eé]f|enfermer[ií]a|nurs|infirmary)',
    re.IGNORECASE
) # format: starts with ...

re_line_medicalcenter = re.compile(
    r'^([A-ZÁÉÍÓÚÑ0-9\s.\-]+?,\s*C\.?\s*S\.?)$'
    r'|^([A-ZÁÉÍÓÚÑ0-9\s.\-]*CENTRO[A-ZÁÉÍÓÚÑ0-9\s.\-]*)$',
    re.IGNORECASE)

def _strip_accents(s: str) -> str:
    if not s:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFKD", s)
        if not unicodedata.combining(c)
    )

def _normalize_name(s: str) -> str:
    """Simplifica texto para comparación flexible."""
    s = _strip_accents(s).upper()
    s = re.sub(r"[-_,.;:]+", " ", s)
    s = re.sub(r"\bC\.?\s*S\.?\b", "CS", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _similar(a: str, b: str) -> float:
    """Similitud 0–1."""
    return SequenceMatcher(None, a, b).ratio()

map_tipo_cita = {
    'T':['phone','telef','telefono','tel '],
    'E':['enferme','infirmary','nurs']
}


class ImageLoad:
    def __init__(self):
        self._imagenes = {}
        self._next_id = 1

    def extract(self, file: str):
        img = Image.open(file)
        text = pytesseract.image_to_string(img, lang='spa+eng')
        text = clean_text(text)

        file_name = file.split('/')[-1]
        file_date0 = re.findall(r'[_-](\d{4}[01]\d[0-3]\d)[_-]', file_name)
        file_date = datetime.strptime(file_date0[0], '%Y%m%d').strftime("%Y-%m-%d")

        if file_name not in self._imagenes:
            appload = AppointmentImagen(
                id_im=self._next_id,
                archivo = file_name,
                fecha=file_date,
                texto=text,
            )
            self._imagenes[file_name] = appload
            self._next_id += 1
        return self._imagenes[file_name]

class CentroMedicoExtractor:
    def __init__(self):
        self._centros = {}
        self._next_id = 101

    def extract(self, text: str) -> CentroMedico:
        nombre = None
        for ll in text.splitlines():
            ll = ll.strip()
            match = re_line_medicalcenter.search(ll)
            if match:
                nombre_detectado = match.group(1) if match.group(1) else match.group(2)
                nombre_detectado = nombre_detectado.strip()

                #Normaliza el texto detectado
                norm_name = _normalize_name(nombre_detectado)

                #Si ya había centros previos, revisa similitud
                if hasattr(self, "_centros_previos") and self._centros_previos:
                    for prev in self._centros_previos:
                        if _similar(norm_name, _normalize_name(prev)) > 0.9:
                            nombre_detectado = prev  # usa el canónico ya visto
                            break

                #Guarda este nombre como visto
                if not hasattr(self, "_centros_previos"):
                    self._centros_previos = set()
                self._centros_previos.add(nombre_detectado)

                nombre = nombre_detectado

        if nombre not in list(self._centros.keys()):
            cm = CentroMedico(
                id_cm=self._next_id,
                nombre=nombre,
                direccion='Null', telefono='Null', ciudad='Null', cp='Null'
            )
            self._centros[nombre] = cm
            self._next_id += 1

        return self._centros[nombre]

class PacienteExtractor:
    def __init__(self):
        self._paciente = {}
        self._next_id = 1

    def extract(self, text: str) -> Paciente:
        nombre_match = re_line_patient.search(text)
        if nombre_match:
            nombre = nombre_match.group()
        else:
            nombre = 'Unavailable'

        if nombre not in list(self._paciente.keys()):
            pac = Paciente(
                id_pc=self._next_id,
                nombre=nombre
            )
            self._paciente[nombre] = pac
            self._next_id += 1
        return self._paciente[nombre]

class CitasExtractor:
    def __init__(self):
        self._next_id = 1

    def extract(self, text: str, imag = AppointmentImagen) -> List[Cita]:
        #
        fecha_reg = datetime.strptime(imag.fecha, '%Y-%m-%d')

        citas: List[Cita] = []
        for ll in text.splitlines():
            try:
                dt = parse_fecha(ll)
                #print(f"\tFecha: {dt}")
            except ValueError:
                continue
            proximas = diff_days(dt, fecha_reg)

            citas.append(
                Cita(
                    id=self._next_id,
                    id_reg=imag.id_im,
                    fecha=dt.strftime('%Y-%m-%d'),
                    dia=dt.strftime('%A'),
                    proximas_citas=proximas,
                    delta_fechas=999
                )
            )
            self._next_id += 1

        # Calcular delta_fechas: fechas consecutivas
        for i in range(len(citas)-1):
            d1 = datetime.strptime(citas[i+1].fecha, '%Y-%m-%d')
            d0 = datetime.strptime(citas[i].fecha, '%Y-%m-%d')
            citas[i].delta_fechas = diff_days(d1, d0)
            if citas[i].dia in ["Friday","Viernes"]:
                citas[i].delta_fechas -= 2
        return citas

class RegistroExtractor:
    def __init__(self):
        self.registros = {}
        self._next_id = 1

    def extract(self,text: str, img: AppointmentImagen, cm: CentroMedico, lista_citas: List[Cita]) -> Registro:
        # Hora
        hora = None
        for ll in text.splitlines():
            ll = ll.strip()
            match = re_line_time.search(ll)
            if match:
                hora = match.group(1) if match.group(1) else match.group(2)
                break
        # Tipo de Cita
        linea_match = None
        for ll in text.splitlines():
            ll = ll.strip()
            ll_norm = _strip_accents(ll).lower()
            if re_line_type_appointment.search(ll_norm):
                linea_match = ll_norm
                break
        tipo_cita = 'P'
        print(f"\tAppoimntment type: {linea_match} #")

        lm = linea_match or ""  # evita None

        for kk,list_re in map_tipo_cita.items():
            if any(lre in lm for lre in list_re):
                tipo_cita = kk

        # Próxima Cita
        cita_cercana = lista_citas[0].proximas_citas if lista_citas else 0

        # Cita estándar: dos delta_fechas consecutivos iguales a 1
        cita_normal = 0
        for i in range(len(lista_citas) - 1):
            if lista_citas[i].delta_fechas == 1 and lista_citas[i+1].delta_fechas == 1:
                cita_normal = lista_citas[i].proximas_citas
                break
        # Registro
        reg = Registro(
            id_reg=self._next_id,
            id_cm=cm.id_cm,
            fecha=img.fecha,
            hora=hora,
            tipo_cita=tipo_cita,
            archivo=img.archivo,
            cita_cercana=cita_cercana,
            cita_normal=cita_normal
        )
        self._next_id += 1
        return reg

#No utilizada
class MainExtractor:
    def extract(self, cm: CentroMedico, reg: Registro, citas: List[Cita]) -> Main:
        # Manejo de caso sin citas
        if not citas:
            dia = datetime.strptime(reg.fecha, '%Y/%m/%d').strftime('%A') if reg.fecha else 'Null'
            return Main(
                id=None,
                id_reg=reg.id_reg,
                fecha=reg.fecha,
                dia=dia,
                id_cm=cm.id_cm,
                tipo_cita=reg.tipo_cita,
                proxima_cita=None,
                cita_normal=None
            )

        # Calcular proxima cita minima
        valid_proximas = [c.proximas_citas for c in citas if c.proximas_citas is not None]
        proxima = min(valid_proximas) if valid_proximas else None

        # Buscar cita normal: dos deltas consecutivos iguales a 1
        cita_normal = proxima
        for i in range(len(citas) - 1):
            if citas[i].delta_fechas == 1 and citas[i+1].delta_fechas == 1:
                cita_normal = citas[i+1].proximas_citas
                break

        dia = datetime.strptime(reg.fecha, '%Y/%m/%d').strftime('%A')
        return Main(
            id=citas[0].id,
            id_reg=reg.id_reg,
            fecha=reg.fecha,
            dia=dia,
            id_cm=cm.id_cm,
            tipo_cita=reg.tipo_cita,
            proxima_cita=proxima,
            cita_normal=cita_normal
        )
