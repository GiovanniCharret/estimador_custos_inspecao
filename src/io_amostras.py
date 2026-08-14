# -*- coding: utf-8 -*-
"""Leitura e validacao das entradas do estimador (Lote de amostras + Painel de coordenadas)."""
from pathlib import Path
import re

import pandas as pd

from src import config

# Bounding box aproximada do Brasil: coordenada fora daqui e' erro de digitacao/projecao.
BBOX_BRASIL = {"lat_min": -34.0, "lat_max": 5.5, "lon_min": -74.0, "lon_max": -34.0}

# Trecho que o nome do arquivo de coordenadas precisa conter (convencao D7).
# O arquivo real e' o "Anexo V - Painel de Monitoramento preenchido - <CONTRATO>.xlsx",
# saida do projeto irmao monitoramentolpt_producao_enbpar. Exigimos "Anexo V" (e nao
# "Painel de Monitoramento") porque e' o rotulo do anexo no contrato: estavel entre
# tranches e o que o usuario reconhece.
PADRAO_ARQUIVO_COORDENADAS = "Anexo V"

# Apelidos de cabecalho do Painel: nome real (ja normalizado por _norm) -> nome interno.
# Por que existe: o Painel real e' o "Anexo V - Painel de Monitoramento", saida do projeto
# irmao (monitoramentolpt_producao_enbpar), cujos cabecalhos sao PETREOS - 'Numero ODI' e
# 'Numero da Unidade Consumidora' em vez de 'ODI'/'UC'. Mapear aqui evita espalhar
# condicionais de nome pelo leitor e aceita tambem os paineis antigos (que ja usavam ODI/UC).
ALIAS_PAINEL = {
    "odi": "odi",
    "numero odi": "odi",
    "n odi": "odi",
    "uc": "uc",
    "numero da unidade consumidora": "uc",
    "numero da uc": "uc",
    "municipio": "municipio",
    "latitude": "latitude",
    "longitude": "longitude",
    # Classificacao do beneficiario: escolha UNICA por UC, de uma lista suspensa cujo
    # dominio mora na aba 'Dominios' (colunas D e E). Alimentam a aba 'Resumo
    # beneficiarios' e nao participam de nenhum calculo de custo.
    "tipo de comunidade": "tipo_comunidade",
    "enquadramento do beneficiario": "enquadramento",
}

# Colunas sem as quais o Painel nao serve para nada (a UC, o municipio e a classificacao
# do beneficiario sao opcionais - sem elas o custo sai igual).
COLUNAS_MINIMAS_PAINEL = {"odi", "latitude", "longitude"}

# Aba e colunas dos DOMINIOS das listas suspensas do Anexo V. As colunas D e E sao as
# duas classificacoes do beneficiario, e cada uma vira um bloco de colunas da aba
# 'Resumo beneficiarios'. Ler o dominio da planilha (em vez de deduzir dos valores
# presentes) e' o que garante que uma categoria com ZERO ocorrencias apareca mesmo assim -
# na leitura gerencial, "nenhuma familia indigena" e' informacao, nao ausencia de linha.
ABA_DOMINIOS = "Dominios"
COLUNAS_DOMINIOS = {
    # coluna da aba 'Dominios' -> coluna interna do painel que ela classifica
    "D": "tipo_comunidade",
    "E": "enquadramento",
}

# Linhas de cabecalho testadas no Painel, nesta ordem. A 0 cobre o formato simples
# (e todos os testes sinteticos); a 1 cobre o Anexo V real, cuja primeira linha e' uma
# faixa MESCLADA de grupos ('Identificacao minima' / 'Classificacao geral') e o cabecalho
# de verdade mora na segunda linha.
LINHAS_CABECALHO_PAINEL = (0, 1)


class EntradaInvalida(Exception):
    """Erro de entrada com mensagem pronta para o usuario final.

    Por que existe: separa erros de dados (culpa da entrada, mensagem amigavel,
    exit 1 sem traceback) de bugs do programa (traceback normal).
    """


