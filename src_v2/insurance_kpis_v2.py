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

    # Pre-cálculo vectorizado de subcuentas por subramo de Deudas con Asegurados (2.01.01.01.01.*)
    sub_liab = df[df['cod_cuenta'].str.startswith('2.01.01.01.01.') & (df['cod_subramo'] != '') & df['cod_subramo'].notna()]
    ibnr_accts = (
        '2.01.01.01.01.08.00.00',
        '2.01.01.01.01.10.00.00',
        '2.01.01.01.01.20.00.00',
        '2.01.01.01.01.25.00.00',
        '2.01.01.01.01.28.13.00'
    )
    otras_deudas_aseg_accts = (
        '2.01.01.01.01.11.00.00',
        '2.01.01.01.01.12.00.00',
        '2.01.01.01.01.13.00.00',
        '2.01.01.01.01.14.00.00',
        '2.01.01.01.01.50.00.00'
    )
    juicios_accts = (
        '2.01.01.01.01.02.00.00',
        '2.01.01.01.01.18.02.00',
        '2.01.01.01.01.18.03.00',
        '2.01.01.01.01.26.00.00',
        '2.01.01.01.01.28.07.00',
        '2.01.01.01.01.28.08.00',
        '2.01.01.01.01.28.16.00',
        '2.01.01.01.01.29.00.00'
    )
    ibnr_by_cia = sub_liab[sub_liab['cod_cuenta'].isin(ibnr_accts)].groupby('cod_cia')['importe'].sum().to_dict() if not sub_liab.empty else {}
    juicios_by_cia = sub_liab[sub_liab['cod_cuenta'].isin(juicios_accts)].groupby('cod_cia')['importe'].sum().to_dict() if not sub_liab.empty else {}
    sin_pend_mask = ~sub_liab['cod_cuenta'].isin(ibnr_accts + otras_deudas_aseg_accts) if not sub_liab.empty else None
    sin_pend_by_cia = sub_liab[sin_pend_mask].groupby('cod_cia')['importe'].sum().to_dict() if not sub_liab.empty else {}

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
        deudas_asegurados = get_account_value(df_c, '2.01.01.00.00.00.00.00', exact=True)
        reserva_sin_pendientes = float(sin_pend_by_cia.get(cod, 0.0))
        ibnr_val = float(ibnr_by_cia.get(cod, 0.0))
        reserva_juicios_val = float(juicios_by_cia.get(cod, 0.0))
        comp_tec_pasivo = get_account_value(df_c, '2.02.00.00.00.00.00.00', exact=True)
        prev = get_account_value(df_c, '2.03.00.00.00.00.00.00', exact=True)
        pn = get_account_value(df_c, '3.00.00.00.00.00.00.00', exact=True)
        acciones_grupo_econ = (
            get_account_value(df_c, '1.02.01.02.01.02.00.00', exact=True)
            + get_account_value(df_c, '1.02.01.02.02.02.00.00', exact=True)
            + get_account_value(df_c, '1.02.02.01.02.02.00.00', exact=True)
        )

        # ----------------------------------------------------
        # 2. ESTADO DE RESULTADOS OFICIAL (SSN)
        # ----------------------------------------------------
        tipo_entidad = cia['tipo_entidad']
        is_retiro = (tipo_entidad == 'Seguros de Retiro')

        # Paso 1: Emisión Directa Neta (Fórmula Oficial: 6 Cuentas 5.01 - 4 Cuentas 4.01)
        cuentas_emision_directa = (
            '5.01.01.01.01.01.01', '5.01.01.01.01.01.99',
            '5.01.01.01.01.02.01', '5.01.01.01.01.02.99',
            '5.01.01.01.01.03.02', '5.01.01.01.01.03.99'
        )
        cuentas_anulaciones_directas = (
            '4.01.04.04.04.01.01', '4.01.04.04.04.01.99',
            '4.01.04.04.04.02.01', '4.01.04.04.04.02.99'
        )

        emision_directa_bruta = float(df_c[df_c['cod_cuenta'].str.startswith(cuentas_emision_directa)]['importe'].sum())
        anulaciones_directas = float(df_c[df_c['cod_cuenta'].str.startswith(cuentas_anulaciones_directas)]['importe'].sum())
        
        # Emisión Directa Neta como base unificada de producción (idéntico a Boletín de Producción SSN)
        primas_emit = max(0.0, emision_directa_bruta - anulaciones_directas)

        # Paso 2: Primas Netas Devengadas Oficiales SSN (Seguros Directos + Reaseguros Activos)
        # 5.01.01 (Primas y Recargos Totales) - 4.01.04 (Anulaciones Totales)
        # - [4.01.03 (Primas Cedidas) - 5.01.02 (Créditos por Anulaciones de Primas Cedidas)]
        # - [4.01.05 (Cargo Compromisos Técnicos) - 5.01.04.04.04.{11,12,13,16,18,21} (Liberación Compromisos Técnicos)]
        primas_y_recargos_tot = get_account_value(df_c, '5.01.01.00.00.00.00.00', exact=True)
        anulaciones = get_account_value(df_c, '4.01.04.00.00.00.00.00', exact=True)
        primas_cedidas_brutas = get_account_value(df_c, '4.01.03.00.00.00.00.00', exact=True)
        anulaciones_cedidas = get_account_value(df_c, '5.01.02.00.00.00.00.00', exact=True)
        primas_cedidas = primas_cedidas_brutas - anulaciones_cedidas
        cesiones_anul = primas_cedidas + anulaciones

        comp_tec_cargo = get_account_value(df_c, '4.01.05.00.00.00.00.00', exact=True)
        comp_tec_liberacion = sum(
            get_account_value(df_c, f'5.01.04.04.04.{k:02d}.00.00', exact=True)
            for k in (11, 12, 13, 16, 18, 21)
        )
        var_comp_tec = comp_tec_cargo - comp_tec_liberacion

        # Primas Netas Devengadas (Exacto Cuadro 3 SSN)
        primas_dev = (primas_y_recargos_tot - anulaciones) - primas_cedidas - var_comp_tec

        # Paso 4: Siniestros Netos Devengados Oficiales SSN (Exacto Cuadro 3 SSN)
        # 4.01.01 (Siniestros Totales) - [5.01.04 (Créditos por Recuperos Totales) - Liberación Comp. Téc. - 5.01.04.04.04.08 (Part. Utilidades Reaseg.)]
        part_util_reaseg = get_account_value(df_c, '5.01.04.04.04.08.00.00', exact=True)
        siniestros_cargo = get_account_value(df_c, '4.01.01.00.00.00.00.00', exact=True)
        recup_tot = get_account_value(df_c, '5.01.04.00.00.00.00.00', exact=True)
        recup_sin = recup_tot - comp_tec_liberacion - part_util_reaseg
        siniestros_dev = siniestros_cargo - recup_sin

        # Paso 5: Otras Indemnizaciones, Rescates y Rentas Vitalicias (4.01.02)
        rescates = get_account_value(df_c, '4.01.02.00.00.00.00.00', exact=True)

        # Paso 6: Gastos de Producción Netos, Explotación y Prevención ART
        gtos_prod_cargo = get_account_value(df_c, '4.01.06.00.00.00.00.00', exact=True)
        recup_gtos_prod = get_account_value(df_c, '5.01.03.00.00.00.00.00', exact=True)
        gtos_prod = gtos_prod_cargo - recup_gtos_prod

        gtos_expl_base = get_account_value(df_c, '4.01.07.00.00.00.00.00', exact=True)
        gtos_prev_art = get_account_value(df_c, '4.01.60.00.00.00.00.00', exact=True)
        gtos_expl = gtos_expl_base + gtos_prev_art
        gtos_operativos = gtos_prod + gtos_expl

        # Paso 7: Otros Ingresos y Egresos Técnicos
        otros_ing_tec = get_account_value(df_c, '5.01.05.00.00.00.00.00', exact=True) + part_util_reaseg
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
        loss_ratio = 0.0 if is_retiro else ((siniestros_dev / primas_dev * 100.0) if primas_dev > 0 else 0.0)
        rescates_ratio = (rescates / base_primas) * 100.0 if base_primas > 0 else 0.0
        comm_ratio = (gtos_prod / base_primas) * 100.0 if base_primas > 0 else 0.0
        exp_ratio = (gtos_expl / base_primas) * 100.0 if base_primas > 0 else 0.0
        combined_ratio = ((costo_prestacional + gtos_operativos) / primas_dev * 100.0) if primas_dev > 0 else 0.0

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
            'acciones_grupo_economico': acciones_grupo_econ,
            'creditos': cred,
            'premios_a_cobrar': premios_a_cobrar,
            'inmuebles': inm,
            'bienes_uso': bienes_uso,
            'otros_activos': otros_act,
            'pasivo': pasivo_tot,
            'deudas': deudas,
            'deudas_asegurados': deudas_asegurados,
            'reserva_siniestros_pendientes': reserva_sin_pendientes,
            'ibnr': ibnr_val,
            'reserva_juicios': reserva_juicios_val,
            'compromisos_tecnicos': comp_tec_pasivo,
            'previsiones': prev,
            'patrimonio_neto': pn,
            'primas_emitidas': primas_emit,
            'emision_directa_bruta': emision_directa_bruta,
            'anulaciones_directas': anulaciones_directas,
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

    sub_df = sub_df[(sub_df['cod_subramo'] != '') & (sub_df['cod_subramo'] != '3.000.99') & (sub_df['desc_subramo'] != '') & (sub_df['desc_subramo'].notna())]
    if sub_df.empty:
        return []

    cuentas_emision_directa = (
        '5.01.01.01.01.01.01', '5.01.01.01.01.01.99',
        '5.01.01.01.01.02.01', '5.01.01.01.01.02.99',
        '5.01.01.01.01.03.02', '5.01.01.01.01.03.99'
    )
    cuentas_anulaciones_directas = (
        '4.01.04.04.04.01.01', '4.01.04.04.04.01.99',
        '4.01.04.04.04.02.01', '4.01.04.04.04.02.99'
    )
    ct_lib_pfxs = tuple(f'5.01.04.04.04.{k:02d}.' for k in (11, 12, 13, 16, 18, 21))

    desc_map = sub_df.groupby('cod_subramo')['desc_subramo'].first()

    def sum_by_sub(mask):
        s = sub_df[mask]
        if s.empty:
            return pd.Series(dtype=float)
        return s.groupby('cod_subramo')['importe'].sum()

    em_dir = sum_by_sub(sub_df['cod_cuenta'].str.startswith(cuentas_emision_directa))
    an_dir = sum_by_sub(sub_df['cod_cuenta'].str.startswith(cuentas_anulaciones_directas))
    primas_emit = em_dir.subtract(an_dir, fill_value=0.0)

    # Primas Netas Devengadas exactas por subramo (Cuadro 3 SSN)
    p_brut = sum_by_sub(sub_df['cod_cuenta'].str.startswith('5.01.01.'))
    p_anul = sum_by_sub(sub_df['cod_cuenta'].str.startswith('4.01.04.'))
    p_ced  = sum_by_sub(sub_df['cod_cuenta'].str.startswith('4.01.03.'))
    p_aced = sum_by_sub(sub_df['cod_cuenta'].str.startswith('5.01.02.'))
    ct_car = sum_by_sub(sub_df['cod_cuenta'].str.startswith('4.01.05.'))
    ct_lib = sum_by_sub(sub_df['cod_cuenta'].str.startswith(ct_lib_pfxs))
    primas_dev = (p_brut.subtract(p_anul, fill_value=0.0)
                  .subtract(p_ced.subtract(p_aced, fill_value=0.0), fill_value=0.0)
                  .subtract(ct_car.subtract(ct_lib, fill_value=0.0), fill_value=0.0))

    # Siniestros Netos Devengados exactos por subramo (Cuadro 3 SSN)
    part_util = sum_by_sub(sub_df['cod_cuenta'].str.startswith('5.01.04.04.04.08.'))
    sin_car = sum_by_sub(sub_df['cod_cuenta'].str.startswith('4.01.01.'))
    rec_tot = sum_by_sub(sub_df['cod_cuenta'].str.startswith('5.01.04.'))
    sin_lib = rec_tot.subtract(ct_lib, fill_value=0.0).subtract(part_util, fill_value=0.0)
    sin_dev = sin_car.subtract(sin_lib, fill_value=0.0)

    all_codes = desc_map.index
    merged = pd.DataFrame({
        'cod_subramo': all_codes,
        'desc_subramo': desc_map.values,
        'primas': primas_emit.reindex(all_codes, fill_value=0.0).values,
        'primas_devengadas': primas_dev.reindex(all_codes, fill_value=0.0).values,
        'siniestros': sin_dev.reindex(all_codes, fill_value=0.0).values
    })

    # Seguros de Retiro (2.060 / 2.070) no registran siniestralidad técnica
    is_ret_sub = merged['cod_subramo'].str.startswith(('2.06', '2.07'))
    merged.loc[is_ret_sub, 'siniestros'] = 0.0
    merged['siniestralidad_%'] = np.where(
        (~is_ret_sub) & (merged['primas_devengadas'] > 0),
        (merged['siniestros'] / merged['primas_devengadas']) * 100.0,
        0.0
    )

    merged = merged[(merged['primas'].abs() > 0.01) | (merged['siniestros'].abs() > 0.01)]
    merged = merged.sort_values(by='primas', ascending=False)

    for col in ('primas', 'primas_devengadas', 'siniestros', 'siniestralidad_%'):
        merged[col] = merged[col].round(2)

    return merged[['cod_subramo', 'desc_subramo', 'primas', 'primas_devengadas', 'siniestros', 'siniestralidad_%']].to_dict(orient='records')

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
    grp['porcentaje'] = (grp['importe'] / tot * 100.0).round(2) if tot > 0 else 0.0
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
