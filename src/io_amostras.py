# -*- coding: utf-8 -*-
"""Leitura e validacao das entradas do estimador (Lote de amostras + Painel de coordenadas)."""
from pathlib import Path
import re
import pandas as pd

# Bounding box aproximada do Brasil: coordenada fora daqui e' erro de digitacao/projecao.
BBOX_BRASIL = {"lat_min": -34.0, "lat_max": 5.5, "lon_min": -74.0, "lon_max": -34.0}


class EntradaInvalida(Exception):
    """Erro de entrada com mensagem pronta para o usuario final.

    Por que existe: separa erros de dados (culpa da entrada, mensagem amigavel,
    exit 1 sem traceback) de bugs do programa (traceback normal).
    """


def achar_entradas(pasta):
    """Localiza os dois arquivos de entrada dentro de Entrada/.

    Por que existe: o usuario deposita arquivos por convencao de nome (D7);
    centralizar a busca da um unico lugar para mensagens de erro claras.

    Logica: Entrada (pasta) -> Fase 1: valida Lote.xlsx -> Fase 2: procura
    *Painel de Monitoramento*.xlsx e exige exatamente 1 -> Saida: (lote, painel).
    """
    # Fase 1: o Lote.xlsx tem nome fixo; sem ele nao ha amostras a precificar.
    lote = Path(pasta) / "Lote.xlsx"
    # Se nao existe, aborta ja dizendo onde colocar o arquivo.
    if not lote.exists():
        raise EntradaInvalida(f"Lote.xlsx nao encontrado.\nColoque o arquivo com as amostras em: {pasta}\\Lote.xlsx")
    # Fase 2: o painel e localizado por nome contendo o padrao (D7), ignorando temporarios do Excel (~$).
    paineis = [p for p in Path(pasta).glob("*Painel de Monitoramento*.xlsx") if not p.name.startswith("~$")]
    # Nenhum painel: aborta explicando a convencao de nome.
    if not paineis:
        raise EntradaInvalida(f"Arquivo de coordenadas nao encontrado.\nColoque em {pasta}\\ um .xlsx cujo nome contenha 'Painel de Monitoramento'.")
    # Mais de um painel: ambiguidade — aborta listando para o usuario remover o excedente.
    if len(paineis) > 1:
        nomes = "\n  - ".join(p.name for p in paineis)
        raise EntradaInvalida(f"Mais de um Painel de Monitoramento em {pasta}:\n  - {nomes}\nDeixe apenas um.")
    # Saida: os dois caminhos validados.
    return lote, paineis[0]


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
        # Projeta e renomeia para o contrato interno (ODI como str preserva zeros a esquerda).
        resultado[k] = pd.DataFrame({
            "ODI": sel[colmap["odi"]].astype(str).str.strip(),
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

    Logica: Entrada (caminho) -> Fase 1: acha a primeira aba com as colunas necessarias
    -> Fase 2: projeta ODI/UC/Municipio/lat/long -> Fase 3: descarta coordenadas invalidas
    com aviso -> Saida: df de UCs validas.
    """
    xls = pd.ExcelFile(caminho)
    # Fase 1: varre as abas procurando uma que tenha ODI, latitude e longitude.
    for aba in xls.sheet_names:
        df = xls.parse(aba)
        colmap = {_norm(c): c for c in df.columns}
        if {"odi", "latitude", "longitude"} <= set(colmap):
            break
    else:
        raise EntradaInvalida(f"Nenhuma aba de {caminho.name} tem colunas ODI/LATITUDE/LONGITUDE.")
    # Fase 2: projeta para o contrato interno; UC pode nao existir (usa o indice como id).
    # Municipio tambem e' projetado (quando existir): a regra do orfao com Cons==0 precisa dele
    # para achar o centroide das UCs do mesmo municipio no painel (ver juntar_amostras_painel).
    ucs = pd.DataFrame({
        "ODI": df[colmap["odi"]].astype(str).str.strip(),
        "UC": df[colmap["uc"]].astype(str).str.strip() if "uc" in colmap else df.index.astype(str),
        "Municipio": df[colmap["municipio"]].astype(str).str.strip() if "municipio" in colmap else "",
        "LATITUDE": pd.to_numeric(df[colmap["latitude"]], errors="coerce"),
        "LONGITUDE": pd.to_numeric(df[colmap["longitude"]], errors="coerce"),
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


def juntar_amostras_painel(amostras, ucs):
    """Junta cada amostra com as UCs do painel pela chave ODI, validando o casamento.

    Por que existe: e' o detector do erro 'amostra de uma tranche x painel de outra'
    (intersecao zero) e de ODIs orfaos - os dois erros de dados mais provaveis. Tambem
    aplica a REGRA DO ORFAO (decisao do gate F1): ODI sorteada sem UC no painel e' erro
    quando a obra tem UC esperada (Cons > 0), mas vira uma pseudo-UC no centroide do
    municipio quando a obra nao tem UC nenhuma (Cons == 0, ex.: reforco de rede).

    Logica: Entrada (amostras, ucs) -> Fase 1: intersecao global de ODIs (zero = tranche
    errada) -> Fase 2: por amostra, separa ODIs orfaos em dois grupos (Cons>0 vira erro;
    Cons==0 vira pseudo-UC no centroide municipal, ou erro se o municipio tambem nao tem
    UC no painel) -> Fase 3: merge por ODI dos nao-orfaos + concatena as pseudo-UCs ->
    Saida: dict {k: df} com uma linha por UC (real ou pseudo) de ODI sorteada.
    """
    # Fase 1: intersecao zero indica arquivos de tranches diferentes - mensagem especifica.
    odis_painel = set(ucs["ODI"])
    odis_amostras = set().union(*[set(df["ODI"]) for df in amostras.values()])
    if not odis_amostras & odis_painel:
        raise EntradaInvalida(
            "Nenhuma ODI das amostras existe no Painel: os arquivos parecem ser de "
            "tranche/UF diferentes.\nConfira se Lote.xlsx e o Painel sao do MESMO certame."
        )
    juntas = {}
    for k, df in amostras.items():
        # Fase 2: ODIs sorteadas sem nenhuma UC no painel = orfaos; separa pela regra do Cons.
        orfaos = sorted(set(df["ODI"]) - odis_painel)
        orfaos_com_uc_esperada = []   # Cons > 0: erro (comportamento original)
        pseudo_linhas = []            # Cons == 0: pseudo-UC no centroide do municipio
        for odi in orfaos:
            # Localiza a linha da amostra para essa ODI (Estrato/Municipio/Cons ja conhecidos).
            linha = df.loc[df["ODI"] == odi].iloc[0]
            if int(linha["Cons"]) > 0:
                # Obra com UC esperada mas sem nenhuma no painel: dado incompleto, aborta.
                orfaos_com_uc_esperada.append(odi)
                continue
            # Cons == 0 (obra sem UC, ex.: reforco de rede): busca UCs do mesmo municipio no
            # painel para calcular o centroide (comparacao sem acento/caixa nao e' necessaria
            # aqui pois ambos vem da mesma normalizacao de string; usamos upper+strip por seguranca).
            municipio = linha["Municipio"]
            candidatas = ucs[ucs["Municipio"].astype(str).str.upper().str.strip() == str(municipio).upper().strip()]
            if candidatas.empty:
                # Nem o municipio tem UC no painel: nao ha centroide possivel - erro.
                raise EntradaInvalida(
                    f"Amostra {k}: ODI {odi} (Cons=0, obra sem UC) nao tem UC propria no Painel, "
                    f"e o municipio '{municipio}' tambem nao tem nenhuma UC no Painel "
                    "(impossivel estimar o centroide)."
                )
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
            })
        # Orfaos com UC esperada (Cons>0): aborta listando, como no comportamento original.
        if orfaos_com_uc_esperada:
            mostra = ", ".join(orfaos_com_uc_esperada[:10]) + ("..." if len(orfaos_com_uc_esperada) > 10 else "")
            raise EntradaInvalida(f"Amostra {k}: {len(orfaos_com_uc_esperada)} ODI(s) sem coordenada no Painel: {mostra}")
        # Fase 3: merge 1-para-N (cada ODI tem varias UCs) para os ODIs com UC real no painel;
        # remove Municipio de ucs antes do merge para nao duplicar a coluna ja vinda da amostra.
        juntas_k = df.merge(ucs.drop(columns=["Municipio"]), on="ODI", how="inner")
        # Concatena as pseudo-UCs dos orfaos Cons==0 (pode ser uma lista vazia).
        if pseudo_linhas:
            juntas_k = pd.concat([juntas_k, pd.DataFrame(pseudo_linhas)], ignore_index=True)
        juntas[k] = juntas_k
    # Saida: amostras enriquecidas com as UCs geolocalizadas (reais e/ou pseudo).
    return juntas
