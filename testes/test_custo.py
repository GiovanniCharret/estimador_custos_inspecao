# -*- coding: utf-8 -*-
"""Testes do motor de custo (modelo F15: N equipes independentes, grade equipes x prazo)."""
import math

import pandas as pd
import pytest

from src import config
from src import custo as modulo_custo
from src.custo import custo_amostra, grade_cenarios, tarifa_campo
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
    """Fixa parametros redondos para a formula ser conferivel a mao.

    N_EQUIPES_PADRAO cai para 1 aqui de proposito: com uma equipe so ha um roteiro, e a
    conta fecha na mao. Os testes que tratam de DIVIDIR sobem esse numero explicitamente.
    """
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
    monkeypatch.setattr(config, "N_EQUIPES_PADRAO", 1)
    monkeypatch.setattr(config, "N_EQUIPES_MIN", 1)
    monkeypatch.setattr(config, "N_EQUIPES_MAX", 3)
    monkeypatch.setattr(config, "MAX_DIAS_POR_EQUIPE", 20)


def test_custo_amostra_formula(monkeypatch):
    # Confere a cadeia inteira km -> horas -> dias -> R$ com numeros redondos.
    _config_redonda(monkeypatch)
    numeros, detalhe = custo_amostra(_odis_teste(), uf="PA", tipo_contrato="LPT")
    # 6 UCs x (8h / 4 UCs por dia) = 12h de inspecao.
    assert numeros["n_ucs"] == 6
    assert numeros["horas_inspecao"] == pytest.approx(12.0)
    # Roteiro: km do itinerario + percurso interno (2 + 0 + 5), FATOR_RODOVIARIO = 1.
    km_itinerario = detalhe["km_trecho"].sum() + haversine_km(
        detalhe.iloc[-1]["lat_centro"], detalhe.iloc[-1]["lon_centro"], *config.CAPITAIS_UF["PA"])
    assert numeros["km_roteiro"] == pytest.approx(km_itinerario + 7.0)
    # Horas de roteiro = km / 50.
    assert numeros["horas_roteiro"] == pytest.approx(numeros["km_roteiro"] / 50.0)
    # Dias de trabalho = teto das horas de campo / 8; faturados somam 1 de mobilizacao.
    horas_campo = numeros["horas_roteiro"] + numeros["horas_inspecao"]
    assert numeros["dias_trabalho"] == math.ceil(horas_campo / 8.0)
    assert numeros["dias_faturados"] == numeros["dias_trabalho"] + 1
    # Custo de campo = equipes x pessoas x dias x jornada x tarifa; fixo = 10h x 50.
    assert numeros["n_equipes"] == 1
    assert numeros["custo_campo"] == pytest.approx(1 * 1 * numeros["dias_faturados"] * 8 * 100.0)
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
    # PESSOAS dentro da MESMA equipe: uma dupla faz um roteiro so, na metade dos dias.
    # O custo nao cai junto: o contrato paga por hora-profissional.
    _config_redonda(monkeypatch)
    um, _ = custo_amostra(_odis_teste(), uf="PA", tipo_contrato="LPT")
    monkeypatch.setattr(config, "TAMANHO_EQUIPE", 2.0)
    dois, _ = custo_amostra(_odis_teste(), uf="PA", tipo_contrato="LPT")
    # Os dias caem (aproximadamente pela metade, com o teto por cima).
    assert dois["dias_trabalho"] == math.ceil(um["dias_fracionarios"] / 2)
    assert dois["dias_trabalho"] < um["dias_trabalho"]
    # Um roteiro so nos dois casos - a dupla viaja junta.
    assert dois["km_roteiro"] == pytest.approx(um["km_roteiro"])
    # O custo de campo NAO cai - e' >= o de uma pessoa so.
    assert dois["custo_campo"] >= um["custo_campo"]
    # O fixo de escritorio nao tem nada a ver com equipe.
    assert dois["custo_fixo"] == pytest.approx(um["custo_fixo"])


def test_duas_equipes_rodam_mais_km_e_custam_mais_que_uma(monkeypatch):
    # O CORACAO DA F15: equipes independentes nao dividem o deslocamento, elas o
    # DUPLICAM - cada uma sai da capital e volta. Antes da F15 o custo assumia trabalho
    # perfeitamente divisivel e esse km extra nunca aparecia.
    _config_redonda(monkeypatch)
    uma, _ = custo_amostra(_odis_teste(), uf="PA", tipo_contrato="LPT", n_equipes=1)
    duas, _ = custo_amostra(_odis_teste(), uf="PA", tipo_contrato="LPT", n_equipes=2)
    # A inspecao e' a mesma (as mesmas UCs), mas o km somado cresce.
    assert duas["horas_inspecao"] == pytest.approx(uma["horas_inspecao"])
    assert duas["km_roteiro"] > uma["km_roteiro"]
    # O prazo cai, o custo sobe.
    assert duas["dias_trabalho"] <= uma["dias_trabalho"]
    assert duas["custo_total"] > uma["custo_total"]
    assert duas["n_equipes"] == 2


