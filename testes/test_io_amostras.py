# -*- coding: utf-8 -*-
"""Testes de localizacao dos arquivos de entrada e leitura/juncao de amostras e painel."""
from pathlib import Path
import pandas as pd
import pytest
from src.io_amostras import (achar_entradas, ler_amostras, ler_painel, juntar_amostras_painel,
                             EntradaInvalida, _norm_odi)
from testes.fixtures import (escrever_lote, escrever_painel, escrever_painel_anexo_v,
                             ODIS, ODIS_LOTE_TEXTO, ODIS_PAINEL_NUMERO)

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


def test_ler_amostras_filtra_selecionado(tmp_path):
    escrever_lote(tmp_path / "Lote.xlsx", abas=(1, 2))
    amostras = ler_amostras(tmp_path / "Lote.xlsx")
    assert set(amostras) == {1, 2}                       # uma entrada por aba existente
    assert len(amostras[1]) == 5                         # linha nao-selecionada filtrada
    assert list(amostras[1].columns) == ["ODI", "Estrato", "Municipio", "Cons"]
    assert (amostras[1]["Cons"] > 0).all()                # fixture usa Cons > 0 para ODIs normais

def test_ler_amostras_sem_coluna_cons_usa_zero(tmp_path):
    # Lote sem coluna 'Cons.': o leitor preenche Cons=0 (obra sem informacao de UC).
    df = pd.DataFrame({
        "ODI": ODIS,
        "Estrato": [1, 1, 2, 2, 3],
        "Município": ["BARCARENA"] * 5,
        "STATUS": ["Selecionado"] * 5,
    })
    df.to_excel(tmp_path / "Lote.xlsx", sheet_name="Amostra 1", index=False)
    amostras = ler_amostras(tmp_path / "Lote.xlsx")
    assert (amostras[1]["Cons"] == 0).all()

def test_ler_amostras_sem_aba_amostra(tmp_path):
    # Lote sem nenhuma aba 'Amostra K': erro claro.
    pd.DataFrame({"x": [1]}).to_excel(tmp_path / "Lote.xlsx", sheet_name="Outra", index=False)
    with pytest.raises(EntradaInvalida, match="Amostra"):
        ler_amostras(tmp_path / "Lote.xlsx")

def test_ler_painel_detecta_aba_e_descarta_invalidas(tmp_path):
    escrever_painel(tmp_path / "Painel de Monitoramento.xlsx")
    ucs = ler_painel(tmp_path / "Painel de Monitoramento.xlsx")
    assert {"ODI", "UC", "LATITUDE", "LONGITUDE"} <= set(ucs.columns)
    assert len(ucs) == 10                                # 5 ODIs x 2 UCs

def test_ler_painel_reporta_coordenada_fora_do_brasil(tmp_path):
    escrever_painel(tmp_path / "Painel de Monitoramento.xlsx")
    # Corrompe uma UC com longitude positiva (fora da bbox do Brasil).
    df = pd.read_excel(tmp_path / "Painel de Monitoramento.xlsx", sheet_name="Base_UC")
    df.loc[0, "LONGITUDE"] = 48.65
    with pd.ExcelWriter(tmp_path / "Painel de Monitoramento.xlsx") as xls:
        df.to_excel(xls, sheet_name="Base_UC", index=False)
    ucs = ler_painel(tmp_path / "Painel de Monitoramento.xlsx")
    assert len(ucs) == 9                                 # UC invalida removida (com aviso impresso)

def test_juntar_erro_odi_orfao(tmp_path):
    # Orfaos com Cons > 0 (obra com UC esperada): aborta listando os ODIs sem coordenada.
    escrever_lote(tmp_path / "Lote.xlsx", abas=(1,))
    escrever_painel(tmp_path / "Painel.xlsx", odis=ODIS[:3])    # faltam PA004/PA005
    amostras = ler_amostras(tmp_path / "Lote.xlsx")
    ucs = ler_painel(tmp_path / "Painel.xlsx")
    with pytest.raises(EntradaInvalida, match="PA004"):
        juntar_amostras_painel(amostras, ucs)

