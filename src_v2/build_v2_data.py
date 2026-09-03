import os
import json
import time
import pandas as pd
import numpy as np
from db_engine_v2 import get_all_periods, load_period_data
from insurance_kpis_v2 import (
    compute_all_companies_summary,
    get_company_subramos,
    get_company_investments_breakdown
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_V2_DIR = os.path.join(BASE_DIR, "data_v2")
JSON_OUTPUT = os.path.join(DATA_V2_DIR, "dataset_v2.json")
JS_OUTPUT = os.path.join(DATA_V2_DIR, "dataset_v2.js")

GROUPS_DEFINITIONS = [
    {
        "id": "sancor",
        "name": "Grupo Sancor Seguros",
        "short_name": "Sancor Seguros",
        "codes": ["0224", "0626", "0930"],
        "description": "Sancor Seguros, Prevención ART, Prevención Retiro"
    },
    {
        "id": "federacion_patronal",
        "name": "Grupo Federación Patronal",
        "short_name": "Federación Patronal",
        "codes": ["0726", "0425"],
        "description": "Federación Patronal Seguros (PM+ART), Federación Patronal Retiro"
    },
    {
        "id": "provincia",
        "name": "Grupo Provincia",
        "short_name": "Provincia",
        "codes": ["0499", "0621", "0532"],
        "description": "Provincia Seguros, Provincia ART, Provincia Vida"
    },
    {
        "id": "san_cristobal",
        "name": "Grupo San Cristóbal",
        "short_name": "San Cristóbal",
        "codes": ["0192", "0620", "0442", "0856"],
        "description": "San Cristóbal Seguros, Asociart ART, San Cristóbal Retiro, Iunigo"
    },
    {
        "id": "la_segunda",
        "name": "Grupo Asegurador La Segunda",
        "short_name": "La Segunda",
        "codes": ["0317", "0618", "0117", "0436"],
        "description": "La Segunda Generales, La Segunda ART, La Segunda Personas, La Segunda Retiro"
    },
    {
        "id": "la_caja_generali",
        "name": "Grupo La Caja / Generali",
        "short_name": "La Caja / Generali",
        "codes": ["0501"],
        "description": "Caja de Seguros S.A. (Patrimoniales y Vida)"
    },
    {
        "id": "zurich",
        "name": "Grupo Zurich",
        "short_name": "Zurich",
        "codes": ["0228", "0692", "0541"],
        "description": "Zurich Argentina, Zurich Santander, Zurich International Life"
    },
    {
        "id": "experta_werthein",
        "name": "Grupo Experta / Werthein",
        "short_name": "Experta / Werthein",
        "codes": ["0880", "0616", "0419"],
        "description": "Experta Seguros, Experta ART, La Estrella Retiro"
    },
    {
        "id": "mercantil_andina",
        "name": "Grupo Mercantil Andina",
        "short_name": "Mercantil Andina",
        "codes": ["0116", "0959"],
        "description": "Mercantil Andina, Andina ART"
    },
    {
        "id": "nacion",
        "name": "Grupo Nación",
        "short_name": "Nación",
        "codes": ["0515", "0534"],
        "description": "Nación Seguros, Nación Retiro"
    },
    {
        "id": "rivadavia",
        "name": "Grupo Asegurador Rivadavia",
        "short_name": "Rivadavia",
        "codes": ["0222", "0678"],
        "description": "Seguros Bernardino Rivadavia, Mutual Rivadavia TP"
    },
    {
        "id": "galicia",
        "name": "Grupo Galicia Seguros",
        "short_name": "Galicia Seguros",
        "codes": ["0025", "0589", "0443", "0426"],
        "description": "Galicia Seguros, Sudamericana Seguros Galicia, Galicia Retiro"
    },
    {
        "id": "swiss_medical",
        "name": "Grupo Swiss Medical (SMG)",
        "short_name": "Swiss Medical (SMG)",
        "codes": ["0002", "0605", "0580", "0710", "0661"],
        "description": "SMG Seguros, Swiss Medical ART, SMG Life, SMG Retiro, Instituto de Salta"
    },
    {
        "id": "st",
        "name": "Grupo ST",
        "short_name": "Grupo ST",
        "codes": ["0251", "0423"],
        "description": "Life Seguros, Orígenes Retiro"
    },
    {
        "id": "meridional",
        "name": "Grupo La Meridional",
        "short_name": "La Meridional",
        "codes": ["0244"],
        "description": "La Meridional Compañía Argentina de Seguros"
    },
    {
        "id": "mapfre",
        "name": "Grupo Mapfre",
        "short_name": "Mapfre",
        "codes": ["0213", "0699"],
        "description": "Mapfre Seguros, Mapfre Vida"
    },
    {
        "id": "barbuss_hdi",
        "name": "Grupo Barbuss / HDI",
        "short_name": "Barbuss / HDI",
        "codes": ["0335"],
        "description": "Barbuss Risk Seguros (ex HDI Seguros)"
    },
    {
        "id": "galeno",
        "name": "Grupo Galeno",
        "short_name": "Galeno",
        "codes": ["0878"],
        "description": "Galeno Seguros (Patrimoniales y ART)"
    }
]

BRANCH_TAXONOMY = {
    "total_mercado": {"name": "Total del Mercado", "prefix": ""},
    "patrimoniales": {"name": "Patrimoniales Total", "prefix": "1."},
    "automotores": {"name": "Automotores y Motos", "codes": ["1.030.01", "1.030.02", "1.030.03", "1.180.01", "1.180.02", "1.180.03"]},
    "art": {"name": "Riesgos del Trabajo (ART)", "codes": ["1.050.01", "1.050.99"]},
    "agro": {"name": "Agropecuario y Forestal", "codes": ["1.070.01", "1.070.02", "1.070.99"]},
    "incendio_comb": {"name": "Incendio y Combinados", "codes": ["1.010.99", "1.020.01", "1.020.02", "1.020.99"]},
    "rc": {"name": "Responsabilidad Civil", "codes": ["1.080.01", "1.080.02", "1.080.03", "1.080.99"]},
    "caucion": {"name": "Caución y Créditos", "codes": ["1.100.01", "1.100.99", "1.110.01", "1.110.02", "1.110.99"]},
    "transporte": {"name": "Transporte y Cascos", "codes": ["1.040.99", "1.120.99", "1.130.01", "1.130.99", "1.140.99", "1.150.99"]},
    "otros_patrimoniales": {"name": "Otros Patrimoniales", "codes": ["1.010.99", "1.020.01", "1.020.02", "1.020.99", "1.080.01", "1.080.02", "1.080.03", "1.080.99", "1.100.01", "1.100.99", "1.110.01", "1.110.02", "1.110.99", "1.040.99", "1.120.99", "1.130.01", "1.130.99", "1.140.99", "1.150.99", "1.090.99", "1.160.99", "1.170.01", "1.170.02", "1.170.03", "1.170.99"]},
    "personas": {"name": "Personas Total", "prefix": "2."},
    "vida": {"name": "Seguros de Vida", "codes": ["2.030.01", "2.030.02", "2.030.03", "2.030.04", "2.030.05"]},
    "ap": {"name": "Accidentes Personales", "codes": ["2.010.01", "2.010.02"]},
    "salud": {"name": "Salud", "codes": ["2.020.01", "2.020.02"]},
    "sepelio": {"name": "Sepelio", "codes": ["2.050.01", "2.050.02"]},
    "retiro": {"name": "Seguros de Retiro", "codes": ["2.060.01", "2.060.02", "2.070.01", "2.070.02"]},
    "retiro_individual": {"name": "Retiro Individual", "codes": ["2.060.01"]},
    "retiro_colectivo": {"name": "Retiro Colectivo", "codes": ["2.060.02"]}
}

def get_period_label(p_str):
    try:
        parts = p_str.split("-")
        yr = int(parts[0])
        q = int(parts[1])
        if q == 3:
            return f"30-09-{yr} (3 Meses - Ej. {yr}/{yr+1})"
        elif q == 4:
            return f"31-12-{yr} (6 Meses - Ej. {yr}/{yr+1})"
        elif q == 1:
            return f"31-03-{yr} (9 Meses - Ej. {yr-1}/{yr})"
        elif q == 2:
            return f"30-06-{yr} (12 Meses Cierre - Ej. {yr-1}/{yr})"
    except:
        pass
    return p_str


def aggregate_standard_branches(market_subramos):
    """
    Agrupa los 48 subramos contables SSN en los 10 ramos oficiales estandarizados:
    1. Automóviles (Automotores + Motos + TPP)
    2. Riesgos del Trabajo (ART)
    3. Vida Colectivo (Colectivo + Saldo Deudor + Obligatorios)
    4. Vida Individual
    5. Retiro (Colectivo + Individual + Rentas)
    6. Accidentes Personales (Colectivo + Individual + Acc. Pasajeros)
    7. Salud (Colectivo + Individual)
    8. Sepelio (Colectivo + Individual)
    9. Agropecuarios y Forestales (Granizo + Ganado + Otros)
    10. Otros Riesgos Patrimoniales (Incendio, Integral, RC, Caución, Robo, Técnico, etc.)
    """
    b_map = {
        "ramo_automotores": 0.0,
        "ramo_art": 0.0,
        "ramo_vida_colectivo": 0.0,
        "ramo_vida_individual": 0.0,
        "ramo_retiro": 0.0,
        "ramo_accidentes_personales": 0.0,
        "ramo_salud": 0.0,
        "ramo_sepelio": 0.0,
        "ramo_agro": 0.0,
        "ramo_otros_patrimoniales": 0.0
    }
    
    for s in market_subramos:
        cod = str(s.get('cod_subramo', ''))
        desc = str(s.get('desc_subramo', '')).lower()
        p = float(s.get('primas', 0.0))
        
        # 1. Automotores / Motos / TPP
        if cod.startswith('1.030.') or cod.startswith('1.180.') or cod.startswith('1.040.'):
            b_map["ramo_automotores"] += p
        # 2. ART
        elif cod.startswith('1.050.'):
            b_map["ramo_art"] += p
        # 3. Vida Colectivo
        elif cod in ('2.030.02', '2.030.04', '2.030.05') or ('vida' in desc and 'colect' in desc) or ('saldo deudor' in desc):
            b_map["ramo_vida_colectivo"] += p
        # 4. Vida Individual
        elif cod == '2.030.01' or ('vida' in desc and 'indiv' in desc):
            b_map["ramo_vida_individual"] += p
        # 5. Retiro
        elif cod.startswith('2.060.') or cod.startswith('2.070.') or 'retiro' in desc:
            b_map["ramo_retiro"] += p
        # 6. Accidentes Personales
        elif cod.startswith('2.010.') or cod.startswith('1.120.') or 'acc. personales' in desc or 'acc. a pasaj' in desc:
            b_map["ramo_accidentes_personales"] += p
        # 7. Salud
        elif cod.startswith('2.020.') or 'salud' in desc:
            b_map["ramo_salud"] += p
        # 8. Sepelio
        elif cod.startswith('2.050.') or 'sepelio' in desc:
            b_map["ramo_sepelio"] += p
        # 9. Agropecuarios y Forestales
        elif cod.startswith('1.070.') or 'agrop' in desc:
            b_map["ramo_agro"] += p
        # 10. Otros Patrimoniales
        else:
            b_map["ramo_otros_patrimoniales"] += p

    for k in b_map:
        b_map[k] = round(b_map[k], 2)
        
    return b_map

def compute_rankings_for_df(df_raw, df_summary, groups_dict):
    total_mkt_primas = float(df_summary['primas_emitidas'].sum())
    rankings = {}

    # 1. Total Mercado
    tm = df_summary[['cod_cia', 'razon_social', 'primas_emitidas', 'tipo_entidad']].copy()
    tm = tm.sort_values(by='primas_emitidas', ascending=False)
    tm_list = []
    for pos, (_, r) in enumerate(tm.iterrows(), 1):
        p_val = float(r['primas_emitidas'])
        tm_list.append({
            "posicion": pos,
            "cod_cia": r['cod_cia'],
            "entidad": r['razon_social'],
            "tipo_entidad": r['tipo_entidad'],
            "prima": round(p_val, 2),
            "participacion": round((p_val / total_mkt_primas * 100.0), 2) if total_mkt_primas > 0 else 0.0
        })
    rankings['total_mercado'] = tm_list

    # 2. Grupos Aseguradores
    grp_list = []
    for gid, ginfo in groups_dict.items():
        g_primas = float(ginfo.get('primas_emitidas', 0.0))
        grp_list.append({
            "id": gid,
            "entidad": ginfo['name'],
            "short_name": ginfo['short_name'],
            "prima": round(g_primas, 2),
            "participacion": round((g_primas / total_mkt_primas * 100.0), 2) if total_mkt_primas > 0 else 0.0,
            "members_count": ginfo['entities_count']
        })
    grp_list.sort(key=lambda x: x['prima'], reverse=True)
    for pos, g in enumerate(grp_list, 1):
        g['posicion'] = pos
    rankings['grupos_aseguradores'] = grp_list

    # Subramos emission filter accounts
    accounts_primas = (
        '5.01.01.01.01.01.01', '5.01.01.01.01.01.99',
        '5.01.01.01.01.02.01', '5.01.01.01.01.02.99',
        '5.01.01.01.01.03.02', '5.01.01.01.01.03.99',
        '5.01.01.01.01.04.01', '5.01.01.01.01.04.99'
    )
    primas_sub = df_raw[df_raw['cod_cuenta'].str.startswith(accounts_primas) & (df_raw['desc_subramo'] != '') & (df_raw['desc_subramo'].notna())]

    for b_key, b_def in BRANCH_TAXONOMY.items():
        if b_key in ['total_mercado']:
            continue
        
        if 'codes' in b_def:
            sub_b = primas_sub[primas_sub['cod_subramo'].isin(b_def['codes'])]
        elif 'prefix' in b_def:
            prefix = b_def['prefix']
            if b_key == 'patrimoniales':
                sub_b = primas_sub[primas_sub['cod_subramo'].str.startswith('1.') & (~primas_sub['cod_subramo'].str.startswith('1.050'))]
            else:
                sub_b = primas_sub[primas_sub['cod_subramo'].str.startswith(prefix)]
        else:
            continue

        if b_key == 'agro':
            # Excluir inconsistencia de declaración de Experta (0880) en código de Granizo 1.070
            sub_b = sub_b[sub_b['cod_cia'] != '0880']

        b_agg = sub_b.groupby(['cod_cia', 'razon_social'])['importe'].sum().reset_index()
        b_agg = b_agg[b_agg['importe'] > 0].sort_values(by='importe', ascending=False)
        tot_b = float(b_agg['importe'].sum())

        b_list = []
        for pos, (_, r) in enumerate(b_agg.iterrows(), 1):
            p_val = float(r['importe'])
            b_list.append({
                "posicion": pos,
                "cod_cia": r['cod_cia'],
                "entidad": r['razon_social'],
                "prima": round(p_val, 2),
                "participacion": round((p_val / tot_b * 100.0), 2) if tot_b > 0 else 0.0
            })
        rankings[f"total_{b_key}" if not b_key.startswith("total_") else b_key] = b_list

    return rankings

def process_single_period(period_code):
    print(f"[{period_code}] Loading and processing dataset...")
    df_raw = load_period_data(period_code)
    df_summary = compute_all_companies_summary(df_raw)

    tot_emit = float(df_summary['primas_emitidas'].sum())
    tot_dev = float(df_summary['primas_devengadas'].sum())

    # 1. Macro Totals BY ENTITY TYPE
    def get_seg_sums(seg_name):
        sub = df_summary[df_summary['tipo_entidad'] == seg_name]
        return {
            'emitidas': float(sub['primas_emitidas'].sum()),
            'devengadas': float(sub['primas_devengadas'].sum()),
            'entidades': int(len(sub))
        }

    patrim_ent = get_seg_sums('Patrimoniales y Mixtas')
    art_ent = get_seg_sums('Riesgos del Trabajo (ART)')
    personas_ent = get_seg_sums('Seguros de Personas')
    retiro_ent = get_seg_sums('Seguros de Retiro')

    macro_entidades = {
        "total_mercado_emitidas": round(tot_emit, 2),
        "total_mercado_devengadas": round(tot_dev, 2),
        "patrimoniales_emitidas": round(patrim_ent['emitidas'], 2),
        "patrimoniales_devengadas": round(patrim_ent['devengadas'], 2),
        "patrimoniales_entidades": patrim_ent['entidades'],
        "art_emitidas": round(art_ent['emitidas'], 2),
        "art_devengadas": round(art_ent['devengadas'], 2),
        "art_entidades": art_ent['entidades'],
        "personas_emitidas": round(personas_ent['emitidas'], 2),
        "personas_devengadas": round(personas_ent['devengadas'], 2),
        "personas_entidades": personas_ent['entidades'],
        "retiro_emitidas": round(retiro_ent['emitidas'], 2),
        "retiro_devengadas": round(retiro_ent['devengadas'], 2),
        "retiro_entidades": retiro_ent['entidades']
    }

    # 2. Macro Totals BY REAL PRODUCT LINE (SUBRAMOS PUROS)
    accounts_primas = (
        '5.01.01.01.01.01.01', '5.01.01.01.01.01.99',
        '5.01.01.01.01.02.01', '5.01.01.01.01.02.99',
        '5.01.01.01.01.03.02', '5.01.01.01.01.03.99',
        '5.01.01.01.01.04.01', '5.01.01.01.01.04.99'
    )
    primas_sub = df_raw[df_raw['cod_cuenta'].str.startswith(accounts_primas) & (df_raw['desc_subramo'] != '') & (df_raw['desc_subramo'].notna())]
    sin_sub = df_raw[df_raw['cod_cuenta'].str.startswith(('4.01.01.01.01.01', '4.01.01.01.01.99', '4.01.01.01.02.01', '4.01.01.01.02.99', '4.01.01.01.03.01', '4.01.01.01.03.99', '4.01.01.01.04.01', '4.01.01.01.04.99', '4.01.02.01', '4.01.02.02', '4.01.02.03')) & (df_raw['desc_subramo'] != '') & (df_raw['desc_subramo'].notna())]

    def get_macro_product(cod_sub):
        cod_str = str(cod_sub).strip()
        if cod_str.startswith('1.050') or cod_str.startswith('1.50') or cod_str == '1.05':
            return 'art'
        elif cod_str.startswith('1.'):
            return 'patrimoniales'
        elif cod_str.startswith('2.06') or cod_str.startswith('2.07') or cod_str.startswith('2.08'):
            return 'retiro'
        elif cod_str.startswith('2.'):
            return 'personas'
        return 'otros'

    p_df = primas_sub.copy()
    s_df = sin_sub.copy()
    p_df['macro_prod'] = p_df['cod_subramo'].apply(get_macro_product)
    s_df['macro_prod'] = s_df['cod_subramo'].apply(get_macro_product)

    tot_prod_p = float(p_df['importe'].sum())
    tot_prod_s = float(s_df['importe'].sum())

    macro_productos = {}
    for k in ['patrimoniales', 'art', 'personas', 'retiro']:
        p_val = float(p_df[p_df['macro_prod'] == k]['importe'].sum())
        s_val = float(s_df[s_df['macro_prod'] == k]['importe'].sum())
        sin_pct = (s_val / p_val * 100.0) if p_val > 0 else 0.0
        part_pct = (p_val / tot_prod_p * 100.0) if tot_prod_p > 0 else 0.0

        macro_productos[k] = {
            "primas": round(p_val, 2),
            "siniestros": round(s_val, 2),
            "siniestralidad": round(sin_pct, 1),
            "participacion": round(part_pct, 1)
        }

    # Cross-selling breakdown for Personas (how much is sold by Mixtas vs Exclusivas)
    pers_p_df = p_df[p_df['macro_prod'] == 'personas']
    pers_in_mixtas = float(pers_p_df[pers_p_df['tipo_entidad'] == 'Patrimoniales y Mixtas']['importe'].sum())
    pers_in_personas = float(pers_p_df[pers_p_df['tipo_entidad'] == 'Seguros de Personas']['importe'].sum())
    pers_in_art = float(pers_p_df[pers_p_df['tipo_entidad'] == 'Riesgos del Trabajo (ART)']['importe'].sum())

    macro_productos['personas_cross_selling'] = {
        "en_mixtas": round(pers_in_mixtas, 2),
        "en_personas": round(pers_in_personas, 2),
        "en_art": round(pers_in_art, 2),
        "pct_en_mixtas": round((pers_in_mixtas / macro_productos['personas']['primas'] * 100.0), 1) if macro_productos['personas']['primas'] > 0 else 0.0,
        "pct_en_personas": round((pers_in_personas / macro_productos['personas']['primas'] * 100.0), 1) if macro_productos['personas']['primas'] > 0 else 0.0
    }

    macro_productos['total'] = {
        "primas": round(tot_prod_p, 2),
        "siniestros": round(tot_prod_s, 2),
        "siniestralidad": round((tot_prod_s / tot_prod_p * 100.0), 1) if tot_prod_p > 0 else 0.0
    }

    # 3. Company profiles
    companies_dict = {}
    strategic_matrix = []

    for _, row in df_summary.iterrows():
        c_code = row['cod_cia']
        df_cia_raw = df_raw[df_raw['cod_cia'] == c_code]
        subramos = get_company_subramos(df_raw, cod_cia=c_code)
        investments = get_company_investments_breakdown(df_cia_raw)

        c_data = row.to_dict()
        for k, v in c_data.items():
            if isinstance(v, float):
                c_data[k] = 0.0 if np.isnan(v) or np.isinf(v) else round(v, 2)
            elif isinstance(v, (np.int64, np.int32)):
                c_data[k] = int(v)

        c_data['subramos'] = subramos
        c_data['investments'] = investments
        companies_dict[c_code] = c_data

        # Build Strategic Matrix points
        m_tec = float(c_data.get('margen_tecnico', 0.0))
        roi = float(c_data.get('roi_inversiones', 0.0))
        p_dev = float(c_data.get('primas_devengadas', 0.0))
        p_emit = float(c_data.get('primas_emitidas', 0.0))
        comb = float(c_data.get('combined_ratio', 0.0))

        # Quadrant classification
        if m_tec >= 0 and roi >= 0:
            quadrant = "Q1_LIDERES"
            quadrant_label = "Ganadoras Integrales (Técnico + / Financiero +)"
        elif m_tec < 0 and roi >= 0:
            quadrant = "Q2_DEP_FIN"
            quadrant_label = "Dependencia Financiera (Técnico - / Financiero +)"
        elif m_tec >= 0 and roi < 0:
            quadrant = "Q3_ESP_TEC"
            quadrant_label = "Especialistas Técnicos (Técnico + / Financiero -)"
        else:
            quadrant = "Q4_RIESGO"
            quadrant_label = "En Riesgo Operativo (Técnico - / Financiero -)"

        if p_emit > 0:
            strategic_matrix.append({
                "cod_cia": c_code,
                "razon_social": c_data['razon_social'],
                "tipo_entidad": c_data['tipo_entidad'],
                "x": round(max(-150.0, min(150.0, m_tec)), 2), # Margen Técnico (%)
                "y": round(max(-60.0, min(120.0, roi)), 2),     # Rendimiento Financiero (%)
                "primas_devengadas": p_dev,
                "primas_emitidas": p_emit,
                "resultado_tecnico": float(c_data.get('resultado_tecnico', 0.0)),
                "resultado_financiero": float(c_data.get('resultado_financiero', 0.0)),
                "resultado_neto": float(c_data.get('resultado_neto', 0.0)),
                "combined_ratio": comb,
                "quadrant": quadrant,
                "quadrant_label": quadrant_label
            })

    # 4. Group consolidation
    groups_dict = {}
    for gdef in GROUPS_DEFINITIONS:
        gid = gdef['id']
        members = []
        tot_g_emit = 0.0
        tot_g_dev = 0.0
        tot_g_sin = 0.0
        tot_g_res_tec = 0.0
        tot_g_res_fin = 0.0
        tot_g_res_neto = 0.0
        tot_g_activo = 0.0
        tot_g_inv = 0.0
        tot_g_pn = 0.0

        for cd in gdef['codes']:
            if cd in companies_dict:
                c = companies_dict[cd]
                members.append(c)
                tot_g_emit += float(c.get('primas_emitidas', 0.0))
                tot_g_dev += float(c.get('primas_devengadas', 0.0))
                tot_g_sin += float(c.get('siniestros', 0.0))
                tot_g_res_tec += float(c.get('resultado_tecnico', 0.0))
                tot_g_res_fin += float(c.get('resultado_financiero', 0.0))
                tot_g_res_neto += float(c.get('resultado_neto', 0.0))
                tot_g_activo += float(c.get('activo', 0.0))
                tot_g_inv += float(c.get('inversiones', 0.0))
                tot_g_pn += float(c.get('patrimonio_neto', 0.0))

        if not members:
            continue

        loss_ratio = (tot_g_sin / tot_g_dev * 100.0) if tot_g_dev > 0 else 0.0
        mkt_share = (tot_g_emit / tot_emit * 100.0) if tot_emit > 0 else 0.0

        members_summary = []
        for m in members:
            m_emit = float(m.get('primas_emitidas', 0.0))
            members_summary.append({
                "cod_cia": m['cod_cia'],
                "razon_social": m['razon_social'],
                "tipo_entidad": m['tipo_entidad'],
                "primas_emitidas": m_emit,
                "share_of_group": round((m_emit / tot_g_emit * 100.0), 1) if tot_g_emit > 0 else 0.0,
                "resultado_neto": float(m.get('resultado_neto', 0.0)),
                "combined_ratio": float(m.get('combined_ratio', 0.0))
            })
        members_summary.sort(key=lambda x: x['primas_emitidas'], reverse=True)

        g_m_tec = (tot_g_res_tec / tot_g_dev * 100.0) if tot_g_dev > 0 else 0.0
        g_roi = (tot_g_res_fin / tot_g_inv * 100.0) if tot_g_inv > 0 else 0.0
        g_comb = (tot_g_sin + (tot_g_emit - tot_g_dev)) / tot_g_dev * 100.0 if tot_g_dev > 0 else 100.0

        if g_m_tec >= 0 and g_roi >= 0:
            g_quad = "Q1_LIDERES"
            g_quad_label = "Ganadoras Integrales (Técnico + / Financiero +)"
        elif g_m_tec < 0 and g_roi >= 0:
            g_quad = "Q2_DEP_FIN"
            g_quad_label = "Dependencia Financiera (Técnico - / Financiero +)"
        elif g_m_tec >= 0 and g_roi < 0:
            g_quad = "Q3_ESP_TEC"
            g_quad_label = "Especialistas Técnicos (Técnico + / Financiero -)"
        else:
            g_quad = "Q4_RIESGO"
            g_quad_label = "En Riesgo Operativo (Técnico - / Financiero -)"

        groups_dict[gid] = {
            "id": gid,
            "name": gdef['name'],
            "short_name": gdef['short_name'],
            "description": gdef['description'],
            "entities_count": len(members),
            "members": members_summary,
            "primas_emitidas": round(tot_g_emit, 2),
            "primas_devengadas": round(tot_g_dev, 2),
            "siniestros": round(tot_g_sin, 2),
            "resultado_tecnico": round(tot_g_res_tec, 2),
            "resultado_financiero": round(tot_g_res_fin, 2),
            "resultado_neto": round(tot_g_res_neto, 2),
            "activo": round(tot_g_activo, 2),
            "inversiones": round(tot_g_inv, 2),
            "patrimonio_neto": round(tot_g_pn, 2),
            "margen_tecnico": round(g_m_tec, 2),
            "roi_inversiones": round(g_roi, 2),
            "combined_ratio": round(g_comb, 2),
            "loss_ratio": round(loss_ratio, 2),
            "market_share": round(mkt_share, 2),
            "quadrant": g_quad,
            "quadrant_label": g_quad_label
        }

    # Strategic matrix for groups
    strategic_matrix_groups = []
    for gid, g in groups_dict.items():
        strategic_matrix_groups.append({
            "id": gid,
            "cod_cia": gid,
            "razon_social": g['name'],
            "short_name": g['short_name'],
            "tipo_entidad": "Grupos Aseguradores",
            "x": round(max(-150.0, min(150.0, g['margen_tecnico'])), 2),
            "y": round(max(-60.0, min(120.0, g['roi_inversiones'])), 2),
            "primas_devengadas": g['primas_devengadas'],
            "primas_emitidas": g['primas_emitidas'],
            "resultado_tecnico": g['resultado_tecnico'],
            "resultado_financiero": g['resultado_financiero'],
            "resultado_neto": g['resultado_neto'],
            "combined_ratio": g['combined_ratio'],
            "quadrant": g['quadrant'],
            "quadrant_label": g['quadrant_label'],
            "entities_count": g['entities_count']
        })

    # Strategic matrix for segments / insurer types
    segments_agg = {}
    for c in companies_dict.values():
        tipo = c.get('tipo_entidad', 'Otras')
        if tipo not in segments_agg:
            segments_agg[tipo] = {
                "tipo_entidad": tipo,
                "entities_count": 0,
                "primas_emitidas": 0.0,
                "primas_devengadas": 0.0,
                "siniestros": 0.0,
                "resultado_tecnico": 0.0,
                "resultado_financiero": 0.0,
                "resultado_neto": 0.0,
                "inversiones": 0.0,
                "activo": 0.0,
                "patrimonio_neto": 0.0
            }
        s = segments_agg[tipo]
        s["entities_count"] += 1
        s["primas_emitidas"] += float(c.get('primas_emitidas', 0.0))
        s["primas_devengadas"] += float(c.get('primas_devengadas', 0.0))
        s["siniestros"] += float(c.get('siniestros', 0.0))
        s["resultado_tecnico"] += float(c.get('resultado_tecnico', 0.0))
        s["resultado_financiero"] += float(c.get('resultado_financiero', 0.0))
        s["resultado_neto"] += float(c.get('resultado_neto', 0.0))
        s["inversiones"] += float(c.get('inversiones', 0.0))
        s["activo"] += float(c.get('activo', 0.0))
        s["patrimonio_neto"] += float(c.get('patrimonio_neto', 0.0))

    strategic_matrix_segments = []
    for tipo, s in segments_agg.items():
        m_tec = (s["resultado_tecnico"] / s["primas_devengadas"] * 100.0) if s["primas_devengadas"] > 0 else 0.0
        roi = (s["resultado_financiero"] / s["inversiones"] * 100.0) if s["inversiones"] > 0 else 0.0
        loss_r = (s["siniestros"] / s["primas_devengadas"] * 100.0) if s["primas_devengadas"] > 0 else 0.0
        mkt_sh = (s["primas_emitidas"] / tot_emit * 100.0) if tot_emit > 0 else 0.0
        
        if m_tec >= 0 and roi >= 0:
            quad = "Q1_LIDERES"
            quad_lbl = "Ganadoras Integrales (Técnico + / Financiero +)"
        elif m_tec < 0 and roi >= 0:
            quad = "Q2_DEP_FIN"
            quad_lbl = "Dependencia Financiera (Técnico - / Financiero +)"
        elif m_tec >= 0 and roi < 0:
            quad = "Q3_ESP_TEC"
            quad_lbl = "Especialistas Técnicos (Técnico + / Financiero -)"
        else:
            quad = "Q4_RIESGO"
            quad_lbl = "En Riesgo Operativo (Técnico - / Financiero -)"

        comb = (s["siniestros"] + (s["primas_emitidas"] - s["primas_devengadas"])) / s["primas_devengadas"] * 100.0 if s["primas_devengadas"] > 0 else 100.0

        item = {
            "id": "SEG_" + tipo.upper().replace(" ", "_").replace("/", "_"),
            "cod_cia": "SEG_" + tipo[:4].upper(),
            "razon_social": tipo,
            "short_name": tipo,
            "tipo_entidad": "Segmentos Consolidados",
            "entities_count": s["entities_count"],
            "x": round(max(-150.0, min(150.0, m_tec)), 2),
            "y": round(max(-60.0, min(120.0, roi)), 2),
            "margen_tecnico": round(m_tec, 2),
            "roi_inversiones": round(roi, 2),
            "primas_emitidas": round(s["primas_emitidas"], 2),
            "primas_devengadas": round(s["primas_devengadas"], 2),
            "resultado_tecnico": round(s["resultado_tecnico"], 2),
            "resultado_financiero": round(s["resultado_financiero"], 2),
            "resultado_neto": round(s["resultado_neto"], 2),
            "inversiones": round(s["inversiones"], 2),
            "patrimonio_neto": round(s["patrimonio_neto"], 2),
            "activo": round(s["activo"], 2),
            "loss_ratio": round(loss_r, 2),
            "combined_ratio": round(comb, 2),
            "market_share": round(mkt_sh, 2),
            "quadrant": quad,
            "quadrant_label": quad_lbl
        }
        strategic_matrix_segments.append(item)
    strategic_matrix_segments.sort(key=lambda x: x["primas_emitidas"], reverse=True)

    # 5. Rankings
    rankings = compute_rankings_for_df(df_raw, df_summary, groups_dict)

    # 6. Market investments & subramos
    market_investments = get_company_investments_breakdown(df_raw)
    market_subramos = get_company_subramos(df_raw)

    # 7. La Segunda Group Details
    ls_group = groups_dict.get('la_segunda', {})
    ls_details = {
        "tot_grupo": ls_group.get('primas_emitidas', 0.0),
        "share_mercado": ls_group.get('market_share', 0.0),
        "companies": [c for c in companies_dict.values() if c['cod_cia'] in ["0317", "0618", "0117", "0436"]]
    }

    return {
        "periodo": period_code,
        "period_label": get_period_label(period_code),
        "total_entidades": len(df_summary),
        "macro_entidades": macro_entidades,
        "macro_productos": macro_productos,
        "strategic_matrix": strategic_matrix,
        "strategic_matrix_groups": strategic_matrix_groups,
        "strategic_matrix_segments": strategic_matrix_segments,
        "companies_by_code": companies_dict,
        "companies": list(companies_dict.values()),
        "groups_by_id": groups_dict,
        "groups": list(groups_dict.values()),
        "rankings": rankings,
        "market_investments": market_investments,
        "market_subramos": market_subramos,
        "la_segunda": ls_details
    }

def build_all_v2_datasets():
    start_time = time.time()
    os.makedirs(DATA_V2_DIR, exist_ok=True)
    periods = get_all_periods()
    print(f"=== INICIANDO PROCESAMIENTO MULTI-PERÍODO ({len(periods)} trimestres) ===")

    periods_data = {}
    quarterly_time_series = {
        "periods": [],
        "period_labels": [],
        "total_mercado_emitidas": [],
        "total_mercado_devengadas": [],
        "patrimoniales_emitidas": [],
        "art_emitidas": [],
        "personas_emitidas": [],
        "retiro_emitidas": [],
        "patrimoniales_prod_emitidas": [],
        "art_prod_emitidas": [],
        "personas_prod_emitidas": [],
        "retiro_prod_emitidas": [],
        "branches": {},
        "groups": {},
        "top_companies": {}
    }

    for b_key in BRANCH_TAXONOMY.keys():
        quarterly_time_series["branches"][b_key] = []
    for gdef in GROUPS_DEFINITIONS:
        quarterly_time_series["groups"][gdef['id']] = []

    for p in periods:
        p_res = process_single_period(p)
        periods_data[p] = p_res

        # Append to historical quarterly time series
        quarterly_time_series["periods"].append(p)
        quarterly_time_series["period_labels"].append(p_res["period_label"])
        macro_e = p_res["macro_entidades"]
        macro_p = p_res["macro_productos"]

        quarterly_time_series["total_mercado_emitidas"].append(macro_e["total_mercado_emitidas"])
        quarterly_time_series["total_mercado_devengadas"].append(macro_e["total_mercado_devengadas"])
        quarterly_time_series["patrimoniales_emitidas"].append(macro_e["patrimoniales_emitidas"])
        quarterly_time_series["art_emitidas"].append(macro_e["art_emitidas"])
        quarterly_time_series["personas_emitidas"].append(macro_e["personas_emitidas"])
        quarterly_time_series["retiro_emitidas"].append(macro_e["retiro_emitidas"])

        quarterly_time_series["patrimoniales_prod_emitidas"].append(macro_p["patrimoniales"]["primas"])
        quarterly_time_series["art_prod_emitidas"].append(macro_p["art"]["primas"])
        quarterly_time_series["personas_prod_emitidas"].append(macro_p["personas"]["primas"])
        quarterly_time_series["retiro_prod_emitidas"].append(macro_p["retiro"]["primas"])

        # Branch time series
        for b_key in BRANCH_TAXONOMY.keys():
            rk_key = f"total_{b_key}" if not b_key.startswith("total_") else b_key
            rk_list = p_res["rankings"].get(rk_key, [])
            tot_b = sum(item['prima'] for item in rk_list)
            quarterly_time_series["branches"][b_key].append(round(tot_b, 2))

        # Groups time series
        for gdef in GROUPS_DEFINITIONS:
            gid = gdef['id']
            g_obj = p_res["groups_by_id"].get(gid, {})
            quarterly_time_series["groups"][gid].append(round(float(g_obj.get('primas_emitidas', 0.0)), 2))

    # Supplementary data & Inflation IPC Indices
    old_dataset_path = os.path.join(BASE_DIR, "data", "insurance_dataset.json")
    supplementary_data = {
        "monthly_flash_series": {},
        "retiro_vidas_stats": {},
        "metadata_sources": {
            "mdb_accounting": "Bases de Balances SSN (SINENSUP Oficial) - 21 Trimestres (2021-2 a 2026-2)",
            "monthly_flash": "Boletín Estadístico SSN - Serie de Producción Mensual Provisoria",
            "retiro_vidas": "Boletín Estadístico SSN - Seguros de Retiro (Cantidad de Vidas Físicas)"
        }
    }

    PERIOD_IPC = {
        "2021-2": 483.60,   # 30-06-2021 (12M Cierre 20/21)
        "2021-3": 532.06,   # 30-09-2021 (3M 21/22)
        "2021-4": 582.46,   # 31-12-2021 (6M 21/22)
        "2022-1": 676.06,   # 31-03-2022 (9M 21/22)
        "2022-2": 788.62,   # 30-06-2022 (12M Cierre 21/22)
        "2022-3": 950.89,   # 30-09-2022 (3M 22/23)
        "2022-4": 1134.59,  # 31-12-2022 (6M 22/23)
        "2023-1": 1381.18,  # 31-03-2023 (9M 22/23)
        "2023-2": 1710.22,  # 30-06-2023 (12M Cierre 22/23)
        "2023-3": 2304.59,  # 30-09-2023 (3M 23/24)
        "2023-4": 3533.22,  # 31-12-2023 (6M 23/24)
        "2024-1": 5357.65,  # 31-03-2024 (9M 23/24)
        "2024-2": 6314.15,  # 30-06-2024 (12M Cierre 23/24)
        "2024-3": 7083.82,  # 30-09-2024 (3M 24/25)
        "2024-4": 7752.48,  # 31-12-2024 (6M 24/25)
        "2025-1": 8432.22,  # 31-03-2025 (9M 24/25)
        "2025-2": 9054.40,  # 30-06-2025 (12M Cierre 24/25)
        "2025-3": 9688.21,  # 30-09-2025 (3M 25/26)
        "2025-4": 10366.38, # 31-12-2025 (6M 25/26)
        "2026-1": 11195.69, # 31-03-2026 (9M 25/26)
        "2026-2": 11979.38  # 30-06-2026 (12M Cierre 25/26)
    }

    if os.path.exists(old_dataset_path):
        try:
            with open(old_dataset_path, "r", encoding="utf-8") as f:
                old_d = json.load(f)
                supplementary_data["monthly_flash_series"] = old_d.get("ssn_produccion_mensual", {})
                sr_d = old_d.get("ssn_seg_retiro", {})
                supplementary_data["ssn_seg_retiro"] = sr_d
                supplementary_data["retiro_vidas_stats"] = sr_d.get("asegurados", [])
                supplementary_data["retiro_vidas_total_row"] = sr_d.get("asegurados_total_row", {})
                supplementary_data["retiro_compromisos"] = sr_d.get("compromisos_tecnicos", [])
                supplementary_data["retiro_compromisos_total_row"] = sr_d.get("compromisos_total_row", {})
                supplementary_data["retiro_primas_desglose"] = sr_d.get("primas_emitidas", [])
                supplementary_data["retiro_primas_total_row"] = sr_d.get("primas_emitidas_total_row", {})
                supplementary_data["retiro_periodo"] = sr_d.get("periodo", "Marzo 2026")
        except Exception as e:
            print(f"Warning reading old supplementary data: {e}")

    latest_period = periods[-1] if periods else "2026-2"
    latest_ipc = PERIOD_IPC.get(latest_period, 11979.38)

    # Build Ejercicios Fiscales structure (Exact SSN Fiscal Calendar)
    ejercicios_map = {}
    for p in periods:
        yr, q = map(int, p.split('-'))
        if q == 3:
            ej_key = f"{yr}/{yr+1}"
            pos = 1
            q_label = f"1º Trimestre (30-09-{yr} • 3 Meses)"
            short_q = "Q1 (3 Meses)"
            prev_p = f"{yr-1}-3"
            prev_ej = f"{yr-1}/{yr}"
        elif q == 4:
            ej_key = f"{yr}/{yr+1}"
            pos = 2
            q_label = f"2º Trimestre (31-12-{yr} • 6 Meses)"
            short_q = "Q2 (6 Meses)"
            prev_p = f"{yr-1}-4"
            prev_ej = f"{yr-1}/{yr}"
        elif q == 1:
            ej_key = f"{yr-1}/{yr}"
            pos = 3
            q_label = f"3º Trimestre (31-03-{yr} • 9 Meses)"
            short_q = "Q3 (9 Meses)"
            prev_p = f"{yr-1}-1"
            prev_ej = f"{yr-2}/{yr-1}"
        elif q == 2:
            ej_key = f"{yr-1}/{yr}"
            pos = 4
            q_label = f"4º Trimestre (30-06-{yr} • 12 Meses Cierre)"
            short_q = "Q4 (12M Cierre)"
            prev_p = f"{yr-1}-2"
            prev_ej = f"{yr-2}/{yr-1}"

        if ej_key not in ejercicios_map:
            ej_parts = ej_key.split('/')
            ejercicios_map[ej_key] = {
                "id": ej_key,
                "label": f"Ejercicio {ej_key} (01-07-{ej_parts[0]} al 30-06-{ej_parts[1]})",
                "short_label": f"Ej. {ej_key}",
                "start_year": int(ej_parts[0]),
                "end_year": int(ej_parts[1]),
                "quarters": {}
            }

        has_prev = prev_p in periods_data
        p_ipc = PERIOD_IPC.get(p, latest_ipc)
        prev_ipc = PERIOD_IPC.get(prev_p, p_ipc) if has_prev else p_ipc
        deflator = (latest_ipc / p_ipc) if p_ipc > 0 else 1.0
        prev_deflator = (latest_ipc / prev_ipc) if (has_prev and prev_ipc > 0) else 1.0

        cur_data = periods_data[p]
        me = cur_data["macro_entidades"]
        
        # Standard 10 Branches totals
        branch_map = aggregate_standard_branches(cur_data.get("market_subramos", []))

        # Groups totals
        groups_map = {}
        for g in cur_data.get("strategic_matrix_groups", []):
            g_id = g.get("id", "")
            groups_map[g_id] = round(float(g.get("primas_emitidas", 0)), 2)

        prev_metrics = None
        if has_prev:
            prev_p_data = periods_data[prev_p]
            prev_me = prev_p_data["macro_entidades"]
            prev_branch_map = aggregate_standard_branches(prev_p_data.get("market_subramos", []))
            prev_groups_map = {}
            for g in prev_p_data.get("strategic_matrix_groups", []):
                prev_groups_map[g.get("id", "")] = round(float(g.get("primas_emitidas", 0)), 2)

            prev_metrics = {
                "period": prev_p,
                "period_label": prev_p_data["period_label"],
                "ipc_index": prev_ipc,
                "deflator_to_latest": round(prev_deflator, 4),
                "total_mercado": prev_me["total_mercado_emitidas"],
                "patrimoniales": prev_me["patrimoniales_emitidas"],
                "art": prev_me["art_emitidas"],
                "personas": prev_me["personas_emitidas"],
                "retiro": prev_me["retiro_emitidas"],
                "branches": prev_branch_map,
                "groups": prev_groups_map
            }

        ejercicios_map[ej_key]["quarters"][str(pos)] = {
            "period": p,
            "quarter_num": pos,
            "short_label": short_q,
            "quarter_label": q_label,
            "ipc_index": p_ipc,
            "deflator_to_latest": round(deflator, 4),
            "current_metrics": {
                "total_mercado": me["total_mercado_emitidas"],
                "patrimoniales": me["patrimoniales_emitidas"],
                "art": me["art_emitidas"],
                "personas": me["personas_emitidas"],
                "retiro": me["retiro_emitidas"],
                "branches": branch_map,
                "groups": groups_map
            },
            "prev_period": prev_p if has_prev else None,
            "prev_ejercicio": prev_ej if has_prev else None,
            "prev_metrics": prev_metrics
        }

    # Determine latest ejercicio
    l_yr, l_q = map(int, latest_period.split('-'))
    if l_q in (3, 4):
        latest_ejercicio_key = f"{l_yr}/{l_yr+1}"
    else:
        latest_ejercicio_key = f"{l_yr-1}/{l_yr}"

    master_payload = {
        "latest_period": latest_period,
        "latest_ejercicio": latest_ejercicio_key,
        "available_periods": periods,
        "ejercicios_fiscales": ejercicios_map,
        "ipc_indices": PERIOD_IPC,
        "quarterly_time_series": quarterly_time_series,
        "periods_data": periods_data,
        "supplementary_data": supplementary_data,
        "branch_taxonomy": BRANCH_TAXONOMY,
        "groups_definitions": GROUPS_DEFINITIONS,
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "last_updated_human": time.strftime("%d/%m/%Y %H:%M hs")
    }

    # Save to JSON
    print(f"Saving {JSON_OUTPUT}...")
    with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(master_payload, f, ensure_ascii=False)

    # Save to JS for standalone distribution
    print(f"Saving {JS_OUTPUT}...")
    with open(JS_OUTPUT, "w", encoding="utf-8") as f:
        f.write("/* Tablero de Seguros v2 - Dataset Multi-Trimestral SSN */\n")
        f.write("window.INSURANCE_DATA_V2 = ")
        json.dump(master_payload, f, ensure_ascii=False)
        f.write(";\n")

    elapsed = time.time() - start_time
    print(f"=== COMPILACIÓN EXITOSA EN {elapsed:.1f}s ===")
    print(f"JSON Size: {os.path.getsize(JSON_OUTPUT):,} bytes")
    print(f"JS Size: {os.path.getsize(JS_OUTPUT):,} bytes")

if __name__ == '__main__':
    build_all_v2_datasets()
