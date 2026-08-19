# -*- coding: utf-8 -*-
"""Motor de custo: transforma a geometria de uma amostra em R$ (modelo F15).

=== MEMORIA DE CALCULO (para humanos) ===
[Mesmo bloco de src/config.py -- duplicado de proposito: quem abrir qualquer um dos
dois arquivos entende o calculo sem ler mais nada.]

O custo e' POR AMOSTRA (nao por estrato):

  custo_amostra = CUSTO_FIXO + custo_campo

  CUSTO_FIXO  = horas de escritorio DO TIPO x tarifa_escritorio (1x por amostra)
                LPT: 8+24+4 = 36h x 360 = 12.960 | MLA: 4+16+4 = 24h x 360 = 8.640
  custo_campo = N_EQUIPES x TAMANHO_EQUIPE x dias_faturados x HORAS_DIA_CAMPO x tarifa_campo

  dias_faturados = teto(horas da equipe MAIS LENTA / (HORAS_DIA_CAMPO x TAMANHO_EQUIPE))
                   + DIAS_MOBILIZACAO

As N equipes sao INDEPENDENTES: o itinerario e' cortado em N blocos geograficos
contiguos e cada equipe sai da capital, varre o seu bloco e volta. Tres consequencias
que o modelo anterior (uma equipe so, trabalho perfeitamente divisivel) escondia:

  - o km SOMADO cresce ao dividir, porque a ida e a volta sao cobradas uma vez por
    equipe (+18% a +37% com duas equipes, nos dados reais);
  - o prazo e' ditado pela equipe MAIS LENTA, nao pela media;
  - mais equipes NAO barateiam (o contrato paga por hora-profissional): encarecem, pelo
    km extra, pelo dia de mobilizacao de cada equipe e pelo arredondamento para dia
    inteiro.

  Por equipe:
    horas_campo    = horas_roteiro + horas_inspecao
    horas_roteiro  = km_estrada / VELOCIDADE_KMH
      km_estrada   = FATOR_RODOVIARIO x (roteiro do bloco: capital -> obras -> capital,
                     + percurso entre as UCs de cada obra)
    horas_inspecao = n_ucs do bloco x (HORAS_DIA_CAMPO / UCS_POR_DIA[tipo])
                     (LPT 30/dia; MLA 3/dia)

O ESTRATO nao participa do custo. Ele identifica de onde cada obra veio na
estratificacao e aparece so como coluna informativa no detalhe.

BENCHMARK: a engenharia da PB 7a Tranche obedece, ao centavo, a
  custo = 12.960 + 9.600 x (dias + 1), com 9.600 = 2 pessoas x 8h x R$600.
E' esta formula com TAMANHO_EQUIPE = 2 e N_EQUIPES = 1 (uma dupla, UM roteiro). O
padrao daqui - N_EQUIPES = 2, TAMANHO_EQUIPE = 1 - tem a mesma mao de obra e custa
MAIS, porque sao dois roteiros em vez de um.
=== FIM DA MEMORIA DE CALCULO ===
"""
import math

import pandas as pd

from src import config
from src.distancias import dividir_roteiro


def tarifa_campo(tipo_contrato):
    """Tarifa horaria de campo do perfil ativo, com diaria diluida por hora.

    Por que existe: G1/G2 do gate viram parametros; le config NA CHAMADA (nao no
    import) para monkeypatch e ajustes sem rebuild funcionarem. Recebe o tipo do
    contrato porque o Formulario de OS tem uma tabela de perfil por tipo de obra -
    o engenheiro custa igual nos dois, o tecnico nao.

    Logica: Entrada (tipo do contrato) -> Fase 1: tarifa 'campo' do perfil ativo naquele
    tipo -> Fase 2: soma CUSTO_DIARIA diluida pela jornada -> Saida: R$/hora.
    """
    # Fase 1: tarifa de campo (COM deslocamento) do perfil ativo (G1: ENGENHEIRO).
    base = config.TARIFAS_HORA[tipo_contrato][config.PERFIL_EQUIPE]["campo"]
    # Fase 2: diaria (G2: 0 por padrao) diluida pelas horas do dia de campo.
    return base + config.CUSTO_DIARIA / config.HORAS_DIA_CAMPO


