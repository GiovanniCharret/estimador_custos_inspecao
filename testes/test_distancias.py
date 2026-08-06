# -*- coding: utf-8 -*-
"""Testes de geometria: valores conferidos a mao/na calculadora geodesica."""
import pandas as pd
import pytest
from src.distancias import haversine_km, resumo_por_odi

def test_haversine_valor_conhecido():
    # Belem (-1.4558, -48.4902) -> Castanhal (-1.2939, -47.9264): ~65.2 km em linha reta geodesica.
    d = haversine_km(-1.4558, -48.4902, -1.2939, -47.9264)
    assert d == pytest.approx(65.2, abs=1.5)

def test_haversine_zero():
    # Mesmo ponto: distancia zero.
    assert haversine_km(-1.5, -48.5, -1.5, -48.5) == pytest.approx(0.0, abs=1e-9)

def test_resumo_por_odi():
    # 1 ODI com 3 UCs em linha (0.01 grau de lat ~ 1.11 km entre vizinhas).
    df = pd.DataFrame({
        "ODI": ["A"] * 3, "Estrato": [1] * 3, "Municipio": ["X"] * 3,
        "UC": ["u1", "u2", "u3"],
        "LATITUDE": [-1.60, -1.61, -1.62], "LONGITUDE": [-48.65] * 3,
    })
    r = resumo_por_odi(df)
    assert len(r) == 1 and r.loc[0, "n_ucs"] == 3
    assert r.loc[0, "lat_centro"] == pytest.approx(-1.61)
    # Rota u1->u2->u3 = ~2.22 km (2 x 1.11).
    assert r.loc[0, "dist_interna_km"] == pytest.approx(2.22, abs=0.05)

def test_resumo_odi_uma_uc_dist_zero():
    # ODI com 1 UC: sem percurso interno.
    df = pd.DataFrame({"ODI": ["A"], "Estrato": [1], "Municipio": ["X"], "UC": ["u1"],
                       "LATITUDE": [-1.6], "LONGITUDE": [-48.65]})
    assert resumo_por_odi(df).loc[0, "dist_interna_km"] == 0.0
