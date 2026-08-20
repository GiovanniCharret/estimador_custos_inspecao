# -*- coding: utf-8 -*-
"""Mapa interativo (folium) de uma estratificacao: onde estao as obras sorteadas."""
import folium

# Cor unica dos pontos: o mapa nao categoriza nada, so localiza.
# Vermelho desde 2026-08-20 (decisao do humano): era azul (#1f77b4) e se perdia sobre a
# agua e as vias do mapa-base, que tambem sao azuis. O vermelho e' a cor mais distante do
# fundo do OpenStreetMap, entao o ponto sobressai sem precisar aumentar o raio.
COR_PONTO = "#e31a1c"


def gravar_mapa(df_ucs, lat_origem, lon_origem, caminho):
    """Grava o mapa de uma estratificacao marcando as UCs sorteadas.

    Por que existe: substitui o mapa manual do QGIS (D3) e responde UMA pergunta -
    "onde estao as obras que cairam na amostra". O desenho do roteiro saiu em 2026-08-13
    por decisao do humano: a linha e a numeracao das paradas eram uma hipotese do modelo
    (rota gulosa) desenhada com a mesma tinta dos fatos (as coordenadas), e quem olha o
    mapa nao usa a ordem para nada - quem usa o itinerario e' o calculo de custo, que
    continua intacto em distancias.py. Sem rota nao ha o que separar por equipe, entao
    o radio 'Equipes em campo' tambem saiu e o mapa voltou a ter uma camada so.

    Logica: Entrada (df de UCs, capital da UF, caminho) -> Fase 1: centraliza o mapa nas
    UCs -> Fase 2: marca a capital, que e' de onde a equipe parte -> Fase 3: conta as UCs
    de cada obra, para o popup dizer o tamanho da obra e nao so o ponto -> Fase 4: um
    marcador por UC -> Saida: .html autocontido.
    """
    # Fase 1: centro do mapa = centroide das UCs; sem UC nenhuma, a base da equipe.
    if len(df_ucs):
        centro = [df_ucs["LATITUDE"].mean(), df_ucs["LONGITUDE"].mean()]
    else:
        centro = [lat_origem, lon_origem]
    mapa = folium.Map(location=centro, zoom_start=8)
    # Fase 2: a capital nao e' obra - e' de onde a equipe sai. Icone e cor proprios.
    folium.Marker(
        location=[lat_origem, lon_origem],
        popup="Base da equipe (capital da UF)",
        icon=folium.Icon(color="black", icon="home"),
    ).add_to(mapa)
    # Fase 3: quantas UCs tem cada obra. Uma ODI vira varios pontos quando tem varias UCs,
    # e sem esse numero o popup nao diria se o ponto e' uma obra grande ou pequena.
    if len(df_ucs):
        ucs_por_odi = df_ucs["ODI"].value_counts().to_dict()
    else:
        ucs_por_odi = {}
    # Fase 4: um marcador por UC, todos iguais - o mapa localiza, nao classifica.
    for _, uc in df_ucs.iterrows():
        folium.CircleMarker(
            location=[uc["LATITUDE"], uc["LONGITUDE"]],
            radius=4,
            color=COR_PONTO,
            fill=True,
            popup=folium.Popup(
                f"<b>ODI {uc['ODI']}</b><br>{uc['Municipio']}<br>"
                f"{ucs_por_odi.get(uc['ODI'], '?')} UC(s) na obra",
                max_width=250),
        ).add_to(mapa)
    # Saida: HTML autocontido.
    mapa.save(str(caminho))