def test_prazo_e_ditado_pela_equipe_mais_lenta(monkeypatch):
    # O trabalho nao e' perfeitamente divisivel: se uma equipe pega um bloco mais pesado,
    # e' ela quem define o prazo - as outras esperam (e sao faturadas do mesmo jeito).
    _config_redonda(monkeypatch)
    numeros, _ = custo_amostra(_odis_teste(), uf="PA", tipo_contrato="LPT", n_equipes=2)
    # As horas criticas sao as de UMA equipe, nunca a soma das duas.
    assert numeros["horas_equipe_critica"] <= numeros["horas_roteiro"] + numeros["horas_inspecao"]
    assert numeros["dias_trabalho"] == math.ceil(
        numeros["horas_equipe_critica"] / (8.0 * config.TAMANHO_EQUIPE))


def test_detalhe_diz_de_qual_equipe_e_cada_obra(monkeypatch):
    # Com equipes independentes, saber QUEM pega o que e' parte do resultado.
    _config_redonda(monkeypatch)
    _, detalhe = custo_amostra(_odis_teste(), uf="PA", tipo_contrato="LPT", n_equipes=2)
    # Nenhuma obra sem dono, nenhuma obra em duas equipes.
    assert len(detalhe) == 3
    assert sorted(detalhe["ODI"]) == ["A", "B", "C"]
    assert set(detalhe["equipe"]) == {1, 2}


def test_grade_varre_equipes_e_prazos(monkeypatch):
    # A aba Cenarios e' uma GRADE: para cada numero de equipes, todos os prazos viaveis
    # ate o teto. O prazo e' a entrada; a viabilidade e' quem filtra.
    _config_redonda(monkeypatch)
    monkeypatch.setattr(config, "N_EQUIPES_MAX", 3)
    monkeypatch.setattr(config, "MAX_DIAS_POR_EQUIPE", 6)
    linhas = grade_cenarios(_odis_teste(), uf="PA", tipo_contrato="LPT")
    assert linhas
    # Nenhuma linha fora dos limites declarados.
    assert all(1 <= c["n_equipes"] <= 3 for c in linhas)
    assert all(1 <= c["dias_trabalho"] <= 6 for c in linhas)
    # Ordenada por equipes e, dentro de cada bloco, por prazo crescente.
    chaves = [(c["n_equipes"], c["dias_trabalho"]) for c in linhas]
    assert chaves == sorted(chaves)
    # Dentro de um mesmo numero de equipes, mais dias = mais caro (folga custa).
    for n in {c["n_equipes"] for c in linhas}:
        custos = [c["custo_total"] for c in linhas if c["n_equipes"] == n]
        assert custos == sorted(custos)
    # Cada linha fecha com a mesma formula do motor.
    for c in linhas:
        assert c["custo_campo"] == pytest.approx(
            c["n_equipes"] * config.TAMANHO_EQUIPE * c["dias_faturados"] * 8.0 * 100.0)
        assert c["custo_total"] == pytest.approx(c["custo_campo"] + c["custo_fixo"])


def test_grade_marca_a_linha_que_e_o_numero_oficial(monkeypatch):
    # A grade e o Resumo tem de falar do mesmo caso: a linha 'calculado' e' o padrao de
    # equipes no seu prazo minimo, e o custo dela bate com o da aba Resumo.
    _config_redonda(monkeypatch)
    monkeypatch.setattr(config, "N_EQUIPES_PADRAO", 2)
    numeros, _ = custo_amostra(_odis_teste(), uf="PA", tipo_contrato="LPT")
    linhas = grade_cenarios(_odis_teste(), uf="PA", tipo_contrato="LPT")
    marcadas = [c for c in linhas if c["cenario"] == "calculado"]
    assert len(marcadas) == 1
    assert marcadas[0]["n_equipes"] == numeros["n_equipes"]
    assert marcadas[0]["dias_trabalho"] == numeros["dias_trabalho"]
    assert marcadas[0]["custo_total"] == pytest.approx(numeros["custo_total"])