def tarifa_escritorio(tipo_contrato):
    """Tarifa horaria de escritorio (sem deslocamento) do perfil ativo.

    Por que existe: par do tarifa_campo() para o termo fixo por OS; le config na
    chamada pelo mesmo motivo.

    Logica: Entrada (tipo do contrato) -> Fase 1: tarifa 'escritorio' do perfil naquele
    tipo -> Saida: R$/h.
    """
    # Fase 1/Saida: tarifa SEM deslocamento do perfil ativo naquele tipo de contrato.
    return config.TARIFAS_HORA[tipo_contrato][config.PERFIL_EQUIPE]["escritorio"]


def horas_escritorio(tipo_contrato):
    """Horas de escritorio de uma OS: planejamento + relatorio + apresentacao.

    Por que existe: o Formulario de OS decide essas horas por um parametro binario
    ('Tipo de obra', celula E48) que o modelo ignorava ate 2026-08-13 - eram 36 h fixas,
    que sao as da Extensao de Redes. Geracao Descentralizada usa 24 h. Somar aqui, a
    partir do desdobramento por etapa, mantem o config conferivel contra a planilha
    original (que mostra as tres etapas separadas) sem espalhar a soma pelo codigo.

    Logica: Entrada (tipo do contrato) -> Fase 1: pega as etapas daquele tipo ->
    Saida: total de horas de escritorio da amostra.
    """
    # Fase 1/Saida: soma das tres etapas de escritorio do tipo (LPT 36 h, MLA 24 h).
    return sum(config.HORAS_ESCRITORIO_POR_TIPO[tipo_contrato].values())


def horas_por_uc(tipo_contrato):
    """Horas que uma UC consome na inspecao, pela produtividade do tipo de contrato.

    Por que existe: o mesmo numero e' usado no custo oficial e no pre-filtro da grade de
    cenarios; uma funcao evita as duas copias divergirem. Le config na chamada.

    Logica: Entrada (tipo do contrato) -> Fase 1: jornada / UCs por dia daquele tipo ->
    Saida: horas por UC (LPT 8/30; MLA 8/3).
    """
    # Fase 1/Saida: a jornada dividida pela produtividade diaria do tipo (decisao G5).
    return config.HORAS_DIA_CAMPO / config.UCS_POR_DIA[tipo_contrato]


