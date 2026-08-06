# -*- coding: utf-8 -*-
"""Testes de localizacao dos arquivos de entrada."""
from pathlib import Path
import pytest
from src.io_amostras import achar_entradas, EntradaInvalida

def _cria(pasta, *nomes):
    # Cria arquivos vazios com os nomes dados dentro de pasta.
    for n in nomes:
        (pasta / n).write_bytes(b"")

def test_acha_lote_e_painel(tmp_path):
    # Caso feliz: um Lote.xlsx e um arquivo contendo "Painel de Monitoramento".
    _cria(tmp_path, "Lote.xlsx", "2026 Painel de Monitoramento PA.xlsx")
    lote, painel = achar_entradas(tmp_path)
    assert lote.name == "Lote.xlsx"
    assert "Painel de Monitoramento" in painel.name

def test_erro_sem_lote(tmp_path):
    # Sem Lote.xlsx: erro dizendo o que colocar na pasta.
    _cria(tmp_path, "Painel de Monitoramento.xlsx")
    with pytest.raises(EntradaInvalida, match="Lote.xlsx"):
        achar_entradas(tmp_path)

def test_erro_sem_painel(tmp_path):
    _cria(tmp_path, "Lote.xlsx")
    with pytest.raises(EntradaInvalida, match="Painel de Monitoramento"):
        achar_entradas(tmp_path)

def test_erro_dois_paineis(tmp_path):
    # Dois arquivos casando o padrao: aborta listando ambos.
    _cria(tmp_path, "Lote.xlsx", "Painel de Monitoramento A.xlsx", "Painel de Monitoramento B.xlsx")
    with pytest.raises(EntradaInvalida, match="A.xlsx"):
        achar_entradas(tmp_path)
