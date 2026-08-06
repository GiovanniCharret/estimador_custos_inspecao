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

def resumo_por_odi(df_ucs):
    """Reduz o df de UCs a uma linha por ODI com centroide e percurso interno.

    Por que existe: o custo e' calculado por ODI; esta funcao faz a ponte entre a
    granularidade UC (entrada) e ODI (modelo de custo).

    Logica: Entrada (df com ODI/Estrato/Municipio/UC/lat/long) -> Fase 1: agrupa por
    ODI -> Fase 2: centroide (media simples) e rota interna -> Saida: df por ODI.
    """
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
    # Saida: uma linha por ODI, pronta para o motor de custo.
    return pd.DataFrame(linhas)