def repartir_entre_equipes(df_odis, uf, tipo_contrato, n_equipes):
    """Divide a amostra entre N equipes independentes e mede o campo de cada uma.

    Por que existe: e' a ponte entre a geometria (distancias.py) e o R$ (este modulo),
    e o lugar onde a divisao deixa de ser aproximacao. Antes da F15 o custo assumia o
    trabalho perfeitamente divisivel - N equipes rodariam os mesmos km que uma. Aqui
    cada equipe recebe um bloco geografico e roteia a partir da capital, o que cobra a
    ida e a volta de CADA uma. Funcao separada porque tanto o custo oficial quanto cada
    linha da grade de cenarios precisam exatamente disto.

    Logica: Entrada (df por ODI, uf, tipo, n_equipes) -> Fase 1: corta o itinerario em
    N blocos contiguos, cada um roteado da capital -> Fase 2: por bloco, soma o percurso
    interno das obras e converte linha reta em estrada -> Fase 3: km -> horas de roteiro,
    UCs -> horas de inspecao -> Saida: lista de dicts, um por equipe (na ordem geografica
    do itinerario de referencia).
    """
    # Capital da UF do contrato (G3); KeyError aqui = UF invalida (bug, nao dado).
    lat_cap, lon_cap = config.CAPITAIS_UF[uf]
    # Fase 1: um roteiro por equipe, cada um fechado na capital. Pode devolver MENOS
    # rotas que equipes pedidas quando ha menos obras que equipes - quem chama decide.
    rotas = dividir_roteiro(df_odis, lat_cap, lon_cap, n_equipes)
    por_uc = horas_por_uc(tipo_contrato)
    equipes = []
    for roteiro, km_reta in rotas:
        # Fase 2: o percurso entre as UCs de cada obra soma ao roteiro; so entao vira estrada.
        km_interno = float(roteiro["dist_interna_km"].sum()) if len(roteiro) else 0.0
        km_estrada = (km_reta + km_interno) * config.FATOR_RODOVIARIO
        n_ucs = int(roteiro["n_ucs"].sum()) if len(roteiro) else 0
        # Fase 3: as duas parcelas do dia de campo desta equipe.
        horas_roteiro = km_estrada / config.VELOCIDADE_KMH
        horas_inspecao = n_ucs * por_uc
        equipes.append({
            "roteiro": roteiro,
            "n_odis": len(roteiro),
            "n_ucs": n_ucs,
            "km_estrada": km_estrada,
            "horas_roteiro": horas_roteiro,
            "horas_inspecao": horas_inspecao,
            "horas_campo": horas_roteiro + horas_inspecao,
        })
    # Saida: uma entrada por equipe que de fato tem obra.
    return equipes


def _dias_para(horas_da_equipe_mais_lenta):
    """Converte as horas da equipe critica em dias inteiros de trabalho.

    Por que existe: o arredondamento para cima e a divisao pelo TAMANHO_EQUIPE aparecem
    no custo oficial e na grade; concentrar aqui evita que uma das duas esqueca um dos
    dois passos (foi exatamente o defeito corrigido na F10).

    Logica: Entrada (horas da equipe mais lenta) -> Fase 1: divide pela capacidade
    diaria da equipe (jornada x pessoas) -> Fase 2: arredonda para cima, porque a
    equipe nao vende meio dia -> Saida: (dias inteiros, fracao antes do arredondamento).
    """
    # Fase 1: capacidade de um dia = jornada x pessoas da equipe.
    fracao = horas_da_equipe_mais_lenta / (config.HORAS_DIA_CAMPO * config.TAMANHO_EQUIPE)
    # Fase 2: teto - meio dia de equipe nao existe no contrato.
    return (math.ceil(fracao) if fracao > 0 else 0), fracao


def _custo_campo(n_equipes, dias_faturados, tipo_contrato):
    """Preco do campo: pessoas x dias x jornada x tarifa.

    Por que existe: a mesma multiplicacao vale para o numero oficial e para cada linha
    da grade; duplicar seria convidar as duas a divergirem.

    Logica: Entrada (n de equipes, dias faturados, tipo) -> Fase 1: pessoas em campo =
    equipes x tamanho da equipe -> Saida: R$ (o contrato paga por hora-PROFISSIONAL).
    """
    # Fase 1/Saida: cada pessoa de cada equipe cobra a jornada inteira de cada dia faturado.
    return (n_equipes * config.TAMANHO_EQUIPE * dias_faturados
            * config.HORAS_DIA_CAMPO * tarifa_campo(tipo_contrato))


def _custo_fixo(tipo_contrato):
    """Termo fixo de escritorio da amostra: horas da OS x tarifa sem deslocamento.

    Por que existe: entra UMA vez por amostra (correcao da F9) e agora depende do tipo
    (correcao da F16); tres call sites precisavam do mesmo par horas x tarifa.

    Logica: Entrada (tipo do contrato) -> Saida: R$ (LPT 36h x 360; MLA 24h x 360).
    """
    # Saida: as horas de escritorio daquele tipo, a tarifa sem deslocamento do perfil.
    return horas_escritorio(tipo_contrato) * tarifa_escritorio(tipo_contrato)


