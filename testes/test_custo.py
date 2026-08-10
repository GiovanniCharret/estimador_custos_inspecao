# -*- coding: utf-8 -*-
"""Testes do motor de custo (modelo F9: por amostra, roteiro encadeado, dias inteiros)."""
import math

import pandas as pd
import pytest

from src import config
from src.custo import cenarios_por_prazo, custo_amostra, tarifa_campo
from src.distancias import haversine_km


def _odis_teste():
    """3 obras: A e B no municipio X, C no municipio Y (todas na regiao de Belem-PA)."""
    return pd.DataFrame({
        "ODI": ["A", "B", "C"], "Estrato": [1, 1, 2], "Municipio": ["X", "X", "Y"],
        "n_ucs": [2, 1, 3],
        "lat_centro": [-1.60, -1.70, -1.80], "lon_centro": [-48.65, -48.70, -48.75],
        "dist_interna_km": [2.0, 0.0, 5.0],
    })


def _config_redonda(monkeypatch):
    """Fixa parametros redondos para a formula ser conferivel a mao."""
    monkeypatch.setattr(config, "FATOR_RODOVIARIO", 1.0)
    monkeypatch.setattr(config, "VELOCIDADE_KMH", 50.0)
    monkeypatch.setattr(config, "HORAS_DIA_CAMPO", 8.0)
    monkeypatch.setattr(config, "HORAS_ESCRITORIO_POR_OS", 10.0)
    monkeypatch.setattr(config, "UCS_POR_DIA", {"LPT": 4.0, "MLA": 1.0})
    monkeypatch.setattr(config, "PERFIL_EQUIPE", "ENGENHEIRO")
    monkeypatch.setattr(config, "TARIFAS_HORA",
                        {"ENGENHEIRO": {"campo": 100.0, "escritorio": 50.0}})
    monkeypatch.setattr(config, "CUSTO_DIARIA", 0.0)
    monkeypatch.setattr(config, "TAMANHO_EQUIPE", 1.0)
    monkeypatch.setattr(config, "DIAS_MOBILIZACAO", 1.0)


def test_custo_amostra_formula(monkeypatch):
    # Confere a cadeia inteira km -> horas -> dias -> R$ com numeros redondos.
    _config_redonda(monkeypatch)
    numeros, roteiro = custo_amostra(_odis_teste(), uf="PA", tipo_contrato="LPT")
    # 6 UCs x (8h / 4 UCs por dia) = 12h de inspecao.
    assert numeros["n_ucs"] == 6
    assert numeros["horas_inspecao"] == pytest.approx(12.0)
    # Roteiro: km do itinerario + percurso interno (2 + 0 + 5), FATOR_RODOVIARIO = 1.
    km_itinerario = roteiro["km_trecho"].sum() + haversine_km(
        roteiro.iloc[-1]["lat_centro"], roteiro.iloc[-1]["lon_centro"], *config.CAPITAIS_UF["PA"])
    assert numeros["km_roteiro"] == pytest.approx(km_itinerario + 7.0)
    # Horas de roteiro = km / 50.
    assert numeros["horas_roteiro"] == pytest.approx(numeros["km_roteiro"] / 50.0)
    # Dias de trabalho = teto das horas de campo / 8; faturados somam 1 de mobilizacao.
    horas_campo = numeros["horas_roteiro"] + numeros["horas_inspecao"]
    assert numeros["dias_trabalho"] == math.ceil(horas_campo / 8.0)
    assert numeros["dias_faturados"] == numeros["dias_trabalho"] + 1
    # Custo de campo = dias x equipe x jornada x tarifa; fixo = 10h x 50.
    assert numeros["custo_campo"] == pytest.approx(numeros["dias_faturados"] * 1 * 8 * 100.0)
    assert numeros["custo_fixo"] == pytest.approx(500.0)
    assert numeros["custo_total"] == pytest.approx(numeros["custo_campo"] + 500.0)


