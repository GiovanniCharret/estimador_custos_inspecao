# -*- coding: utf-8 -*-
"""Mapas interativos (folium) de uma estratificacao: um cenario de equipes por vez."""
import folium
from folium.plugins import GroupedLayerControl

# Paleta fixa por EQUIPE dentro de um cenario (equipe 1 azul, equipe 2 vermelha, ...).
CORES = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf"]


def gravar_mapa(df_ucs, roteiros_por_equipes, lat_origem, lon_origem, caminho):
    """Grava o mapa de uma estratificacao com um cenario de equipes por vez (radio).

    Por que existe: substitui o mapa manual do QGIS (D3) e responde as duas perguntas que
    sobram depois da planilha - "por onde a equipe passa" e "o que muda se eu botar mais
    uma equipe". O controle e' de RADIO (um cenario por vez), nao de caixas: sobrepor os
    dois cenarios na mesma tela nao ajuda ninguem, porque as obras sao as mesmas e so as
    cores e as linhas mudam. Como o folium poe os layers exclusivos padrao no mesmo grupo
    do tile de fundo (o que apagaria o mapa ao trocar de cenario), usamos o
    GroupedLayerControl, que cria um grupo de radio proprio.

    Logica: Entrada ({n_equipes: [(roteiro, km), ...]}, origem, caminho) -> Fase 1:
    centraliza o mapa nas UCs -> Fase 2: marca a capital, que e' origem e fim de todo
    roteiro -> Fase 3: por cenario, desenha uma polilinha e os marcadores de cada equipe,
    numa cor propria -> Fase 4: junta os cenarios num controle de radio -> Saida: .html.
    """
    # Fase 1: centro do mapa = centroide das UCs; sem UC nenhuma, a base da equipe.
    if len(df_ucs):
        centro = [df_ucs["LATITUDE"].mean(), df_ucs["LONGITUDE"].mean()]
    else:
        centro = [lat_origem, lon_origem]
    mapa = folium.Map(location=centro, zoom_start=8)
    # Fase 2: a capital e' a origem e o fim de todo roteiro - fora dos cenarios, sempre visivel.
    folium.Marker(
        location=[lat_origem, lon_origem],
        popup="Base da equipe (capital da UF)",
        icon=folium.Icon(color="black", icon="home"),
    ).add_to(mapa)
    grupos = []
    # Fase 3: um cenario por numero de equipes, em ordem crescente.
    for posicao, n_equipes in enumerate(sorted(roteiros_por_equipes)):
        rotas = roteiros_por_equipes[n_equipes]
        # Cenarios sem nenhuma obra nao viram camada (amostra vazia).
        if not any(len(roteiro) for roteiro, _ in rotas):
            continue
        # O km somado do cenario vai no rotulo: e' o preco de dividir, visivel na legenda.
        km_total = sum(km for _, km in rotas)
        rotulo = f"{n_equipes} equipe{'s' if n_equipes > 1 else ''} - {km_total:,.0f} km"
        # show apenas no primeiro cenario: o radio comeca no de menos equipes.
        grupo = folium.FeatureGroup(name=rotulo, show=(posicao == 0))
        for i, (roteiro, km) in enumerate(rotas):
            if not len(roteiro):
                continue
            cor = CORES[i % len(CORES)]
            # Polilinha do itinerario desta equipe: capital -> obras na ordem -> capital.
            pontos = ([[lat_origem, lon_origem]]
                      + roteiro[["lat_centro", "lon_centro"]].values.tolist()
                      + [[lat_origem, lon_origem]])
            folium.PolyLine(
                pontos, color=cor, weight=2, opacity=0.6,
                tooltip=f"Equipe {i + 1}: {len(roteiro)} obras, {km:,.0f} km (linha reta)",
            ).add_to(grupo)
            # Indice de ordem/municipio por ODI, para o popup do marcador da UC.
            info = roteiro.set_index("ODI")[["ordem", "Municipio", "n_ucs"]].to_dict("index")
            # Marcadores das UCs das obras DESTA equipe, na cor dela.
            for _, uc in df_ucs[df_ucs["ODI"].isin(roteiro["ODI"])].iterrows():
                dados = info.get(uc["ODI"], {})
                folium.CircleMarker(
                    location=[uc["LATITUDE"], uc["LONGITUDE"]],
                    radius=4,
                    color=cor,
                    fill=True,
                    popup=folium.Popup(
                        f"<b>Equipe {i + 1} - parada {dados.get('ordem', '?')}</b><br>"
                        f"ODI {uc['ODI']}<br>{dados.get('Municipio', '')}<br>"
                        f"{dados.get('n_ucs', '?')} UC(s) na obra<br>"
                        f"Estrato {uc['Estrato']}",
                        max_width=250),
                ).add_to(grupo)
        grupo.add_to(mapa)
        grupos.append(grupo)
    # Fase 4: radio entre os cenarios (nao caixas): so um numero de equipes por vez.
    # Sem cenario nenhum (amostra vazia) nao ha o que controlar.
    if grupos:
        GroupedLayerControl(groups={"Equipes em campo": grupos},
                            exclusive_groups=True, collapsed=False).add_to(mapa)
    # Saida: HTML autocontido.
    mapa.save(str(caminho))
