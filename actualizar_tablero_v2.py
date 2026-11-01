#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
TABLERO DE SEGUROS V2 - MERCADO ASEGURADOR ARGENTINO
Monitor Automático SINENSUP (SSN), Descargador de Bases MDB, Compilador y Deploy
===============================================================================
1. Consulta en vivo el portal oficial SINENSUP (https://sinensup.ssn.gob.ar/Sinensup/).
2. Verifica el calendario regulatorio SSN (RGAA Punto 39.8.1 - 45 días post-cierre):
   - YYYY-3 (30-09-YYYY • 3M Ej. YYYY/YYYY+1) -> Vence 15-Nov (Publicación ~18-Nov a 15-Dic)
   - YYYY-4 (31-12-YYYY • 6M Ej. YYYY/YYYY+1) -> Vence 15-Feb (Publicación ~18-Feb a 15-Mar)
   - YYYY-1 (31-03-YYYY • 9M Ej. YYYY-1/YYYY) -> Vence 15-May (Publicación ~18-May a 10-Jun)
   - YYYY-2 (30-06-YYYY • 12M Ej. YYYY-1/YYYY) -> Vence 15-Ago (Publicación ~20-Ago a 15-Sep)
3. Si detecta un nuevo período en SINENSUP que no esté en 'Bases/', descarga el ZIP,
   extrae el archivo .mdb en 'Bases/', recompila los datasets con Emisión Directa Neta
   y publica automáticamente en GitHub Pages.

Uso:
  python actualizar_tablero_v2.py                 # Modo inteligente: busca nuevos períodos en SSN, descarga, compila y despliega
  python actualizar_tablero_v2.py --check         # Solo verifica períodos disponibles en SINENSUP vs locales
  python actualizar_tablero_v2.py --force         # Fuerza recompilación de todas las bases locales y despliegue a GitHub
  python actualizar_tablero_v2.py --period 2026-3 # Fuerza descarga de un período específico desde SINENSUP
  python actualizar_tablero_v2.py --deploy-only   # Solo sube los archivos actuales a GitHub Pages
"""

import os
import sys
import glob
import time
import base64
import shutil
import zipfile
import argparse
import datetime
import subprocess
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASES_DIR = os.path.join(BASE_DIR, "Bases")
SRC_V2_DIR = os.path.join(BASE_DIR, "src_v2")
DATA_V2_DIR = os.path.join(BASE_DIR, "data_v2")
TOKEN_FILE = os.path.join(BASE_DIR, "GitHub token.txt")
REPO_NAME = "tablero-seguros-v2"

PORTAL_URL = "https://sinensup.ssn.gob.ar/Sinensup/menu.faces?idSession=reportes"
FRAME_CENTRAL_URL = "https://sinensup.ssn.gob.ar/Sinensup/sinesup_frame_central.html"
MENU2_URL = "https://sinensup.ssn.gob.ar/Sinensup/menu2.faces"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

FILES_TO_DEPLOY = [
    ("tablero_v2.html", "index.html"),
    ("tablero_v2.html", "tablero_v2.html"),
    (".nojekyll", ".nojekyll"),
    (".gitignore", ".gitignore"),
    ("README.md", "README.md"),
    ("actualizar_tablero_v2.py", "actualizar_tablero_v2.py"),
    ("src_v2/db_engine_v2.py", "src_v2/db_engine_v2.py"),
    ("src_v2/insurance_kpis_v2.py", "src_v2/insurance_kpis_v2.py"),
    ("src_v2/build_v2_data.py", "src_v2/build_v2_data.py"),
    ("data_v2/dataset_v2.js", "data_v2/dataset_v2.js"),
    ("data_v2/dataset_v2.json", "data_v2/dataset_v2.json"),
    ("favicon.svg", "favicon.svg"),
    ("favicon-32x32.png", "favicon-32x32.png"),
    ("favicon-192x192.png", "favicon-192x192.png")
]

sys.path.insert(0, SRC_V2_DIR)
from build_v2_data import build_all_v2_datasets


def notify_windows(title, message, is_error=False):
    """Muestra una notificación nativa en Windows."""
    try:
        ps_script = f"""
        [reflection.assembly]::loadwithpartialname('System.Windows.Forms') | Out-Null
        $notify = New-Object System.Windows.Forms.NotifyIcon
        $notify.Icon = [System.Drawing.SystemIcons]::Information
        $notify.BalloonTipTitle = "{title}"
        $notify.BalloonTipText = "{message}"
        $notify.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::{"Error" if is_error else "Info"}
        $notify.Visible = $True
        $notify.ShowBalloonTip(10000)
        Start-Sleep -Seconds 1
        $notify.Dispose()
        """
        subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)
    except Exception:
        pass


def get_local_periods():
    """Devuelve la lista ordenada de períodos (.mdb) disponibles en Bases/."""
    os.makedirs(BASES_DIR, exist_ok=True)
    mdb_files = glob.glob(os.path.join(BASES_DIR, "*.mdb"))
    periods = []
    for f in mdb_files:
        base = os.path.basename(f).replace(".mdb", "").strip()
        if "-" in base:
            periods.append(base)
    return sorted(periods)


def get_ssn_calendar_status():
    """
    Evalúa el calendario regulatorio exacto de la SSN (RGAA Punto 39.8.1):
    - Cierre 30-09 (Período YYYY-3): Vence 15-Nov -> Ventana de sondeo: 10-Nov a 31-Dic
    - Cierre 31-12 (Período YYYY-4): Vence 15-Feb -> Ventana de sondeo: 10-Feb a 31-Mar
    - Cierre 31-03 (Período YYYY-1): Vence 15-May -> Ventana de sondeo: 10-May a 30-Jun
    - Cierre 30-06 (Período YYYY-2): Vence 15-Ago -> Ventana de sondeo: 10-Ago a 30-Sep
    """
    today = datetime.date.today()
    yr = today.year

    windows = [
        (
            datetime.date(yr, 2, 10),
            datetime.date(yr, 3, 31),
            datetime.date(yr - 1, 12, 31),
            f"{yr - 1}-4",
            f"2º Trimestre Ej. {yr-1}/{yr} (31-12-{yr-1} • 6 Meses)"
        ),
        (
            datetime.date(yr, 5, 10),
            datetime.date(yr, 6, 30),
            datetime.date(yr, 3, 31),
            f"{yr}-1",
            f"3º Trimestre Ej. {yr-1}/{yr} (31-03-{yr} • 9 Meses)"
        ),
        (
            datetime.date(yr, 8, 10),
            datetime.date(yr, 9, 30),
            datetime.date(yr, 6, 30),
            f"{yr}-2",
            f"4º Trimestre Cierre Anual Ej. {yr-1}/{yr} (30-06-{yr} • 12 Meses)"
        ),
        (
            datetime.date(yr, 11, 10),
            datetime.date(yr, 12, 31),
            datetime.date(yr, 9, 30),
            f"{yr}-3",
            f"1º Trimestre Ej. {yr}/{yr+1} (30-09-{yr} • 3 Meses)"
        ),
    ]

    for start_d, end_d, close_d, p_code, desc in windows:
        if start_d <= today <= end_d:
            days_since_close = (today - close_d).days
            return {
                "in_window": True,
                "expected_period": p_code,
                "description": desc,
                "days_since_close": days_since_close,
                "deadline_passed": days_since_close > 45
            }

    # Si estamos antes del día 40 post-cierre (ej. 1 de Noviembre -> 32 días desde el 30-09)
    if datetime.date(yr, 10, 1) <= today < datetime.date(yr, 11, 10):
        days_since = (today - datetime.date(yr, 9, 30)).days
        return {
            "in_window": False,
            "expected_period": f"{yr}-3",
            "description": f"En plazo legal de presentación para {yr}-3 (30-09-{yr}): día {days_since}/45 (Vence 15-Nov; publicación SSN estimada 18-Nov a 05-Dic)",
            "days_since_close": days_since,
            "deadline_passed": False
        }

    return {
        "in_window": False,
        "expected_period": None,
        "description": "Al día según calendario regulatorio SSN (45 días post-cierre)",
        "days_since_close": 0,
        "deadline_passed": False
    }


def connect_ssn_portal():
    """Conecta al portal SINENSUP de la SSN y obtiene los períodos disponibles para descarga."""
    s = requests.Session()
    s.headers.update(HEADERS)

    s.get(PORTAL_URL, verify=False, timeout=20)
    s.get(FRAME_CENTRAL_URL, verify=False, timeout=20)
    r_menu2 = s.get(MENU2_URL, verify=False, timeout=20)

    soup = BeautifulSoup(r_menu2.text, 'html.parser')
    view_state_el = soup.find('input', {'name': 'javax.faces.ViewState'})
    if not view_state_el:
        raise RuntimeError("No se pudo obtener el ViewState en el portal SINENSUP.")

    view_state = view_state_el['value']

    post_data = {
        'j_id6': 'j_id6',
        'j_id6_SUBMIT': '1',
        'javax.faces.ViewState': view_state,
        'jscook_action': 'j_id6_j_id19_menu:A]archivozipbalances'
    }
    r_zip_page = s.post(MENU2_URL, data=post_data, verify=False, timeout=20)
    soup2 = BeautifulSoup(r_zip_page.text, 'html.parser')

    form_dl = soup2.find('form', {'id': 'j_id33'}) or soup2.find_all('form')[-1]
    action = form_dl.get('action') or '/Sinensup/facelets/archivoZipBalances.faces'
    view_state_dl = soup2.find('input', {'name': 'javax.faces.ViewState'})['value']
    select_el = soup2.find('select')
    select_name = select_el.get('name') if select_el else 'j_id33:periodo'

    available_periods = [opt.get('value').strip() for opt in soup2.find_all('option') if opt.get('value')]

    return {
        "session": s,
        "action_url": f"https://sinensup.ssn.gob.ar{action}",
        "form_id": form_dl.get('id', 'j_id33'),
        "view_state": view_state_dl,
        "select_name": select_name,
        "available_periods": available_periods
    }


def download_and_extract_period_to_bases(portal_info, target_period):
    """Descarga el ZIP del período desde SINENSUP y extrae el archivo .mdb en Bases/{target_period}.mdb."""
    s = portal_info['session']
    action_url = portal_info['action_url']
    form_id = portal_info['form_id']
    view_state = portal_info['view_state']
    select_name = portal_info['select_name']

    print(f"[SINENSUP] Descargando paquete oficial '{target_period}.zip' desde la SSN...")
    dl_data = {
        form_id: form_id,
        f"{form_id}_SUBMIT": "1",
        'javax.faces.ViewState': view_state,
        select_name: target_period,
        f'{form_id}:j_id39': 'Descargar'
    }

    r_file = s.post(action_url, data=dl_data, verify=False, stream=True, timeout=90)
    if r_file.status_code != 200:
        raise RuntimeError(f"Error HTTP {r_file.status_code} al descargar {target_period}.zip.")

    os.makedirs(BASES_DIR, exist_ok=True)
    zip_filename = os.path.join(BASES_DIR, f"{target_period}.zip")
    with open(zip_filename, 'wb') as f:
        for chunk in r_file.iter_content(chunk_size=65536):
            if chunk:
                f.write(chunk)

    file_size = os.path.getsize(zip_filename)
    print(f"[SINENSUP] ZIP descargado ({file_size:,} bytes). Descomprimiendo en Bases/...")

    if file_size < 10000:
        os.remove(zip_filename)
        raise RuntimeError("El archivo descargado no es un ZIP válido.")

    extracted_mdb = None
    with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
        for member in zip_ref.namelist():
            if member.lower().endswith('.mdb'):
                target_mdb_path = os.path.join(BASES_DIR, f"{target_period}.mdb")
                with zip_ref.open(member) as source, open(target_mdb_path, "wb") as target_f:
                    shutil.copyfileobj(source, target_f)
                extracted_mdb = target_mdb_path
                print(f"[SINENSUP] Base Access extraída: {extracted_mdb} ({os.path.getsize(extracted_mdb):,} bytes)")
                break

    try:
        os.remove(zip_filename)
    except Exception:
        pass

    # Invalidar caché parquet previo si existía para ese período
    parquet_cache = os.path.join(BASE_DIR, ".cache", "v2_parquet", f"{target_period}.parquet")
    if os.path.exists(parquet_cache):
        try:
            os.remove(parquet_cache)
        except Exception:
            pass

    return extracted_mdb


def deploy_to_github_pages(commit_msg=None, force_upload_datasets=True):
    """Sube los archivos actualizados a GitHub Pages reutilizando blobs inalterados."""
    if not os.path.exists(TOKEN_FILE):
        print("[GitHub] No se encontró 'GitHub token.txt', omitiendo despliegue remoto.")
        return False

    with open(TOKEN_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.read().splitlines() if l.strip().startswith(("ghp_", "github_pat_"))]
        token = lines[0] if lines else None

    if not token:
        print("[GitHub] Token inválido o vacío en 'GitHub token.txt'.")
        return False

    # Sincronizar index.html con tablero_v2.html
    shutil.copyfile(os.path.join(BASE_DIR, "tablero_v2.html"), os.path.join(BASE_DIR, "index.html"))

    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504, 429])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    user_resp = session.get("https://api.github.com/user", headers=headers, timeout=30)
    user_login = user_resp.json()["login"]
    repo_full = f"{user_login}/{REPO_NAME}"

    ref_resp = session.get(f"https://api.github.com/repos/{repo_full}/git/ref/heads/main", headers=headers, timeout=30)
    latest_commit_sha = ref_resp.json()["object"]["sha"]
    print(f"[GitHub] Rama base 'main' (Commit: {latest_commit_sha[:7]})")

    commit_resp = session.get(f"https://api.github.com/repos/{repo_full}/git/commits/{latest_commit_sha}", headers=headers, timeout=30)
    base_tree_sha = commit_resp.json()["tree"]["sha"]

    tree_resp = session.get(f"https://api.github.com/repos/{repo_full}/git/trees/{base_tree_sha}?recursive=1", headers=headers, timeout=30)
    existing_tree_map = {item["path"]: item["sha"] for item in tree_resp.json().get("tree", [])}

    always_upload = {"index.html", "tablero_v2.html", "actualizar_tablero_v2.py", "src_v2/build_v2_data.py", "src_v2/insurance_kpis_v2.py"}
    if force_upload_datasets:
        always_upload.update({"data_v2/dataset_v2.js", "data_v2/dataset_v2.json"})

    def create_blob(file_path):
        with open(file_path, "rb") as bf:
            encoded = base64.b64encode(bf.read()).decode("ascii")
        url = f"https://api.github.com/repos/{repo_full}/git/blobs"
        for attempt in range(1, 6):
            try:
                resp = session.post(url, headers=headers, json={"content": encoded, "encoding": "base64"}, timeout=180)
                if resp.status_code in (200, 201):
                    return resp.json()["sha"]
            except Exception as e:
                print(f"    Reintento {attempt} subiendo blob ({e})...")
            time.sleep(2 * attempt)
        raise RuntimeError(f"No se pudo subir blob para {file_path}")

    tree_items = []
    for local_rel, repo_rel in FILES_TO_DEPLOY:
        full_src = os.path.join(BASE_DIR, local_rel)
        if not os.path.exists(full_src):
            continue

        if repo_rel in always_upload or repo_rel not in existing_tree_map:
            print(f"  -> Subiendo {repo_rel} ({os.path.getsize(full_src):,} bytes)...")
            sha = create_blob(full_src)
        else:
            sha = existing_tree_map[repo_rel]
            print(f"  -> Reutilizando {repo_rel} (SHA: {sha[:7]})")

        tree_items.append({
            "path": repo_rel,
            "mode": "100644",
            "type": "blob",
            "sha": sha
        })

    tree_create_resp = session.post(f"https://api.github.com/repos/{repo_full}/git/trees", headers=headers, json={"tree": tree_items}, timeout=60)
    new_tree_sha = tree_create_resp.json()["sha"]

    msg = commit_msg or f"Actualización automática Tablero de Seguros V2 ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M')})"
    new_commit_resp = session.post(
        f"https://api.github.com/repos/{repo_full}/git/commits",
        headers=headers,
        json={"message": msg, "tree": new_tree_sha, "parents": [latest_commit_sha]},
        timeout=60
    )
    new_commit_sha = new_commit_resp.json()["sha"]

    patch_resp = session.patch(
        f"https://api.github.com/repos/{repo_full}/git/refs/heads/main",
        headers=headers,
        json={"sha": new_commit_sha},
        timeout=60
    )
    if patch_resp.status_code == 200:
        print("\n===========================================================================")
        print(f"  [OK] DESPLIEGUE EXITOSO EN GITHUB PAGES (Commit: {new_commit_sha[:7]})")
        print(f"  URL Pública: https://{user_login.lower()}.github.io/{REPO_NAME}/")
        print("===========================================================================\n")
        return True
    else:
        print(f"[Error GitHub] {patch_resp.text}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Monitor SINENSUP, Compilador y Desplegador del Tablero de Seguros V2")
    parser.add_argument("--check", action="store_true", help="Solo consultar SINENSUP y comparar con las bases locales")
    parser.add_argument("--force", action="store_true", help="Forzar recompilación de todas las bases locales y despliegue")
    parser.add_argument("--period", type=str, help="Forzar descarga de un período específico desde SINENSUP (ej: 2026-3)")
    parser.add_argument("--deploy-only", action="store_true", help="Solo desplegar los archivos actuales a GitHub Pages")
    args = parser.parse_args()

    local_periods = get_local_periods()
    latest_local = local_periods[-1] if local_periods else "Ninguno"
    cal_status = get_ssn_calendar_status()

    print("=" * 80)
    print("  TABLERO DE SEGUROS V2 - MONITOR AUTOMÁTICO SINENSUP (SSN)")
    print(f"  Fecha de ejecución      : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Bases locales en Bases/ : {len(local_periods)} ({local_periods[0] if local_periods else '-'} a {latest_local})")
    print(f"  Estado Calendario SSN   : {cal_status['description']}")
    print("=" * 80)

    if args.deploy_only:
        deploy_to_github_pages(commit_msg="Update Tablero de Seguros V2", force_upload_datasets=False)
        return

    new_periods_downloaded = []
    try:
        portal_info = connect_ssn_portal()
        remote_periods = portal_info["available_periods"]
        latest_remote = remote_periods[0] if remote_periods else None
        print(f"[SINENSUP Web] Períodos publicados en SSN: {', '.join(remote_periods[:8])}...")
        print(f"[SINENSUP Web] Último período disponible en SSN: {latest_remote} | Último local: {latest_local}")

        if args.check:
            missing = [p for p in remote_periods if p >= "2021-2" and p not in local_periods]
            if missing:
                print(f"\n[NOVEDAD] Períodos disponibles en SSN pendientes de descarga: {missing}")
            else:
                print("\n[AL DÍA] La carpeta 'Bases/' contiene todos los períodos publicados por la SSN.")
            return

        if args.period:
            print(f"\n>> Descargando período solicitado manualmente: {args.period}...")
            download_and_extract_period_to_bases(portal_info, args.period)
            new_periods_downloaded.append(args.period)
        else:
            # Detectar cualquier período publicado en SINENSUP posterior o faltante desde 2021-2
            missing = [p for p in remote_periods if p >= "2021-2" and p not in local_periods]
            if missing:
                for p_new in sorted(missing):
                    print(f"\n[¡NUEVO BALANCE SSN DETECTADO!] Descargando período '{p_new}'...")
                    download_and_extract_period_to_bases(portal_info, p_new)
                    new_periods_downloaded.append(p_new)
            else:
                print("\n[SINENSUP] No hay nuevos períodos publicados en la SSN respecto a las bases locales.")

    except Exception as e:
        print(f"\n[Aviso SINENSUP] No se pudo consultar el portal en vivo ({e}).")
        if args.check:
            return

    if new_periods_downloaded or args.force:
        start_time = time.time()
        print("\n>> Ejecutando compilación multi-trimestral con Emisión Directa Neta...")
        build_all_v2_datasets()
        elapsed = time.time() - start_time
        print(f"[OK] Compilación finalizada en {elapsed:.1f}s.")

        commit_title = (
            f"Incorporación automática balance SSN {', '.join(new_periods_downloaded)}"
            if new_periods_downloaded
            else "Recompilación completa Tablero de Seguros V2"
        )
        deploy_to_github_pages(commit_msg=commit_title, force_upload_datasets=True)

        if new_periods_downloaded:
            notify_windows(
                "Tablero de Seguros V2 Actualizado",
                f"Se descargó y publicó el nuevo período SSN: {', '.join(new_periods_downloaded)}",
                is_error=False
            )
    else:
        print("\n[FIN] El tablero ya se encuentra actualizado con el último período de la SSN. (Usa --force si deseas recompilar).")


if __name__ == "__main__":
    main()
