import pandas as pd
import numpy as np

def get_account_value(df_cia, account_code_prefix, exact=False):
    """Safely retrieves the sum of imports for a given account code pattern."""
    if df_cia.empty:
        return 0.0
    if exact:
        sub = df_cia[df_cia['cod_cuenta'] == account_code_prefix]
    else:
        sub = df_cia[df_cia['cod_cuenta'].str.startswith(account_code_prefix)]
    if sub.empty:
        return 0.0
    return float(sub['importe'].sum())

def compute_all_companies_summary(df):
    """
    Computes standard SSN financial and technical KPIs for all companies.
    Values are in ARS (Pesos Homogéneos / Corrientes según el período).
    """
    companies = df[['cod_cia', 'razon_social', 'tipo_entidad']].drop_duplicates()
    records = []

    for _, cia in companies.iterrows():
        cod = cia['cod_cia']
        df_c = df[df['cod_cia'] == cod]

        # ----------------------------------------------------
        # 1. BALANCE PATRIMONIAL
        # ----------------------------------------------------
        activo_tot = get_account_value(df_c, '1.00.00.00.00.00.00.00', exact=True)
        disp = get_account_value(df_c, '1.01.00.00.00.00.00.00', exact=True)
        inv = get_account_value(df_c, '1.02.00.00.00.00.00.00', exact=True)
        cred = get_account_value(df_c, '1.03.00.00.00.00.00.00', exact=True)
        inm = get_account_value(df_c, '1.04.00.00.00.00.00.00', exact=True)
        bienes_uso = get_account_value(df_c, '1.05.00.00.00.00.00.00', exact=True)
        otros_act = get_account_value(df_c, '1.06.00.00.00.00.00.00', exact=True)

        pasivo_tot = get_account_value(df_c, '2.00.00.00.00.00.00.00', exact=True)
        deudas = get_account_value(df_c, '2.01.00.00.00.00.00.00', exact=True)
        comp_tec_pasivo = get_account_value(df_c, '2.02.00.00.00.00.00.00', exact=True)
        prev = get_account_value(df_c, '2.03.00.00.00.00.00.00', exact=True)
        pn = get_account_value(df_c, '3.00.00.00.00.00.00.00', exact=True)

        # ----------------------------------------------------
        # 2. ESTADO DE RESULTADOS OFICIAL (SSN)
        # ----------------------------------------------------
        tipo_entidad = cia['tipo_entidad']
        is_retiro = (tipo_entidad == 'Seguros de Retiro')

        # Paso 1: Primas y Recargos Emitidos
        primas_emit = get_account_value(df_c, '5.01.01.00.00.00.00.00', exact=True)

        # Paso 2: Cesiones y Anulaciones
        primas_cedidas = get_account_value(df_c, '4.01.03.00.00.00.00.00', exact=True)
        anulaciones = get_account_value(df_c, '4.01.04.00.00.00.00.00', exact=True)
        cesiones_anul = primas_cedidas + anulaciones

        # Paso 3: Variación Neta de Compromisos Técnicos / Reservas Matemáticas
        if is_retiro:
            var_reservas_cargo = get_account_value(df_c, '4.01.05.00.00.00.00.00', exact=True)
            var_reservas_liberacion = get_account_value(df_c, '5.01.04.04.04.12.00.00', exact=True)
            var_comp_tec = var_reservas_cargo - var_reservas_liberacion
        else:
            var_riesgos_cargo = get_account_value(df_c, '4.01.05.00.00.00.00.00', exact=True)
            var_riesgos_lib = (
                get_account_value(df_c, '5.01.04.04.04.11.00.00', exact=True) +
                get_account_value(df_c, '5.01.04.04.04.12.00.00', exact=True) +
                get_account_value(df_c, '5.01.04.04.04.13.00.00', exact=True)
            )
            if var_riesgos_lib == 0:
                var_riesgos_lib = (
                    get_account_value(df_c, '5.01.04.04.04.11', exact=False) +
                    get_account_value(df_c, '5.01.04.04.04.12', exact=False) +
                    get_account_value(df_c, '5.01.04.04.04.13', exact=False)
                )
            var_comp_tec = var_riesgos_cargo - var_riesgos_lib

        # Primas Devengadas Técnicas
        primas_dev = primas_emit - cesiones_anul - var_comp_tec

        # Paso 4: Siniestros Devengados Netos
        if is_retiro:
            siniestros_dev = 0.0
        else:
            siniestros_cargo = get_account_value(df_c, '4.01.01.00.00.00.00.00', exact=True)
            recup_sin = (
                get_account_value(df_c, '5.01.04.04.04.01.00.00', exact=True) +
                get_account_value(df_c, '5.01.04.04.04.06.00.00', exact=True) +
                get_account_value(df_c, '5.01.04.04.04.07.00.00', exact=True) +
                get_account_value(df_c, '5.01.04.04.04.08.00.00', exact=True) +
                get_account_value(df_c, '5.01.04.04.04.09.00.00', exact=True) +
                get_account_value(df_c, '5.01.04.04.04.10.00.00', exact=True) +
                get_account_value(df_c, '5.01.04.04.04.14.00.00', exact=True) +
                get_account_value(df_c, '5.01.04.04.04.15.00.00', exact=True) +
                get_account_value(df_c, '5.01.04.04.04.16.00.00', exact=True) +
                get_account_value(df_c, '5.01.04.04.04.17.00.00', exact=True) +
                get_account_value(df_c, '5.01.04.04.04.20.00.00', exact=True)
            )
            if recup_sin == 0:
                recup_sin = (
                    get_account_value(df_c, '5.01.04.04.04.01', exact=False) +
                    get_account_value(df_c, '5.01.04.04.04.06', exact=False) +
                    get_account_value(df_c, '5.01.04.04.04.07', exact=False) +
                    get_account_value(df_c, '5.01.04.04.04.08', exact=False) +
                    get_account_value(df_c, '5.01.04.04.04.09', exact=False) +
                    get_account_value(df_c, '5.01.04.04.04.10', exact=False) +
                    get_account_value(df_c, '5.01.04.04.04.14', exact=False) +
                    get_account_value(df_c, '5.01.04.04.04.15', exact=False) +
                    get_account_value(df_c, '5.01.04.04.04.16', exact=False) +
                    get_account_value(df_c, '5.01.04.04.04.17', exact=False) +
                    get_account_value(df_c, '5.01.04.04.04.20', exact=False)
                )
            siniestros_dev = max(0.0, siniestros_cargo - recup_sin)

        # Paso 5: Rescates y Rentas
        rescates = get_account_value(df_c, '4.01.02.00.00.00.00.00', exact=True)

        # Paso 6: Gastos de Producción y Explotación
        gtos_prod_cargo = get_account_value(df_c, '4.01.06.00.00.00.00.00', exact=True)
        recup_gtos_prod = get_account_value(df_c, '5.01.03.00.00.00.00.00', exact=True)
        gtos_prod = max(0.0, gtos_prod_cargo - recup_gtos_prod)

        gtos_expl = get_account_value(df_c, '4.01.07.00.00.00.00.00', exact=True)
        gtos_operativos = gtos_prod + gtos_expl

        # Paso 7: Otros Ingresos y Egresos Técnicos
        otros_ing_tec = get_account_value(df_c, '5.01.05.00.00.00.00.00', exact=True)
        otros_egr_tec = get_account_value(df_c, '4.01.50.00.00.00.00.00', exact=True)

        # Resultados Oficiales
        res_tec = get_account_value(df_c, '5.01.00.00.00.00.00.00', exact=True) - get_account_value(df_c, '4.01.00.00.00.00.00.00', exact=True)
        gan_fin = get_account_value(df_c, '5.02.00.00.00.00.00.00', exact=True)
        perd_fin = get_account_value(df_c, '4.02.00.00.00.00.00.00', exact=True)
        res_fin = gan_fin - perd_fin
        imp_gan = get_account_value(df_c, '4.05.00.00.00.00.00.00', exact=True)

        gan_tot = get_account_value(df_c, '5.00.00.00.00.00.00.00', exact=True)
        perd_tot = get_account_value(df_c, '4.00.00.00.00.00.00.00', exact=True)
        res_neto = gan_tot - perd_tot

        # ----------------------------------------------------
        # 3. RATIOS TÉCNICOS & FINANCIEROS
        # ----------------------------------------------------
        base_primas = primas_dev if primas_dev > 0 else (primas_emit if primas_emit > 0 else 1.0)
        
        costo_prestacional = siniestros_dev + rescates
        loss_ratio = (costo_prestacional / base_primas) * 100.0 if base_primas > 0 else 0.0
        rescates_ratio = (rescates / base_primas) * 100.0 if base_primas > 0 else 0.0
        comm_ratio = (gtos_prod / base_primas) * 100.0 if base_primas > 0 else 0.0
        exp_ratio = (gtos_expl / base_primas) * 100.0 if base_primas > 0 else 0.0
        combined_ratio = loss_ratio + ((gtos_operativos) / base_primas * 100.0) if base_primas > 0 else 0.0

        margen_tecnico = (res_tec / base_primas) * 100.0 if base_primas > 0 else 0.0
        roi_inversiones = (res_fin / inv) * 100.0 if inv > 0 else 0.0

        # Solvencia SSN
        cobertura_res = (inv + inm + disp) / comp_tec_pasivo if comp_tec_pasivo > 0 else 1.0
        apalancamiento = base_primas / pn if pn > 0 else 0.0
        premios_a_cobrar = get_account_value(df_c, '1.03.01.00.00.00.00.00', exact=True)
        calidad_cartera = (premios_a_cobrar / base_primas) * 100.0 if base_primas > 0 else 0.0

        retencion_ratio = max(0.0, min(100.0, ((primas_emit - primas_cedidas) / primas_emit * 100.0))) if primas_emit > 0 else 100.0
        cesion_ratio = (primas_cedidas / primas_emit * 100.0) if primas_emit > 0 else 0.0
        roe = (res_neto / pn * 100.0) if pn > 0 else 0.0
        roa = (res_neto / activo_tot * 100.0) if activo_tot > 0 else 0.0
        margen_neto = (res_neto / base_primas * 100.0) if base_primas > 0 else 0.0
        densidad_inversiones = (inv / activo_tot * 100.0) if activo_tot > 0 else 0.0

        records.append({
            'cod_cia': cod,
            'razon_social': cia['razon_social'],
            'tipo_entidad': tipo_entidad,
            'activo': activo_tot,
            'disponibilidades': disp,
            'inversiones': inv,
            'creditos': cred,
            'premios_a_cobrar': premios_a_cobrar,
            'inmuebles': inm,
            'bienes_uso': bienes_uso,
            'otros_activos': otros_act,
            'pasivo': pasivo_tot,
            'deudas': deudas,
            'compromisos_tecnicos': comp_tec_pasivo,
            'previsiones': prev,
            'patrimonio_neto': pn,
            'primas_emitidas': primas_emit,
            'primas_cedidas': primas_cedidas,
            'cesiones_anulaciones': cesiones_anul,
            'var_reservas': var_comp_tec,
            'primas_devengadas': primas_dev,
            'siniestros': siniestros_dev,
            'rescates': rescates,
            'gtos_produccion': gtos_prod,
            'gtos_explotacion': gtos_expl,
            'gtos_operativos': gtos_operativos,
            'resultado_tecnico': res_tec,
            'resultado_financiero': res_fin,
            'impuesto_ganancias': imp_gan,
            'resultado_neto': res_neto,
            'loss_ratio': loss_ratio,
            'rescates_ratio': rescates_ratio,
            'comm_ratio': comm_ratio,
            'exp_ratio': exp_ratio,
            'combined_ratio': combined_ratio,
            'margen_tecnico': margen_tecnico,
            'roi_inversiones': roi_inversiones,
            'cobertura_reservas': cobertura_res,
            'apalancamiento': apalancamiento,
            'calidad_cartera': calidad_cartera,
            'retencion_ratio': retencion_ratio,
            'cesion_ratio': cesion_ratio,
            'roe': roe,
            'roa': roa,
            'margen_neto': margen_neto,
            'densidad_inversiones': densidad_inversiones
        })

    return pd.DataFrame(records)