def achar_entradas(pasta):
    """Localiza as planilhas de amostra e o painel de coordenadas dentro de Entrada/.

    Por que existe: o sistema amostral upstream gera UMA planilha por numero de estratos
    ('Estratos 3/4/5/6 - Python.xlsx', as vezes renomeada para 'Lote.xlsx') e o humano
    quer precificar TODAS de uma vez para escolher a estratificacao. Descobrir os arquivos
    pelo CONTEUDO (ter abas 'Amostra K') em vez de por um nome fixo evita que uma
    estratificacao seja ignorada em silencio so por causa do nome do arquivo.

    Logica: Entrada (pasta) -> Fase 1: acha o arquivo de coordenadas pelo nome (contendo
    PADRAO_ARQUIVO_COORDENADAS, D7) e exige exatamente 1 -> Fase 2: varre os demais .xlsx
    e fica com os que tem aba 'Amostra K' -> Fase 3:
    descobre o numero de estratos de cada um e descarta duplicatas com aviso -> Saida:
    (lista de (n_estratos, caminho) ordenada por n, caminho do painel).
    """
    pasta = Path(pasta)
    # Fase 1: o painel e' localizado por nome contendo o padrao (D7), ignorando temporarios (~$).
    paineis = [p for p in pasta.glob(f"*{PADRAO_ARQUIVO_COORDENADAS}*.xlsx")
               if not p.name.startswith("~$")]
    # Nenhum painel: aborta explicando a convencao de nome e listando o que ha na pasta,
    # que e' o que permite ao usuario ver que o arquivo dele so tem o nome errado.
    if not paineis:
        presentes = sorted(p.name for p in pasta.glob("*.xlsx") if not p.name.startswith("~$"))
        raise EntradaInvalida(
            f"Arquivo de coordenadas nao encontrado.\n"
            f"Coloque em {pasta}\\ um .xlsx cujo nome contenha "
            f"'{PADRAO_ARQUIVO_COORDENADAS}'.\n"
            f"Arquivos que existem hoje nessa pasta: {presentes or 'nenhum'}"
        )
    # Mais de um painel: ambiguidade - aborta listando para o usuario remover o excedente.
    if len(paineis) > 1:
        nomes = "\n  - ".join(p.name for p in paineis)
        raise EntradaInvalida(
            f"Mais de um arquivo '{PADRAO_ARQUIVO_COORDENADAS}' em {pasta}:\n  - {nomes}\n"
            f"Deixe apenas um."
        )
    painel = paineis[0]
    # Fase 2: candidato a planilha de amostra = qualquer .xlsx (menos o painel) com aba 'Amostra K'.
    candidatos = []
    for arquivo in sorted(pasta.glob("*.xlsx")):
        if arquivo.name.startswith("~$") or arquivo == painel:
            continue
        # Le apenas os NOMES das abas; arquivo ilegivel simplesmente nao e' candidato.
        try:
            abas = pd.ExcelFile(arquivo).sheet_names
        except Exception:
            continue
        if any(re.fullmatch(r"Amostra\s*\d+", str(a).strip()) for a in abas):
            candidatos.append(arquivo)
    # Sem nenhuma planilha de amostra: aborta dizendo o que colocar na pasta.
    if not candidatos:
        raise EntradaInvalida(
            f"Nenhuma planilha de amostras encontrada em {pasta}.\n"
            f"Coloque ali o(s) arquivo(s) gerado(s) pelo sistema amostral - 'Lote.xlsx' ou\n"
            f"'Estratos N - Python.xlsx' - que tenham abas 'Amostra 1/2/3'."
        )
    # Fase 3: descobre o N de cada candidato; duas planilhas com o mesmo N seriam a mesma
    # estratificacao contada duas vezes, entao a segunda e' descartada COM aviso.
    lotes = {}
    for arquivo in candidatos:
        n = ler_n_estratos(arquivo)
        if n in lotes:
            print(f"AVISO: {arquivo.name} declara {n} estratos, igual a {lotes[n].name}; "
                  f"sera IGNORADO para nao contar a mesma estratificacao duas vezes.")
            continue
        lotes[n] = arquivo
    # Saida: estratificacoes ordenadas por numero de estratos + o painel.
    return [(n, lotes[n]) for n in sorted(lotes)], painel