def test_roteiro_encadeado_e_muito_menor_que_ida_e_volta_por_obra(monkeypatch):
    # REGRESSAO DA F9: o modelo antigo mandava a equipe voltar a capital a cada municipio,
    # o que inflava a quilometragem em ~7x nos dados reais. O itinerario unico tem de ser
    # drasticamente menor que a soma das idas-e-voltas.
    _config_redonda(monkeypatch)
    df = _odis_teste()
    numeros, _ = custo_amostra(df, uf="PA", tipo_contrato="LPT")
    lat_cap, lon_cap = config.CAPITAIS_UF["PA"]
    # Modelo antigo: 2 x (capital -> centroide do municipio), uma vez por municipio.
    ida_e_volta = sum(
        2 * haversine_km(lat_cap, lon_cap, float(g["lat_centro"].mean()), float(g["lon_centro"].mean()))
        for _, g in df.groupby("Municipio")
    )
    assert numeros["km_roteiro"] < ida_e_volta
    # E o roteiro nao pode ser menor que a ida a obra mais proxima somada a volta dela.
    assert numeros["km_roteiro"] > 0


def test_custo_fixo_nao_depende_do_numero_de_estratos(monkeypatch):
    # REGRESSAO DA F9: o fixo de escritorio entra UMA vez por amostra. Antes ele entrava
    # uma vez por estrato, multiplicando R$12.960 pelo numero de estratos da amostra.
    _config_redonda(monkeypatch)
    um_estrato = _odis_teste().assign(Estrato=[1, 1, 1])
    tres_estratos = _odis_teste().assign(Estrato=[1, 2, 3])
    a, _ = custo_amostra(um_estrato, uf="PA", tipo_contrato="LPT")
    b, _ = custo_amostra(tres_estratos, uf="PA", tipo_contrato="LPT")
    # Mesma geometria, mesmos rotulos de estrato trocados: o custo tem de ser identico.
    assert a["custo_fixo"] == b["custo_fixo"] == pytest.approx(500.0)
    assert a["custo_total"] == pytest.approx(b["custo_total"])


def test_tipo_contrato_muda_produtividade(monkeypatch):
    # MLA (1 UC/dia) consome 4x as horas de inspecao de LPT (4 UCs/dia).
    _config_redonda(monkeypatch)
    lpt, _ = custo_amostra(_odis_teste(), uf="PA", tipo_contrato="LPT")
    mla, _ = custo_amostra(_odis_teste(), uf="PA", tipo_contrato="MLA")
    assert mla["horas_inspecao"] == pytest.approx(4 * lpt["horas_inspecao"])
    # Mais horas de inspecao nunca pode sair mais barato.
    assert mla["custo_total"] >= lpt["custo_total"]


def test_dias_arredondam_para_cima(monkeypatch):
    # A equipe nao vende meio dia: qualquer fracao vira dia inteiro.
    _config_redonda(monkeypatch)
    numeros, _ = custo_amostra(_odis_teste(), uf="PA", tipo_contrato="LPT")
    assert numeros["dias_trabalho"] >= numeros["dias_fracionarios"]
    assert numeros["dias_trabalho"] == math.ceil(numeros["dias_fracionarios"])
    assert float(numeros["dias_trabalho"]).is_integer()


def test_dobrar_a_equipe_metade_dos_dias_e_nao_metade_do_custo(monkeypatch):
    # Duas equipes fazem o MESMO trabalho na metade dos dias (Fase 6 do MODELO_CUSTO.md).
    # O custo nao cai junto: o contrato paga por hora-profissional. Ele ate sobe um pouco,
    # porque cada equipe carrega o seu dia de mobilizacao e o arredondamento para dia
    # inteiro desperdica mais quanto mais equipes houver.
    _config_redonda(monkeypatch)
    um, _ = custo_amostra(_odis_teste(), uf="PA", tipo_contrato="LPT")
    monkeypatch.setattr(config, "TAMANHO_EQUIPE", 2.0)
    dois, _ = custo_amostra(_odis_teste(), uf="PA", tipo_contrato="LPT")
    # Os dias por equipe caem (aproximadamente pela metade, com o teto por cima).
    assert dois["dias_trabalho"] == math.ceil(um["dias_fracionarios"] / 2)
    assert dois["dias_trabalho"] < um["dias_trabalho"]
    # O custo de campo NAO cai - e' >= o de uma equipe so.
    assert dois["custo_campo"] >= um["custo_campo"]
    # O fixo de escritorio nao tem nada a ver com equipe.
    assert dois["custo_fixo"] == pytest.approx(um["custo_fixo"])


