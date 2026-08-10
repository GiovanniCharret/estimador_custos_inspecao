# -*- coding: utf-8 -*-
"""Mapas interativos (folium) de uma estratificacao: uma camada por amostra, com o roteiro."""
import folium

# Paleta fixa por amostra (a 1 e' a principal; 2 e 3 sao as reservas).
CORES = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf"]


def gravar_mapa(amostras, lat_origem, lon_origem, caminho):
    """Grava um mapa HTML de uma estratificacao, com uma camada ligavel por amostra.

    Por que existe: substitui o mapa manual do QGIS (D3) e responde a pergunta que o mapa
    precisa responder desde a F9 - "por onde a equipe passa e quanto anda". A camada e' por
    AMOSTRA (nao por estrato) porque a comparacao util e' entre a amostra principal e as
    duas reservas; o estrato nao entra no custo e so poluia a legenda. A linha do roteiro
    e' o que torna visivel a correcao central: uma viagem so, nao ida-e-volta por obra.

    Logica: Entrada (dict {k: (df_ucs, roteiro)}, origem, caminho) -> Fase 1: centraliza o
    mapa no conjunto das UCs -> Fase 2: marca a capital (origem do roteiro) -> Fase 3: por
    amostra, desenha a polilinha capital -> obras -> capital e um marcador por UC ->
    Fase 4: LayerControl -> Saida: .html gravado.
    """
    # Fase 1: centro do mapa = media de todas as UCs de todas as amostras da estratificacao.
    # Amostras vazias (aba sem obra sorteada) nao contribuem e nem viram camada.
    com_obras = {k: v for k, v in amostras.items() if len(v[0])}
    lats = [lat for df_ucs, _ in com_obras.values() for lat in df_ucs["LATITUDE"]]
    lons = [lon for df_ucs, _ in com_obras.values() for lon in df_ucs["LONGITUDE"]]
    # Nenhuma obra em nenhuma amostra: centraliza na base da equipe, que e' o unico ponto que ha.
    centro = [sum(lats) / len(lats), sum(lons) / len(lons)] if lats else [lat_origem, lon_origem]
    mapa = folium.Map(location=centro, zoom_start=8)
    # Fase 2: a capital e' a origem e o fim de todo roteiro - marcada uma vez, fora das camadas.
    folium.Marker(
        location=[lat_origem, lon_origem],
        popup="Base da equipe (capital da UF)",
        icon=folium.Icon(color="black", icon="home"),
    ).add_to(mapa)
    # Fase 3: uma camada por amostra COM obras, em ordem numerica.
    for i, k in enumerate(sorted(com_obras)):
        df_ucs, roteiro = com_obras[k]
        cor = CORES[i % len(CORES)]
        # A camada da amostra 1 (principal) ja vem ligada; as reservas vem desligadas.
        grupo = folium.FeatureGroup(name=f"Amostra {k}", show=(i == 0))
        # Polilinha do itinerario: capital -> obras na ordem de visita -> capital.
        pontos = ([[lat_origem, lon_origem]]
                  + roteiro[["lat_centro", "lon_centro"]].values.tolist()
                  + [[lat_origem, lon_origem]])
        folium.PolyLine(pontos, color=cor, weight=2, opacity=0.6,
                        tooltip=f"Roteiro da amostra {k}").add_to(grupo)
        # Indice de ordem/municipio por ODI, para o popup do marcador da UC.
        info = roteiro.set_index("ODI")[["ordem", "Municipio", "n_ucs"]].to_dict("index")
        # Um marcador por UC (granularidade fina; a polilinha usa o centroide da obra).
        for _, uc in df_ucs.iterrows():
            dados = info.get(uc["ODI"], {})
            folium.CircleMarker(
                location=[uc["LATITUDE"], uc["LONGITUDE"]],
                radius=4,
                color=cor,
                fill=True,
                popup=folium.Popup(
                    f"<b>Parada {dados.get('ordem', '?')}</b><br>"
                    f"ODI {uc['ODI']}<br>{dados.get('Municipio', '')}<br>"
                    f"{dados.get('n_ucs', '?')} UC(s) na obra<br>"
                    f"Estrato {uc['Estrato']}",
                    max_width=250),
            ).add_to(grupo)
        grupo.add_to(mapa)
    # Fase 4: controle para ligar/desligar amostras.
    folium.LayerControl(collapsed=False).add_to(mapa)
    # Saida: HTML autocontido.
    mapa.save(str(caminho))