def test_juntar_erro_intersecao_zero(tmp_path):
    escrever_lote(tmp_path / "Lote.xlsx", abas=(1,))
    escrever_painel(tmp_path / "Painel.xlsx", odis=["TO900", "TO901", "TO902", "TO903", "TO904"])
    amostras = ler_amostras(tmp_path / "Lote.xlsx")
    ucs = ler_painel(tmp_path / "Painel.xlsx")
    with pytest.raises(EntradaInvalida, match="tranche"):
        juntar_amostras_painel(amostras, ucs)

def test_juntar_orfao_cons_zero_usa_centroide_municipio(tmp_path):
    # ODI extra "PA006": obra sem UC (ex. reforco de rede), Cons=0, mesmo municipio do painel.
    odis_lote = ODIS + ["PA006"]
    escrever_lote(tmp_path / "Lote.xlsx", abas=(1,), odis=odis_lote, cons={"PA006": 0})
    escrever_painel(tmp_path / "Painel.xlsx")                   # so tem ODIS, todos em BARCARENA
    amostras = ler_amostras(tmp_path / "Lote.xlsx")
    ucs = ler_painel(tmp_path / "Painel.xlsx")
    juntas = juntar_amostras_painel(amostras, ucs)
    linha = juntas[1][juntas[1]["ODI"] == "PA006"]
    assert len(linha) == 1                                       # pseudo-UC unica -> n_ucs = 1
    assert linha.iloc[0]["UC"] == "PA006-BARCARENA"
    # Centroide esperado = media de lat/long de TODAS as UCs de BARCARENA no painel.
    assert linha.iloc[0]["LATITUDE"] == pytest.approx(ucs["LATITUDE"].mean())
    assert linha.iloc[0]["LONGITUDE"] == pytest.approx(ucs["LONGITUDE"].mean())

def test_juntar_orfao_cons_zero_sem_uc_no_municipio_erro(tmp_path):
    # ODI extra em municipio sem NENHUMA UC no painel: mesmo com Cons=0, nao ha centroide possivel.
    odis_lote = ODIS + ["TO900"]
    escrever_lote(tmp_path / "Lote.xlsx", abas=(1,), odis=odis_lote,
                  municipios={"TO900": "PALMAS"}, cons={"TO900": 0})
    escrever_painel(tmp_path / "Painel.xlsx")                   # so tem municipio BARCARENA
    amostras = ler_amostras(tmp_path / "Lote.xlsx")
    ucs = ler_painel(tmp_path / "Painel.xlsx")
    with pytest.raises(EntradaInvalida, match="PALMAS"):
        juntar_amostras_painel(amostras, ucs)

def test_achar_entradas_avisa_lote_alternativo_ignorado(tmp_path, capsys):
    # O sistema amostral upstream gera um arquivo por numero de estratos; se sobrar algum
    # na Entrada/, o programa le SO o Lote.xlsx - e precisa dizer isso em voz alta.
    escrever_lote(tmp_path / "Lote.xlsx", abas=(1,))
    escrever_lote(tmp_path / "Estratos 5 - Python.xlsx", abas=(1,))
    escrever_painel(tmp_path / "Painel de Monitoramento T.xlsx")
    achar_entradas(tmp_path)
    saida = capsys.readouterr().out
    assert "Estratos 5 - Python.xlsx" in saida and "IGNORADO" in saida
    # O Painel nao tem aba 'Amostra K': nao pode ser confundido com um lote alternativo.
    assert "Painel de Monitoramento T.xlsx" not in saida


def test_ler_painel_anexo_v_cabecalho_na_segunda_linha(tmp_path):
    # Formato real: faixa mesclada na linha 1, cabecalho na 2, colunas por extenso.
    escrever_painel_anexo_v(tmp_path / "Painel de Monitoramento.xlsx")
    ucs = ler_painel(tmp_path / "Painel de Monitoramento.xlsx")
    assert {"ODI", "UC", "Municipio", "LATITUDE", "LONGITUDE"} <= set(ucs.columns)
    assert len(ucs) == 10                                # 5 ODIs x 2 UCs
    # 'Numero ODI' virou ODI, ja normalizada (sem zeros a esquerda, como texto).
    assert set(ucs["ODI"]) == {str(o) for o in ODIS_PAINEL_NUMERO}


