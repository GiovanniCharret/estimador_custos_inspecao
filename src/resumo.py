# -*- coding: utf-8 -*-
"""Gravacao da tabela-resumo de custos em Excel (formato do benchmark da engenharia)."""
import pandas as pd

from src import config
from src.io_amostras import EntradaInvalida

# Renomeacao de apresentacao da aba Resumo (apenas exibicao; nao afeta o calculo).
# A ordem deste dicionario e' a ordem das colunas na planilha.
# Como o Formulario de Ordem de Servico chama cada tipo de contrato. O usuario reconhece a
# obra por este nome (e' o que ele escolhe na celula 'Tipo de obra' da OS), nao pela sigla.
NOME_TIPO_OBRA = {
    "LPT": "Extensao de Redes de Distribuicao",
    "MLA": "Sistemas de Geracao Descentralizada",
}

# 'Equipes' (quantas) e 'Pessoas por equipe' (tamanho de cada) sao GRANDEZAS DIFERENTES
# e ficam lado a lado de proposito: ate a F15 a planilha tinha 'Equipe' aqui e 'Equipes'
# na aba Cenarios querendo dizer coisas distintas, o que era leitura errada esperando
# acontecer.
COLUNAS_RESUMO = {
    "n_estratos": "Estratos",
    "amostra": "Amostra",
    "n_odis": "ODIs",
    "n_municipios": "Municipios",
    "n_ucs": "UCs",
    "n_equipes": "Equipes",
    "tamanho_equipe": "Pessoas por equipe",
    "km_roteiro": "Roteiro somado (km estrada)",
    "horas_roteiro": "Horas roteiro",
    "horas_inspecao": "Horas inspecao",
    "horas_escritorio": "Horas escritorio",
    "horas_equipe_critica": "Horas da equipe mais lenta",
    "dias_fracionarios": "Dias (fracao)",
    "dias_trabalho": "Dias trabalho (por equipe)",
    "dias_faturados": "Dias faturados (por equipe)",
    "custo_campo": "Custo campo (R$)",
    "custo_fixo": "Custo fixo OS (R$)",
    "custo_total": "Custo total (R$)",
}

# Renomeacao de apresentacao da aba Cenarios (grade equipes x prazo por estratificacao).
COLUNAS_CENARIOS = {
    "n_estratos": "Estratos",
    "amostra": "Amostra",
    "n_equipes": "Equipes",
    "dias_trabalho": "Dias trabalho (por equipe)",
    "dias_faturados": "Dias faturados (por equipe)",
    "km_roteiro": "Roteiro somado (km estrada)",
    "ocupacao": "Ocupacao da equipe",
    "custo_campo": "Custo campo (R$)",
    "custo_fixo": "Custo fixo OS (R$)",
    "custo_total": "Custo total (R$)",
    "cenario": "Cenario",
}