def ler_n_estratos(caminho):
    """Descobre quantos estratos uma planilha de amostras usa.

    Por que existe: o numero de estratos e' o rotulo que distingue uma estratificacao da
    outra no resumo final, e ele NAO esta nas abas de amostra - so na aba 'Leia-me' que o
    sistema upstream escreve. Ter os tres caminhos aqui (Leia-me, nome do arquivo, contagem)
    evita que o programa recuse uma planilha valida so porque o Leia-me sumiu.

    Logica: Entrada (caminho) -> Fase 1: procura na aba 'Leia-me' a linha 'N (estratos por
    grupo)' -> Fase 2: se nao achou, tenta o numero no nome do arquivo ('Estratos 4 - ...')
    -> Fase 3: em ultimo caso conta os estratos distintos da primeira aba de amostra, com
    aviso -> Saida: int.
    """
    xls = pd.ExcelFile(caminho)
    # Fase 1: o Leia-me do upstream traz 'Campo | Valor'; procuramos a linha do N.
    if "Leia-me" in xls.sheet_names:
        leia = xls.parse("Leia-me", header=None)
        for _, linha in leia.iterrows():
            # A primeira celula e' o rotulo; normalizamos para nao depender de acento/caixa.
            rotulo = _norm(linha.iloc[0]) if len(linha) else ""
            if rotulo.startswith("n (estratos por grupo)"):
                try:
                    return int(float(linha.iloc[1]))
                except (ValueError, TypeError):
                    # Rotulo achado mas valor ilegivel: cai nos proximos caminhos.
                    break
    # Fase 2: nome do arquivo no padrao do upstream ('Estratos 4 - Python.xlsx').
    achado = re.search(r"estratos\s*(\d+)", caminho.name, flags=re.IGNORECASE)
    if achado:
        return int(achado.group(1))
    # Fase 3: ultimo recurso - conta os estratos distintos da primeira aba de amostra.
    for aba in xls.sheet_names:
        if re.fullmatch(r"Amostra\s*\d+", str(aba).strip()):
            df = xls.parse(aba)
            colmap = {_norm(c): c for c in df.columns}
            if "estrato" in colmap:
                # So as obras SORTEADAS contam: a aba traz o lote inteiro, e as linhas nao
                # selecionadas podem carregar rotulos de estrato que nao existem na amostra.
                if "status" in colmap:
                    df = df[df[colmap["status"]].astype(str).str.strip() == "Selecionado"]
                n = int(df[colmap["estrato"]].dropna().nunique())
                print(f"AVISO: {caminho.name} nao diz quantos estratos usa (sem 'Leia-me' nem "
                      f"numero no nome); contei {n} estratos distintos na aba '{aba}'.")
                return n
            break
    # Nenhum caminho funcionou: e' erro de dado, com instrucao de como resolver.
    raise EntradaInvalida(
        f"Nao consegui descobrir quantos estratos {caminho.name} usa.\n"
        f"Renomeie o arquivo para 'Estratos N - Python.xlsx' (N = numero de estratos)\n"
        f"ou mantenha a aba 'Leia-me' gerada pelo sistema amostral."
    )


def _norm(nome):
    """Normaliza nome de coluna (minusculas, sem acento, sem ponto final) para deteccao robusta.

    Por que existe: os cabecalhos reais variam (com/sem acento, com ponto final como em
    'Cons.'); concentrar a normalizacao aqui evita repetir esse tratamento nos leitores.

    Logica: Entrada (nome) -> Fase 1: string, sem espacos nas pontas, minusculas -> Fase 2:
    traduz acentos comuns -> Fase 3: remove ponto final (ex.: 'Cons.' -> 'cons') -> Saida: chave normalizada.
    """
    # Fase 1: garante string, tira espacos nas pontas e baixa a caixa.
    s = str(nome).strip().lower()
    # Fase 2: traduz acentos comuns; suficiente para os cabecalhos reais do Lote/Painel.
    tabela = str.maketrans("áàâãéêíóôõúç", "aaaaeeiooouc")
    s = s.translate(tabela)
    # Fase 3: remove ponto final (cabecalhos como 'Cons.' viram 'cons').
    return s.rstrip(".")


def _norm_odi(valor):
    """Normaliza uma ODI para a forma canonica de juncao (so digitos, sem zeros a esquerda).

    Por que existe: a MESMA ODI chega escrita de dois jeitos. No Lote.xlsx ela e' TEXTO com
    zeros a esquerda ('0012500186'); no Painel e' NUMERO ('12500186', que o pandas pode ainda
    entregar como float '12500186.0'). Sem normalizar, a juncao por ODI depende de o pandas ter
    convertido a coluna inteira para inteiro - basta uma celula suja no Lote para a coluna virar
    texto, a intersecao dar zero e o programa acusar 'tranche errada', que e' um erro FALSO e
    muito confuso. Normalizar os dois lados torna a chave imune a como cada planilha guardou.

    Logica: Entrada (valor de celula) -> Fase 1: string sem espacos nas pontas -> Fase 2: se veio
    como float inteiro ('12500186.0'), corta a parte decimal -> Fase 3: se sobrou so digitos,
    remove zeros a esquerda -> Saida: chave canonica. IDs nao numericos (ex.: 'PA001' das
    fixtures) passam intactos, pois neles o zero a esquerda pode ser significativo.
    """
    # Fase 1: garante string e tira espacos nas pontas.
    s = str(valor).strip()
    # Fase 2: float inteiro vindo do Excel ('12500186.0') volta a ser inteiro textual.
    if re.fullmatch(r"\d+\.0+", s):
        s = s.split(".")[0]
    # Fase 3: so mexe em ODI puramente numerica; 'PA001' fica como esta.
    if re.fullmatch(r"\d+", s):
        # O 'or "0"' protege o caso degenerado '000' (viraria string vazia).
        s = s.lstrip("0") or "0"
    # Saida: chave pronta para comparar entre Lote e Painel.
    return s