def custo_amostra(df_odis, uf, tipo_contrato, n_equipes=None):
    """Precifica uma amostra inteira a partir do resumo geometrico por ODI.

    Por que existe: e' o UNICO lugar onde a formula de custo vive. Trabalha na
    granularidade AMOSTRA porque e' assim que o custo se comporta: o fixo de escritorio
    e' uma OS so, e o roteiro de cada equipe e' uma viagem so (nao da para somar viagens
    por obra). Devolver tambem o detalhe por obra - ja com a equipe dona de cada uma -
    evita que o resumo recalcule a divisao por conta propria e acabe discordando.

    Logica: Entrada (df por ODI, uf, tipo, n_equipes) -> Fase 1: reparte a amostra entre
    as equipes e mede o campo de cada uma -> Fase 2: o prazo e' o da equipe MAIS LENTA,
    em dias inteiros, mais a mobilizacao -> Fase 3: dias -> R$, mais o fixo de
    escritorio -> Fase 4: empilha os roteiros das equipes num detalhe so -> Saida:
    (dict com os numeros da amostra, df do detalhe por obra).
    """
    # Padrao vem de config (decisao do humano: 2 equipes independentes).
    n_equipes = config.N_EQUIPES_PADRAO if n_equipes is None else int(n_equipes)
    # Fase 1: a divisao concreta - cada equipe com o seu roteiro saindo da capital.
    equipes = repartir_entre_equipes(df_odis, uf, tipo_contrato, n_equipes)
    # Mais equipes que obras: quem manda e' quantas equipes REALMENTE tem servico.
    # Faturar as ociosas seria cobrar por gente que nao sai da garagem.
    n_efetivo = max(1, len(equipes))
    # Fase 2: o prazo tem de caber para TODAS - quem dita e' a equipe mais lenta.
    horas_criticas = max((e["horas_campo"] for e in equipes), default=0.0)
    dias_trabalho, dias_fracionarios = _dias_para(horas_criticas)
    dias_faturados = dias_trabalho + config.DIAS_MOBILIZACAO
    # Fase 3: dias -> R$ e o fixo de escritorio, uma vez por amostra (e por tipo).
    custo_campo = _custo_campo(n_efetivo, dias_faturados, tipo_contrato)
    custo_fixo = _custo_fixo(tipo_contrato)
    # Fase 4: um detalhe so, com a equipe dona de cada obra. A ordem dentro de cada
    # equipe e' a ordem de visita dela; equipes entram na ordem geografica do itinerario.
    detalhes = []
    for i, equipe in enumerate(equipes, start=1):
        roteiro = equipe["roteiro"].copy()
        if len(roteiro):
            roteiro["equipe"] = i
            # km de estrada de cada trecho (so exibicao; o total ja esta fechado acima).
            roteiro["km_trecho_estrada"] = roteiro["km_trecho"] * config.FATOR_RODOVIARIO
        detalhes.append(roteiro)
    detalhe = pd.concat(detalhes, ignore_index=True) if detalhes else pd.DataFrame()
    # Saida: os numeros da amostra + o detalhe que os gerou.
    return {
        "n_odis": sum(e["n_odis"] for e in equipes),
        "n_municipios": int(detalhe["Municipio"].nunique()) if len(detalhe) else 0,
        "n_ucs": sum(e["n_ucs"] for e in equipes),
        "n_equipes": n_efetivo,
        # O tipo viaja com os numeros porque a planilha precisa dele para explicar as
        # horas de escritorio no Leia-me (elas mudam com ele).
        "tipo_contrato": tipo_contrato,
        "horas_escritorio": horas_escritorio(tipo_contrato),
        "km_roteiro": sum(e["km_estrada"] for e in equipes),
        "horas_roteiro": sum(e["horas_roteiro"] for e in equipes),
        "horas_inspecao": sum(e["horas_inspecao"] for e in equipes),
        "horas_equipe_critica": horas_criticas,
        "dias_fracionarios": dias_fracionarios,
        "dias_trabalho": dias_trabalho,
        "dias_faturados": dias_faturados,
        "tamanho_equipe": config.TAMANHO_EQUIPE,
        "custo_campo": custo_campo,
        "custo_fixo": custo_fixo,
        "custo_total": custo_campo + custo_fixo,
    }, detalhe