def get_company_subramos(df, cod_cia=None):
    if cod_cia:
        sub_df = df[df['cod_cia'] == cod_cia]
    else:
        sub_df = df

    accounts_primas = (
        '5.01.01.01.01.01.01', '5.01.01.01.01.01.99',
        '5.01.01.01.01.02.01', '5.01.01.01.01.02.99',
        '5.01.01.01.01.03.02', '5.01.01.01.01.03.99',
        '5.01.01.01.01.04.01', '5.01.01.01.04.99'
    )
    primas_rows = sub_df[sub_df['cod_cuenta'].str.startswith(accounts_primas) & (sub_df['desc_subramo'] != '') & (sub_df['desc_subramo'].notna())]
    siniestros_rows = sub_df[sub_df['cod_cuenta'].str.startswith(('4.01.01.01.01.01', '4.01.01.01.01.99', '4.01.01.01.02.01', '4.01.01.01.02.99', '4.01.01.01.03.01', '4.01.01.01.03.99', '4.01.01.01.04.01', '4.01.01.01.04.99', '4.01.02.01', '4.01.02.02', '4.01.02.03')) & (sub_df['desc_subramo'] != '') & (sub_df['desc_subramo'].notna())]

    primas_by_sub = primas_rows.groupby(['cod_subramo', 'desc_subramo'])['importe'].sum().reset_index()
    sin_by_sub = siniestros_rows.groupby(['cod_subramo', 'desc_subramo'])['importe'].sum().reset_index()

    merged = pd.merge(primas_by_sub, sin_by_sub, on=['cod_subramo', 'desc_subramo'], how='outer', suffixes=('_primas', '_siniestros')).fillna(0)
    merged['primas'] = merged['importe_primas']
    merged['siniestros'] = merged['importe_siniestros']
    merged['siniestralidad_%'] = np.where(merged['primas'] > 0, (merged['siniestros'] / merged['primas']) * 100.0, 0.0)

    merged = merged[merged['desc_subramo'].notna() & (merged['desc_subramo'] != '') & ((merged['primas'] > 0) | (merged['siniestros'] > 0))]
    merged = merged.sort_values(by='primas', ascending=False)
    
    return merged[['cod_subramo', 'desc_subramo', 'primas', 'siniestros', 'siniestralidad_%']].to_dict(orient='records')

