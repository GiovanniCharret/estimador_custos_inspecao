# -*- coding: utf-8 -*-
"""Geometria do estimador: distancias geodesicas, centroides e percurso interno por ODI."""
import numpy as np
import pandas as pd

# Raio medio da Terra em km (esfera equivalente) - constante da formula de haversine.
RAIO_TERRA_KM = 6371.0088

def haversine_km(lat1, lon1, lat2, lon2):
    """Distancia geodesica (grande circulo) entre dois pontos, em km.

    Por que existe: todo o modelo de custo se apoia em distancias; concentrar a formula
    aqui permite valida-la uma unica vez contra valores conhecidos.

    Logica: Entrada (graus) -> Fase 1: converte para radianos -> Fase 2: formula de
    haversine -> Saida: km (float ou array, e' vetorizada via numpy).
    """
    # Fase 1: graus -> radianos (numpy aceita escalares e arrays).
    la1, lo1, la2, lo2 = map(np.radians, (lat1, lon1, lat2, lon2))
    # Fase 2: formula de haversine sobre as diferencas.
    dlat = la2 - la1
    dlon = lo2 - lo1
    a = np.sin(dlat / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin(dlon / 2) ** 2
    # Saida: arco * raio da Terra = distancia em km.
    return float(2 * RAIO_TERRA_KM * np.arcsin(np.sqrt(a))) if np.isscalar(lat1) else 2 * RAIO_TERRA_KM * np.arcsin(np.sqrt(a))

def _rota_vizinho_mais_proximo(lats, lons):
    """Percurso guloso pelas UCs: sempre vai a UC nao visitada mais proxima.

    Por que existe: aproxima o deslocamento interno do inspetor dentro do ODI sem
    resolver TSP; deterministico (comeca na primeira UC na ordem de entrada).

    Logica: Entrada (arrays lat/lon) -> Fase 1: parte do indice 0 -> Fase 2: repete
    'vai ao mais proximo' ate visitar todos -> Saida: soma dos trechos em km.
    """
    # Fase 1: menos de 2 pontos nao tem percurso.
    n = len(lats)
    if n < 2:
        return 0.0
    # Estado: conjunto de nao-visitados e posicao atual (indice 0 = primeira UC).
    restam = set(range(1, n))
    atual = 0
    total = 0.0
    # Fase 2: passo guloso ate esgotar os pontos.
    while restam:
        # Distancia da posicao atual a todos os que restam.
        dists = {j: haversine_km(lats[atual], lons[atual], lats[j], lons[j]) for j in restam}
        # Escolhe o mais proximo (desempate pelo menor indice, para determinismo).
        prox = min(dists, key=lambda j: (dists[j], j))
        total += dists[prox]
        restam.remove(prox)
        atual = prox
    # Saida: km totais do percurso guloso.
    return total

def montar_roteiro(df_odis, lat_origem, lon_origem):
    """Monta o itinerario UNICO da equipe: sai da capital, encadeia todas as obras, volta.

    Por que existe: e' a correcao central da F9. O modelo anterior mandava a equipe voltar
    a capital a cada municipio (ida e volta, uma vez por municipio), o que inflava a
    quilometragem em ~7x (10.521 km contra 1.529 km reais na amostra da PB 7a Tranche) e
    superestimava o custo. Na pratica a inspecao e' uma viagem so: a equipe segue da ultima
    obra alcancada para a proxima mais proxima e so retorna a capital no fim.

    A ordem e' hierarquica de proposito - primeiro escolhe o MUNICIPIO mais proximo, depois
    varre todas as obras dele antes de sair. Uma rota gulosa direta sobre as obras poderia
    entrar e sair do mesmo municipio varias vezes, o que nao corresponde a como a equipe
    trabalha (e produziria um roteiro impossivel de ler no mapa).

    Logica: Entrada (df por ODI com lat_centro/lon_centro/Municipio, origem) -> Fase 1:
    reduz cada municipio ao seu ponto medio -> Fase 2: escolhe guloso o proximo MUNICIPIO
    a partir da posicao atual -> Fase 3: dentro do municipio escolhido, escolhe guloso a
    proxima OBRA, acumulando o km de cada trecho -> Fase 4: fecha o circuito voltando a
    origem -> Saida: (df por ODI com 'ordem' e 'km_trecho', km total em linha reta).

    O km total NAO inclui o percurso interno entre as UCs de cada obra (esse ja vem em
    dist_interna_km, calculado por resumo_por_odi) - quem soma os dois e' custo.py.
    """
    # Fase 1: sem obras nao ha roteiro (amostra vazia) - devolve o mesmo esquema, sem linhas.
    if len(df_odis) == 0:
        vazio = df_odis.copy()
        vazio["ordem"] = pd.Series(dtype="int64")
        vazio["km_trecho"] = pd.Series(dtype="float64")
        return vazio, 0.0
    r = df_odis.copy().reset_index(drop=True)
    # Ponto medio de cada municipio = media dos centroides das suas obras.
    pontos_municipio = {
        mun: (float(g["lat_centro"].mean()), float(g["lon_centro"].mean()))
        for mun, g in r.groupby("Municipio", sort=False)
    }
    # Indices das obras de cada municipio (listas, para irem sendo consumidas).
    obras_do_municipio = {mun: list(g.index) for mun, g in r.groupby("Municipio", sort=False)}
    # Estado do caminhamento: onde a equipe esta e quais municipios faltam.
    atual = (float(lat_origem), float(lon_origem))
    faltam_municipios = list(obras_do_municipio)
    ordem = {}          # indice da obra -> posicao no roteiro (1, 2, 3, ...)
    km_trecho = {}      # indice da obra -> km desde a parada anterior
    km_total = 0.0
    passo = 0
    # Fase 2: enquanto houver municipio nao visitado, vai ao mais proximo da posicao atual.
    while faltam_municipios:
        # Desempate pelo nome do municipio para determinismo (mesma entrada, mesma rota).
        proximo_mun = min(
            faltam_municipios,
            key=lambda m: (haversine_km(atual[0], atual[1], *pontos_municipio[m]), m),
        )
        faltam_municipios.remove(proximo_mun)
        # Fase 3: varre TODAS as obras deste municipio antes de seguir viagem.
        faltam_obras = list(obras_do_municipio[proximo_mun])
        while faltam_obras:
            # Desempate pelo indice da obra (menor primeiro), mesma regra do resto do projeto.
            proxima = min(
                faltam_obras,
                key=lambda i: (haversine_km(atual[0], atual[1],
                                            r.at[i, "lat_centro"], r.at[i, "lon_centro"]), i),
            )
            faltam_obras.remove(proxima)
            # Acumula o trecho percorrido ate esta obra.
            d = haversine_km(atual[0], atual[1], r.at[proxima, "lat_centro"], r.at[proxima, "lon_centro"])
            km_total += d
            passo += 1
            ordem[proxima] = passo
            km_trecho[proxima] = d
            # A equipe passa a estar nesta obra.
            atual = (r.at[proxima, "lat_centro"], r.at[proxima, "lon_centro"])
    # Fase 4: uma unica volta a capital, no fim de tudo (nao uma por municipio).
    km_total += haversine_km(atual[0], atual[1], lat_origem, lon_origem)
    # Anota ordem e trecho e devolve o df JA ordenado pelo roteiro (e como o humano le no mapa).
    r["ordem"] = r.index.map(ordem)
    r["km_trecho"] = r.index.map(km_trecho)
    # Saida: df na ordem de visita + km em linha reta do itinerario fechado.
    return r.sort_values("ordem").reset_index(drop=True), km_total


def resumo_por_odi(df_ucs):
    """Reduz o df de UCs a uma linha por ODI com centroide e percurso interno.

    Por que existe: o custo e' calculado por ODI; esta funcao faz a ponte entre a
    granularidade UC (entrada) e ODI (modelo de custo).

    Logica: Entrada (df com ODI/Estrato/Municipio/UC/lat/long) -> Fase 1: agrupa por
    ODI -> Fase 2: centroide (media simples) e rota interna -> Saida: df por ODI.

    O df devolvido tem SEMPRE as mesmas colunas, mesmo quando a amostra e' vazia (aba
    'Amostra K' sem nenhuma obra sorteada). Sem isso, um pandas vazio sai sem coluna
    nenhuma e cada consumidor rio abaixo (roteiro, custo, mapa) precisaria se defender
    do caso - foi exatamente assim que a amostra vazia derrubou o mapa uma vez.
    """
    # Colunas do contrato desta funcao - a garantia de esquema estavel citada acima.
    COLUNAS = ["ODI", "Estrato", "Municipio", "n_ucs", "lat_centro", "lon_centro", "dist_interna_km"]
    linhas = []
    # Fase 1: um grupo por ODI, preservando a ordem de entrada (determinismo).
    for odi, g in df_ucs.groupby("ODI", sort=False):
        # Fase 2: centroide = media das coordenadas; rota = guloso sobre as UCs do grupo.
        linhas.append({
            "ODI": odi,
            "Estrato": int(g["Estrato"].iloc[0]),
            "Municipio": g["Municipio"].iloc[0],
            "n_ucs": len(g),
            "lat_centro": float(g["LATITUDE"].mean()),
            "lon_centro": float(g["LONGITUDE"].mean()),
            "dist_interna_km": _rota_vizinho_mais_proximo(g["LATITUDE"].to_numpy(), g["LONGITUDE"].to_numpy()),
        })
    # Saida: uma linha por ODI, pronta para o motor de custo (colunas fixas mesmo se vazio).
    return pd.DataFrame(linhas, columns=COLUNAS)
