import os
import json
from datetime import datetime
from glob import glob
import pandas as pd

from .extractors import (
    CentroMedicoExtractor, RegistroExtractor,
    CitasExtractor, ImageLoad,PacienteExtractor
)

def load_appointments(image_folder: str):
    im_load = ImageLoad()
    cm_ext = CentroMedicoExtractor()
    pac_ext = PacienteExtractor()
    #
    reg_ext = RegistroExtractor()
    cit_ext = CitasExtractor()

    imagenes, centros, pacientes, registros, todas_citas, mains = [], [], [], [], [], []

    extensiones = ('.jpg', '.jpeg', '.png')
    lista_imagenes = [f for f in glob(os.path.join(image_folder, '*')) if f.lower().endswith(extensiones)]

    for path in lista_imagenes:
        print(f"\nProcessing image: '{path}'")
        img = im_load.extract(path)
        text = img.texto

        cm = cm_ext.extract(text)
        _ = pac_ext.extract(text)

        citas = cit_ext.extract(text, img)
        reg = reg_ext.extract(text,img,cm,citas)

        imagenes.append(img)
        registros.append(reg)
        todas_citas.extend(citas)

    # Guardar DDBB
    # JSON
    with open('Appointments.json', 'w', encoding='utf-8') as f:
        json.dump({
            'ARCHIVOS': [im.__dict__ for im in imagenes],
            'CENTROMEDICO': [c.__dict__ for kk,c in cm_ext._centros.items()],
            'REGISTRO': [r.__dict__ for r in registros],
            'CITAS': [c.__dict__ for c in todas_citas]
        }, f, ensure_ascii=False, indent=2)

    # Pacientes
    with open('Pacientes.json', 'w', encoding='utf-8') as f:
        json.dump({
            'PACIENTES': [pp.__dict__ for kk,pp in pac_ext._paciente.items()],
            'INFO': {'Date':datetime.today().strftime('%Y-%m-%d')},
        }, f, ensure_ascii=False, indent=2)
    # CSV
    # REGISTRO
    df_registro = pd.DataFrame([r.__dict__ for r in registros])
    df_registro.to_csv('REGISTRO.csv', index=False, encoding='utf-8')

    # CENTROMEDICO
    df_centros = pd.DataFrame([c.__dict__ for _, c in cm_ext._centros.items()])
    df_centros.to_csv('CENTROMEDICO.csv', index=False, encoding='utf-8')

    # CITAS
    df_citas = pd.DataFrame([c.__dict__ for c in todas_citas])
    df_citas.to_csv('CITAS.csv', index=False, encoding='utf-8')


# --------------------------------------------------------------
# Main routine to load
# --------------------------------------------------------------
if __name__ == '__main__':
    import argparse
    from pathlib import Path

    def _normpath(p: str) -> Path:
        # Quita comillas accidentales y expande
        return Path(p.strip().strip('"').strip("'")).expanduser().resolve()

    parser = argparse.ArgumentParser(
        description="Read images and provides JSON and CVS"
    )
    parser.add_argument(
        "-i", "--images",
        type=str,
        help="Folder path with images."
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=".",
        help="Output folder with JSON and CSV files."
    )
    args = parser.parse_args()

    # Resolver rutas
    if args.images:
        images_dir = _normpath(args.images)
    else:
        images_dir = _normpath(input("Proveide the folder of APP's (miCita) images:\n> "))

    output_dir = _normpath(args.output)

    # Validaciones mínimas
    if not images_dir.exists() or not images_dir.is_dir():
        raise SystemExit(f"[ERROR] Path is wrong: {images_dir}")

    # Crear carpeta de salida si no existe
    output_dir.mkdir(parents=True, exist_ok=True)

    # Informativo
    print(f"[INFO] Input folder : {images_dir}")
    print(f"[INFO] Output folder:   {output_dir}")

    # Guardar outputs en la carpeta indicada
    old_cwd = os.getcwd()
    try:
        os.chdir(str(output_dir))
        load_appointments(str(images_dir))
    finally:
        os.chdir(old_cwd)