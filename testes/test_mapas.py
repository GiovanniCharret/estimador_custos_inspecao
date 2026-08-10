# -*- coding: utf-8 -*-
"""Testes do mapa folium: radio de equipes, roteiro por equipe, base da equipe."""
import re

import pandas as pd

from src import config
from src.distancias import dividir_roteiro, resumo_por_odi
from src.mapas import gravar_mapa
from testes.test_custo import _odis_teste


def _ucs_teste():
    """UCs correspondentes as obras de _odis_teste (2 para A, 1 para B, 3 para C)."""
    return pd.DataFrame({
        "ODI": ["A", "A", "B", "C", "C", "C"],
        "Estrato": [1, 1, 1, 2, 2, 2],
        "Municipio": ["X", "X", "X", "Y", "Y", "Y"],
        "UC": ["a1", "a2", "b1", "c1", "c2", "c3"],
        "LATITUDE": [-1.60, -1.605, -1.70, -1.80, -1.805, -1.81],
        "LONGITUDE": [-48.65, -48.652, -48.70, -48.75, -48.752, -48.755],
    })


def _rotas(*quantidades_de_equipes):
    """Monta o dict {n_equipes: [(roteiro, km), ...]} que gravar_mapa espera."""
    return {n: dividir_roteiro(_odis_teste(), *config.CAPITAIS_UF["PA"], n)
            for n in quantidades_de_equipes}


def test_gravar_mapa_radio_por_numero_de_equipes(tmp_path):
    # O painel oferece um cenario de equipes por vez (radio), nao a amostra.
    destino = tmp_path / "Mapa_Estratos_3.html"
    gravar_mapa(_ucs_teste(), _rotas(1, 2), *config.CAPITAIS_UF["PA"], destino)
    html = destino.read_text(encoding="utf-8")
    assert destino.exists()
    # GroupedLayerControl (radio proprio) e nao o LayerControl padrao, que misturaria
    # os cenarios com o tile de fundo e apagaria o mapa ao trocar de cenario.
    assert "groupedlayers" in html.lower()
    assert "Equipes em campo" in html
    # Um rotulo por cenario, com o km somado - e' o que revela o preco de dividir.
    rotulos = re.findall(r"\d+ equipes? - [\d,]+ km", html)
    assert len(rotulos) == 2
    # A amostra nao e' mais camada (so uma e' precificada por execucao).
    assert "Amostra 1" not in html


def test_gravar_mapa_desenha_roteiro_e_base(tmp_path):
    # A polilinha e o marcador da capital tornam visivel "uma viagem so".
    destino = tmp_path / "Mapa_Estratos_3.html"
    gravar_mapa(_ucs_teste(), _rotas(1), *config.CAPITAIS_UF["PA"], destino)
    html = destino.read_text(encoding="utf-8")
    assert "poly_line" in html.lower() or "polyline" in html.lower()
    assert "Base da equipe" in html
    # O popup diz de qual equipe e' a parada e em que ordem ela cai.
    assert "Equipe 1 - parada" in html and "ODI A" in html


def test_gravar_mapa_duas_equipes_tem_duas_linhas(tmp_path):
    # Com 2 equipes ha 2 polilinhas, cada uma com o seu tooltip de obras/km.
    destino = tmp_path / "Mapa_Estratos_3.html"
    gravar_mapa(_ucs_teste(), _rotas(2), *config.CAPITAIS_UF["PA"], destino)
    html = destino.read_text(encoding="utf-8")
    assert "Equipe 1:" in html and "Equipe 2:" in html


def test_gravar_mapa_amostra_vazia(tmp_path):
    # Amostra sem obra nenhuma: mapa so com a base, sem camadas e sem estourar.
    vazio = resumo_por_odi(pd.DataFrame(columns=["ODI", "Estrato", "Municipio", "UC",
                                                 "LATITUDE", "LONGITUDE"]))
    destino = tmp_path / "Mapa_Estratos_3.html"
    gravar_mapa(_ucs_teste().iloc[0:0],
                {1: dividir_roteiro(vazio, *config.CAPITAIS_UF["PA"], 1)},
                *config.CAPITAIS_UF["PA"], destino)
    html = destino.read_text(encoding="utf-8")
    assert destino.exists()
    assert "Base da equipe" in html
    assert "Equipes em campo" not in html
