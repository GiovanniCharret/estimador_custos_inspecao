# -*- coding: utf-8 -*-
"""Testes do mapa folium: pontos das UCs, base da equipe, ausencia de rota."""
import pandas as pd

from src import config
from src.mapas import gravar_mapa


def _ucs_teste():
    """UCs de tres obras (2 para A, 1 para B, 3 para C), em dois municipios."""
    return pd.DataFrame({
        "ODI": ["A", "A", "B", "C", "C", "C"],
        "Estrato": [1, 1, 1, 2, 2, 2],
        "Municipio": ["X", "X", "X", "Y", "Y", "Y"],
        "UC": ["a1", "a2", "b1", "c1", "c2", "c3"],
        "LATITUDE": [-1.60, -1.605, -1.70, -1.80, -1.805, -1.81],
        "LONGITUDE": [-48.65, -48.652, -48.70, -48.75, -48.752, -48.755],
    })


def test_gravar_mapa_marca_uma_uc_por_ponto(tmp_path):
    # Cada UC vira um ponto - a obra com 3 UCs aparece 3 vezes, nao uma.
    destino = tmp_path / "Mapa_Estratos_3.html"
    gravar_mapa(_ucs_teste(), *config.CAPITAIS_UF["PA"], destino)
    html = destino.read_text(encoding="utf-8")
    assert destino.exists()
    assert html.count("circle_marker") >= 6 or html.lower().count("circlemarker") >= 6
    # O popup localiza a obra e diz o tamanho dela, sem nenhuma nocao de ordem.
    assert "ODI A" in html and "3 UC(s) na obra" in html


def test_gravar_mapa_nao_desenha_rota(tmp_path):
    # Decisao do humano (2026-08-13): o mapa localiza, nao propoe itinerario.
    destino = tmp_path / "Mapa_Estratos_3.html"
    gravar_mapa(_ucs_teste(), *config.CAPITAIS_UF["PA"], destino)
    html = destino.read_text(encoding="utf-8")
    assert "poly_line" not in html.lower() and "polyline" not in html.lower()
    assert "parada" not in html.lower()
    # Sem rota nao ha o que dividir entre equipes: o radio saiu junto.
    assert "Equipes em campo" not in html
    assert "groupedlayers" not in html.lower()


def test_gravar_mapa_marca_a_base_da_equipe(tmp_path):
    # A capital continua no mapa: e' de onde a equipe parte, e nao e' obra.
    destino = tmp_path / "Mapa_Estratos_3.html"
    gravar_mapa(_ucs_teste(), *config.CAPITAIS_UF["PA"], destino)
    html = destino.read_text(encoding="utf-8")
    assert "Base da equipe" in html


def test_gravar_mapa_amostra_vazia(tmp_path):
    # Amostra sem obra nenhuma: mapa so com a base, sem ponto e sem estourar.
    destino = tmp_path / "Mapa_Estratos_3.html"
    gravar_mapa(_ucs_teste().iloc[0:0], *config.CAPITAIS_UF["PA"], destino)
    html = destino.read_text(encoding="utf-8")
    assert destino.exists()
    assert "Base da equipe" in html
    assert "UC(s) na obra" not in html
