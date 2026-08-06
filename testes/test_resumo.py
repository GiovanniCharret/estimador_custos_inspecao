# -*- coding: utf-8 -*-
"""Testes da gravacao da tabela-resumo."""
import pandas as pd
import pytest
from src.custo import custo_por_odi
from src.resumo import gravar_resumo
from src.io_amostras import EntradaInvalida
from testes.test_custo import _odis_teste

def _custos():
    # Custos de campo calculados com a config real (valores nao importam aqui;
    # o teste confere ESTRUTURA da planilha, nao numeros).
    return custo_por_odi(_odis_teste(), uf="PA", tipo_contrato="LPT")

def test_gravar_resumo_estrutura(tmp_path):
    custos = {1: _custos(), 2: _custos()}
    destino = tmp_path / "Resumo_Custos.xlsx"
    gravar_resumo(custos, destino)
    xls = pd.ExcelFile(destino)
    # Abas esperadas: Leia-me + (resumo, detalhe) por amostra.
    assert xls.sheet_names == ["Leia-me", "Amostra 1", "Detalhe 1", "Amostra 2", "Detalhe 2"]
    # A aba de resumo tem a linha TOTAL e as colunas novas do modelo do gate.
    aba = xls.parse("Amostra 1")
    assert (aba["Estrato"].astype(str) == "TOTAL").any()
    assert "Equipe-dias" in aba.columns and "Custo fixo OS (R$)" in aba.columns

def test_gravar_resumo_arquivo_aberto(tmp_path):
    # Simula 'planilha aberta no Excel': arquivo destino travado para escrita.
    # No Windows, open(destino, "w") nao impede pd.ExcelWriter de regravar (compartilhamento CRT).
    # Adaptacao legitima: criar um DIRETORIO com o nome do arquivo, que gera PermissionError.
    destino = tmp_path / "Resumo_Custos.xlsx"
    destino.mkdir()  # Cria diretorio com o nome do arquivo destino
    custos = {1: _custos()}
    with pytest.raises(EntradaInvalida, match="[Ff]eche"):
        gravar_resumo(custos, destino)