def ler_amostras(caminho):
    """Le as abas 'Amostra K' do Lote.xlsx e devolve so as obras selecionadas.

    Por que existe: o Lote.xlsx traz TODAS as obras com coluna STATUS; o estimador
    so precifica as sorteadas. Isolar a leitura permite validar o formato num lugar so.

    Logica: Entrada (caminho) -> Fase 1: lista abas 'Amostra K' -> Fase 2: por aba,
    filtra STATUS=='Selecionado' e projeta ODI/Estrato/Municipio/Cons -> Saida: dict {k: df}.
    """
    # Fase 1: abre o workbook e localiza abas cujo nome casa 'Amostra <numero>'.
    xls = pd.ExcelFile(caminho)
    abas = {int(m.group(1)): a for a in xls.sheet_names if (m := re.fullmatch(r"Amostra\s*(\d+)", a.strip()))}
    # Sem nenhuma aba de amostra: o arquivo nao e' o esperado - erro claro.
    if not abas:
        raise EntradaInvalida(f"Nenhuma aba 'Amostra 1/2/3' em {caminho.name}.\nAbas encontradas: {xls.sheet_names}")
    resultado = {}
    # Fase 2: processa cada aba de amostra existente (processa as que existirem - D7).
    for k, aba in sorted(abas.items()):
        df = xls.parse(aba)
        # Normaliza os nomes de coluna para achar ODI/Estrato/Municipio/Cons/STATUS com robustez.
        colmap = {_norm(c): c for c in df.columns}
        # Valida colunas obrigatorias; lista as ausentes na mensagem (Cons e' opcional - ver abaixo).
        faltam = [c for c in ("odi", "estrato", "status") if c not in colmap]
        if faltam:
            raise EntradaInvalida(f"Aba '{aba}' sem colunas obrigatorias: {faltam}.\nColunas: {list(df.columns)}")
        # Filtra apenas as obras sorteadas (STATUS == 'Selecionado').
        sel = df[df[colmap["status"]].astype(str).str.strip() == "Selecionado"]
        # Projeta e renomeia para o contrato interno. A ODI passa por _norm_odi para casar
        # com a do Painel: aqui ela vem como texto com zeros a esquerda ('0012500186'),
        # la vem como numero - sem normalizar, a juncao falharia por formato, nao por dado.
        resultado[k] = pd.DataFrame({
            "ODI": sel[colmap["odi"]].map(_norm_odi),
            "Estrato": sel[colmap["estrato"]].astype(int),
            "Municipio": sel[colmap["municipio"]].astype(str).str.strip() if "municipio" in colmap else "",
            # Cons ('Cons.' no Lote real) = numero de UCs da obra; 0 quando a coluna nao existe
            # (obra sem informacao de UC no Lote - tratado como "sem UC esperada" pela regra do orfao).
            "Cons": sel[colmap["cons"]].astype(int) if "cons" in colmap else 0,
        }).reset_index(drop=True)
    # Saida: uma entrada por aba de amostra encontrada.
    return resultado