def get_company_investments_breakdown(df_cia):
    inv4 = df_cia[df_cia['cod_cuenta'].str.startswith('1.02.01.') & df_cia['cod_cuenta'].apply(
        lambda x: len(x.split('.')) >= 4 and x.split('.')[3] != '00' and (len(x.split('.')) == 4 or x.split('.')[4] == '00')
    )]
    inv_ext = df_cia[df_cia['cod_cuenta'] == '1.02.02.00.00.00.00.00']
    combined = pd.concat([inv4, inv_ext]) if not inv_ext.empty else inv4

    if combined.empty:
        combined = df_cia[df_cia['cod_cuenta'].str.startswith('1.02.') & df_cia['cod_cuenta'].apply(
            lambda x: len(x.split('.')) >= 3 and x.split('.')[2] != '00' and (len(x.split('.')) == 3 or x.split('.')[3] == '00')
        )]

    if combined.empty:
        return []

    grp = combined.groupby(['cod_cuenta', 'desc_cuenta'])['importe'].sum().reset_index()
    tot = grp['importe'].sum()
    grp['porcentaje'] = (grp['importe'] / tot * 100.0).round(1) if tot > 0 else 0.0
    grp = grp[grp['importe'] > 0].sort_values(by='importe', ascending=False)

    records = []
    for _, row in grp.iterrows():
        records.append({
            'cod_cuenta': str(row['cod_cuenta']),
            'desc_cuenta': str(row['desc_cuenta']),
            'importe': float(row['importe']),
            'porcentaje': float(row['porcentaje'])
        })
    return records