def test_grade_descarta_o_que_nao_cabe_no_teto_de_dias(monkeypatch):
    # O caso do humano: 80 UCs de MLA a 3 UCs/dia sao 80 x 8/3 = 213h de inspecao, ou
    # ~27 dias para UMA equipe - flagrantemente acima do teto de 20. Essa combinacao nao
    # e' apresentada, e nem sequer e' calculada (ver o teste seguinte).
    _config_redonda(monkeypatch)
    monkeypatch.setattr(config, "UCS_POR_DIA", {"LPT": 30.0, "MLA": 3.0})
    monkeypatch.setattr(config, "N_EQUIPES_MAX", 7)
    monkeypatch.setattr(config, "MAX_DIAS_POR_EQUIPE", 20)
    # 8 obras vizinhas de 10 UCs cada = 80 UCs, com deslocamento pequeno.
    oitenta = pd.DataFrame({
        "ODI": [f"O{i}" for i in range(8)],
        "Estrato": [1] * 8,
        "Municipio": [f"M{i}" for i in range(8)],
        "n_ucs": [10] * 8,
        "lat_centro": [-1.50 - 0.02 * i for i in range(8)],
        "lon_centro": [-48.55 - 0.02 * i for i in range(8)],
        "dist_interna_km": [1.0] * 8,
    })
    linhas = grade_cenarios(oitenta, uf="PA", tipo_contrato="MLA")
    # Uma equipe nao cabe; a grade comeca em duas ou mais.
    assert 1 not in {c["n_equipes"] for c in linhas}
    assert min(c["n_equipes"] for c in linhas) >= 2
    # E nenhuma linha viola o teto.
    assert all(c["dias_trabalho"] <= 20 for c in linhas)


def test_grade_nem_roteia_a_combinacao_inviavel(monkeypatch):
    # "Sequer calcule": quando nem as horas de INSPECAO cabem no teto, o numero de equipes
    # e' descartado antes de rotear - rotear e' a parte cara. O contador prova que
    # dividir_roteiro nao chega a ser chamado para 1 equipe.
    _config_redonda(monkeypatch)
    monkeypatch.setattr(config, "UCS_POR_DIA", {"LPT": 30.0, "MLA": 3.0})
    monkeypatch.setattr(config, "N_EQUIPES_MAX", 3)
    monkeypatch.setattr(config, "MAX_DIAS_POR_EQUIPE", 20)
    chamadas = []
    original = modulo_custo.dividir_roteiro

    def espiao(df, lat, lon, n_equipes):
        chamadas.append(n_equipes)
        return original(df, lat, lon, n_equipes)

    monkeypatch.setattr(modulo_custo, "dividir_roteiro", espiao)
    oitenta = pd.DataFrame({
        "ODI": [f"O{i}" for i in range(8)],
        "Estrato": [1] * 8,
        "Municipio": [f"M{i}" for i in range(8)],
        "n_ucs": [10] * 8,
        "lat_centro": [-1.50 - 0.02 * i for i in range(8)],
        "lon_centro": [-48.55 - 0.02 * i for i in range(8)],
        "dist_interna_km": [1.0] * 8,
    })
    grade_cenarios(oitenta, uf="PA", tipo_contrato="MLA")
    # 213h de inspecao / (1 equipe x 8h) = 26,7 dias > 20: nem roteou.
    assert 1 not in chamadas
    # As viaveis, sim.
    assert 2 in chamadas


def test_grade_de_amostra_vazia(monkeypatch):
    # Amostra sem obra nenhuma nao tem grade - lista vazia, nao divisao por zero.
    _config_redonda(monkeypatch)
    vazio = _odis_teste().iloc[0:0]
    assert grade_cenarios(vazio, uf="PA", tipo_contrato="LPT") == []


def test_grade_nao_propoe_mais_equipes_que_obras(monkeypatch):
    # 3 obras nao ocupam 7 equipes: alguma ficaria sem servico e seria faturada a toa.
    _config_redonda(monkeypatch)
    monkeypatch.setattr(config, "N_EQUIPES_MAX", 7)
    linhas = grade_cenarios(_odis_teste(), uf="PA", tipo_contrato="LPT")
    assert max(c["n_equipes"] for c in linhas) <= 3


def test_reproduz_a_formula_do_benchmark_da_engenharia(monkeypatch):
    # A engenharia da PB 7a Tranche estimou 3 amostras e as tres obedecem, ao centavo, a
    #     custo = 12.960 + 9.600 x (dias + 1),  com 9.600 = 2 pessoas x 8h x R$600.
    # Aquela e' UMA DUPLA em UM roteiro: TAMANHO_EQUIPE = 2 com N_EQUIPES = 1 - nao duas
    # equipes independentes, que rodariam dois roteiros e custariam mais.
    monkeypatch.setattr(config, "TAMANHO_EQUIPE", 2.0)
    numeros, _ = custo_amostra(_odis_teste(), uf="PB", tipo_contrato="LPT", n_equipes=1)
    esperado = 12960 + 9600 * (numeros["dias_trabalho"] + 1)
    assert numeros["custo_total"] == pytest.approx(esperado, abs=0.01)


def test_tarifa_campo_inclui_diaria(monkeypatch):
    _config_redonda(monkeypatch)
    # CUSTO_DIARIA = 80 por dia de campo -> 80/8h = +10/h sobre a tarifa 100.
    monkeypatch.setattr(config, "CUSTO_DIARIA", 80.0)
    assert tarifa_campo() == pytest.approx(110.0)