def ler_painel(caminho):
    """Le o Painel de Monitoramento e devolve as UCs geolocalizadas.

    Por que existe: o painel real tem varias abas; detectar a aba certa pelas colunas
    (ODI + latitude + longitude) evita depender do nome da aba, que varia entre tranches.
    Alem disso o Anexo V real tem DUAS linhas de cabecalho (a primeira e' uma faixa mesclada
    de grupos) e nomeia as colunas por extenso - por isso a busca testa mais de uma linha de
    cabecalho e traduz os nomes por ALIAS_PAINEL.

    Logica: Entrada (caminho) -> Fase 1: para cada aba, tenta cada linha de cabecalho de
    LINHAS_CABECALHO_PAINEL e para na primeira combinacao que produza ODI+lat+long ->
    Fase 2: projeta ODI/UC/Municipio/lat/long (ODI normalizada por _norm_odi) -> Fase 3:
    descarta coordenadas invalidas com aviso -> Saida: df de UCs validas.
    """
    xls = pd.ExcelFile(caminho)
    achado = None
    # Fase 1: varre aba x linha-de-cabecalho procurando ODI + latitude + longitude.
    for aba in xls.sheet_names:
        for linha_cabecalho in LINHAS_CABECALHO_PAINEL:
            df = xls.parse(aba, header=linha_cabecalho)
            # Traduz cada cabecalho real pelo apelido; o 'not in' preserva a PRIMEIRA
            # coluna que reivindicar cada papel (evita uma coluna posterior sobrescrever).
            colmap = {}
            for coluna in df.columns:
                interno = ALIAS_PAINEL.get(_norm(coluna))
                if interno and interno not in colmap:
                    colmap[interno] = coluna
            if COLUNAS_MINIMAS_PAINEL <= set(colmap):
                achado = (aba, linha_cabecalho, df, colmap)
                break
        if achado:
            break
    if achado is None:
        raise EntradaInvalida(
            f"Nenhuma aba de {caminho.name} tem colunas de ODI/LATITUDE/LONGITUDE.\n"
            f"Abas vistas: {xls.sheet_names}\n"
            f"Cabecalhos aceitos para a ODI: {sorted(a for a, i in ALIAS_PAINEL.items() if i == 'odi')}."
        )
    aba, linha_cabecalho, df, colmap = achado
    # Diz de onde os dados vieram: com duas linhas de cabecalho possiveis, o usuario precisa
    # poder conferir que o programa leu a linha certa.
    print(f"Painel: aba '{aba}' (cabecalho na linha {linha_cabecalho + 1}), {len(df)} linha(s).")
    # Fase 2: projeta para o contrato interno; UC pode nao existir (usa o indice como id).
    # Municipio tambem e' projetado (quando existir): a regra do orfao com Cons==0 precisa dele
    # para achar o centroide das UCs do mesmo municipio no painel (ver juntar_amostras_painel).
    ucs = pd.DataFrame({
        # Mesma normalizacao aplicada no Lote: e' o que faz a chave casar entre as duas planilhas.
        "ODI": df[colmap["odi"]].map(_norm_odi),
        # A UC passa pela MESMA normalizacao da ODI porque ela tambem e' chave de juncao:
        # em contrato MLA (sistema individual) cada obra do Lote e' uma UC, e o 'ODI' do
        # Lote casa com o numero da UC do Anexo V (ver juntar_amostras_painel).
        "UC": df[colmap["uc"]].map(_norm_odi) if "uc" in colmap else df.index.astype(str),
        "Municipio": df[colmap["municipio"]].astype(str).str.strip() if "municipio" in colmap else "",
        "LATITUDE": pd.to_numeric(df[colmap["latitude"]], errors="coerce"),
        "LONGITUDE": pd.to_numeric(df[colmap["longitude"]], errors="coerce"),
        # Classificacao do beneficiario. Vem com espaco sobrando no Anexo V real
        # ('11 - Rural geral / demais comunidades rurais '), e sem o strip ela nao casa
        # com o dominio da aba 'Dominios'. Ausente vira "" - a aba de beneficiarios
        # mostra zeros, e o custo nao muda.
        "TipoComunidade": (df[colmap["tipo_comunidade"]].astype(str).str.strip()
                           if "tipo_comunidade" in colmap else ""),
        "Enquadramento": (df[colmap["enquadramento"]].astype(str).str.strip()
                          if "enquadramento" in colmap else ""),
    })
    # Fase 3: marca invalidas - NaN, zero exato ou fora da bounding box do Brasil.
    b = BBOX_BRASIL
    validas = (ucs["LATITUDE"].between(b["lat_min"], b["lat_max"])
               & ucs["LONGITUDE"].between(b["lon_min"], b["lon_max"])
               & (ucs["LATITUDE"] != 0) & (ucs["LONGITUDE"] != 0))
    # Reporta as descartadas (limitacao explicita, nunca silenciosa).
    if (~validas).any():
        print(f"AVISO: {(~validas).sum()} UC(s) com coordenada invalida descartada(s) de {caminho.name}.")
    # Saida: somente UCs com coordenada valida.
    return ucs[validas].reset_index(drop=True)