def test_ler_painel_sem_coluna_de_odi_lista_cabecalhos_aceitos(tmp_path):
    # Painel so com lat/long: o erro precisa dizer quais nomes de coluna servem para a ODI.
    pd.DataFrame({"Latitude": [-1.6], "Longitude": [-48.6]}).to_excel(
        tmp_path / "Painel.xlsx", sheet_name="Preenchimento", index=False)
    with pytest.raises(EntradaInvalida, match="numero odi"):
        ler_painel(tmp_path / "Painel.xlsx")


def test_norm_odi_iguala_texto_com_zeros_e_numero():
    # As tres grafias que a MESMA ODI assume entre Lote (texto), Painel (int) e pandas (float).
    assert _norm_odi("0012500186") == _norm_odi(12500186) == _norm_odi(12500186.0) == "12500186"
    # ID nao numerico e' preservado: nele o zero a esquerda pode ser significativo.
    assert _norm_odi("PA001") == "PA001"
    # Caso degenerado: so zeros nao pode virar string vazia.
    assert _norm_odi("000") == "0"


def test_juntar_casa_odi_texto_do_lote_com_odi_numerica_do_painel(tmp_path):
    # Sem a normalizacao, '0012500186' != 12500186 e a intersecao daria ZERO - o programa
    # acusaria "tranche errada", que e' um erro falso e desnorteante.
    escrever_lote(tmp_path / "Lote.xlsx", abas=(1,), odis=ODIS_LOTE_TEXTO)
    escrever_painel_anexo_v(tmp_path / "Painel.xlsx")
    amostras = ler_amostras(tmp_path / "Lote.xlsx")
    ucs = ler_painel(tmp_path / "Painel.xlsx")
    juntas = juntar_amostras_painel(amostras, ucs)
    assert juntas[1]["ODI"].nunique() == len(ODIS_LOTE_TEXTO)     # todas casaram
    assert len(juntas[1]) == len(ODIS_LOTE_TEXTO) * 2             # 2 UCs por ODI


def test_juntar_orfao_cons_zero_municipio_com_acento(tmp_path):
    # Lote grava 'GURINHEM' (sem acento) e o Painel 'GURINHÉM' (com): a comparacao passa
    # por _norm, senao o fallback do orfao acusaria falsamente "municipio sem UC no Painel".
    odis_lote = ODIS_LOTE_TEXTO + ["0012599999"]
    escrever_lote(tmp_path / "Lote.xlsx", abas=(1,), odis=odis_lote,
                  municipios={odi: "GURINHEM" for odi in odis_lote}, cons={"0012599999": 0})
    escrever_painel_anexo_v(tmp_path / "Painel.xlsx", municipio="GURINHÉM")
    amostras = ler_amostras(tmp_path / "Lote.xlsx")
    ucs = ler_painel(tmp_path / "Painel.xlsx")
    juntas = juntar_amostras_painel(amostras, ucs)
    linha = juntas[1][juntas[1]["ODI"] == "12599999"]
    assert len(linha) == 1                                        # pseudo-UC criada
    assert linha.iloc[0]["LATITUDE"] == pytest.approx(ucs["LATITUDE"].mean())


def test_juntar_orfao_misto_cons_maior_zero_aborta_sem_aviso_de_fallback(tmp_path, capsys):
    # Amostra com DOIS tipos de orfao ao mesmo tempo: PA003 (Cons>0, sem UC no Painel -> erro)
    # e PA006 (Cons=0, obra sem UC, municipio BARCARENA TEM UC no Painel -> fallback valido).
    # Regra: o erro do Cons>0 deve abortar a amostra inteira SEM que o aviso de pseudo-UC do
    # PA006 seja impresso antes (nada de progresso parcial anunciado num fluxo que aborta).
    odis_lote = ODIS[:3] + ["PA006"]
    escrever_lote(tmp_path / "Lote.xlsx", abas=(1,), odis=odis_lote, cons={"PA006": 0})
    escrever_painel(tmp_path / "Painel.xlsx", odis=ODIS[:2])    # falta PA003 (Cons>0) no Painel
    amostras = ler_amostras(tmp_path / "Lote.xlsx")
    ucs = ler_painel(tmp_path / "Painel.xlsx")
    with pytest.raises(EntradaInvalida, match="PA003"):
        juntar_amostras_painel(amostras, ucs)
    # Nenhum aviso de fallback (pseudo-UC do PA006) pode ter sido impresso antes do erro.
    saida = capsys.readouterr()
    assert "AVISO" not in saida.out
