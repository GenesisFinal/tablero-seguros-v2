import os
import glob
import pyodbc
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASES_DIR = os.path.join(BASE_DIR, "Bases")
CACHE_DIR = os.path.join(BASE_DIR, ".cache", "v2_parquet")

def get_connection_string(mdb_path):
    drivers = [d for d in pyodbc.drivers() if 'Access' in d or 'ACE' in d]
    if 'Microsoft Access Driver (*.mdb, *.accdb)' in drivers:
        return f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={mdb_path};"
    elif 'Microsoft Access Driver (*.mdb)' in drivers:
        return f"DRIVER={{Microsoft Access Driver (*.mdb)}};DBQ={mdb_path};"
    return f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={mdb_path};"

def get_all_periods():
    mdb_files = sorted(glob.glob(os.path.join(BASES_DIR, "*.mdb")))
    periods = []
    for f in mdb_files:
        p = os.path.basename(f).replace(".mdb", "").strip()
        periods.append(p)
    return sorted(periods)

def load_period_data(period, force_reload=False):
    os.makedirs(CACHE_DIR, exist_ok=True)
    parquet_path = os.path.join(CACHE_DIR, f"{period}.parquet")
    
    if not force_reload and os.path.exists(parquet_path):
        try:
            return pd.read_parquet(parquet_path)
        except Exception as e:
            print(f"Error reading cache {parquet_path}: {e}")

    mdb_path = os.path.join(BASES_DIR, f"{period}.mdb")
    if not os.path.exists(mdb_path):
        raise FileNotFoundError(f"Database not found: {mdb_path}")

    conn_str = get_connection_string(mdb_path)
    conn = pyodbc.connect(conn_str)
    query = "SELECT cod_cia, razon_social, periodo, cod_subramo, desc_subramo, importe, cod_cuenta, desc_cuenta, nivel, id_padre FROM Balance"
    df = pd.read_sql(query, conn)
    conn.close()

    # Standardize types and strings
    df['cod_cia'] = df['cod_cia'].astype(str).str.strip().str.zfill(4)
    df['razon_social'] = df['razon_social'].astype(str).str.strip()
    df['periodo'] = str(period)
    df['cod_cuenta'] = df['cod_cuenta'].astype(str).str.strip()
    df['desc_cuenta'] = df['desc_cuenta'].astype(str).str.strip()
    df['cod_subramo'] = df['cod_subramo'].fillna('').astype(str).str.strip()
    df['desc_subramo'] = df['desc_subramo'].fillna('').astype(str).str.strip()
    df['importe'] = pd.to_numeric(df['importe'], errors='coerce').fillna(0.0)
    df['nivel'] = pd.to_numeric(df['nivel'], errors='coerce').fillna(0).astype(int)

    # Entity classification
    cias = df[['cod_cia', 'razon_social']].drop_duplicates()
    seg_map = {}

    for _, row in cias.iterrows():
        c = row['cod_cia']
        name = row['razon_social']
        sub = df[df['cod_cia'] == c]
        
        sub_ramos = sub[(sub['desc_subramo'] != '') & (sub['desc_subramo'].notna()) & (sub['cod_cuenta'].str.startswith('5.01'))]
        
        patrim = sub_ramos[sub_ramos['cod_subramo'].str.startswith('1.') & (~sub_ramos['cod_subramo'].str.startswith('1.050'))]['importe'].sum()
        art = sub_ramos[sub_ramos['cod_subramo'].str.startswith('1.050')]['importe'].sum()
        personas = sub_ramos[sub_ramos['cod_subramo'].str.startswith(('2.01', '2.02', '2.03', '2.05'))]['importe'].sum()
        retiro = sub_ramos[sub_ramos['cod_subramo'].str.startswith(('2.06', '2.07'))]['importe'].sum()
        
        tot_primas = patrim + art + personas + retiro
        rs_upper = name.upper()

        if 'RETIRO' in rs_upper or retiro > 0.5 * max(1, tot_primas):
            seg = 'Seguros de Retiro'
        elif 'RIESGOS DEL TRABAJO' in rs_upper or ' ART' in rs_upper or 'A.R.T.' in rs_upper or art > 0.5 * max(1, tot_primas):
            seg = 'Riesgos del Trabajo (ART)'
        elif personas > 0.5 * max(1, tot_primas) or any(w in rs_upper for w in ['PERSONAS', 'VIDA', 'LIFE', 'SALUD', 'SEPELIO', 'CARDIF', 'METLIFE', 'CNP', 'PRUDENTIAL', 'ZURICH INTERNATIONAL LIFE']):
            seg = 'Seguros de Personas'
        else:
            seg = 'Patrimoniales y Mixtas'

        seg_map[c] = seg

    df['tipo_entidad'] = df['cod_cia'].map(seg_map)

    try:
        df.to_parquet(parquet_path, index=False)
    except Exception as e:
        print(f"Failed to cache parquet {parquet_path}: {e}")

    return df

if __name__ == '__main__':
    periods = get_all_periods()
    print(f"Available periods: {len(periods)} -> {periods}")
    if periods:
        print(f"Loading {periods[-1]}...")
        df = load_period_data(periods[-1])
        print(f"Loaded {len(df):,} rows for {df['cod_cia'].nunique()} companies.")
