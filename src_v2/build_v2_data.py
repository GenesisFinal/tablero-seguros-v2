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
        "parent_code": "0224",
        "description": "Sancor Seguros (Controlante VPP), Prevención ART, Prevención Retiro"
    },
    {
        "id": "federacion_patronal",
        "name": "Grupo Federación Patronal",
        "short_name": "Federación Patronal",
        "codes": ["0726", "0425"],
        "parent_code": "0726",
        "description": "Federación Patronal Seguros (Controlante VPP), Federación Patronal Retiro"
    },
    {
        "id": "provincia",
        "name": "Grupo Provincia",
        "short_name": "Provincia",
        "codes": ["0499", "0621", "0532"],
        "vpp_links": [("0499", ["0532"])],
        "description": "Provincia Seguros, Provincia ART, Provincia Vida"
    },
    {
        "id": "san_cristobal",
        "name": "Grupo San Cristóbal",
        "short_name": "San Cristóbal",
        "codes": ["0192", "0620", "0442", "0823"],
        "parent_code": "0192",
        "description": "San Cristóbal Seguros (Controlante VPP), Asociart ART, San Cristóbal Retiro, Iúnigo"
    },
    {
        "id": "la_segunda",
        "name": "Grupo Asegurador La Segunda",
        "short_name": "La Segunda",
        "codes": ["0317", "0618", "0117", "0436"],
        "parent_code": "0317",
        "description": "La Segunda Cooperativa (Controlante VPP), La Segunda ART, La Segunda Personas, La Segunda Retiro"
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
        "codes": ["0228", "0692", "0541", "0039", "0422"],
        "vpp_links": [("0228", ["0422"])],
        "description": "Zurich Argentina, Zurich Santander, Zurich International Life, Zurich Aseguradora, Zurich Retiro"
    },
    {
        "id": "experta_werthein",
        "name": "Grupo Experta / Werthein",
        "short_name": "Experta / Werthein",
        "codes": ["0880", "0616", "0419", "0433"],
        "description": "Experta Seguros, Experta ART, La Estrella Retiro, Experta Retiro"
    },
    {
        "id": "mercantil_andina",
        "name": "Grupo Mercantil Andina",
        "short_name": "Mercantil Andina",
        "codes": ["0116", "0959"],
        "parent_code": "0116",
        "description": "Mercantil Andina (Controlante VPP), Andina ART"
    },
    {
        "id": "nacion",
        "name": "Grupo Nación",
        "short_name": "Nación",
        "codes": ["0515", "0534"],
        "vpp_links": [("0515", ["0534"])],
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
        "codes": ["0025", "0589", "0516", "0443", "0426"],
        "description": "Seguros Galicia (ex Sura), Galicia Seguros, GGAL Seguros, Galicia Retiro"
    },
    {
        "id": "swiss_medical",
        "name": "Grupo Swiss Medical (SMG)",
        "short_name": "Swiss Medical (SMG)",
        "codes": ["0002", "0605", "0580", "0710", "0661"],
        "vpp_links": [("0580", ["0710", "0661"])],
        "description": "SMG Seguros, Swiss Medical ART, SMG Life, SMG Retiro, Instituto de Salta"
    },
    {
        "id": "st",
        "name": "Grupo ST",
        "short_name": "Grupo ST",
        "codes": ["0251", "0694", "0294", "0423", "0420"],
        "vpp_links": [("0423", ["0420"])],
        "description": "Life Seguros, Life Group, Orígenes Seguros, Orígenes Retiro, Genes II Retiro"
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
        "vpp_links": [("0213", ["0699"])],
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
        "codes": ["0878", "0619"],
        "description": "Galeno Seguros, Galeno ART"
    }
]

