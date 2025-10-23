#
# CHLC

import re
from dataclasses import dataclass, field
from typing import Optional, List

## Classes (strcutures of tables)
@dataclass
class Paciente:
    id_pc: int
    nombre: str
    ciudad: Optional[str] = field(default=None)
    cp: Optional[str] = field(default=None)

@dataclass
class AppointmentImagen:
    id_im: int
    archivo: str
    fecha: str
    texto: str

@dataclass
class CentroMedico:
    id_cm: int
    nombre: str
    direccion: Optional[str] = field(default=None)
    telefono: Optional[str] = field(default=None)
    ciudad: Optional[str] = field(default=None)
    cp: Optional[str] = field(default=None)

@dataclass
class Registro:
    id_reg: int
    id_cm: int
    fecha: str        # YYYY/MM/DD
    tipo_cita: str    # 'P', 'T', 'E'
    cita_cercana: int
    cita_normal: int
    archivo: str
    medio: Optional[str] = field(default='App')        # 'App', 'CM' o 'CT'
    hora: Optional[str] = field(default=None)       # HH:MM

@dataclass
class Cita:
    id: int
    id_reg: int
    fecha: str        # YYYY/MM/DD
    dia: str   # Dia de la semana
    proximas_citas: int # Dias
    delta_fechas: int   # Dias

@dataclass
class Main:
    id: int
    id_reg: int
    fecha: str        # YYYY/MM/DD
    dia: str
    id_cm: int
    tipo_cita: str
    proxima_cita: int
    cita_normal: int