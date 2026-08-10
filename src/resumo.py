# -*- coding: utf-8 -*-
"""Gravacao da tabela-resumo de custos em Excel (formato do benchmark da engenharia)."""
import pandas as pd

from src import config
from src.io_amostras import EntradaInvalida

# Renomeacao de apresentacao da aba Resumo (apenas exibicao; nao afeta o calculo).
# A ordem deste dicionario e' a ordem das colunas na planilha.
COLUNAS_RESUMO = {
    "n_estratos": "Estratos",
    "amostra": "Amostra",
    "n_odis": "ODIs",
    "n_municipios": "Municipios",
    "n_ucs": "UCs",
    "km_roteiro": "Roteiro (km estrada)",
    "horas_roteiro": "Horas roteiro",
    "horas_inspecao": "Horas inspecao",
    "dias_fracionarios": "Dias (fracao)",
    "dias_trabalho": "Dias trabalho",
    "dias_faturados": "Dias faturados",
    "tamanho_equipe": "Equipe",
    "custo_campo": "Custo campo (R$)",
    "custo_fixo": "Custo fixo OS (R$)",
    "custo_total": "Custo total (R$)",
}

# Renomeacao de apresentacao da aba Detalhe (uma linha por obra, na ordem do roteiro).
COLUNAS_DETALHE = {
    "n_estratos": "Estratos",
    "amostra": "Amostra",
    "ordem": "Ordem",
    "ODI": "ODI",
    "Municipio": "Municipio",
    "Estrato": "Estrato",
    "n_ucs": "UCs",
    "lat_centro": "Latitude",
    "lon_centro": "Longitude",
    "km_trecho_estrada": "Trecho ate aqui (km)",
    "dist_interna_km": "Percurso interno (km)",
}


def _texto_leia_me():
    """Monta as linhas da aba Leia-me a partir dos parametros vigentes.

    Por que existe: a planilha e' lida por quem nunca vai abrir o codigo. Gerar o texto
    a partir de config (em vez de escrever numeros a mao) garante que a explicacao nunca
    fique defasada em relacao ao que foi de fato calculado.

    Logica: Entrada (config) -> Fase 1: monta as linhas de conteudo -> Fase 2: monta as
    linhas de parametros com os valores vigentes -> Saida: lista de strings.
    """
    # Fase 1: o que cada aba contem e como ler os numeros.
    linhas = [
        "Estimativa de custo de inspecao das amostras, por estratificacao e por amostra.",
        "",
        "Aba 'Resumo'  : uma linha por (estratificacao, amostra). E' o numero que vale.",
        "Aba 'Detalhe' : uma linha por obra, NA ORDEM DO ROTEIRO da equipe.",
        "",
        "O custo e' por AMOSTRA, nao por estrato:",
        "  custo = custo fixo de escritorio (1x) + dias faturados x equipe x jornada x tarifa",
        "  dias faturados = teto(horas de campo / jornada) + dias de mobilizacao",
        "  horas de campo = roteiro (km de estrada / velocidade) + inspecao (UCs / produtividade)",
        "",
        "O roteiro e' UMA viagem so: sai da capital da UF, encadeia todas as obras",
        "(municipio a municipio, obra a obra) e volta a capital uma unica vez no fim.",
        "",
        "PARAMETROS USADOS NESTA EXECUCAO:",
    ]
    # Fase 2: os parametros vigentes, lidos de config na hora da gravacao.
    linhas += [
        f"  Perfil da equipe            : {config.PERFIL_EQUIPE} x {config.TAMANHO_EQUIPE:g} pessoa(s)",
        f"  Tarifa campo / escritorio   : R$ {config.TARIFAS_HORA[config.PERFIL_EQUIPE]['campo']:.2f}/h"
        f" / R$ {config.TARIFAS_HORA[config.PERFIL_EQUIPE]['escritorio']:.2f}/h",
        f"  Jornada de campo            : {config.HORAS_DIA_CAMPO:g} h/dia",
        f"  Horas de escritorio por OS  : {config.HORAS_ESCRITORIO_POR_OS:g} h (uma vez por amostra)",
        f"  Dias de mobilizacao         : {config.DIAS_MOBILIZACAO:g}",
        f"  Velocidade / fator rodoviario: {config.VELOCIDADE_KMH:g} km/h / {config.FATOR_RODOVIARIO:g}",
        f"  Produtividade (UCs/dia)     : {config.UCS_POR_DIA}",
        "",
        "Todos os parametros ficam em src/config.py e podem ser ajustados sem rebuild.",
    ]
    # Saida: as linhas prontas para virar uma coluna do Excel.
    return linhas


def gravar_resumo(resultados, caminho):
    """Grava o Resumo_Custos.xlsx com todas as estratificacoes numa planilha so.

    Por que existe: e' o produto principal do estimador - a tabela que o humano cola na
    apresentacao. Uma planilha unica (em vez de um arquivo por estratificacao) e' o que
    permite comparar Estratos 3 x 4 x 5 lado a lado, que e' a decisao que o humano precisa
    tomar. Isolar a gravacao permite ajustar formato sem tocar no calculo.

    Logica: Entrada (lista de dicts com os numeros + o roteiro de cada amostra, caminho)
    -> Fase 1: separa os numeros do resumo dos roteiros de detalhe -> Fase 2: grava
    Leia-me -> Fase 3: grava a aba Resumo (uma linha por amostra) -> Fase 4: grava a aba
    Detalhe (todas as obras de todas as amostras, empilhadas) -> Saida: .xlsx gravado.
    """
    # Fase 1: separa as duas granularidades. O 'roteiro' sai do dict do resumo e vira detalhe.
    linhas_resumo = []
    detalhes = []
    for item in resultados:
        # Copia sem o roteiro: o que sobra sao os numeros da amostra.
        numeros = {c: item[c] for c in COLUNAS_RESUMO if c in item}
        linhas_resumo.append(numeros)
        # O roteiro ganha as duas chaves que dizem de qual amostra ele e'.
        roteiro = item["roteiro"].copy()
        roteiro["n_estratos"] = item["n_estratos"]
        roteiro["amostra"] = item["amostra"]
        detalhes.append(roteiro)
    # Monta os dois dataframes ja com as colunas na ordem de apresentacao.
    resumo = pd.DataFrame(linhas_resumo).reindex(columns=list(COLUNAS_RESUMO))
    detalhe = pd.concat(detalhes, ignore_index=True) if detalhes else pd.DataFrame()
    detalhe = detalhe.reindex(columns=[c for c in COLUNAS_DETALHE if c in detalhe.columns])
    try:
        # Abre o writer; PermissionError aqui = arquivo aberto no Excel.
        with pd.ExcelWriter(caminho) as xls:
            # Fase 2: aba Leia-me com a memoria de calculo e os parametros vigentes.
            pd.DataFrame({"Leia-me": _texto_leia_me()}).to_excel(xls, sheet_name="Leia-me", index=False)
            # Fase 3: a tabela que importa - uma linha por (estratificacao, amostra).
            resumo.rename(columns=COLUNAS_RESUMO).round(2).to_excel(xls, sheet_name="Resumo", index=False)
            # Fase 4: o detalhe por obra, na ordem em que a equipe as visita.
            detalhe.rename(columns=COLUNAS_DETALHE).round(4).to_excel(xls, sheet_name="Detalhe", index=False)
    except PermissionError:
        # Arquivo travado (aberto no Excel): mensagem de usuario, nao traceback.
        raise EntradaInvalida(f"Nao consegui gravar {caminho}.\nFeche o arquivo no Excel e rode de novo.")
