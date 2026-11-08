import io
import os
import glob
import struct
import pandas as pd

try:
    import pyodbc
except ImportError:
    pyodbc = None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASES_DIR = os.path.join(BASE_DIR, "Bases")
CACHE_DIR = os.path.join(BASE_DIR, ".cache", "v2_parquet")

def get_connection_string(mdb_path):
    if pyodbc is None:
        return None
    drivers = [d for d in pyodbc.drivers() if 'Access' in d or 'ACE' in d]
    if 'Microsoft Access Driver (*.mdb, *.accdb)' in drivers:
        return f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={mdb_path};"
    elif 'Microsoft Access Driver (*.mdb)' in drivers:
        return f"DRIVER={{Microsoft Access Driver (*.mdb)}};DBQ={mdb_path};"
    return None

def _read_mdb_via_access_parser(mdb_path):
    """Lee la tabla Balance desde un archivo .mdb usando access_parser (compatible con macOS/Linux)."""
    from access_parser import AccessParser
    import access_parser.access_parser as ap

    def _fixed_parse_row(self, record):
        original_record = record
        reverse_record = record[::-1]
        null_table_len = (self.table_header.column_count + 7) // 8
        if null_table_len and null_table_len < len(original_record):
            null_table = record[-null_table_len:]
            null_table = [((null_table[i // 8]) & (1 << (i % 8))) != 0 for i in range(len(null_table) * 8)]
        else:
            return
        if self.version > 3:
            record = record[2:]
        else:
            record = record[1:]

        relative_records_column_map = {}
        for i, column in self.columns.items():
            if not column.column_flags.fixed_length:
                var_idx = getattr(column, 'variable_column_number', i)
                relative_records_column_map[var_idx] = column
                continue
            self._parse_fixed_length_data(record, column, null_table)
        if relative_records_column_map:
            relative_records_column_map = dict(sorted(relative_records_column_map.items()))
            metadata = self._parse_dynamic_length_records_metadata(reverse_record, original_record, null_table_len)
            if not metadata:
                return
            if metadata.variable_length_field_offsets:
                self._parse_dynamic_length_data(original_record, metadata, relative_records_column_map, null_table)

    ap.AccessTable._parse_row = _fixed_parse_row

    # Materializar archivo en Google Drive CloudStorage antes de parsear
    with open(mdb_path, "rb") as f:
        _ = f.read(65536)

    db = AccessParser(mdb_path)
    tbl = db.parse_table("Balance")
    df = pd.DataFrame.from_dict(tbl)
    cols = ["cod_cia", "razon_social", "periodo", "cod_subramo", "desc_subramo", "importe", "cod_cuenta", "desc_cuenta", "nivel", "id_padre"]
    return df[[c for c in cols if c in df.columns]]

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
            with open(parquet_path, "rb") as f:
                buf = io.BytesIO(f.read())
            return pd.read_parquet(buf)
        except Exception as e:
            print(f"Error reading cache {parquet_path}: {e}")

    mdb_path = os.path.join(BASES_DIR, f"{period}.mdb")
    if not os.path.exists(mdb_path):
        raise FileNotFoundError(f"Database not found: {mdb_path}")

    conn_str = get_connection_string(mdb_path)
    if conn_str:
        conn = pyodbc.connect(conn_str)
        query = "SELECT cod_cia, razon_social, periodo, cod_subramo, desc_subramo, importe, cod_cuenta, desc_cuenta, nivel, id_padre FROM Balance"
        df = pd.read_sql(query, conn)
        conn.close()
    else:
        df = _read_mdb_via_access_parser(mdb_path)

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
        buf = io.BytesIO()
        df.to_parquet(buf, index=False)
        with open(parquet_path, "wb") as f:
            f.write(buf.getvalue())
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