def ler_dominios(caminho):
    """Le os dominios das listas suspensas de classificacao do beneficiario (aba 'Dominios').

    Por que existe: a aba 'Resumo beneficiarios' tem UMA COLUNA POR CATEGORIA POSSIVEL, e
    nao por categoria presente nos dados. A diferenca importa na leitura gerencial: uma
    coluna 'Familia indigena' com zero e' um fato ('a amostra nao pegou nenhuma'), enquanto
    a coluna ausente e' um mistero ('esqueceram ou nao existe?'). Por isso a lista de
    colunas vem da PLANILHA, e nao dos valores encontrados.

    A aba e' opcional: paineis antigos (e todos os sinteticos dos testes) nao a tem. Sem
    ela, a aba de beneficiarios sai com as categorias que aparecerem nos dados - degradado,
    mas util - e o resto do programa segue igual.

    Logica: Entrada (caminho do Anexo V) -> Fase 1: sem a aba 'Dominios', devolve dominios
    vazios -> Fase 2: le a aba inteira sem cabecalho, para pegar as colunas por POSICAO
    (D e E), que e' como o humano as identifica -> Fase 3: primeira linha e' o titulo do
    dominio; o resto sao os valores, na ordem da planilha -> Saida: {coluna interna:
    [valores...]}.
    """
    xls = pd.ExcelFile(caminho)
    # Fase 1: aba ausente nao e' erro - so nao ha dominio declarado.
    aba = next((a for a in xls.sheet_names if _norm(a) == _norm(ABA_DOMINIOS)), None)
    if aba is None:
        return {interno: [] for interno in COLUNAS_DOMINIOS.values()}
    # Fase 2: sem cabecalho, para que a posicao da coluna (D=3, E=4) seja o que manda -
    # e' assim que o humano se refere a elas, e o titulo da linha 1 nao e' um dado.
    df = xls.parse(aba, header=None)
    dominios = {}
    for letra, interno in COLUNAS_DOMINIOS.items():
        # Letra da coluna -> indice 0-based ('D' -> 3).
        indice = ord(letra.upper()) - ord("A")
        if indice >= len(df.columns):
            dominios[interno] = []
            continue
        # Fase 3: pula o titulo (linha 1) e mantem a ordem da planilha, que e' a ordem
        # em que o usuario ve as opcoes na lista suspensa.
        valores = df.iloc[1:, indice].dropna().astype(str).str.strip()
        dominios[interno] = [v for v in valores if v]
    # Saida: um dominio por classificacao, ja na ordem de apresentacao.
    return dominios


def escolher_chave_juncao(amostras, ucs, tipo_contrato=None):
    """Decide com QUAL coluna do Anexo V a coluna 'ODI' do Lote deve casar.

    Por que existe: ha um GAP SEMANTICO no sistema legado que gera o Lote. A coluna se
    chama 'ODI' nos dois tipos de contrato, mas o que ela guarda muda:
      - LPT: numero da ODI mesmo (uma ODI agrupa varias UCs);
      - MLA: numero da UNIDADE CONSUMIDORA. Cada obra e' um sistema fotovoltaico
        individual, entao o legado nunca criou numero de ODI proprio e reaproveitou a
        coluna. No Anexo V esse numero mora em 'Numero da Unidade Consumidora'.
    Sem esta funcao o programa juntava pela coluna errada e acusava "tranche errada" em
    dados validos (3a Tranche RO, ECM 022/2025: 862 de 862 obras casam pela UC, nenhuma
    pela ODI, com Lote e Anexo V comprovadamente do mesmo certame).

    A escolha e' DECLARADA (vem do tipo do contrato, em config.CHAVE_JUNCAO_POR_TIPO) e
    nao adivinhada. Isso importa: se algum numero de UC coincidisse por acaso com um
    numero de ODI, uma heuristica de tentativa-e-erro casaria pela chave errada em
    silencio. A verificacao contra os dados so entra como REDE DE SEGURANCA, para o caso
    de o contrato nao ter sido informado ou de a planilha fugir do padrao do seu tipo.

    Logica: Entrada (amostras, ucs, tipo) -> Fase 1: le a chave declarada para o tipo
    -> Fase 2: monta a ordem de tentativa (declarada primeiro, a outra como reserva)
    -> Fase 3: fica com a primeira que tenha alguma obra em comum -> Fase 4: avisa se a
    escolhida nao foi a declarada, ou aborta se nenhuma casar -> Saida: (df de UCs
    re-chaveado, nome da coluna escolhida).
    """
    # Fase 1: a chave declarada para este tipo de contrato (LPT -> ODI, MLA -> UC).
    # Le config na chamada, nunca no import, como o resto do projeto.
    declarada = config.CHAVE_JUNCAO_POR_TIPO.get(str(tipo_contrato).upper().strip(), "ODI")
    # As duas colunas do Anexo V que podem servir de chave.
    candidatas = {"ODI": set(ucs["ODI"]), "UC": set(ucs["UC"])}
    obras = set().union(*[set(df["ODI"]) for df in amostras.values()])
    # Fase 2: tenta a declarada primeiro; a outra so como rede de seguranca.
    ordem = [declarada] + [nome for nome in ("ODI", "UC") if nome != declarada]
    # Fase 3: a primeira coluna com alguma obra em comum vence.
    escolhida = next((nome for nome in ordem if obras & candidatas[nome]), None)
    # Fase 4a: amostra legitimamente VAZIA (aba sem obra sorteada) tambem nao casa com
    # nada - nao ha o que decidir e acusa-la de tranche errada seria erro falso.
    if not obras:
        return ucs, declarada
    # Fase 4b: nenhuma das duas colunas casa - agora sim os arquivos sao de certames diferentes.
    if escolhida is None:
        raise EntradaInvalida(
            "Nenhuma obra das amostras existe no Anexo V, nem pelo numero da ODI nem "
            "pelo numero da UC:\nos arquivos parecem ser de tranche/UF diferentes.\n"
            "Confira se as planilhas de amostra e o Anexo V sao do MESMO certame."
        )
    # Fase 4c: comunica a decisao. Quando a chave e' a declarada, e' so informacao; quando
    # a declarada falhou e a reserva salvou, e' AVISO - alguma premissa esta errada
    # (contrato nao informado, tipo errado na base, ou planilha fora do padrao do tipo).
    if escolhida == "UC" and declarada == "UC":
        print("Contrato MLA: a coluna 'ODI' do Lote guarda numeros de UC; juntando pelo "
              "'Numero da Unidade Consumidora' do Anexo V.")
    elif escolhida != declarada:
        print(f"AVISO: pelo tipo do contrato a juncao deveria ser pela coluna '{declarada}', "
              f"mas nenhuma obra casou por ela. Casaram pela coluna '{escolhida}' - usando "
              f"essa. Confira se o contrato informado corresponde a estas planilhas.")
    # Re-chaveia o painel quando a chave escolhida nao e' a ODI: a UC passa a ser a chave
    # de juncao, e cada obra fica com exatamente uma UC.
    if escolhida != "ODI":
        ucs = ucs.assign(ODI=ucs[escolhida])
    # Saida: painel pronto para o merge + qual coluna acabou valendo.
    return ucs, escolhida


