# -*- coding: utf-8 -*-
"""Motor de custo: transforma distancias em R$ conforme o modelo aprovado (F1).

=== MEMORIA DE CALCULO (para humanos) ===
[Mesmo bloco de src/config.py -- duplicado de proposito: quem abrir qualquer um dos
dois arquivos entende o calculo sem ler mais nada.]
custo_estrato = CUSTO_FIXO + custo_campo, onde:
  CUSTO_FIXO  = HORAS_ESCRITORIO_POR_OS x tarifa_escritorio  (36h x 360 = 12.960, 1x por estrato)
  custo_campo = (horas_desloc + horas_inspecao) x tarifa_campo (600/h = 4.800/equipe-dia)
  horas_desloc = km_estrada / VELOCIDADE_KMH, com km_estrada = FATOR_RODOVIARIO x
    (mobilizacao: capital da UF -> centro do municipio, ida e volta, UMA vez por municipio
     + saltos entre as obras do municipio + percurso entre as UCs de cada obra)
  horas_inspecao = n_ucs x (HORAS_DIA_CAMPO / UCS_POR_DIA[tipo])  (LPT: 30/dia; MLA: 3/dia)
Amostra = soma dos estratos. A mobilizacao municipal e' rateada igualmente entre as
obras do municipio so para exibir custo por obra; o total do estrato nao depende do rateio.
=== FIM DA MEMORIA DE CALCULO ===
"""
import pandas as pd
from src import config
from src.distancias import haversine_km, _rota_vizinho_mais_proximo

def tarifa_campo():
    """Tarifa horaria de campo do perfil ativo, com diaria diluida por hora.

    Por que existe: G1/G2 do gate viram parametros; le config NA CHAMADA (nao no
    import) para monkeypatch e ajustes sem rebuild funcionarem.

    Logica: Entrada (config) -> Fase 1: tarifa 'campo' do perfil ativo -> Fase 2:
    soma CUSTO_DIARIA diluida pela jornada -> Saida: R$/hora.
    """
    # Fase 1: tarifa de campo do perfil ativo (G1: ENGENHEIRO).
    base = config.TARIFAS_HORA[config.PERFIL_EQUIPE]["campo"]
    # Fase 2: diaria (G2: 0 por padrao) diluida pelas horas do dia de campo.
    return base + config.CUSTO_DIARIA / config.HORAS_DIA_CAMPO

def tarifa_escritorio():
    """Tarifa horaria de escritorio (sem deslocamento) do perfil ativo.

    Por que existe: par do tarifa_campo() para o termo fixo por OS; le config na
    chamada pelo mesmo motivo.

    Logica: Entrada (config) -> Fase 1: tarifa 'escritorio' do perfil -> Saida: R$/h.
    """
    # Fase 1/Saida: tarifa de escritorio do perfil ativo.
    return config.TARIFAS_HORA[config.PERFIL_EQUIPE]["escritorio"]

