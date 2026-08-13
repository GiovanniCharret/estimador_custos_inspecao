# -*- coding: utf-8 -*-
"""Testes da gravacao da tabela-resumo (planilha unica com todas as estratificacoes)."""
import pandas as pd
import pytest

from src.custo import custo_amostra, grade_cenarios
from src.io_amostras import EntradaInvalida
from src.resumo import gravar_resumo
from testes.test_custo import _odis_teste


def _resultado(n_estratos, amostra=1):
    """Monta um item da lista que gravar_resumo espera (numeros + detalhe + cenarios)."""
    numeros, roteiro = custo_amostra(_odis_teste(), uf="PA", tipo_contrato="LPT")
    return {"n_estratos": n_estratos, "amostra": amostra, "roteiro": roteiro,
            "cenarios": grade_cenarios(_odis_teste(), uf="PA", tipo_contrato="LPT"),
            **numeros}


def test_gravar_resumo_estrutura(tmp_path):
    # Varias estratificacoes da MESMA amostra cabem numa planilha so (decisao da F9).
    resultados = [_resultado(3), _resultado(4), _resultado(5)]
    destino = tmp_path / "Resumo_Custos.xlsx"
    gravar_resumo(resultados, destino)
    xls = pd.ExcelFile(destino)
    # Quatro abas fixas, independentemente de quantas estratificacoes existirem.
    assert xls.sheet_names == ["Leia-me", "Resumo", "Cenarios", "Detalhe"]
    resumo = xls.parse("Resumo")
    # Uma linha por estratificacao - sem abertura por estrato e sem as amostras reserva.
    assert len(resumo) == 3
    assert "Estrato" not in resumo.columns
    assert {"Estratos", "Amostra", "Dias faturados (por equipe)",
            "Custo total (R$)"} <= set(resumo.columns)
    # As duas grandezas parecidas convivem, e sao diferentes (armadilha fechada na F15).
    assert {"Equipes", "Pessoas por equipe"} <= set(resumo.columns)
    # As estratificacoes saem ordenadas, para comparacao lado a lado.
    assert list(resumo["Estratos"]) == [3, 4, 5]
    assert set(resumo["Amostra"]) == {1}


def test_gravar_resumo_cenarios(tmp_path):
    # A aba Cenarios traz a grade (equipes x prazo) de CADA estratificacao.
    destino = tmp_path / "Resumo_Custos.xlsx"
    gravar_resumo([_resultado(3), _resultado(4)], destino)
    cenarios = pd.read_excel(destino, sheet_name="Cenarios")
    esperado = grade_cenarios(_odis_teste(), uf="PA", tipo_contrato="LPT")
    assert len(cenarios) == 2 * len(esperado)
    assert set(cenarios["Estratos"]) == {3, 4}
    # Exatamente um cenario 'calculado' por estratificacao - e' o que casa com o Resumo.
    assert (cenarios["Cenario"] == "calculado").sum() == 2
    assert {"Equipes", "Ocupacao da equipe", "Roteiro somado (km estrada)",
            "Custo total (R$)"} <= set(cenarios.columns)
    resumo = pd.read_excel(destino, sheet_name="Resumo")
    base = cenarios[(cenarios["Cenario"] == "calculado") & (cenarios["Estratos"] == 3)].iloc[0]
    oficial = resumo[resumo["Estratos"] == 3].iloc[0]
    assert base["Custo total (R$)"] == pytest.approx(oficial["Custo total (R$)"])
    # E a grade fala do MESMO numero de equipes que o Resumo naquela linha.
    assert base["Equipes"] == oficial["Equipes"]


def test_gravar_resumo_detalhe_traz_equipe_e_ordem(tmp_path):
    # O detalhe existe para o humano conferir QUEM pega cada obra e em que ordem.
    destino = tmp_path / "Resumo_Custos.xlsx"
    gravar_resumo([_resultado(3, 1)], destino)
    detalhe = pd.read_excel(destino, sheet_name="Detalhe")
    # Uma linha por obra; a ordem reinicia dentro de cada equipe (cada uma tem seu roteiro).
    assert len(detalhe) == 3
    assert "Equipe" in detalhe.columns
    for _, obras in detalhe.groupby("Equipe"):
        assert list(obras["Ordem"]) == list(range(1, len(obras) + 1))
    # Sabe de qual estratificacao/amostra cada linha veio.
    assert set(detalhe["Estratos"]) == {3} and set(detalhe["Amostra"]) == {1}
    # O estrato sobrevive como coluna informativa (nao entra no custo, mas identifica a obra).
    assert "Estrato" in detalhe.columns


def test_gravar_resumo_leia_me_traz_os_parametros_usados(tmp_path):
    # O Leia-me e' gerado de config: quem abre a planilha ve com que numeros ela foi feita.
    destino = tmp_path / "Resumo_Custos.xlsx"
    gravar_resumo([_resultado(3, 1)], destino)
    texto = "\n".join(pd.read_excel(destino, sheet_name="Leia-me")["Leia-me"].fillna("").map(str))
    assert "Dias de mobilizacao" in texto and "Pessoas por equipe" in texto
    # Explica os dois invariantes que mais confundem: as duas colunas parecidas...
    assert "'Equipes'" in texto and "'Pessoas por equipe'" in texto
    # ...e que dividir CUSTA quilometragem, em vez de economizar.
    assert "CRESCE ao dividir" in texto


def test_gravar_resumo_arquivo_aberto(tmp_path):
    # Simula 'planilha aberta no Excel': arquivo destino travado para escrita.
    # No Windows, open(destino, "w") nao impede pd.ExcelWriter de regravar (compartilhamento CRT).
    # Adaptacao legitima: criar um DIRETORIO com o nome do arquivo, que gera PermissionError.
    destino = tmp_path / "Resumo_Custos.xlsx"
    destino.mkdir()
    with pytest.raises(EntradaInvalida, match="[Ff]eche"):
        gravar_resumo([_resultado(3, 1)], destino)
