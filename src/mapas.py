# -*- coding: utf-8 -*-
"""Mapas interativos (folium) das amostras: UCs coloridas por estrato com popup de custo."""
import folium
import pandas as pd

# Paleta fixa por estrato (cores distinguiveis; cicla se houver mais estratos que cores).
CORES = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf"]

def gravar_mapa(df_ucs, custos, caminho):
    """Grava um mapa HTML da amostra com uma camada ligavel por estrato.

    Por que existe: substitui o mapa manual do QGIS (D3); um arquivo autocontido que o
    humano abre no browser e explora por camadas.

    Logica: Entrada (UCs, custos por ODI, caminho) -> Fase 1: centro do mapa = media
    das UCs -> Fase 2: FeatureGroup por estrato com CircleMarker por UC e popup
    ODI/municipio/custo -> Fase 3: LayerControl -> Saida: .html gravado.
    """
    # Fase 1: centraliza o mapa no centroide geral da amostra.
    mapa = folium.Map(location=[df_ucs["LATITUDE"].mean(), df_ucs["LONGITUDE"].mean()], zoom_start=8)
    # Indice de custo por ODI para preencher o popup.
    custo_odi = custos.set_index("ODI")["custo_total"].to_dict()
    # Fase 2: uma camada por estrato, na ordem crescente.
    for i, (estrato, g) in enumerate(df_ucs.groupby("Estrato", sort=True)):
        grupo = folium.FeatureGroup(name=f"Estrato {estrato}")
        # Um marcador por UC do estrato.
        for _, uc in g.iterrows():
            folium.CircleMarker(
                location=[uc["LATITUDE"], uc["LONGITUDE"]],
                radius=4,
                color=CORES[i % len(CORES)],   # cor estavel por estrato
                fill=True,
                popup=folium.Popup(
                    f"ODI {uc['ODI']}<br>{uc['Municipio']}<br>"
                    f"Custo ODI: R$ {custo_odi.get(uc['ODI'], float('nan')):,.2f}",
                    max_width=250),
            ).add_to(grupo)
        grupo.add_to(mapa)
    # Fase 3: controle para ligar/desligar estratos.
    folium.LayerControl(collapsed=False).add_to(mapa)
    # Saida: HTML autocontido.
    mapa.save(str(caminho))