def custo_por_odi(df_odis, uf, tipo_contrato):
    """Calcula o custo de CAMPO de cada ODI a partir do resumo geometrico.

    Por que existe: e' o UNICO lugar onde a formula de custo vive; contrato estavel
    permite ajustar o modelo so por config.py, sem tocar no resto do pipeline.
    O termo fixo de escritorio NAO entra aqui (e' por estrato, ver agregar_por_estrato).

    Logica: Entrada (df por ODI, uf, tipo) -> Fase 1: por municipio, mobilizacao
    (capital -> centroide municipal, ida e volta, uma vez) + saltos entre ODIs,
    rateados igualmente entre as ODIs do municipio -> Fase 2: km -> horas (desloc)
    e produtividade do tipo -> horas (inspecao) -> Fase 3: horas x tarifa de campo
    -> Saida: df com as colunas de custo de campo.
    """
    # Copia para nao mutar a entrada.
    r = df_odis.copy()
    # Capital da UF do contrato (G3); KeyError aqui = UF invalida (bug, nao dado).
    lat_cap, lon_cap = config.CAPITAIS_UF[uf]
    # Fase 1: distancia de acesso rateada por municipio.
    acesso = {}
    # Um grupo por municipio: a equipe mobiliza uma vez por municipio, nao por ODI.
    for _mun, g in r.groupby("Municipio", sort=False):
        # Centroide municipal = media dos centroides das ODIs do municipio.
        lat_m, lon_m = float(g["lat_centro"].mean()), float(g["lon_centro"].mean())
        # Mobilizacao: capital -> municipio, ida e volta, UMA vez.
        mob = 2 * haversine_km(lat_cap, lon_cap, lat_m, lon_m)
        # Saltos: rota gulosa entre os centroides das ODIs do municipio.
        saltos = _rota_vizinho_mais_proximo(g["lat_centro"].to_numpy(), g["lon_centro"].to_numpy())
        # Rateio igual entre as ODIs do municipio (so para exibicao por ODI).
        for odi in g["ODI"]:
            acesso[odi] = (mob + saltos) / len(g)
    # Aplica o rateio e a correcao linha reta -> estrada em todas as distancias.
    r["dist_acesso_km"] = r["ODI"].map(acesso) * config.FATOR_RODOVIARIO
    r["dist_interna_corrigida_km"] = r["dist_interna_km"] * config.FATOR_RODOVIARIO
    # Fase 2: km -> horas; inspecao usa a produtividade do tipo de contrato (G5).
    r["horas_desloc"] = (r["dist_acesso_km"] + r["dist_interna_corrigida_km"]) / config.VELOCIDADE_KMH
    # Horas por UC derivadas da jornada e da produtividade do tipo (LPT 30, MLA 3).
    horas_por_uc = config.HORAS_DIA_CAMPO / config.UCS_POR_DIA[tipo_contrato]
    r["horas_inspecao"] = r["n_ucs"] * horas_por_uc
    # Fase 3: horas -> R$ pela tarifa de campo (G1/G2 via tarifa_campo()).
    r["custo_desloc"] = r["horas_desloc"] * tarifa_campo()
    r["custo_insp"] = r["horas_inspecao"] * tarifa_campo()
    r["custo_total"] = r["custo_desloc"] + r["custo_insp"]
    # Saida: mesmo df, enriquecido com as colunas de custo de campo.
    return r

def agregar_por_estrato(df_custos):
    """Agrega por estrato, acrescenta o custo fixo de OS e a linha TOTAL.

    Por que existe: a formula decifrada tem um termo FIXO por estrato (planejamento/
    relatorio/apresentacao) que nao pertence a nenhuma ODI; ele entra aqui, garantindo
    que resumo e mapas usem os mesmos numeros.

    Logica: Entrada (df por ODI com custos de campo) -> Fase 1: groupby Estrato
    somando -> Fase 2: equipe_dias e custo_fixo_os por estrato; total = campo + fixo
    -> Fase 3: linha TOTAL -> Saida: df por estrato + TOTAL.
    """
    # Fase 1: soma por estrato das grandezas aditivas de campo.
    agg = (df_custos.groupby("Estrato", sort=True)
           .agg(n_odis=("ODI", "count"), n_ucs=("n_ucs", "sum"),
                dist_acesso_km=("dist_acesso_km", "sum"),
                dist_interna_km=("dist_interna_corrigida_km", "sum"),
                horas_desloc=("horas_desloc", "sum"), horas_inspecao=("horas_inspecao", "sum"),
                custo_desloc=("custo_desloc", "sum"), custo_insp=("custo_insp", "sum"),
                custo_campo=("custo_total", "sum"))
           .reset_index())
    # Fase 2: equipe-dias (horas de campo / jornada) e o termo fixo de OS por estrato.
    agg["equipe_dias"] = (agg["horas_desloc"] + agg["horas_inspecao"]) / config.HORAS_DIA_CAMPO
    agg["custo_fixo_os"] = config.HORAS_ESCRITORIO_POR_OS * tarifa_escritorio()
    # Total do estrato = campo (soma dos ODIs) + fixo (uma vez).
    agg["custo_total"] = agg["custo_campo"] + agg["custo_fixo_os"]
    # Fase 3: linha TOTAL = soma das colunas numericas (fixo somado por estrato).
    total = agg.drop(columns="Estrato").sum()
    total["Estrato"] = "TOTAL"
    # Saida: estratos ordenados + TOTAL ao final.
    return pd.concat([agg, total.to_frame().T], ignore_index=True)
