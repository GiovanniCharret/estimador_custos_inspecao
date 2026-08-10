# -*- coding: utf-8 -*-
"""Testes da gravacao da tabela-resumo (planilha unica com todas as estratificacoes)."""
import pandas as pd
import pytest

from src.custo import custo_amostra
from src.io_amostras import EntradaInvalida
from src.resumo import gravar_resumo
from testes.test_custo import _odis_teste


def _resultado(n_estratos, amostra):
    """Monta um item da lista que gravar_resumo espera (numeros + roteiro de uma amostra)."""
    numeros, roteiro = custo_amostra(_odis_teste(), uf="PA", tipo_contrato="LPT")
    return {"n_estratos": n_estratos, "amostra": amostra, "roteiro": roteiro, **numeros}


def test_gravar_resumo_estrutura(tmp_path):
    # Duas estratificacoes x duas amostras: tudo cabe numa planilha so (decisao da F9).
    resultados = [_resultado(3, 1), _resultado(3, 2), _resultado(4, 1), _resultado(4, 2)]
    destino = tmp_path / "Resumo_Custos.xlsx"
    gravar_resumo(resultados, destino)
    xls = pd.ExcelFile(destino)
    # Tres abas fixas, independentemente de quantas estratificacoes existirem.
    assert xls.sheet_names == ["Leia-me", "Resumo", "Detalhe"]
    resumo = xls.parse("Resumo")
    # Uma linha por (estratificacao, amostra) - sem abertura por estrato.
    assert len(resumo) == 4
    assert "Estrato" not in resumo.columns
    assert {"Estratos", "Amostra", "Dias faturados", "Custo total (R$)"} <= set(resumo.columns)
    # As estratificacoes saem ordenadas, para comparacao lado a lado.
    assert list(resumo["Estratos"]) == [3, 3, 4, 4]
    assert list(resumo["Amostra"]) == [1, 2, 1, 2]


def test_gravar_resumo_detalhe_traz_a_ordem_do_roteiro(tmp_path):
    # O detalhe existe para o humano conferir POR ONDE a equipe passa, na ordem.
    destino = tmp_path / "Resumo_Custos.xlsx"
    gravar_resumo([_resultado(3, 1)], destino)
    detalhe = pd.read_excel(destino, sheet_name="Detalhe")
    # Uma linha por obra, numerada de 1 a N na ordem de visita.
    assert list(detalhe["Ordem"]) == [1, 2, 3]
    # Sabe de qual estratificacao/amostra cada linha veio.
    assert set(detalhe["Estratos"]) == {3} and set(detalhe["Amostra"]) == {1}
    # O estrato sobrevive como coluna informativa (nao entra no custo, mas identifica a obra).
    assert "Estrato" in detalhe.columns


def test_gravar_resumo_leia_me_traz_os_parametros_usados(tmp_path):
    # O Leia-me e' gerado de config: quem abre a planilha ve com que numeros ela foi feita.
    destino = tmp_path / "Resumo_Custos.xlsx"
    gravar_resumo([_resultado(3, 1)], destino)
    texto = "\n".join(pd.read_excel(destino, sheet_name="Leia-me")["Leia-me"].fillna("").map(str))
    assert "Dias de mobilizacao" in texto and "Perfil da equipe" in texto
    # Explica o invariante que mais confunde: uma viagem so, e custo por amostra.
    assert "UMA viagem" in texto


def test_gravar_resumo_arquivo_aberto(tmp_path):
    # Simula 'planilha aberta no Excel': arquivo destino travado para escrita.
    # No Windows, open(destino, "w") nao impede pd.ExcelWriter de regravar (compartilhamento CRT).
    # Adaptacao legitima: criar um DIRETORIO com o nome do arquivo, que gera PermissionError.
    destino = tmp_path / "Resumo_Custos.xlsx"
    destino.mkdir()
    with pytest.raises(EntradaInvalida, match="[Ff]eche"):
        gravar_resumo([_resultado(3, 1)], destino)
