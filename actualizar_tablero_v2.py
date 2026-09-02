#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
TABLERO DE SEGUROS V2 - MERCADO ASEGURADOR ARGENTINO
Script Maestro de Actualización y Compilación Multi-Trimestral (SSN Bases MDB)
===============================================================================
Procesa automáticamente las 21 bases de datos de Access (.mdb) ubicadas en
la carpeta 'Bases/' y regenera los datasets optimizados data_v2/dataset_v2.json
y data_v2/dataset_v2.js para el nuevo sitio tablero_v2.html.
"""

import os
import sys
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_V2_DIR = os.path.join(BASE_DIR, "src_v2")
DATA_V2_DIR = os.path.join(BASE_DIR, "data_v2")

sys.path.insert(0, SRC_V2_DIR)

from build_v2_data import build_all_v2_datasets

def run_update_v2():
    print("=" * 80)
    print("  INICIANDO ACTUALIZACIÓN Y COMPILACIÓN DEL TABLERO DE SEGUROS V2")
    print(f"  Fecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    start_time = time.time()
    try:
        build_all_v2_datasets()
        elapsed = time.time() - start_time
        print("=" * 80)
        print(f"  [ÉXITO] ACTUALIZACIÓN V2 COMPLETADA EN {elapsed:.1f} SEGUNDOS.")
        print("  El sitio 'tablero_v2.html' se encuentra 100% actualizado.")
        print("=" * 80)
        return True
    except Exception as e:
        print(f"  [ERROR] Falló la actualización V2: {e}")
        return False

if __name__ == "__main__":
    success = run_update_v2()
    sys.exit(0 if success else 1)
