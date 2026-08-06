# -*- coding: utf-8 -*-
"""Testes do motor de custo com valores conferidos em planilha manual."""
import pandas as pd
import pytest
from src import config
from src.custo import custo_por_odi, agregar_por_estrato, tarifa_campo

def _odis_teste():
    # 2 ODIs no estrato 1 (mesmo municipio X), 1 no estrato 2 (municipio Y).
    return pd.DataFrame({
        "ODI": ["A", "B", "C"], "Estrato": [1, 1, 2], "Municipio": ["X", "X", "Y"],
        "n_ucs": [2, 1, 3],
        "lat_centro": [-1.60, -1.70, -1.80], "lon_centro": [-48.65, -48.70, -48.75],
        "dist_interna_km": [2.0, 0.0, 5.0],
    })

def _config_redonda(monkeypatch):
    # Fixa parametros redondos para conferencia manual da formula.
    monkeypatch.setattr(config, "FATOR_RODOVIARIO", 1.0)
    monkeypatch.setattr(config, "VELOCIDADE_KMH", 50.0)
    monkeypatch.setattr(config, "HORAS_DIA_CAMPO", 8.0)
    monkeypatch.setattr(config, "HORAS_ESCRITORIO_POR_OS", 10.0)
    monkeypatch.setattr(config, "UCS_POR_DIA", {"LPT": 4.0, "MLA": 1.0})
    monkeypatch.setattr(config, "PERFIL_EQUIPE", "ENGENHEIRO")
    monkeypatch.setattr(config, "TARIFAS_HORA",
                        {"ENGENHEIRO": {"campo": 100.0, "escritorio": 50.0}})
    monkeypatch.setattr(config, "CUSTO_DIARIA", 0.0)

def test_custo_por_odi_formula(monkeypatch):
    _config_redonda(monkeypatch)
    r = custo_por_odi(_odis_teste(), uf="PA", tipo_contrato="LPT")
    a = r[r["ODI"] == "A"].iloc[0]
    # Mobilizacao municipal e' rateada: A e B (mesmo municipio X) tem o MESMO acesso.
    b = r[r["ODI"] == "B"].iloc[0]
    assert a["dist_acesso_km"] == pytest.approx(b["dist_acesso_km"])
    assert a["dist_acesso_km"] > 0
    # horas_inspecao = n_ucs * (8h / 4 UCs por dia) = 2 * 2h = 4h -> custo = 4 * 100.
    assert a["horas_inspecao"] == pytest.approx(4.0)
    assert a["custo_insp"] == pytest.approx(400.0)
    # custo_desloc = horas_desloc * tarifa de campo (100).
    assert a["custo_desloc"] == pytest.approx(a["horas_desloc"] * 100.0)
    # total por ODI = so campo (desloc + inspecao); o fixo de OS entra por estrato.
    assert a["custo_total"] == pytest.approx(a["custo_desloc"] + a["custo_insp"])

def test_tipo_contrato_muda_produtividade(monkeypatch):
    _config_redonda(monkeypatch)
    lpt = custo_por_odi(_odis_teste(), uf="PA", tipo_contrato="LPT")
    mla = custo_por_odi(_odis_teste(), uf="PA", tipo_contrato="MLA")
    # MLA (1 UC/dia) consome 4x as horas de inspecao de LPT (4 UCs/dia).
    assert mla["horas_inspecao"].sum() == pytest.approx(4 * lpt["horas_inspecao"].sum())

def test_agregar_por_estrato_soma_e_fixo(monkeypatch):
    _config_redonda(monkeypatch)
    r = custo_por_odi(_odis_teste(), uf="PA", tipo_contrato="LPT")
    agg = agregar_por_estrato(r)
    # 2 estratos + linha TOTAL.
    assert len(agg) == 3
    e1 = agg[agg["Estrato"] == 1].iloc[0]
    # custo_fixo_os = 10h de escritorio * 50 = 500, UMA vez por estrato.
    assert e1["custo_fixo_os"] == pytest.approx(500.0)
    # equipe_dias = horas de campo do estrato / 8.
    assert e1["equipe_dias"] == pytest.approx((e1["horas_desloc"] + e1["horas_inspecao"]) / 8.0)
    # custo_total do estrato = campo (soma dos ODIs) + fixo.
    soma_campo = r[r["Estrato"] == 1]["custo_total"].sum()
    assert e1["custo_total"] == pytest.approx(soma_campo + 500.0)
    # TOTAL soma os estratos (fixo incluido 2x: uma vez por estrato).
    total = agg[agg["Estrato"] == "TOTAL"].iloc[0]
    assert total["custo_fixo_os"] == pytest.approx(1000.0)
    assert total["custo_total"] == pytest.approx(agg[agg["Estrato"] != "TOTAL"]["custo_total"].sum())

def test_tarifa_campo_inclui_diaria(monkeypatch):
    _config_redonda(monkeypatch)
    # CUSTO_DIARIA = 80 por dia de campo -> 80/8h = +10/h sobre a tarifa 100.
    monkeypatch.setattr(config, "CUSTO_DIARIA", 80.0)
    assert tarifa_campo() == pytest.approx(110.0)
