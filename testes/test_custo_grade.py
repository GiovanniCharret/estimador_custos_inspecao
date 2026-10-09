# -*- coding: utf-8 -*-
"""Testes da grade do coordenador (F21): o custo aberto equipe por equipe.

O caso mais importante e o primeiro: a grade 'como o automatico' tem de dar exatamente o
custo_total de custo_amostra. E a garantia de que a grade e uma generalizacao da formula
oficial, e nao uma segunda formula que um dia diverge.
"""
import pytest

from src import config
from src.custo import PERFIS_DA_GRADE, custo_amostra, custo_grade, tarifa_campo
from testes.test_custo import _odis_teste


@pytest.mark.parametrize("tipo", ["LPT", "MLA"])
@pytest.mark.parametrize("n_equipes", [1, 2, 3])
def test_a_grade_como_o_automatico_da_o_custo_oficial(tipo, n_equipes):
    """N equipes de TAMANHO_EQUIPE engenheiros, com os dias de trabalho do calculo oficial."""
    numeros, _roteiro = custo_amostra(_odis_teste(), uf="PA", tipo_contrato=tipo,
                                      n_equipes=n_equipes)
    grade = [{"dias": numeros["dias_trabalho"], "engenheiro": int(config.TAMANHO_EQUIPE),
              "tecnico": 0}] * numeros["n_equipes"]
    assert custo_grade(grade, tipo)["total"] == pytest.approx(numeros["custo_total"])


def test_cada_perfil_cobra_a_propria_tarifa_e_o_tecnico_muda_com_o_tipo():
    """LPT: eletrotecnico a 593/h; MLA: tecnico a 513,22/h. O engenheiro custa 600 nos dois."""
    equipe = [{"dias": 1, "engenheiro": 0, "tecnico": 1}]
    dias_faturados = 1 + config.DIAS_MOBILIZACAO
    for tipo in ("LPT", "MLA"):
        esperado = tarifa_campo(tipo, "TECNICO") * dias_faturados * config.HORAS_DIA_CAMPO
        assert custo_grade(equipe, tipo)["campo"] == pytest.approx(esperado)
    assert tarifa_campo("LPT", "TECNICO") != tarifa_campo("MLA", "TECNICO")
    assert tarifa_campo("LPT", "ENGENHEIRO") == tarifa_campo("MLA", "ENGENHEIRO")


def test_a_mobilizacao_entra_uma_vez_por_equipe_que_vai_a_campo():
    """Os dias digitados sao de TRABALHO; o +1 de mobilizacao e somado aqui."""
    r = custo_grade([{"dias": 8, "engenheiro": 1, "tecnico": 0},
                     {"dias": 5, "engenheiro": 1, "tecnico": 1}], "LPT")
    assert [e["dias_faturados"] for e in r["por_equipe"]] == [
        8 + config.DIAS_MOBILIZACAO, 5 + config.DIAS_MOBILIZACAO]


def test_equipe_sem_dias_ou_sem_gente_nao_fatura_nem_a_mobilizacao():
    """Quem nao vai a campo nao sai da capital."""
    r = custo_grade([{"dias": 0, "engenheiro": 2, "tecnico": 0},
                     {"dias": 6, "engenheiro": 0, "tecnico": 0}], "LPT")
    assert [e["custo"] for e in r["por_equipe"]] == [0, 0]
    assert [e["dias_faturados"] for e in r["por_equipe"]] == [0, 0]


def test_o_escritorio_entra_uma_vez_mesmo_com_a_grade_vazia():
    """E e o do TIPO: 36 h em LPT, 24 h em MLA (F16)."""
    for tipo in ("LPT", "MLA"):
        r = custo_grade([], tipo)
        assert r["campo"] == 0
        horas = sum(config.HORAS_ESCRITORIO_POR_TIPO[tipo].values())
        tarifa = config.TARIFAS_HORA[tipo][config.PERFIL_EQUIPE]["escritorio"]
        assert r["escritorio"] == pytest.approx(horas * tarifa) == pytest.approx(r["total"])


def test_exemplo_conferivel_a_mao():
    """O exemplo que o sistema web mostra no schema da grade (LPT):

    equipe 1: 1 eng x 600 x (8+1) x 8 = 43.200
    equipe 2: (1 eng x 600 + 1 tec x 593) x (5+1) x 8 = 57.264
    escritorio: 36 h x 360 = 12.960 -> total 113.424
    """
    r = custo_grade([{"dias": 8, "engenheiro": 1, "tecnico": 0},
                     {"dias": 5, "engenheiro": 1, "tecnico": 1}], "LPT")
    assert [e["custo"] for e in r["por_equipe"]] == [43200.0, 57264.0]
    assert (r["campo"], r["escritorio"], r["total"]) == (100464.0, 12960.0, 113424.0)


def test_tarifa_campo_sem_perfil_continua_igual():
    """Regressao: a assinatura nova nao muda nenhuma chamada antiga."""
    for tipo in ("LPT", "MLA"):
        assert tarifa_campo(tipo) == tarifa_campo(tipo, config.PERFIL_EQUIPE)


def test_os_perfis_da_grade_existem_nas_tarifas_dos_dois_tipos():
    """Se alguem tirar um perfil de TARIFAS_HORA, a grade quebra aqui, e nao numa tela."""
    for tipo in ("LPT", "MLA"):
        for perfil in PERFIS_DA_GRADE.values():
            assert "campo" in config.TARIFAS_HORA[tipo][perfil]
