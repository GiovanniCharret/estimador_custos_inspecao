# -*- coding: utf-8 -*-
"""Testes de geometria: valores conferidos a mao/na calculadora geodesica."""
import pandas as pd
import pytest
from src.distancias import dividir_roteiro, haversine_km, montar_roteiro, resumo_por_odi


def _odis(municipios, lats, lons):
    """Monta o df minimo que montar_roteiro consome (uma linha por obra)."""
    return pd.DataFrame({
        "ODI": [f"O{i}" for i in range(len(lats))],
        "Municipio": municipios, "lat_centro": lats, "lon_centro": lons,
        "n_ucs": [1] * len(lats), "dist_interna_km": [0.0] * len(lats),
    })

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


def test_roteiro_visita_todas_as_obras_uma_vez():
    # Quatro obras em tres municipios: a ordem tem de ser uma permutacao completa de 1..4.
    df = _odis(["X", "X", "Y", "Z"], [-1.60, -1.62, -1.90, -2.30], [-48.65, -48.66, -48.90, -49.10])
    roteiro, km = montar_roteiro(df, -1.4558, -48.4902)
    assert sorted(roteiro["ordem"]) == [1, 2, 3, 4]
    assert set(roteiro["ODI"]) == set(df["ODI"])
    assert km > 0


def test_roteiro_nao_sai_e_volta_ao_mesmo_municipio():
    # As obras de um municipio tem de ser visitadas em sequencia: a equipe nao entra,
    # sai e volta ao mesmo lugar. X esta longe da capital e Y no meio do caminho -
    # uma rota gulosa ingenua sobre as obras poderia intercalar X-Y-X.
    df = _odis(["X", "Y", "X"], [-2.50, -1.90, -2.52], [-49.20, -48.90, -49.22])
    roteiro, _ = montar_roteiro(df, -1.4558, -48.4902)
    ordens_x = sorted(roteiro[roteiro["Municipio"] == "X"]["ordem"])
    # Consecutivas: a diferenca entre a maior e a menor e' o numero de obras menos 1.
    assert ordens_x[-1] - ordens_x[0] == len(ordens_x) - 1


def test_roteiro_km_fecha_com_os_trechos_mais_a_volta():
    # O km total e' a soma dos trechos ate cada obra MAIS a volta unica a capital.
    lat0, lon0 = -1.4558, -48.4902
    df = _odis(["X", "Y", "Z"], [-1.60, -1.90, -2.30], [-48.65, -48.90, -49.10])
    roteiro, km = montar_roteiro(df, lat0, lon0)
    ultima = roteiro.iloc[-1]
    volta = haversine_km(ultima["lat_centro"], ultima["lon_centro"], lat0, lon0)
    assert km == pytest.approx(roteiro["km_trecho"].sum() + volta)


def test_roteiro_e_deterministico():
    # Convencao do canonico: mesma entrada -> mesma rota, sempre.
    df = _odis(["X", "Y", "Z"], [-1.60, -1.90, -2.30], [-48.65, -48.90, -49.10])
    r1, km1 = montar_roteiro(df, -1.4558, -48.4902)
    r2, km2 = montar_roteiro(df, -1.4558, -48.4902)
    assert km1 == km2
    assert list(r1["ODI"]) == list(r2["ODI"])


def test_roteiro_amostra_vazia():
    # Amostra sem nenhuma obra nao pode estourar: roteiro vazio, zero km.
    vazio = _odis([], [], [])
    roteiro, km = montar_roteiro(vazio, -1.4558, -48.4902)
    assert len(roteiro) == 0 and km == 0.0


def test_dividir_roteiro_reparte_todas_as_obras():
    # Toda obra tem exatamente um dono: nenhuma some, nenhuma e' visitada duas vezes.
    df = _odis(["X", "Y", "Z", "W"], [-1.60, -1.90, -2.30, -2.60], [-48.65, -48.90, -49.10, -49.30])
    rotas = dividir_roteiro(df, -1.4558, -48.4902, 2)
    assert len(rotas) == 2
    donos = [odi for roteiro, _ in rotas for odi in roteiro["ODI"]]
    assert sorted(donos) == sorted(df["ODI"])
    # Cada equipe tem o seu roteiro numerado do 1 (sai da capital como qualquer outra).
    for roteiro, _ in rotas:
        assert list(roteiro["ordem"]) == list(range(1, len(roteiro) + 1))


def test_dividir_roteiro_soma_mais_km_que_uma_equipe():
    # O PRECO DE DIVIDIR: cada equipe sai da capital e volta, entao a quilometragem
    # somada de N equipes e' sempre maior que a de uma equipe so. E' o que o mapa mostra
    # e o que torna otimista o cenario de 2 equipes da aba Cenarios.
    df = _odis(["X", "Y", "Z", "W"], [-1.60, -1.90, -2.30, -2.60], [-48.65, -48.90, -49.10, -49.30])
    (_, km_uma), = dividir_roteiro(df, -1.4558, -48.4902, 1)
    km_duas = sum(km for _, km in dividir_roteiro(df, -1.4558, -48.4902, 2))
    assert km_duas > km_uma


def test_dividir_roteiro_uma_equipe_e_o_roteiro_inteiro():
    # Pedir 1 equipe tem de dar exatamente o mesmo que montar_roteiro direto.
    df = _odis(["X", "Y", "Z"], [-1.60, -1.90, -2.30], [-48.65, -48.90, -49.10])
    inteiro, km_inteiro = montar_roteiro(df, -1.4558, -48.4902)
    (rota, km), = dividir_roteiro(df, -1.4558, -48.4902, 1)
    assert km == pytest.approx(km_inteiro)
    assert list(rota["ODI"]) == list(inteiro["ODI"])


def test_dividir_roteiro_mais_equipes_que_obras():
    # Mais equipes que obras: cada obra vira um roteiro, as equipes excedentes ficam sem.
    df = _odis(["X", "Y"], [-1.60, -1.90], [-48.65, -48.90])
    rotas = dividir_roteiro(df, -1.4558, -48.4902, 5)
    assert len(rotas) == 2
    assert all(len(roteiro) == 1 for roteiro, _ in rotas)


def test_dividir_roteiro_e_deterministico():
    # Mesma entrada -> mesma divisao, sempre (convencao do canonico).
    df = _odis(["X", "Y", "Z", "W"], [-1.60, -1.90, -2.30, -2.60], [-48.65, -48.90, -49.10, -49.30])
    a = dividir_roteiro(df, -1.4558, -48.4902, 2)
    b = dividir_roteiro(df, -1.4558, -48.4902, 2)
    assert [list(r["ODI"]) for r, _ in a] == [list(r["ODI"]) for r, _ in b]
    assert [km for _, km in a] == [km for _, km in b]