BRANCH_TAXONOMY = {
    "total_mercado": {"name": "Total del Mercado", "prefix": ""},
    "patrimoniales": {"name": "Patrimoniales Total", "prefix": "1."},
    "automotores": {"name": "Automotores y Motos", "codes": ["1.030.01", "1.030.02", "1.030.03", "1.180.01", "1.180.02", "1.180.03"]},
    "art": {"name": "Riesgos del Trabajo (ART)", "codes": ["1.050.01", "1.050.99"]},
    "agro": {"name": "Agropecuario y Forestal", "codes": ["1.070.01", "1.070.02", "1.070.99"]},
    "incendio_comb": {"name": "Incendio y Combinados", "codes": ["1.010.99", "1.020.01", "1.020.02", "1.020.99"]},
    "rc": {"name": "Responsabilidad Civil", "codes": ["1.080.01", "1.080.02", "1.080.03", "1.080.04", "1.080.05", "1.080.99"]},
    "caucion": {"name": "Caución y Créditos", "codes": ["1.100.01", "1.100.99", "1.110.01", "1.110.02", "1.110.99"]},
    "transporte": {"name": "Transporte y Cascos", "codes": ["1.040.99", "1.120.99", "1.130.01", "1.130.99", "1.140.99", "1.150.99"]},
    "otros_patrimoniales": {"name": "Otros Patrimoniales", "codes": ["1.010.99", "1.020.01", "1.020.02", "1.020.99", "1.080.01", "1.080.02", "1.080.03", "1.080.04", "1.080.05", "1.080.99", "1.100.01", "1.100.99", "1.110.01", "1.110.02", "1.110.99", "1.040.99", "1.120.99", "1.130.01", "1.130.99", "1.140.99", "1.150.99", "1.090.99", "1.160.99", "1.170.01", "1.170.02", "1.170.03", "1.170.99"]},
    "personas": {"name": "Personas Total", "prefix": "2."},
    "vida": {"name": "Seguros de Vida", "codes": ["2.030.01", "2.030.02", "2.030.03", "2.030.04", "2.030.05"]},
    "ap": {"name": "Accidentes Personales", "codes": ["2.010.01", "2.010.02"]},
    "salud": {"name": "Salud", "codes": ["2.020.01", "2.020.02"]},
    "sepelio": {"name": "Sepelio", "codes": ["2.050.01", "2.050.02"]},
    "retiro": {"name": "Seguros de Retiro", "codes": ["2.060.01", "2.060.02", "2.070.01", "2.070.02"]},
    "retiro_individual": {"name": "Retiro Individual", "codes": ["2.060.01", "2.070.01"]},
    "retiro_colectivo": {"name": "Retiro Colectivo", "codes": ["2.060.02", "2.070.02"]}
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
        
        # 1. Automotores / Motos (1.030 + 1.180, idéntico a BRANCH_TAXONOMY['automotores'] y Boletín SSN)
        if cod.startswith('1.030.') or cod.startswith('1.180.'):
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
        # 6. Accidentes Personales (2.010, idéntico a BRANCH_TAXONOMY['ap'] y Boletín SSN)
        elif cod.startswith('2.010.') or 'acc. personales' in desc:
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

    # Cuentas Oficiales de Emisión Directa y Anulaciones Directas
    cuentas_emision_directa = (
        '5.01.01.01.01.01.01', '5.01.01.01.01.01.99',
        '5.01.01.01.01.02.01', '5.01.01.01.01.02.99',
        '5.01.01.01.01.03.02', '5.01.01.01.01.03.99'
    )
    cuentas_anulaciones_directas = (
        '4.01.04.04.04.01.01', '4.01.04.04.04.01.99',
        '4.01.04.04.04.02.01', '4.01.04.04.04.02.99'
    )

    primas_sub = df_raw[df_raw['cod_cuenta'].str.startswith(cuentas_emision_directa) & (df_raw['desc_subramo'] != '') & (df_raw['desc_subramo'].notna())]
    anul_sub = df_raw[df_raw['cod_cuenta'].str.startswith(cuentas_anulaciones_directas) & (df_raw['desc_subramo'] != '') & (df_raw['desc_subramo'].notna())]

    for b_key, b_def in BRANCH_TAXONOMY.items():
        if b_key in ['total_mercado']:
            continue
        
        if 'codes' in b_def:
            sub_b = primas_sub[primas_sub['cod_subramo'].isin(b_def['codes'])]
            anul_b = anul_sub[anul_sub['cod_subramo'].isin(b_def['codes'])]
        elif 'prefix' in b_def:
            prefix = b_def['prefix']
            if b_key == 'patrimoniales':
                sub_b = primas_sub[primas_sub['cod_subramo'].str.startswith('1.') & (~primas_sub['cod_subramo'].str.startswith('1.050'))]
                anul_b = anul_sub[anul_sub['cod_subramo'].str.startswith('1.') & (~anul_sub['cod_subramo'].str.startswith('1.050'))]
            elif b_key == 'personas':
                sub_b = primas_sub[primas_sub['cod_subramo'].str.startswith('2.') & (~primas_sub['cod_subramo'].str.startswith(('2.06', '2.07', '2.08')))]
                anul_b = anul_sub[anul_sub['cod_subramo'].str.startswith('2.') & (~anul_sub['cod_subramo'].str.startswith(('2.06', '2.07', '2.08')))]
            else:
                sub_b = primas_sub[primas_sub['cod_subramo'].str.startswith(prefix)]
                anul_b = anul_sub[anul_sub['cod_subramo'].str.startswith(prefix)]
        else:
            continue

        em_agg = sub_b.groupby(['cod_cia', 'razon_social'])['importe'].sum().reset_index().rename(columns={'importe': 'emision_bruta'})
        an_agg = anul_b.groupby(['cod_cia', 'razon_social'])['importe'].sum().reset_index().rename(columns={'importe': 'anulaciones'})
        
        b_agg = pd.merge(em_agg, an_agg, on=['cod_cia', 'razon_social'], how='outer').fillna(0)
        b_agg['importe'] = b_agg['emision_bruta'] - b_agg['anulaciones']
        b_agg = b_agg[b_agg['importe'].abs() > 0.01].sort_values(by='importe', ascending=False)
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

    # 2. Macro Totals BY REAL PRODUCT LINE (SUBRAMOS PUROS CON EMISIÓN DIRECTA NETA Y SINIESTRALIDAD DEVENGADA SSN)
    cuentas_emision_directa = (
        '5.01.01.01.01.01.01', '5.01.01.01.01.01.99',
        '5.01.01.01.01.02.01', '5.01.01.01.01.02.99',
        '5.01.01.01.01.03.02', '5.01.01.01.01.03.99'
    )
    cuentas_anulaciones_directas = (
        '4.01.04.04.04.01.01', '4.01.04.04.04.01.99',
        '4.01.04.04.04.02.01', '4.01.04.04.04.02.99'
    )
    primas_sub = df_raw[df_raw['cod_cuenta'].str.startswith(cuentas_emision_directa) & (df_raw['desc_subramo'] != '') & (df_raw['desc_subramo'].notna())]
    anul_sub = df_raw[df_raw['cod_cuenta'].str.startswith(cuentas_anulaciones_directas) & (df_raw['desc_subramo'] != '') & (df_raw['desc_subramo'].notna())]

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
    a_df = anul_sub.copy()
    p_df['macro_prod'] = p_df['cod_subramo'].apply(get_macro_product)
    a_df['macro_prod'] = a_df['cod_subramo'].apply(get_macro_product)

    market_subramos = get_company_subramos(df_raw)

    tot_prod_p = float(p_df['importe'].sum()) - float(a_df['importe'].sum())
    tot_prod_dev = sum(float(s.get('primas_devengadas', 0.0)) for s in market_subramos)
    tot_prod_dev_non_ret = sum(float(s.get('primas_devengadas', 0.0)) for s in market_subramos if get_macro_product(s.get('cod_subramo', '')) != 'retiro')
    tot_prod_s = sum(float(s.get('siniestros', 0.0)) for s in market_subramos)

    macro_productos = {}
    for k in ['patrimoniales', 'art', 'personas', 'retiro']:
        em_val = float(p_df[p_df['macro_prod'] == k]['importe'].sum())
        an_val = float(a_df[a_df['macro_prod'] == k]['importe'].sum())
        p_val = em_val - an_val
        sub_k = [s for s in market_subramos if get_macro_product(s.get('cod_subramo', '')) == k]
        dev_val = sum(float(s.get('primas_devengadas', 0.0)) for s in sub_k)
        s_val = 0.0 if k == 'retiro' else sum(float(s.get('siniestros', 0.0)) for s in sub_k)
        sin_pct = 0.0 if k == 'retiro' else ((s_val / dev_val * 100.0) if dev_val > 0 else 0.0)
        part_pct = (p_val / tot_prod_p * 100.0) if tot_prod_p > 0 else 0.0

        macro_productos[k] = {
            "primas": round(p_val, 2),
            "primas_devengadas": round(dev_val, 2),
            "emision_bruta": round(em_val, 2),
            "anulaciones": round(an_val, 2),
            "siniestros": round(s_val, 2),
            "siniestralidad": round(sin_pct, 2),
            "participacion": round(part_pct, 2)
        }

    # Cross-selling breakdown for Personas (how much is sold by Mixtas vs Exclusivas - Emisión Directa Neta)
    pers_p_df = p_df[p_df['macro_prod'] == 'personas']
    pers_a_df = a_df[a_df['macro_prod'] == 'personas']
    pers_in_mixtas = float(pers_p_df[pers_p_df['tipo_entidad'] == 'Patrimoniales y Mixtas']['importe'].sum()) - float(pers_a_df[pers_a_df['tipo_entidad'] == 'Patrimoniales y Mixtas']['importe'].sum())
    pers_in_personas = float(pers_p_df[pers_p_df['tipo_entidad'] == 'Seguros de Personas']['importe'].sum()) - float(pers_a_df[pers_a_df['tipo_entidad'] == 'Seguros de Personas']['importe'].sum())
    pers_in_art = float(pers_p_df[pers_p_df['tipo_entidad'].isin(['Riesgos del Trabajo (ART)', 'Seguros de Retiro'])]['importe'].sum()) - float(pers_a_df[pers_a_df['tipo_entidad'].isin(['Riesgos del Trabajo (ART)', 'Seguros de Retiro'])]['importe'].sum())
    tot_pers_cs = pers_in_mixtas + pers_in_personas + pers_in_art

    macro_productos['personas_cross_selling'] = {
        "en_mixtas": round(pers_in_mixtas, 2),
        "en_personas": round(pers_in_personas, 2),
        "en_art": round(pers_in_art, 2),
        "pct_en_mixtas": round((pers_in_mixtas / tot_pers_cs * 100.0), 2) if tot_pers_cs > 0 else 0.0,
        "pct_en_personas": round((pers_in_personas / tot_pers_cs * 100.0), 2) if tot_pers_cs > 0 else 0.0,
        "pct_en_art": round((pers_in_art / tot_pers_cs * 100.0), 2) if tot_pers_cs > 0 else 0.0
    }

    macro_productos['total'] = {
        "primas": round(tot_prod_p, 2),
        "primas_devengadas": round(tot_prod_dev, 2),
        "siniestros": round(tot_prod_s, 2),
        "siniestralidad": round((tot_prod_s / tot_prod_dev_non_ret * 100.0), 2) if tot_prod_dev_non_ret > 0 else 0.0,
        "participacion": 100.0
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
                "x": round(max(-150.0, min(150.0, m_tec)), 2), # Margen Técnico acotado para gráfico (%)
                "y": round(max(-60.0, min(120.0, roi)), 2),     # Rendimiento Financiero acotado para gráfico (%)
                "margen_tecnico": round(m_tec, 2),
                "roi_inversiones": round(roi, 2),
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
        tot_g_resc = 0.0
        tot_g_gtos_prod = 0.0
        tot_g_gtos_expl = 0.0
        tot_g_gtos_op = 0.0
        tot_g_res_tec = 0.0
        tot_g_res_fin = 0.0
        tot_g_res_neto = 0.0
        tot_g_activo = 0.0
        tot_g_pasivo = 0.0
        tot_g_inv = 0.0
        tot_g_disp = 0.0
        tot_g_inm = 0.0
        tot_g_deudas_aseg = 0.0
        tot_g_res_sin_pend = 0.0
        tot_g_ibnr = 0.0
        tot_g_res_juicios = 0.0
        tot_g_comp_tec = 0.0
        tot_g_pn = 0.0
        grp_subramos_map = {}

        for cd in gdef['codes']:
            if cd in companies_dict:
                c = companies_dict[cd]
                members.append(c)
                tot_g_emit += float(c.get('primas_emitidas', 0.0))
                tot_g_dev += float(c.get('primas_devengadas', 0.0))
                tot_g_sin += float(c.get('siniestros', 0.0))
                tot_g_resc += float(c.get('rescates', 0.0))
                tot_g_gtos_prod += float(c.get('gtos_produccion', 0.0))
                tot_g_gtos_expl += float(c.get('gtos_explotacion', 0.0))
                tot_g_gtos_op += float(c.get('gtos_operativos', 0.0))
                tot_g_res_tec += float(c.get('resultado_tecnico', 0.0))
                tot_g_res_fin += float(c.get('resultado_financiero', 0.0))
                tot_g_res_neto += float(c.get('resultado_neto', 0.0))
                tot_g_activo += float(c.get('activo', 0.0))
                tot_g_pasivo += float(c.get('pasivo', 0.0))
                tot_g_inv += float(c.get('inversiones', 0.0))
                tot_g_disp += float(c.get('disponibilidades', 0.0))
                tot_g_inm += float(c.get('inmuebles', 0.0))
                tot_g_deudas_aseg += float(c.get('deudas_asegurados', 0.0))
                tot_g_res_sin_pend += float(c.get('reserva_siniestros_pendientes', 0.0))
                tot_g_ibnr += float(c.get('ibnr', 0.0))
                tot_g_res_juicios += float(c.get('reserva_juicios', 0.0))
                tot_g_comp_tec += float(c.get('compromisos_tecnicos', 0.0))
                tot_g_pn += float(c.get('patrimonio_neto', 0.0))
                for sr in c.get('subramos', []):
                    scod = sr.get('cod_subramo', '')
                    if scod not in grp_subramos_map:
                        grp_subramos_map[scod] = {
                            'cod_subramo': scod,
                            'desc_subramo': sr.get('desc_subramo', ''),
                            'primas': 0.0,
                            'primas_devengadas': 0.0,
                            'siniestros': 0.0
                        }
                    grp_subramos_map[scod]['primas'] += float(sr.get('primas', 0.0))
                    grp_subramos_map[scod]['primas_devengadas'] += float(sr.get('primas_devengadas', 0.0))
                    grp_subramos_map[scod]['siniestros'] += float(sr.get('siniestros', 0.0))

        if not members:
            continue

        grp_subramos_list = []
        for sr_obj in grp_subramos_map.values():
            p_sr = sr_obj['primas']
            d_sr = sr_obj['primas_devengadas']
            s_sr = sr_obj['siniestros']
            is_ret_sr = str(sr_obj['cod_subramo']).startswith(('2.06', '2.07'))
            sr_obj['primas'] = round(p_sr, 2)
            sr_obj['primas_devengadas'] = round(d_sr, 2)
            sr_obj['siniestros'] = 0.0 if is_ret_sr else round(s_sr, 2)
            sr_obj['siniestralidad_%'] = 0.0 if is_ret_sr else (round((s_sr / d_sr * 100.0), 2) if d_sr > 0 else 0.0)
            grp_subramos_list.append(sr_obj)
        grp_subramos_list.sort(key=lambda x: x['primas'], reverse=True)

        base_g_primas = tot_g_dev if tot_g_dev > 0 else (tot_g_emit if tot_g_emit > 0 else 1.0)
        # Siniestralidad Neta Devengada excluye aseguradoras exclusivas de retiro en numerador y denominador
        dev_non_ret = sum(float(m.get('primas_devengadas', 0.0)) for m in members if m.get('tipo_entidad') != 'Seguros de Retiro')
        sin_non_ret = sum(float(m.get('siniestros', 0.0)) for m in members if m.get('tipo_entidad') != 'Seguros de Retiro')
        loss_ratio = (sin_non_ret / dev_non_ret * 100.0) if dev_non_ret > 0 else 0.0
        mkt_share = (tot_g_emit / tot_emit * 100.0) if tot_emit > 0 else 0.0

        # Consolidación Patrimonial y de Resultados con Eliminación de VPP (RT 21 FACPCE / SSN)
        # En grupos con aseguradora controlante/principal (ej. La Segunda 0317, Sancor 0224, San Cristóbal 0192,
        # Federación Patronal 0726, Mercantil Andina 0116), la entidad cabecera ya registra en su Patrimonio Neto y
        # en su Resultado Financiero/Neto el Valor Patrimonial Proporcional (VPP) de las aseguradoras vinculadas.
        # Sumar los resultados netos o patrimonios netos de las vinculadas duplicaría el resultado y el capital.
        members_by_code = {m['cod_cia']: m for m in members}
        parent_code = gdef.get('parent_code')
        parent_obj = members_by_code.get(parent_code) if parent_code else None
        vpp_elim_rn = 0.0
        vpp_elim_pn = 0.0
        consolidation_method = "entidad_unica" if len(members) == 1 else "suma_horizontal"

        if parent_obj is not None and len(members) > 1 and float(parent_obj.get('acciones_grupo_economico', 0.0)) > 0:
            subsidiaries = [m for m in members if m['cod_cia'] != parent_code]
            vpp_elim_rn = sum(float(s.get('resultado_neto', 0.0)) for s in subsidiaries)
            tot_ge = sum(max(0.0, float(m.get('acciones_grupo_economico', 0.0))) for m in members)
            subs_pn = sum(max(0.0, float(s.get('patrimonio_neto', 0.0))) for s in subsidiaries)
            vpp_elim_pn = min(tot_ge, subs_pn)

            cons_res_neto = float(parent_obj.get('resultado_neto', 0.0))
            cons_pn = float(parent_obj.get('patrimonio_neto', 0.0))
            cons_res_fin = tot_g_res_fin - vpp_elim_rn
            cons_inv = max(0.0, tot_g_inv - vpp_elim_pn)
            cons_activo = max(0.0, tot_g_activo - vpp_elim_pn)
            consolidation_method = "vpp_madre"
        elif gdef.get('vpp_links') and len(members) > 1:
            for holder_cd, target_cds in gdef.get('vpp_links', []):
                if holder_cd in members_by_code:
                    targets_present = [members_by_code[tc] for tc in target_cds if tc in members_by_code]
                    ge_h = max(0.0, float(members_by_code[holder_cd].get('acciones_grupo_economico', 0.0)))
                    pn_t = sum(max(0.0, float(t.get('patrimonio_neto', 0.0))) for t in targets_present)
                    if ge_h > 0 and pn_t > 0:
                        alpha = min(1.0, ge_h / pn_t)
                        vpp_elim_pn += alpha * pn_t
                        vpp_elim_rn += alpha * sum(float(t.get('resultado_neto', 0.0)) for t in targets_present)

            cons_res_neto = tot_g_res_neto - vpp_elim_rn
            cons_pn = tot_g_pn - vpp_elim_pn
            cons_res_fin = tot_g_res_fin - vpp_elim_rn
            cons_inv = max(0.0, tot_g_inv - vpp_elim_pn)
            cons_activo = max(0.0, tot_g_activo - vpp_elim_pn)
            if abs(vpp_elim_pn) > 0.01 or abs(vpp_elim_rn) > 0.01:
                consolidation_method = "vpp_parcial"
        else:
            cons_res_neto = tot_g_res_neto
            cons_pn = tot_g_pn
            cons_res_fin = tot_g_res_fin
            cons_inv = tot_g_inv
            cons_activo = tot_g_activo

        members_summary = []
        for m in members:
            m_emit = float(m.get('primas_emitidas', 0.0))
            members_summary.append({
                "cod_cia": m['cod_cia'],
                "razon_social": m['razon_social'],
                "tipo_entidad": m['tipo_entidad'],
                "is_parent": (m['cod_cia'] == parent_code),
                "primas_emitidas": m_emit,
                "share_of_group": round((m_emit / tot_g_emit * 100.0), 1) if tot_g_emit > 0 else 0.0,
                "resultado_tecnico": float(m.get('resultado_tecnico', 0.0)),
                "resultado_neto": float(m.get('resultado_neto', 0.0)),
                "patrimonio_neto": float(m.get('patrimonio_neto', 0.0)),
                "combined_ratio": float(m.get('combined_ratio', 0.0))
            })
        members_summary.sort(key=lambda x: x['primas_emitidas'], reverse=True)

        g_m_tec = (tot_g_res_tec / base_g_primas * 100.0) if base_g_primas > 0 else 0.0
        g_roi = (cons_res_fin / cons_inv * 100.0) if cons_inv > 0 else 0.0
        g_comb = ((tot_g_sin + tot_g_resc + tot_g_gtos_op) / base_g_primas * 100.0) if base_g_primas > 0 else 100.0
        g_cob_res = ((cons_inv + tot_g_inm + tot_g_disp) / tot_g_comp_tec) if tot_g_comp_tec > 0 else 1.0
        g_roe = (cons_res_neto / cons_pn * 100.0) if cons_pn > 0 else 0.0

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
            "consolidation_method": consolidation_method,
            "parent_code": parent_code if consolidation_method == "vpp_madre" else None,
            "parent_name": parent_obj['razon_social'] if (consolidation_method == "vpp_madre" and parent_obj) else None,
            "vpp_eliminado_resultado": round(vpp_elim_rn, 2),
            "vpp_eliminado_patrimonio": round(vpp_elim_pn, 2),
            "members": members_summary,
            "primas_emitidas": round(tot_g_emit, 2),
            "primas_devengadas": round(tot_g_dev, 2),
            "siniestros": round(tot_g_sin, 2),
            "rescates": round(tot_g_resc, 2),
            "gtos_produccion": round(tot_g_gtos_prod, 2),
            "gtos_explotacion": round(tot_g_gtos_expl, 2),
            "gtos_operativos": round(tot_g_gtos_op, 2),
            "resultado_tecnico": round(tot_g_res_tec, 2),
            "resultado_financiero": round(cons_res_fin, 2),
            "resultado_neto": round(cons_res_neto, 2),
            "activo": round(cons_activo, 2),
            "pasivo": round(tot_g_pasivo, 2),
            "inversiones": round(cons_inv, 2),
            "disponibilidades": round(tot_g_disp, 2),
            "inmuebles": round(tot_g_inm, 2),
            "deudas_asegurados": round(tot_g_deudas_aseg, 2),
            "reserva_siniestros_pendientes": round(tot_g_res_sin_pend, 2),
            "ibnr": round(tot_g_ibnr, 2),
            "reserva_juicios": round(tot_g_res_juicios, 2),
            "compromisos_tecnicos": round(tot_g_comp_tec, 2),
            "patrimonio_neto": round(cons_pn, 2),
            "margen_tecnico": round(g_m_tec, 2),
            "roi_inversiones": round(g_roi, 2),
            "combined_ratio": round(g_comb, 2),
            "loss_ratio": round(loss_ratio, 2),
            "cobertura_reservas": round(g_cob_res, 2),
            "roe": round(g_roe, 2),
            "market_share": round(mkt_share, 2),
            "quadrant": g_quad,
            "quadrant_label": g_quad_label,
            "subramos": grp_subramos_list
        }

    # Strategic matrix for groups
    strategic_matrix_groups = []
    for gid, g in groups_dict.items():
        strategic_matrix_groups.append({
            "id": gid,
            "cod_cia": gid,
            "name": g['name'],
            "razon_social": g['name'],
            "short_name": g['short_name'],
            "tipo_entidad": "Grupos Aseguradores",
            "consolidation_method": g['consolidation_method'],
            "parent_code": g['parent_code'],
            "vpp_eliminado_resultado": g['vpp_eliminado_resultado'],
            "vpp_eliminado_patrimonio": g['vpp_eliminado_patrimonio'],
            "x": round(max(-150.0, min(150.0, g['margen_tecnico'])), 2),
            "y": round(max(-60.0, min(120.0, g['roi_inversiones'])), 2),
            "margen_tecnico": g['margen_tecnico'],
            "roi_inversiones": g['roi_inversiones'],
            "primas_devengadas": g['primas_devengadas'],
            "primas_emitidas": g['primas_emitidas'],
            "siniestros": g['siniestros'],
            "resultado_tecnico": g['resultado_tecnico'],
            "resultado_financiero": g['resultado_financiero'],
            "resultado_neto": g['resultado_neto'],
            "activo": g['activo'],
            "pasivo": g['pasivo'],
            "inversiones": g['inversiones'],
            "deudas_asegurados": g['deudas_asegurados'],
            "reserva_siniestros_pendientes": g['reserva_siniestros_pendientes'],
            "ibnr": g['ibnr'],
            "reserva_juicios": g['reserva_juicios'],
            "compromisos_tecnicos": g['compromisos_tecnicos'],
            "patrimonio_neto": g['patrimonio_neto'],
            "loss_ratio": g['loss_ratio'],
            "combined_ratio": g['combined_ratio'],
            "cobertura_reservas": g['cobertura_reservas'],
            "roe": g['roe'],
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
                "rescates": 0.0,
                "gtos_operativos": 0.0,
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
        s["rescates"] += float(c.get('rescates', 0.0))
        s["gtos_operativos"] += float(c.get('gtos_operativos', 0.0))
        s["resultado_tecnico"] += float(c.get('resultado_tecnico', 0.0))
        s["resultado_financiero"] += float(c.get('resultado_financiero', 0.0))
        s["resultado_neto"] += float(c.get('resultado_neto', 0.0))
        s["inversiones"] += float(c.get('inversiones', 0.0))
        s["activo"] += float(c.get('activo', 0.0))
        s["patrimonio_neto"] += float(c.get('patrimonio_neto', 0.0))

    strategic_matrix_segments = []
    for tipo, s in segments_agg.items():
        base_s_primas = s["primas_devengadas"] if s["primas_devengadas"] > 0 else (s["primas_emitidas"] if s["primas_emitidas"] > 0 else 1.0)
        m_tec = (s["resultado_tecnico"] / base_s_primas * 100.0) if base_s_primas > 0 else 0.0
        roi = (s["resultado_financiero"] / s["inversiones"] * 100.0) if s["inversiones"] > 0 else 0.0
        loss_r = 0.0 if tipo == 'Seguros de Retiro' else ((s["siniestros"] / base_s_primas * 100.0) if base_s_primas > 0 else 0.0)
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

        comb = ((s["siniestros"] + s["rescates"] + s["gtos_operativos"]) / base_s_primas * 100.0) if base_s_primas > 0 else 100.0

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
            "siniestros": round(s["siniestros"], 2),
            "rescates": round(s["rescates"], 2),
            "gtos_operativos": round(s["gtos_operativos"], 2),
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

    # 6. Market investments
    market_investments = get_company_investments_breakdown(df_raw)

    # 7. La Segunda Group Details
    ls_group = groups_dict.get('la_segunda', {})
    ls_details = {
        "tot_grupo": ls_group.get('primas_emitidas', 0.0),
        "share_mercado": ls_group.get('market_share', 0.0),
        "companies": [c for c in companies_dict.values() if c['cod_cia'] in ["0317", "0618", "0117", "0436"]]
    }

    # 8. Retiro Full Suite Details (Compromisos Técnicos, Primas Colectivo/Individual, Asegurados)
    retiro_details = compute_retiro_details_for_df(df_raw, df_summary, period_code)

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
        "groups_by_id": groups_dict,
        "rankings": rankings,
        "market_investments": market_investments,
        "market_subramos": market_subramos,
        "la_segunda": ls_details,
        "retiro_details": retiro_details
    }


_ASEGURADOS_CACHE = None

def _load_retiro_asegurados_cache():
    global _ASEGURADOS_CACHE
    if _ASEGURADOS_CACHE is not None:
        return _ASEGURADOS_CACHE

    cache_file = os.path.join(BASE_DIR, ".cache", "retiro_asegurados_by_period.json")
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    cached = {}
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached = json.load(f)
        except Exception:
            cached = {}

    import io, re, zipfile, requests, urllib3
    urllib3.disable_warnings()

    period_urls = {
        "2024-3": ("Septiembre 2024", "https://www.argentina.gob.ar/sites/default/files/ssn_2024_sep_reserva_matematica.xlsx"),
        "2024-4": ("Diciembre 2024", "https://www.argentina.gob.ar/sites/default/files/ssn_2024_dic_reserva_matematica.xlsx"),
        "2025-1": ("Marzo 2025", "https://www.argentina.gob.ar/sites/default/files/ssn_2025_mar_reserva_matematica.xlsx"),
        "2025-2": ("Junio 2025", "https://www.argentina.gob.ar/sites/default/files/ssn_202506_reserva_matematica.xlsx"),
        "2025-3": ("Septiembre 2025", "https://www.argentina.gob.ar/sites/default/files/ssn_202509_reserva_matematica.xlsx"),
        "2025-4": ("Diciembre 2025", "https://www.argentina.gob.ar/sites/default/files/ssn_202512_reserva_matematica.xlsx"),
        "2026-1": ("Marzo 2026", "https://www.argentina.gob.ar/sites/default/files/ssn_202603_reserva_matematica.xlsx"),
        "2026-2": ("Junio 2026", "https://www.argentina.gob.ar/sites/default/files/ssn_202606_reserva_matematica.xlsx"),
        "2026-3": ("Septiembre 2026", "https://www.argentina.gob.ar/sites/default/files/ssn_202609_reserva_matematica.xlsx"),
    }

    updated = False
    for p_key, (p_lbl, url) in period_urls.items():
        if p_key in cached and cached[p_key].get("asegurados"):
            continue
        try:
            r = requests.get(url, verify=False, timeout=20)
            if r.status_code != 200 or len(r.content) < 5000:
                continue
            fixed_zip = io.BytesIO()
            with zipfile.ZipFile(io.BytesIO(r.content), 'r') as zin:
                with zipfile.ZipFile(fixed_zip, 'w') as zout:
                    for item in zin.infolist():
                        c = zin.read(item.filename)
                        if item.filename.endswith(('.xml', '.rels')):
                            c = c.replace(b'http://purl.oclc.org/ooxml/spreadsheetml/main', b'http://schemas.openxmlformats.org/spreadsheetml/2006/main')
                            c = c.replace(b'http://purl.oclc.org/ooxml/officeDocument/relationships', b'http://schemas.openxmlformats.org/officeDocument/2006/relationships')
                        zout.writestr(item, c)
            fixed_zip.seek(0)
            xls = pd.read_excel(fixed_zip, sheet_name=None, header=None)

            def get_cols(df):
                for col_idx in [0, 1]:
                    vals = df.iloc[:, col_idx].astype(str).str.strip().str.upper().tolist()
                    if 'TOTAL' in vals or 'SUBTOTAL' in vals:
                        return col_idx, col_idx + 1
                return 0, 1

            results = {}
            def ensure_ent(ent):
                ent_c = re.sub(r'\(\d+\)$', '', str(ent).strip().upper()).strip()
                if ent_c not in results:
                    results[ent_c] = {'entidad': ent_c, 'ahorro_indiv': 0, 'ahorro_colec': 0, 'renta_indiv': 0, 'renta_colec': 0, 'rvp': 0, 'art': 0}
                return ent_c

            def parse_stacked(sheet_name, k_ind, k_col):
                df_s = xls.get(sheet_name)
                if df_s is None:
                    return
                ent_col, val_col = get_cols(df_s)
                sub_idxs = df_s[df_s.iloc[:, ent_col].astype(str).str.strip().str.upper() == 'SUBTOTAL'].index.tolist()
                if len(sub_idxs) >= 2:
                    for idx in range(sub_idxs[0] + 1, sub_idxs[1]):
                        raw_ent = df_s.iloc[idx, ent_col]
                        if pd.isna(raw_ent) or str(raw_ent).strip().startswith(('*', '(')):
                            continue
                        ent_c = ensure_ent(raw_ent)
                        v = pd.to_numeric(df_s.iloc[idx, val_col], errors='coerce')
                        results[ent_c][k_ind] = int(round(v)) if not pd.isna(v) else 0
                    for idx in range(sub_idxs[1] + 1, len(df_s)):
                        raw_ent = df_s.iloc[idx, ent_col]
                        if pd.isna(raw_ent) or str(raw_ent).strip().startswith(('*', '(')):
                            continue
                        ent_c = ensure_ent(raw_ent)
                        v = pd.to_numeric(df_s.iloc[idx, val_col], errors='coerce')
                        results[ent_c][k_col] = int(round(v)) if not pd.isna(v) else 0

            def parse_simple(sheet_names, k_val):
                df_s = None
                for sn in sheet_names:
                    if sn in xls:
                        df_s = xls[sn]
                        break
                if df_s is None:
                    return
                ent_col, val_col = get_cols(df_s)
                tot_idxs = df_s[df_s.iloc[:, ent_col].astype(str).str.strip().str.upper() == 'TOTAL'].index.tolist()
                if not tot_idxs:
                    return
                for idx in range(tot_idxs[0] + 1, len(df_s)):
                    raw_ent = df_s.iloc[idx, ent_col]
                    if pd.isna(raw_ent) or str(raw_ent).strip().startswith(('*', '(')):
                        continue
                    ent_c = ensure_ent(raw_ent)
                    v = pd.to_numeric(df_s.iloc[idx, val_col], errors='coerce')
                    results[ent_c][k_val] = int(round(v)) if not pd.isna(v) else 0

            parse_stacked('3 Aseg.  Indiv y  Colec', 'ahorro_indiv', 'ahorro_colec')
            parse_stacked('4 Rentistas Indiv y Colec', 'renta_indiv', 'renta_colec')
            parse_simple(['5 Rentistas Previsional'], 'rvp')
            parse_simple(['6 Rentistas ART ', '6 Rentistas ART'], 'art')

            aseg_list = []
            for ent_c, d in results.items():
                ah_tot = d['ahorro_indiv'] + d['ahorro_colec']
                re_vol = d['renta_indiv'] + d['renta_colec']
                rvp_art = d['rvp'] + d['art']
                re_tot = re_vol + rvp_art
                tot_v = ah_tot + re_tot
                if tot_v > 0:
                    aseg_list.append({
                        "entidad": ent_c,
                        "total_asegurados": tot_v,
                        "ahorro_total": ah_tot,
                        "ahorro_indiv": d['ahorro_indiv'],
                        "ahorro_colec": d['ahorro_colec'],
                        "renta_total": re_tot,
                        "renta_indiv": d['renta_indiv'],
                        "renta_colec": d['renta_colec'],
                        "rvp_art": rvp_art
                    })
            aseg_list.sort(key=lambda x: x["total_asegurados"], reverse=True)
            if aseg_list:
                tot_row = {
                    "entidad": "TOTAL MERCADO",
                    "total_asegurados": sum(x["total_asegurados"] for x in aseg_list),
                    "ahorro_total": sum(x["ahorro_total"] for x in aseg_list),
                    "ahorro_indiv": sum(x["ahorro_indiv"] for x in aseg_list),
                    "ahorro_colec": sum(x["ahorro_colec"] for x in aseg_list),
                    "renta_total": sum(x["renta_total"] for x in aseg_list),
                    "renta_indiv": sum(x["renta_indiv"] for x in aseg_list),
                    "renta_colec": sum(x["renta_colec"] for x in aseg_list),
                    "rvp_art": sum(x["rvp_art"] for x in aseg_list)
                }
                cached[p_key] = {
                    "periodo": p_lbl,
                    "asegurados": aseg_list,
                    "asegurados_total_row": tot_row
                }
                updated = True
                print(f"[SSN Retiro Asegurados] Cached {p_key} ({p_lbl}): {tot_row['total_asegurados']:,} vidas")
        except Exception as e:
            print(f"[SSN Retiro Asegurados] Note for {p_key}: {e}")

    if updated:
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cached, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    _ASEGURADOS_CACHE = cached
    return cached


def compute_retiro_details_for_df(df_raw, df_summary, period_code):
    """
    Calcula directamente de la base .mdb del período:
    1. Compromisos Técnicos y Reservas Matemáticas (en miles de pesos, idéntico al Cuadro 1 de SSN).
    2. Primas Emitidas de Retiro desglosadas en Retiro Colectivo vs Retiro Individual (en pesos).
    3. Población de Asegurados (del boletín de Reserva Matemática del período o el más cercano disponible).
    """
    ret_cias = df_summary[df_summary['tipo_entidad'] == 'Seguros de Retiro'][['cod_cia', 'razon_social']].drop_duplicates()

    # 1. Compromisos Técnicos y Reservas Matemáticas (Cuentas 2.02.02.02.03.*)
    comp_rows = []
    for _, c in ret_cias.iterrows():
        cod = c['cod_cia']
        name = c['razon_social']
        sub = df_raw[(df_raw['cod_cia'] == cod) & (df_raw['cod_subramo'] != '') & (df_raw['cod_subramo'].notna())]

        ah_ind = float(sub[(sub['cod_cuenta'] == '2.02.02.02.03.01.00.00') & (sub['cod_subramo'] == '2.060.01')]['importe'].sum()) / 1000.0
        ah_col = float(sub[(sub['cod_cuenta'] == '2.02.02.02.03.01.00.00') & (sub['cod_subramo'] == '2.060.02')]['importe'].sum()) / 1000.0
        ah_tot = ah_ind + ah_col

        re_ind = float(sub[(sub['cod_cuenta'] == '2.02.02.02.03.04.00.00') & (sub['cod_subramo'] == '2.060.01')]['importe'].sum()) / 1000.0
        re_col = float(sub[(sub['cod_cuenta'] == '2.02.02.02.03.04.00.00') & (sub['cod_subramo'] == '2.060.02')]['importe'].sum()) / 1000.0
        re_tot = re_ind + re_col

        rvp_art = float(sub[sub['cod_cuenta'].isin([
            '2.02.02.02.03.03.00.00', '2.02.02.02.03.05.00.00', '2.02.02.02.03.06.00.00',
            '2.02.02.02.03.20.00.00', '2.02.02.02.03.21.00.00', '2.02.02.02.03.22.00.00'
        ])]['importe'].sum()) / 1000.0

        tot_rm = float(df_raw[(df_raw['cod_cia'] == cod) & (df_raw['cod_cuenta'] == '2.02.02.02.03.00.00.00') & (df_raw['cod_subramo'] == '')]['importe'].sum()) / 1000.0
        if tot_rm <= 0:
            otros_sub = float(sub[sub['cod_cuenta'].isin([
                '2.02.02.02.03.23.00.00', '2.02.02.02.03.24.00.00', '2.02.02.02.03.26.00.00',
                '2.02.02.02.03.30.00.00', '2.02.02.02.03.31.00.00', '2.02.02.02.03.32.00.00',
                '2.02.02.02.03.40.00.00', '2.02.02.02.03.50.00.00'
            ])]['importe'].sum()) / 1000.0
            otros = otros_sub
            tot_rm = ah_tot + re_tot + rvp_art + otros
        else:
            otros = tot_rm - (ah_tot + re_tot + rvp_art)

        if tot_rm > 0:
            comp_rows.append({
                "cod_cia": cod,
                "entidad": name,
                "total": round(tot_rm, 2),
                "ahorro_total": round(ah_tot, 2),
                "ahorro_indiv": round(ah_ind, 2),
                "ahorro_colec": round(ah_col, 2),
                "rentas_total": round(re_tot, 2),
                "rentas_indiv": round(re_ind, 2),
                "rentas_colec": round(re_col, 2),
                "rvp_art": round(rvp_art, 2),
                "otros": round(otros, 2)
            })

    comp_rows.sort(key=lambda x: x["total"], reverse=True)
    tot_comp_all = sum(x["total"] for x in comp_rows)
    tot_ah_all = sum(x["ahorro_total"] for x in comp_rows)
    tot_re_all = sum(x["rentas_total"] for x in comp_rows)

    for r in comp_rows:
        r["total_pct"] = round((r["total"] / tot_comp_all * 100.0), 2) if tot_comp_all > 0 else 0.0
        r["ahorro_pct"] = round((r["ahorro_total"] / tot_ah_all * 100.0), 2) if tot_ah_all > 0 else 0.0
        r["rentas_pct"] = round((r["rentas_total"] / tot_re_all * 100.0), 2) if tot_re_all > 0 else 0.0

    comp_total_row = {
        "entidad": "TOTAL MERCADO",
        "total": round(tot_comp_all, 2),
        "total_pct": 100.0,
        "ahorro_total": round(tot_ah_all, 2),
        "ahorro_pct": 100.0 if tot_ah_all > 0 else 0.0,
        "ahorro_indiv": round(sum(x["ahorro_indiv"] for x in comp_rows), 2),
        "ahorro_colec": round(sum(x["ahorro_colec"] for x in comp_rows), 2),
        "rentas_total": round(tot_re_all, 2),
        "rentas_pct": 100.0 if tot_re_all > 0 else 0.0,
        "rentas_indiv": round(sum(x["rentas_indiv"] for x in comp_rows), 2),
        "rentas_colec": round(sum(x["rentas_colec"] for x in comp_rows), 2),
        "rvp_art": round(sum(x["rvp_art"] for x in comp_rows), 2),
        "otros": round(sum(x["otros"] for x in comp_rows), 2)
    }

    # 2. Primas Emitidas de Retiro (Colectivo vs Individual)
    cuentas_emision_directa = (
        '5.01.01.01.01.01.01', '5.01.01.01.01.01.99',
        '5.01.01.01.01.02.01', '5.01.01.01.01.02.99',
        '5.01.01.01.01.03.02', '5.01.01.01.01.03.99'
    )
    cuentas_anulaciones_directas = (
        '4.01.04.04.04.01.01', '4.01.04.04.04.01.99',
        '4.01.04.04.04.02.01', '4.01.04.04.04.02.99'
    )
    ret_sub = df_raw[df_raw['cod_subramo'].isin(['2.060.01', '2.060.02', '2.070.01', '2.070.02'])]
    em_ret = ret_sub[ret_sub['cod_cuenta'].str.startswith(cuentas_emision_directa)].groupby(['cod_cia', 'razon_social', 'cod_subramo'])['importe'].sum().unstack(fill_value=0.0)
    an_ret = ret_sub[ret_sub['cod_cuenta'].str.startswith(cuentas_anulaciones_directas)].groupby(['cod_cia', 'razon_social', 'cod_subramo'])['importe'].sum().unstack(fill_value=0.0)
    net_ret = em_ret.subtract(an_ret, fill_value=0.0)

    primas_rows = []
    for (cod, name), row_s in net_ret.iterrows():
        p_ind = float(row_s.get('2.060.01', 0.0)) + float(row_s.get('2.070.01', 0.0))
        p_col = float(row_s.get('2.060.02', 0.0)) + float(row_s.get('2.070.02', 0.0))
        p_tot = p_ind + p_col
        if abs(p_tot) > 0.01 or abs(p_ind) > 0.01 or abs(p_col) > 0.01:
            primas_rows.append({
                "cod_cia": cod,
                "entidad": name,
                "primas_total": round(p_tot, 2),
                "primas_colectivo": round(p_col, 2),
                "primas_individual": round(p_ind, 2)
            })

    primas_rows.sort(key=lambda x: x["primas_total"], reverse=True)
    tot_p_all = sum(x["primas_total"] for x in primas_rows)
    tot_p_col = sum(x["primas_colectivo"] for x in primas_rows)
    tot_p_ind = sum(x["primas_individual"] for x in primas_rows)

    for idx, r in enumerate(primas_rows, 1):
        r["rank_total"] = idx
        r["total_pct"] = round((r["primas_total"] / tot_p_all * 100.0), 2) if tot_p_all > 0 else 0.0
        r["colectivo_pct"] = round((r["primas_colectivo"] / tot_p_col * 100.0), 2) if tot_p_col > 0 else 0.0
        r["individual_pct"] = round((r["primas_individual"] / tot_p_ind * 100.0), 2) if tot_p_ind > 0 else 0.0

    primas_total_row = {
        "entidad": "TOTAL MERCADO",
        "primas_total": round(tot_p_all, 2),
        "total_pct": 100.0,
        "primas_colectivo": round(tot_p_col, 2),
        "colectivo_pct": 100.0 if tot_p_col > 0 else 0.0,
        "mix_colectivo_pct": round((tot_p_col / tot_p_all * 100.0), 2) if tot_p_all > 0 else 0.0,
        "primas_individual": round(tot_p_ind, 2),
        "individual_pct": 100.0 if tot_p_ind > 0 else 0.0,
        "mix_individual_pct": round((tot_p_ind / tot_p_all * 100.0), 2) if tot_p_all > 0 else 0.0
    }

    # 3. Asegurados
    aseg_cache = _load_retiro_asegurados_cache()
    aseg_entry = aseg_cache.get(period_code)
    if not aseg_entry and aseg_cache:
        # Use closest available prior period or earliest available
        avail_k = sorted(aseg_cache.keys())
        prior_k = [k for k in avail_k if k <= period_code]
        chosen_k = prior_k[-1] if prior_k else avail_k[0]
        aseg_entry = aseg_cache[chosen_k]

    return {
        "periodo": get_period_label(period_code),
        "compromisos_tecnicos": comp_rows,
        "compromisos_total_row": comp_total_row,
        "primas_emitidas": primas_rows,
        "primas_emitidas_total_row": primas_total_row,
        "asegurados": aseg_entry.get("asegurados", []) if aseg_entry else [],
        "asegurados_total_row": aseg_entry.get("asegurados_total_row", {}) if aseg_entry else {},
        "asegurados_periodo": aseg_entry.get("periodo", "Junio 2026") if aseg_entry else "Junio 2026"
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
            "mdb_accounting": f"Bases de Balances SSN (SINENSUP Oficial) - {len(periods)} Trimestres ({periods[0]} a {periods[-1]})" if periods else "Bases de Balances SSN (SINENSUP Oficial)",
            "monthly_flash": "Boletín Estadístico SSN - Serie de Producción Mensual Provisoria",
            "retiro_vidas": "Boletín Estadístico SSN - Seguros de Retiro (Cantidad de Vidas Físicas)"
        }
    }

    # Índice IPC Nivel General Nacional Oficial INDEC (Base Dic 2016 = 100)
    PERIOD_IPC = {
        "2021-2": 483.6049,   # 30-06-2021 (12M Cierre 20/21)
        "2021-3": 528.4968,   # 30-09-2021 (3M 21/22)
        "2021-4": 582.4575,   # 31-12-2021 (6M 21/22)
        "2022-1": 676.0566,   # 31-03-2022 (9M 21/22)
        "2022-2": 793.0278,   # 30-06-2022 (12M Cierre 21/22)
        "2022-3": 967.3076,   # 30-09-2022 (3M 22/23)
        "2022-4": 1134.5875,  # 31-12-2022 (6M 22/23)
        "2023-1": 1381.1601,  # 31-03-2023 (9M 22/23)
        "2023-2": 1709.6115,  # 30-06-2023 (12M Cierre 22/23)
        "2023-3": 2304.9242,  # 30-09-2023 (3M 23/24)
        "2023-4": 3533.1922,  # 31-12-2023 (6M 23/24)
        "2024-1": 5357.0929,  # 31-03-2024 (9M 23/24)
        "2024-2": 6351.7145,  # 30-06-2024 (12M Cierre 23/24)
        "2024-3": 7122.2421,  # 30-09-2024 (3M 24/25)
        "2024-4": 7694.0075,  # 31-12-2024 (6M 24/25)
        "2025-1": 8353.3158,  # 31-03-2025 (9M 24/25)
        "2025-2": 8855.5681,  # 30-06-2025 (12M Cierre 24/25)
        "2025-3": 9384.0922,  # 30-09-2025 (3M 25/26)
        "2025-4": 10121.3715, # 31-12-2025 (6M 25/26)
        "2026-1": 11077.0608, # 31-03-2026 (9M 25/26)
        "2026-2": 11826.4103, # 30-06-2026 (12M Cierre 25/26)
        "2026-3": 12514.1508  # 30-09-2026 (3M 26/27)
    }
    # Consulta automática a la API oficial de Series de Tiempo de la República Argentina (INDEC)
    # para incorporar automáticamente cualquier trimestre futuro publicado (ej. 2026-4, 2027-1, etc.)
    try:
        import requests
        r_ipc = requests.get(
            "https://apis.datos.gob.ar/series/api/series/?ids=148.3_INIVELNAL_DICI_M_26&start_date=2021-06-01&limit=240",
            timeout=10
        )
        if r_ipc.status_code == 200:
            month_to_q = {"03": "1", "06": "2", "09": "3", "12": "4"}
            for dt_str, ipc_val in r_ipc.json().get("data", []):
                if ipc_val is not None and len(dt_str) >= 7:
                    yr_s, mo_s = dt_str[:4], dt_str[5:7]
                    if mo_s in month_to_q:
                        PERIOD_IPC[f"{yr_s}-{month_to_q[mo_s]}"] = round(float(ipc_val), 4)
    except Exception as e_ipc:
        print(f"[IPC INDEC] Usando serie oficial local de respaldo ({e_ipc})")

    last_known_ipc = 12514.1508
    for p in periods:
        if p in PERIOD_IPC:
            last_known_ipc = PERIOD_IPC[p]
        else:
            last_known_ipc = round(last_known_ipc * 1.06, 4)
            PERIOD_IPC[p] = last_known_ipc

    if os.path.exists(old_dataset_path):
        try:
            with open(old_dataset_path, "r", encoding="utf-8") as f:
                old_d = json.load(f)
                supplementary_data["monthly_flash_series"] = old_d.get("ssn_produccion_mensual", {})
        except Exception as e:
            print(f"Warning reading old supplementary data: {e}")

    latest_period = periods[-1] if periods else "2026-3"
    latest_ipc = PERIOD_IPC.get(latest_period, 12514.1508)

    if latest_period in periods_data and "retiro_details" in periods_data[latest_period]:
        rd = periods_data[latest_period]["retiro_details"]
        supplementary_data["ssn_seg_retiro"] = rd
        supplementary_data["retiro_vidas_stats"] = rd.get("asegurados", [])
        supplementary_data["retiro_vidas_total_row"] = rd.get("asegurados_total_row", {})
        supplementary_data["retiro_compromisos"] = rd.get("compromisos_tecnicos", [])
        supplementary_data["retiro_compromisos_total_row"] = rd.get("compromisos_total_row", {})
        supplementary_data["retiro_primas_desglose"] = rd.get("primas_emitidas", [])
        supplementary_data["retiro_primas_total_row"] = rd.get("primas_emitidas_total_row", {})
        supplementary_data["retiro_periodo"] = rd.get("periodo", get_period_label(latest_period))

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
        json.dump(master_payload, f, ensure_ascii=False, separators=(",", ":"))

    # Save to JS for standalone distribution
    print(f"Saving {JS_OUTPUT}...")
    with open(JS_OUTPUT, "w", encoding="utf-8") as f:
        f.write("/* Tablero de Seguros v2 - Dataset Multi-Trimestral SSN */\n")
        f.write("window.INSURANCE_DATA_V2 = ")
        json.dump(master_payload, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")

    elapsed = time.time() - start_time
    print(f"=== COMPILACIÓN EXITOSA EN {elapsed:.1f}s ===")
    print(f"JSON Size: {os.path.getsize(JSON_OUTPUT):,} bytes")
    print(f"JS Size: {os.path.getsize(JS_OUTPUT):,} bytes")

if __name__ == '__main__':
    build_all_v2_datasets()