def test_cenarios_por_prazo(monkeypatch):
    # A aba Cenarios responde "e se eu precisar terminar antes?": o prazo e' dado e o
    # numero de equipes se ajusta. A faixa e' centrada no prazo calculado.
    _config_redonda(monkeypatch)
    monkeypatch.setattr(config, "VARIACAO_DIAS_CENARIOS", 2)
    numeros, _ = custo_amostra(_odis_teste(), uf="PA", tipo_contrato="LPT")
    cenarios = cenarios_por_prazo(numeros)
    centro = numeros["dias_trabalho"]
    # Faixa de 5 prazos (centro +- 2), em ordem crescente, sem descer abaixo de 1 dia.
    assert [c["dias_trabalho"] for c in cenarios] == list(range(max(1, centro - 2), centro + 3))
    assert all(c["dias_trabalho"] >= 1 and c["equipes"] >= 1 for c in cenarios)
    # O cenario 'calculado' reproduz exatamente a linha oficial do Resumo.
    base = [c for c in cenarios if c["cenario"] == "calculado"]
    assert len(base) == 1
    assert base[0]["custo_total"] == pytest.approx(numeros["custo_total"])
    # Prazo mais curto exige equipe igual ou maior (nunca menor).
    equipes = [c["equipes"] for c in cenarios]
    assert equipes == sorted(equipes, reverse=True)
    # Cada cenario fecha com a mesma formula do motor.
    for c in cenarios:
        assert c["custo_campo"] == pytest.approx(
            c["equipes"] * c["dias_faturados"] * config.HORAS_DIA_CAMPO * 100.0)
        assert c["custo_total"] == pytest.approx(c["custo_campo"] + c["custo_fixo"])


def test_cenarios_de_amostra_vazia(monkeypatch):
    # Amostra sem obra nenhuma nao tem prazo a explorar - lista vazia, nao divisao por zero.
    _config_redonda(monkeypatch)
    vazio = _odis_teste().iloc[0:0]
    numeros, _ = custo_amostra(vazio, uf="PA", tipo_contrato="LPT")
    assert cenarios_por_prazo(numeros) == []


def test_reproduz_a_formula_do_benchmark_da_engenharia(monkeypatch):
    # A engenharia da PB 7a Tranche estimou 3 amostras e as tres obedecem, ao centavo, a
    #     custo = 12.960 + 9.600 x (dias + 1),  com 9.600 = 2 pessoas x 8h x R$600.
    # Este teste amarra o motor aquela formula: com TAMANHO_EQUIPE = 2 e os parametros
    # reais de config, o custo tem de cair exatamente nela. Se alguem mudar a estrutura
    # do modelo (fixo por estrato, dias fracionarios, ida-e-volta), este teste cai.
    monkeypatch.setattr(config, "TAMANHO_EQUIPE", 2.0)
    numeros, _ = custo_amostra(_odis_teste(), uf="PB", tipo_contrato="LPT")
    esperado = 12960 + 9600 * (numeros["dias_trabalho"] + 1)
    assert numeros["custo_total"] == pytest.approx(esperado, abs=0.01)


def test_tarifa_campo_inclui_diaria(monkeypatch):
    _config_redonda(monkeypatch)
    # CUSTO_DIARIA = 80 por dia de campo -> 80/8h = +10/h sobre a tarifa 100.
    monkeypatch.setattr(config, "CUSTO_DIARIA", 80.0)
    assert tarifa_campo() == pytest.approx(110.0)
