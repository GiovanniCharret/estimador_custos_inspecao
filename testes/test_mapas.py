# -*- coding: utf-8 -*-
"""Testes do mapa folium: camada por amostra, roteiro desenhado, base da equipe."""
import re

import pandas as pd

from src import config
from src.custo import custo_amostra
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


def _amostras(quantas):
    """Monta o dict {k: (df_ucs, roteiro)} que gravar_mapa espera."""
    saida = {}
    for k in range(1, quantas + 1):
        _, roteiro = custo_amostra(_odis_teste(), uf="PA", tipo_contrato="LPT")
        saida[k] = (_ucs_teste(), roteiro)
    return saida


def test_gravar_mapa_camada_por_amostra(tmp_path):
    # A camada e' por AMOSTRA (nao por estrato): a comparacao util e' principal x reservas.
    destino = tmp_path / "Mapa_Estratos_3.html"
    gravar_mapa(_amostras(3), *config.CAPITAIS_UF["PA"], destino)
    html = destino.read_text(encoding="utf-8")
    assert destino.exists()
    # O bloco 'overlays' do LayerControl e' a lista de camadas ligaveis do mapa.
    overlays = re.search(r"overlays\s*:\s*\{(.*?)\}", html, flags=re.DOTALL).group(1)
    assert "Amostra 1" in overlays and "Amostra 2" in overlays and "Amostra 3" in overlays
    # O estrato nao pode mais virar camada (foi o que a F9 simplificou); ele segue
    # aparecendo no popup do marcador, que e' informacao, nao filtro.
    assert "Estrato" not in overlays
    assert "Estrato 1" in html


def test_gravar_mapa_desenha_o_roteiro_e_a_base(tmp_path):
    # A polilinha e o marcador da capital sao o que torna visivel "uma viagem so".
    destino = tmp_path / "Mapa_Estratos_3.html"
    gravar_mapa(_amostras(1), *config.CAPITAIS_UF["PA"], destino)
    html = destino.read_text(encoding="utf-8")
    assert "poly_line" in html.lower() or "polyline" in html.lower()
    assert "Base da equipe" in html
    # O popup diz a ordem da parada, que e' a leitura nova do mapa.
    assert "Parada" in html and "ODI A" in html
