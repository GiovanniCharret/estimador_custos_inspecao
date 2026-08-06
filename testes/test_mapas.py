# -*- coding: utf-8 -*-
"""Testes do mapa folium: existencia e conteudo minimo do HTML."""
import pandas as pd
from src.custo import custo_por_odi
from src.mapas import gravar_mapa
from testes.test_custo import _odis_teste

def _ucs_teste():
    # 2 UCs para o ODI A, 1 para B, 1 para C (estratos 1/1/2).
    return pd.DataFrame({
        "ODI": ["A", "A", "B", "C"], "Estrato": [1, 1, 1, 2], "Municipio": ["X"] * 4,
        "UC": ["a1", "a2", "b1", "c1"],
        "LATITUDE": [-1.60, -1.605, -1.70, -1.80],
        "LONGITUDE": [-48.65, -48.652, -48.70, -48.75],
    })

def test_gravar_mapa(tmp_path):
    destino = tmp_path / "Mapa_Amostra_1.html"
    gravar_mapa(_ucs_teste(), custo_por_odi(_odis_teste(), uf="PA", tipo_contrato="LPT"), destino)
    html = destino.read_text(encoding="utf-8")
    # HTML existe, tem os grupos por estrato e os popups com a ODI.
    assert destino.exists()
    assert "Estrato 1" in html and "Estrato 2" in html
    assert "ODI A" in html
