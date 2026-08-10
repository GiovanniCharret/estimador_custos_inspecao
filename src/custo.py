# -*- coding: utf-8 -*-
"""Motor de custo: transforma a geometria de uma amostra em R$ (modelo F9).

=== MEMORIA DE CALCULO (para humanos) ===
[Mesmo bloco de src/config.py -- duplicado de proposito: quem abrir qualquer um dos
dois arquivos entende o calculo sem ler mais nada.]

O custo e' POR AMOSTRA (nao por estrato):

  custo_amostra = CUSTO_FIXO + custo_campo

  CUSTO_FIXO  = HORAS_ESCRITORIO_POR_OS x tarifa_escritorio   (36h x 360 = 12.960, 1x)
  custo_campo = dias_faturados x TAMANHO_EQUIPE x HORAS_DIA_CAMPO x tarifa_campo

  dias_faturados = teto(horas_de_campo / HORAS_DIA_CAMPO) + DIAS_MOBILIZACAO
  horas_de_campo = horas_roteiro + horas_inspecao
    horas_roteiro  = km_estrada / VELOCIDADE_KMH
      km_estrada   = FATOR_RODOVIARIO x (itinerario unico capital -> todas as obras ->
                     capital, encadeado, + percurso entre as UCs de cada obra)
    horas_inspecao = n_ucs x (HORAS_DIA_CAMPO / UCS_POR_DIA[tipo])  (LPT 30/dia; MLA 3/dia)

O ESTRATO nao participa do custo. Ele identifica de onde cada obra veio na
estratificacao e aparece so como coluna informativa no detalhe.

BENCHMARK: a engenharia da PB 7a Tranche obedece, ao centavo, a
  custo = 12.960 + 9.600 x (dias + 1), com 9.600 = 2 pessoas x 8h x R$600.
E' esta mesma formula com TAMANHO_EQUIPE = 2; aqui o parametro vale 1 (decisao G1).
=== FIM DA MEMORIA DE CALCULO ===
"""
import math

import pandas as pd

from src import config
from src.distancias import montar_roteiro


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


def custo_amostra(df_odis, uf, tipo_contrato):
    """Precifica uma amostra inteira a partir do resumo geometrico por ODI.

    Por que existe: e' o UNICO lugar onde a formula de custo vive. Trabalha na
    granularidade AMOSTRA porque e' assim que o custo se comporta: o roteiro e' uma
    viagem so (nao da para somar viagens por obra) e o fixo de escritorio e' uma OS so.
    Devolver tambem o detalhe por obra evita que o resumo e o mapa recalculem o roteiro
    por conta propria e acabem discordando entre si.

    Logica: Entrada (df por ODI, uf, tipo) -> Fase 1: monta o itinerario unico a partir
    da capital da UF -> Fase 2: soma o percurso interno de cada obra e converte linha
    reta em estrada -> Fase 3: km -> horas de roteiro; UCs -> horas de inspecao ->
    Fase 4: horas -> dias inteiros + mobilizacao -> Fase 5: dias -> R$, mais o fixo
    de escritorio -> Saida: (dict com os numeros da amostra, df do roteiro por obra).
    """
    # Capital da UF do contrato (G3); KeyError aqui = UF invalida (bug, nao dado).
    lat_cap, lon_cap = config.CAPITAIS_UF[uf]
    # Fase 1: itinerario unico, encadeado, com volta a capital uma unica vez no fim.
    roteiro, km_roteiro_reta = montar_roteiro(df_odis, lat_cap, lon_cap)
    # Fase 2: o percurso entre as UCs de cada obra soma ao roteiro; so entao vira estrada.
    km_interno_reta = float(roteiro["dist_interna_km"].sum()) if len(roteiro) else 0.0
    km_estrada = (km_roteiro_reta + km_interno_reta) * config.FATOR_RODOVIARIO
    # Fase 3: km -> horas de estrada; UCs -> horas de inspecao pela produtividade do tipo (G5).
    horas_roteiro = km_estrada / config.VELOCIDADE_KMH
    n_ucs = int(roteiro["n_ucs"].sum()) if len(roteiro) else 0
    horas_por_uc = config.HORAS_DIA_CAMPO / config.UCS_POR_DIA[tipo_contrato]
    horas_inspecao = n_ucs * horas_por_uc
    # Fase 4: dias de trabalho arredondados PARA CIMA (a equipe nao vende meio dia),
    # mais os dias de mobilizacao. A fracao fica exposta para o humano conferir o teto.
    horas_campo = horas_roteiro + horas_inspecao
    dias_fracionarios = horas_campo / config.HORAS_DIA_CAMPO
    dias_trabalho = math.ceil(dias_fracionarios) if dias_fracionarios > 0 else 0
    dias_faturados = dias_trabalho + config.DIAS_MOBILIZACAO
    # Fase 5: dias -> R$ (pessoa-dia = jornada x tarifa) e o fixo de escritorio, uma vez.
    custo_campo = dias_faturados * config.TAMANHO_EQUIPE * config.HORAS_DIA_CAMPO * tarifa_campo()
    custo_fixo = config.HORAS_ESCRITORIO_POR_OS * tarifa_escritorio()
    # Anota no detalhe o km de estrada de cada trecho (so exibicao; o total ja esta fechado).
    if len(roteiro):
        roteiro = roteiro.copy()
        roteiro["km_trecho_estrada"] = roteiro["km_trecho"] * config.FATOR_RODOVIARIO
    # Saida: os numeros da amostra + o roteiro que os gerou.
    return {
        "n_odis": len(roteiro),
        "n_municipios": int(roteiro["Municipio"].nunique()) if len(roteiro) else 0,
        "n_ucs": n_ucs,
        "km_roteiro": km_estrada,
        "horas_roteiro": horas_roteiro,
        "horas_inspecao": horas_inspecao,
        "dias_fracionarios": dias_fracionarios,
        "dias_trabalho": dias_trabalho,
        "dias_faturados": dias_faturados,
        "tamanho_equipe": config.TAMANHO_EQUIPE,
        "custo_campo": custo_campo,
        "custo_fixo": custo_fixo,
        "custo_total": custo_campo + custo_fixo,
    }, roteiro


def tabela_resumo(resultados):
    """Empilha os resultados de varias amostras numa unica tabela comparavel.

    Por que existe: a Entrada/ traz varias estratificacoes (Estratos 3, 4, 5...) x 3
    amostras cada; o humano precisa ver todas lado a lado para escolher. Montar a
    tabela aqui - e nao em resumo.py - mantem resumo.py como pura gravacao de Excel.

    Logica: Entrada (lista de dicts com n_estratos/amostra/numeros) -> Fase 1: ordena
    por estratificacao e depois por amostra -> Saida: DataFrame, uma linha por amostra.
    """
    # Fase 1: ordem estavel e previsivel para leitura (N crescente, amostra crescente).
    df = pd.DataFrame(resultados)
    if len(df):
        df = df.sort_values(["n_estratos", "amostra"]).reset_index(drop=True)
    # Saida: uma linha por (estratificacao, amostra).
    return df
