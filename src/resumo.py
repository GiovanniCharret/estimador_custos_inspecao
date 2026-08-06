# -*- coding: utf-8 -*-
"""Gravacao da tabela-resumo de custos em Excel (formato inspirado no gabarito 20260224)."""
import pandas as pd
from src.custo import agregar_por_estrato
from src.io_amostras import EntradaInvalida

# Renomeacao de apresentacao (apenas exibicao; nao afeta o calculo).
COLUNAS_PT = {
    "Estrato": "Estrato", "n_odis": "Qtd ODIs", "n_ucs": "Qtd UCs",
    "dist_acesso_km": "Dist. acesso (km)", "dist_interna_km": "Dist. interna (km)",
    "dist_interna_corrigida_km": "Dist. interna (km, estrada)",
    "horas_desloc": "Horas desloc.", "horas_inspecao": "Horas inspecao",
    "equipe_dias": "Equipe-dias",
    "custo_desloc": "Custo desloc. (R$)", "custo_insp": "Custo inspecao (R$)",
    "custo_campo": "Custo campo (R$)", "custo_fixo_os": "Custo fixo OS (R$)",
    "custo_total": "Custo total (R$)",
}

def gravar_resumo(custos_por_amostra, caminho):
    """Grava o Resumo_Custos.xlsx com uma aba de agregado e uma de detalhe por amostra.

    Por que existe: e' o produto principal do estimador — a tabela que o humano cola
    na apresentacao; isolar a gravacao permite ajustar formato sem tocar no calculo.

    Logica: Entrada (dict {k: df por ODI com custos}, caminho) -> Fase 1: Leia-me ->
    Fase 2: por amostra, agrega por estrato e grava agregado + detalhe -> Saida: .xlsx.
    """
    try:
        # Abre o writer; PermissionError aqui = arquivo aberto no Excel.
        with pd.ExcelWriter(caminho) as xls:
            # Fase 1: aba Leia-me com a explicacao minima do conteudo.
            pd.DataFrame({"Leia-me": [
                "Resumo de custos de inspecao por amostra/estrato.",
                "Aba 'Amostra K' = agregado por estrato; 'Detalhe K' = por ODI.",
                "Parametros do modelo: src/config.py (fontes comentadas).",
            ]}).to_excel(xls, sheet_name="Leia-me", index=False)
            # Fase 2: um par de abas por amostra, em ordem numerica.
            for k in sorted(custos_por_amostra):
                detalhe = custos_por_amostra[k]
                # Agrega por estrato (mesma funcao usada em todo o pipeline).
                agregado = agregar_por_estrato(detalhe)
                # Grava com nomes de coluna de apresentacao e 2 casas decimais.
                agregado.rename(columns=COLUNAS_PT).round(2).to_excel(xls, sheet_name=f"Amostra {k}", index=False)
                detalhe.rename(columns=COLUNAS_PT).round(2).to_excel(xls, sheet_name=f"Detalhe {k}", index=False)
    except PermissionError:
        # Arquivo travado (aberto no Excel): mensagem de usuario, nao traceback.
        raise EntradaInvalida(f"Nao consegui gravar {caminho}.\nFeche o arquivo no Excel e rode de novo.")