def juntar_amostras_painel(amostras, ucs, tipo_contrato=None):
    """Junta cada amostra com as UCs do painel, validando o casamento.

    Por que existe: e' o detector do erro 'amostra de uma tranche x painel de outra'
    (intersecao zero) e de ODIs orfaos - os dois erros de dados mais provaveis. Tambem
    aplica a REGRA DO ORFAO (decisao do gate F1): ODI sorteada sem UC no painel e' erro
    quando a obra tem UC esperada (Cons > 0), mas vira uma pseudo-UC no centroide do
    municipio quando a obra nao tem UC nenhuma (Cons == 0, ex.: reforco de rede).

    Logica: Entrada (amostras, ucs, tipo do contrato) -> Fase 1: escolhe a coluna de
    juncao pelo tipo do contrato (ver escolher_chave_juncao; tranche errada aborta ali)
    -> Fase 2: por amostra, classifica cada ODI orfao SEM efeitos colaterais
    (Cons>0 vira candidato a erro; Cons==0 vira candidato a pseudo-UC, ou candidato a
    erro se o municipio tambem nao tem UC no painel) -> Fase 3: se houver qualquer
    candidato a erro, aborta listando TODOS de uma vez (nada de aviso parcial nem de
    parar no primeiro) -> Fase 4: so entao aplica os fallbacks validos (imprime os
    avisos e monta as pseudo-UCs) -> Fase 5: merge dos nao-orfaos + concatena
    as pseudo-UCs -> Saida: dict {k: df} com uma linha por UC (real ou pseudo) de obra
    sorteada.
    """
    # Fase 1: qual coluna do Anexo V casa com o 'ODI' do Lote depende do TIPO do contrato.
    ucs, _chave = escolher_chave_juncao(amostras, ucs, tipo_contrato)
    odis_painel = set(ucs["ODI"])
    juntas = {}
    for k, df in amostras.items():
        # Fase 2: ODIs sorteadas sem nenhuma UC no painel = orfaos; classifica cada um SEM
        # imprimir nem lancar nada ainda - so decide em qual das tres listas ele cai.
        orfaos = sorted(set(df["ODI"]) - odis_painel)
        orfaos_com_uc_esperada = []   # Cons > 0: erro (comportamento original)
        orfaos_sem_municipio = []     # Cons == 0 mas municipio tambem sem UC no painel: erro
        fallbacks_validos = []        # Cons == 0 com municipio achado: candidato a pseudo-UC
        for odi in orfaos:
            # Localiza a linha da amostra para essa ODI (Estrato/Municipio/Cons ja conhecidos).
            linha = df.loc[df["ODI"] == odi].iloc[0]
            if int(linha["Cons"]) > 0:
                # Obra com UC esperada mas sem nenhuma no painel: dado incompleto, candidato a erro.
                orfaos_com_uc_esperada.append(odi)
                continue
            # Cons == 0 (obra sem UC, ex.: reforco de rede): busca UCs do mesmo municipio no
            # painel para calcular o centroide. A comparacao passa por _norm (minusculas, SEM
            # acento) porque as duas planilhas grafam diferente: o Lote traz 'GURINHEM' e o
            # Painel traz 'GURINHÉM' - comparar so com upper/strip acusaria falsamente
            # "municipio sem nenhuma UC no Painel" e abortaria uma amostra sadia.
            municipio = linha["Municipio"]
            candidatas = ucs[ucs["Municipio"].map(_norm) == _norm(municipio)]
            if candidatas.empty:
                # Nem o municipio tem UC no painel: nao ha centroide possivel - candidato a erro
                # (coletado aqui, NAO lancado direto, para poder ser listado junto dos demais).
                orfaos_sem_municipio.append((odi, municipio))
            else:
                # Guarda tudo que a Fase 4 precisa para montar a pseudo-UC, sem aplicar ainda.
                fallbacks_validos.append((odi, linha, municipio, candidatas))
        # Fase 3: qualquer candidato a erro aborta a amostra inteira, listando TODOS de uma vez -
        # nunca so o primeiro, e nunca depois de avisos de fallback ja terem sido impressos.
        mensagens_erro = []
        if orfaos_com_uc_esperada:
            mostra = ", ".join(orfaos_com_uc_esperada[:10]) + ("..." if len(orfaos_com_uc_esperada) > 10 else "")
            mensagens_erro.append(f"{len(orfaos_com_uc_esperada)} ODI(s) sem coordenada no Painel: {mostra}")
        if orfaos_sem_municipio:
            itens = [f"{odi} (municipio {municipio})" for odi, municipio in orfaos_sem_municipio]
            mostra = ", ".join(itens[:10]) + ("..." if len(itens) > 10 else "")
            mensagens_erro.append(
                f"{len(orfaos_sem_municipio)} ODI(s) com Cons=0 (obra sem UC) cujo municipio "
                f"tambem nao tem nenhuma UC no Painel (impossivel estimar centroide): {mostra}"
            )
        if mensagens_erro:
            raise EntradaInvalida(f"Amostra {k}: " + " | ".join(mensagens_erro))
        # Fase 4: so chega aqui se a amostra passou em TODAS as validacoes - agora sim aplica
        # os fallbacks (aviso + pseudo-UC), sem risco de anunciar progresso que seria abortado.
        pseudo_linhas = []
        for odi, linha, municipio, candidatas in fallbacks_validos:
            # Aviso (nunca silencioso): pseudo-UC criada a partir do centroide municipal.
            print(f"AVISO: Amostra {k}: ODI {odi} (Cons=0, obra sem UC) sem UC propria no Painel; "
                  f"usando pseudo-UC no centroide de {municipio} ({len(candidatas)} UC(s)).")
            pseudo_linhas.append({
                "ODI": odi,
                "Estrato": int(linha["Estrato"]),
                "Municipio": municipio,
                "Cons": int(linha["Cons"]),
                "UC": f"{odi}-{municipio}",
                "LATITUDE": float(candidatas["LATITUDE"].mean()),
                "LONGITUDE": float(candidatas["LONGITUDE"].mean()),
                # A pseudo-UC nao existe no Anexo V, entao nao tem classificacao de
                # beneficiario. Fica "" (e nao NaN) para a contagem por dominio poder
                # trata-la como "sem classificacao" em vez de quebrar.
                "TipoComunidade": "",
                "Enquadramento": "",
            })
        # Fase 5: merge 1-para-N (cada ODI tem varias UCs) para os ODIs com UC real no painel;
        # remove Municipio de ucs antes do merge para nao duplicar a coluna ja vinda da amostra.
        juntas_k = df.merge(ucs.drop(columns=["Municipio"]), on="ODI", how="inner")
        # Concatena as pseudo-UCs dos orfaos Cons==0 (pode ser uma lista vazia).
        if pseudo_linhas:
            juntas_k = pd.concat([juntas_k, pd.DataFrame(pseudo_linhas)], ignore_index=True)
        juntas[k] = juntas_k
    # Saida: amostras enriquecidas com as UCs geolocalizadas (reais e/ou pseudo).
    return juntas