# Renomeacao de apresentacao da aba Detalhe (uma linha por obra, na ordem do roteiro).
COLUNAS_DETALHE = {
    "n_estratos": "Estratos",
    "amostra": "Amostra",
    "equipe": "Equipe",
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


def _texto_leia_me(tipo_contrato=None):
    """Monta as linhas da aba Leia-me a partir dos parametros vigentes.

    Por que existe: a planilha e' lida por quem nunca vai abrir o codigo. Gerar o texto
    a partir de config (em vez de escrever numeros a mao) garante que a explicacao nunca
    fique defasada em relacao ao que foi de fato calculado.

    Recebe o tipo do contrato porque dois parametros mudam com ele - as horas de
    escritorio e a produtividade da inspecao -, e imprimir o valor errado num documento
    que existe para explicar o calculo seria pior que nao imprimir nada.

    Logica: Entrada (tipo do contrato, config) -> Fase 1: monta as linhas de conteudo ->
    Fase 2: monta as linhas de parametros com os valores vigentes -> Saida: lista de
    strings.
    """
    # Fase 1: o que cada aba contem e como ler os numeros.
    linhas = [
        "Estimativa de custo de inspecao das amostras, por estratificacao.",
        "",
        "Aba 'Resumo'   : uma linha por estratificacao. E' o numero que vale.",
        "Aba 'Cenarios' : a grade de combinacoes VIAVEIS (quantas equipes x qual prazo).",
        "Aba 'Detalhe'  : uma linha por obra, com a EQUIPE dona e a ordem de visita dela.",
        "",
        "CUIDADO com duas colunas parecidas e diferentes:",
        "  'Equipes'            = quantas equipes independentes vao a campo;",
        "  'Pessoas por equipe' = quantas pessoas ha DENTRO de cada equipe.",
        "",
        "As HORAS DE ESCRITORIO e a PRODUTIVIDADE da inspecao mudam com o tipo de obra do",
        "contrato - e' o mesmo parametro que a Ordem de Servico pede na celula 'Tipo de obra'.",
        "Extensao de Redes (LPT) usa 36 h de escritorio; Geracao Descentralizada (MLA), 24 h.",
        "",
        "O custo e' por AMOSTRA, nao por estrato:",
        "  custo = fixo de escritorio (1x) + equipes x pessoas x dias faturados x jornada x tarifa",
        "  dias faturados = teto(horas da equipe MAIS LENTA / (jornada x pessoas)) + mobilizacao",
        "  horas de campo = roteiro (km de estrada / velocidade) + inspecao (UCs / produtividade)",
        "",
        "As equipes sao INDEPENDENTES. O itinerario e' cortado em blocos geograficos",
        "contiguos e CADA equipe sai da capital da UF, varre o seu bloco e volta uma unica",
        "vez no fim. Por isso o km somado CRESCE ao dividir: a ida e a volta sao cobradas",
        "uma vez por equipe (nos dados reais, de 18% a 37% a mais com duas equipes).",
        "Este custo ja esta dentro dos numeros - nao e' mais uma ressalva.",
        "",
        "O prazo e' o da equipe MAIS LENTA, porque todas precisam caber nele. Encurtar o",
        "prazo NAO barateia - encarece: o contrato paga por hora-profissional, cada equipe",
        "carrega o seu dia de mobilizacao e o seu deslocamento, e o arredondamento para dia",
        "inteiro desperdica mais quanto mais equipes houver.",
        "",
        "A aba 'Cenarios' mostra SO o que e' viavel. Combinacao que passa do teto de dias",
        "por equipe nao aparece - nao foi omitida, foi descartada por inviabilidade.",
        "Prazos maiores que o minimo de cada linha sao folga deliberada: a equipe fica mais",
        "ociosa (veja 'Ocupacao') e o custo sobe, porque ha mais dias faturados.",
        "",
        "O MAPA mostra apenas ONDE estao as obras da amostra e a base da equipe (capital).",
        "Ele nao desenha itinerario: a ordem de visita usada no calculo e' uma hipotese do",
        "modelo, nao uma recomendacao de rota.",
        "",
        "PARAMETROS USADOS NESTA EXECUCAO:",
    ]
    # Fase 2: os parametros vigentes, lidos de config na hora da gravacao. Sem tipo
    # conhecido, o padrao vale so para escolher QUAIS numeros imprimir.
    tipo = tipo_contrato if tipo_contrato in config.TARIFAS_HORA else config.TIPO_CONTRATO_PADRAO
    tarifas = config.TARIFAS_HORA[tipo][config.PERFIL_EQUIPE]
    etapas = config.HORAS_ESCRITORIO_POR_TIPO[tipo]
    linhas += [
        f"  Tipo de contrato            : {tipo} ({NOME_TIPO_OBRA.get(tipo, tipo)})",
        f"  Equipes (calculo oficial)   : {config.N_EQUIPES_PADRAO:g}, independentes",
        f"  Perfil / pessoas por equipe : {config.PERFIL_EQUIPE} x {config.TAMANHO_EQUIPE:g} pessoa(s)",
        f"  Tarifa campo / escritorio   : R$ {tarifas['campo']:.2f}/h"
        f" / R$ {tarifas['escritorio']:.2f}/h",
        f"  Jornada de campo            : {config.HORAS_DIA_CAMPO:g} h/dia",
        f"  Horas de escritorio por OS  : {sum(etapas.values()):g} h (uma vez por amostra) = "
        + " + ".join(f"{nome} {horas:g}h" for nome, horas in etapas.items()),
        f"  Dias de mobilizacao         : {config.DIAS_MOBILIZACAO:g}",
        f"  Velocidade / fator rodoviario: {config.VELOCIDADE_KMH:g} km/h / {config.FATOR_RODOVIARIO:g}",
        f"  Produtividade (UCs/dia)     : {config.UCS_POR_DIA[tipo]:g} ({tipo})",
        f"  Grade de cenarios           : {config.N_EQUIPES_MIN:g} a {config.N_EQUIPES_MAX:g} equipes,"
        f" no maximo {config.MAX_DIAS_POR_EQUIPE:g} dias por equipe",
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

    Logica: Entrada (lista de dicts com os numeros + roteiro + cenarios de cada amostra,
    caminho) -> Fase 1: separa as tres granularidades (resumo, cenarios, detalhe) -> Fase 2:
    grava Leia-me -> Fase 3: grava a aba Resumo (uma linha por estratificacao) -> Fase 4:
    grava a aba Cenarios (prazos alternativos) -> Fase 5: grava a aba Detalhe (todas as
    obras, empilhadas) -> Saida: .xlsx gravado.
    """
    # Fase 1: separa as tres granularidades a partir da mesma lista de resultados.
    linhas_resumo = []
    linhas_cenarios = []
    detalhes = []
    for item in resultados:
        # Copia sem roteiro/cenarios: o que sobra sao os numeros da amostra.
        numeros = {c: item[c] for c in COLUNAS_RESUMO if c in item}
        linhas_resumo.append(numeros)
        # Cada cenario ganha as duas chaves que dizem de qual amostra ele e'.
        for cenario in item.get("cenarios", []):
            linhas_cenarios.append({"n_estratos": item["n_estratos"], "amostra": item["amostra"], **cenario})
        # O roteiro tambem.
        roteiro = item["roteiro"].copy()
        roteiro["n_estratos"] = item["n_estratos"]
        roteiro["amostra"] = item["amostra"]
        detalhes.append(roteiro)
    # Monta os dataframes ja com as colunas na ordem de apresentacao.
    resumo = pd.DataFrame(linhas_resumo).reindex(columns=list(COLUNAS_RESUMO))
    cenarios = pd.DataFrame(linhas_cenarios).reindex(columns=list(COLUNAS_CENARIOS))
    detalhe = pd.concat(detalhes, ignore_index=True) if detalhes else pd.DataFrame()
    detalhe = detalhe.reindex(columns=[c for c in COLUNAS_DETALHE if c in detalhe.columns])
    try:
        # Abre o writer; PermissionError aqui = arquivo aberto no Excel.
        with pd.ExcelWriter(caminho) as xls:
            # Fase 2: aba Leia-me com a memoria de calculo e os parametros vigentes. O tipo
            # vem dos resultados (uma execucao = um contrato, logo um tipo so).
            tipo = resultados[0].get("tipo_contrato") if resultados else None
            pd.DataFrame({"Leia-me": _texto_leia_me(tipo)}).to_excel(
                xls, sheet_name="Leia-me", index=False)
            # Fase 3: a tabela que importa - uma linha por estratificacao.
            resumo.rename(columns=COLUNAS_RESUMO).round(2).to_excel(xls, sheet_name="Resumo", index=False)
            # Fase 4: os prazos alternativos, para a conversa de planejamento.
            cenarios.rename(columns=COLUNAS_CENARIOS).round(2).to_excel(xls, sheet_name="Cenarios", index=False)
            # Fase 5: o detalhe por obra, na ordem em que a equipe as visita.
            detalhe.rename(columns=COLUNAS_DETALHE).round(4).to_excel(xls, sheet_name="Detalhe", index=False)
    except PermissionError:
        # Arquivo travado (aberto no Excel): mensagem de usuario, nao traceback.
        raise EntradaInvalida(f"Nao consegui gravar {caminho}.\nFeche o arquivo no Excel e rode de novo.")