def grade_cenarios(df_odis, uf, tipo_contrato):
    """Varre as combinacoes viaveis de (numero de equipes x prazo) e precifica cada uma.

    Por que existe: o numero oficial responde "quanto custa"; a pergunta que sobra na
    mesa de planejamento e' "e se eu precisar terminar antes - ou se eu so tiver 3
    equipes?". A grade responde as duas de uma vez, porque varre as duas dimensoes.
    Substituiu (F15) a antiga cenarios_por_prazo, que varria so o prazo em torno do
    calculado e, pior, assumia o trabalho perfeitamente divisivel: ela contava equipes
    sem nunca reparti-las de fato, entao o km extra de cada equipe nunca aparecia.

    Desde 2026-08-19 a grade varre o ESPECTRO INTEIRO de prazos, de 1 dia ao teto -
    inclusive os prazos que o nosso proprio modelo diz que nao cabem. Motivo, e e' o
    motivo que mais importa neste arquivo: a engenharia dimensionou 12 UCs em 2 equipes
    x 4 dias, e essa linha simplesmente NAO EXISTIA na aba, porque o nosso minimo
    geometrico para 2 equipes era 7 dias. Uma aba que se chama 'Cenarios' e nao contem o
    cenario que a engenharia adotou nao esta protegendo ninguem do impossivel: esta
    escondendo o numero que a mesa de decisao precisa ver. O veredito do modelo e' DADO
    (coluna 'cabe'), nao filtro. O preco continua exato: o custo nao depende de a equipe
    dar conta do servico.

    Houve por algumas horas uma TERCEIRA dimensao aqui - a produtividade, varrendo
    tambem 1,5 UC/dia (o numero que a engenharia usa no MLA). Saiu a pedido do humano, e
    vale registrar por que, para nao voltar por engano: o custo NAO depende da
    produtividade (so 'cabe' e 'ocupacao' dependem), e o bloco alternativo nao trazia
    nenhuma combinacao equipes x prazo que o oficial ja nao tivesse - produtividade menor
    so ELIMINA numeros de equipe, nunca acrescenta. Metade das linhas da aba era
    duplicata exata em (equipes, prazo, custo). O espectro inteiro de prazos ja resolve
    sozinho o problema que a varredura de produtividade tinha vindo resolver.

    Duas regras de corte sobrevivem, ambas decisao do humano:
      - de N_EQUIPES_MIN a N_EQUIPES_MAX equipes;
      - numero de equipes cujo prazo minimo passa de MAX_DIAS_POR_EQUIPE nao entra na aba.
    A segunda e' a regra da F15 ("sequer calcule") e continua valendo INTEIRA: ela fala de
    um numero de equipes que nao tem NENHUM prazo viavel dentro do teto - nao ha o que
    apresentar. O que mudou e' o de dentro: escolhido um numero de equipes que funciona,
    todos os prazos ate o teto aparecem, porque ai o prazo e' alavanca do usuario.
    Combinacao que estoura o teto NAO e' calculada nem exibida. O caso que motivou a
    regra: 80 UCs de MLA (3 UCs/dia) sao 27 dias so de inspecao para uma equipe -
    flagrantemente inviavel, e nao ha o que apresentar. O pre-filtro usa exatamente
    esse limite inferior (so inspecao, dividida igualmente) para descartar ANTES de
    rotear, que e' a parte cara.

    Logica: Entrada (df por ODI, uf, tipo) -> Fase 1: amostra vazia nao tem grade ->
    Fase 2: para cada numero de equipes, descarta pelo limite inferior de inspecao sem
    rotear -> Fase 3: reparte de fato e acha o prazo minimo daquele numero de equipes
    (numero de equipes sem nenhum prazo viavel sai aqui) -> Fase 4: uma linha por prazo,
    de 1 ao teto, marcando quais cabem -> Saida: lista de dicts.
    """
    # Fase 1: sem obra nao ha prazo a explorar.
    if not len(df_odis):
        return []
    capacidade_dia = config.HORAS_DIA_CAMPO * config.TAMANHO_EQUIPE
    # Total de horas de inspecao da amostra - nao depende de como se divide.
    horas_inspecao_total = float(df_odis["n_ucs"].sum()) * horas_por_uc(tipo_contrato)
    linhas = []
    # Fase 2: um bloco por numero de equipes.
    for n in range(config.N_EQUIPES_MIN, config.N_EQUIPES_MAX + 1):
        # Mais equipes que obras nao e' cenario: alguem ficaria sem servico.
        if n > len(df_odis):
            break
        # Pre-filtro barato: mesmo distribuindo a inspecao em partes iguais e ignorando
        # TODO o deslocamento, ja passa do teto? Entao nao ha o que rotear.
        if horas_inspecao_total / (n * capacidade_dia) > config.MAX_DIAS_POR_EQUIPE:
            continue
        # Fase 3: a divisao real, com o roteiro de cada equipe saindo da capital.
        equipes = repartir_entre_equipes(df_odis, uf, tipo_contrato, n)
        n_efetivo = len(equipes)
        horas_criticas = max((e["horas_campo"] for e in equipes), default=0.0)
        dias_minimo, _ = _dias_para(horas_criticas)
        # Com o deslocamento contado, o teto pode estourar mesmo tendo passado no pre-filtro.
        if dias_minimo > config.MAX_DIAS_POR_EQUIPE:
            continue
        horas_totais = sum(e["horas_campo"] for e in equipes)
        km_somado = sum(e["km_estrada"] for e in equipes)
        # O fixo nao depende do prazo nem do numero de equipes - so do tipo do contrato.
        custo_fixo = _custo_fixo(tipo_contrato)
        # Fase 4: o espectro inteiro de prazos, de 1 dia ao teto. Abaixo do minimo a linha
        # sai com 'cabe' False (o modelo diz que a equipe nao termina); acima do minimo e'
        # folga deliberada - a equipe fica ociosa e o custo sobe, porque ha mais dias
        # faturados. Nos dois casos o PRECO e' exato: o contrato paga por hora-profissional
        # contratada, dando ela conta do servico ou nao.
        for dias in range(1, config.MAX_DIAS_POR_EQUIPE + 1):
            dias_faturados = dias + config.DIAS_MOBILIZACAO
            custo_campo = _custo_campo(n_efetivo, dias_faturados, tipo_contrato)
            linhas.append({
                "n_equipes": n_efetivo,
                "dias_trabalho": dias,
                "dias_faturados": dias_faturados,
                # O veredito do modelo sobre esta combinacao, como DADO e nao como filtro:
                # cabe se o prazo alcanca o minimo que a geometria exige.
                "cabe": dias >= dias_minimo,
                "km_roteiro": km_somado,
                # Ocupacao = quanto da capacidade contratada e' realmente usada. Baixa
                # demais significa que o prazo esta pagando por gente parada. CUIDADO: ela
                # e' a MEDIA das equipes, enquanto 'cabe' olha a MAIS LENTA - com blocos
                # desiguais, uma linha pode nao caber com ocupacao abaixo de 100%.
                "ocupacao": horas_totais / (n_efetivo * capacidade_dia * dias),
                "custo_campo": custo_campo,
                "custo_fixo": custo_fixo,
                "custo_total": custo_campo + custo_fixo,
                # Marca a linha que corresponde ao numero oficial da aba Resumo.
                "cenario": ("calculado" if n_efetivo == config.N_EQUIPES_PADRAO
                            and dias == dias_minimo else ""),
            })
    # Saida: as combinacoes viaveis, por numero de equipes e depois por prazo.
    return linhas


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
