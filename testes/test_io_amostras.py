# -*- coding: utf-8 -*-
"""Testes de localizacao dos arquivos de entrada e leitura/juncao de amostras e painel."""
from pathlib import Path
import pandas as pd
import pytest
from src.io_amostras import (achar_entradas, ler_amostras, ler_n_estratos, ler_painel,
                             juntar_amostras_painel, EntradaInvalida, _norm_odi)
from testes.fixtures import (escrever_lote, escrever_painel, escrever_painel_anexo_v,
                             ODIS, ODIS_LOTE_TEXTO, ODIS_PAINEL_NUMERO)

def _cria(pasta, *nomes):
    # Cria arquivos vazios com os nomes dados dentro de pasta.
    for n in nomes:
        (pasta / n).write_bytes(b"")

def test_acha_lote_e_painel(tmp_path):
    # Caso feliz: uma planilha de amostras e um arquivo "Anexo V - Painel de Monitoramento".
    escrever_lote(tmp_path / "Lote.xlsx", abas=(1,))
    escrever_painel(tmp_path / "Anexo V - Painel de Monitoramento preenchido - ECO 037-2025.xlsx")
    lotes, painel = achar_entradas(tmp_path)
    # O Lote.xlsx nao diz o N no nome nem tem Leia-me: cai na contagem de estratos (3).
    assert [c.name for _, c in lotes] == ["Lote.xlsx"]
    assert "Anexo V" in painel.name

def test_acha_varias_estratificacoes_ordenadas(tmp_path):
    # A Entrada/ recebe uma planilha por numero de estratos; TODAS devem ser precificadas,
    # em ordem crescente de N (decisao da F9). O N vem do nome quando nao ha Leia-me.
    escrever_lote(tmp_path / "Estratos 5 - Python.xlsx", abas=(1,))
    escrever_lote(tmp_path / "Estratos 3 - Python.xlsx", abas=(1,))
    escrever_lote(tmp_path / "Estratos 4 - Python.xlsx", abas=(1,))
    escrever_painel(tmp_path / "Anexo V - Painel de Monitoramento.xlsx")
    lotes, _ = achar_entradas(tmp_path)
    assert [n for n, _ in lotes] == [3, 4, 5]

def test_estratificacoes_duplicadas_avisam_e_usam_uma(tmp_path, capsys):
    # Dois arquivos com o mesmo N sao a mesma estratificacao: contar as duas dobraria a
    # linha no resumo. Descarta a segunda, mas nunca em silencio.
    escrever_lote(tmp_path / "Estratos 4 - Python.xlsx", abas=(1,))
    escrever_lote(tmp_path / "Estratos 4 - copia.xlsx", abas=(1,))
    escrever_painel(tmp_path / "Anexo V - Painel de Monitoramento.xlsx")
    lotes, _ = achar_entradas(tmp_path)
    assert [n for n, _ in lotes] == [4]
    assert "IGNORADO" in capsys.readouterr().out

def test_erro_sem_planilha_de_amostras(tmp_path):
    # So o painel na pasta: erro dizendo o que falta colocar.
    escrever_painel(tmp_path / "Anexo V - Painel de Monitoramento.xlsx")
    with pytest.raises(EntradaInvalida, match="Nenhuma planilha de amostras"):
        achar_entradas(tmp_path)

def test_painel_nao_e_confundido_com_planilha_de_amostras(tmp_path):
    # O painel tem abas proprias e nao pode virar candidato a lote.
    escrever_lote(tmp_path / "Lote.xlsx", abas=(1,))
    escrever_painel(tmp_path / "Anexo V - Painel de Monitoramento.xlsx")
    lotes, painel = achar_entradas(tmp_path)
    assert painel not in [c for _, c in lotes]

def test_erro_sem_painel_lista_o_que_ha_na_pasta(tmp_path):
    # A convencao de nome mudou de 'Painel de Monitoramento' para 'Anexo V': o erro precisa
    # dizer o nome esperado E listar os arquivos presentes, para o usuario ver que o dele
    # so esta com o nome errado.
    escrever_lote(tmp_path / "Lote.xlsx", abas=(1,))
    escrever_painel(tmp_path / "Painel de Monitoramento antigo.xlsx")
    with pytest.raises(EntradaInvalida, match="Anexo V") as erro:
        achar_entradas(tmp_path)
    assert "Painel de Monitoramento antigo.xlsx" in str(erro.value)

def test_erro_dois_paineis(tmp_path):
    # Dois arquivos casando o padrao: aborta listando ambos.
    escrever_lote(tmp_path / "Lote.xlsx", abas=(1,))
    _cria(tmp_path, "Anexo V - Painel de Monitoramento A.xlsx", "Anexo V - Painel de Monitoramento B.xlsx")
    with pytest.raises(EntradaInvalida, match="A.xlsx"):
        achar_entradas(tmp_path)

def test_n_estratos_vem_do_leia_me(tmp_path):
    # O Leia-me do sistema upstream e' a fonte autoritativa do N - manda sobre o nome
    # do arquivo (que aqui diz 9 de proposito, para provar a precedencia).
    escrever_lote(tmp_path / "Estratos 9 - Python.xlsx", abas=(1,), n_estratos_leia_me=4)
    assert ler_n_estratos(tmp_path / "Estratos 9 - Python.xlsx") == 4

def test_n_estratos_cai_no_nome_do_arquivo(tmp_path):
    # Sem Leia-me, o numero do nome resolve.
    escrever_lote(tmp_path / "Estratos 6 - Python.xlsx", abas=(1,))
    assert ler_n_estratos(tmp_path / "Estratos 6 - Python.xlsx") == 6

def test_n_estratos_cai_na_contagem_com_aviso(tmp_path, capsys):
    # Sem Leia-me e sem numero no nome: conta os estratos distintos, avisando.
    escrever_lote(tmp_path / "Lote.xlsx", abas=(1,))
    assert ler_n_estratos(tmp_path / "Lote.xlsx") == 3      # a fixture cicla estratos 1/2/3
    assert "AVISO" in capsys.readouterr().out


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
    escrever_painel(tmp_path / "Anexo V - Painel de Monitoramento.xlsx")
    ucs = ler_painel(tmp_path / "Anexo V - Painel de Monitoramento.xlsx")
    assert {"ODI", "UC", "LATITUDE", "LONGITUDE"} <= set(ucs.columns)
    assert len(ucs) == 10                                # 5 ODIs x 2 UCs

def test_ler_painel_reporta_coordenada_fora_do_brasil(tmp_path):
    escrever_painel(tmp_path / "Anexo V - Painel de Monitoramento.xlsx")
    # Corrompe uma UC com longitude positiva (fora da bbox do Brasil).
    df = pd.read_excel(tmp_path / "Anexo V - Painel de Monitoramento.xlsx", sheet_name="Base_UC")
    df.loc[0, "LONGITUDE"] = 48.65
    with pd.ExcelWriter(tmp_path / "Anexo V - Painel de Monitoramento.xlsx") as xls:
        df.to_excel(xls, sheet_name="Base_UC", index=False)
    ucs = ler_painel(tmp_path / "Anexo V - Painel de Monitoramento.xlsx")
    assert len(ucs) == 9                                 # UC invalida removida (com aviso impresso)

def test_juntar_erro_odi_orfao(tmp_path):
    # Orfaos com Cons > 0 (obra com UC esperada): aborta listando os ODIs sem coordenada.
    escrever_lote(tmp_path / "Lote.xlsx", abas=(1,))
    escrever_painel(tmp_path / "Painel.xlsx", odis=ODIS[:3])    # faltam PA004/PA005
    amostras = ler_amostras(tmp_path / "Lote.xlsx")
    ucs = ler_painel(tmp_path / "Painel.xlsx")
    with pytest.raises(EntradaInvalida, match="PA004"):
        juntar_amostras_painel(amostras, ucs)

def test_juntar_sem_contrato_informado_ainda_acha_a_chave(tmp_path, capsys):
    # Sem contrato informado (o usuario apertou Enter) nao ha tipo para declarar a chave,
    # entao vale o padrao ODI. Um Lote de contrato MLA cairia em "tranche errada" - a rede
    # de seguranca precisa salvar a execucao, avisando.
    # A fixture gera UC = 4600000 + i*10 + j; com 1 UC por ODI, sao 4600000/4600010/4600020.
    escrever_painel_anexo_v(tmp_path / "Anexo V.xlsx", odis=[9001, 9002, 9003], ucs_por_odi=1)
    escrever_lote(tmp_path / "Lote.xlsx", abas=(1,), odis=["4600000", "4600010", "4600020"],
                  municipios={o: "GURINHEM" for o in ["4600000", "4600010", "4600020"]})
    amostras = ler_amostras(tmp_path / "Lote.xlsx")
    ucs = ler_painel(tmp_path / "Anexo V.xlsx")
    # As ODIs do painel (9001...) nao tem nada a ver com as do lote (4600000...).
    assert not set(amostras[1]["ODI"]) & set(ucs["ODI"])
    juntas = juntar_amostras_painel(amostras, ucs)
    # Casou pela UC: 3 obras, uma UC cada.
    assert len(juntas[1]) == 3
    assert set(juntas[1]["ODI"]) == {"4600000", "4600010", "4600020"}
    # E o desvio de chave e' anunciado (limitacao nunca silenciosa).
    assert "AVISO" in capsys.readouterr().out


def _painel_ambiguo(caminho):
    """Painel em que a ODI de uma linha e' o numero de UC de OUTRA.

    Por que existe: e' o unico cenario que distingue a regra DECLARADA (pelo tipo do
    contrato) de uma heuristica de tentativa-e-erro. Com as duas chaves casando, quem
    adivinha casa pela primeira que funcionar - e pode casar pela linha errada em silencio.

    Linha A: ODI 7001, UC 5001, latitude -7.12
    Linha B: ODI 5001, UC 9001, latitude -7.13
    Uma obra do Lote com 'ODI' = 5001 cai na linha B se a chave for a ODI, e na linha A
    se a chave for a UC.
    """
    escrever_painel_anexo_v(caminho, odis=[7001, 5001], ucs_por_odi=1,
                            numeros_uc=[5001, 9001])


def test_juntar_mla_casa_pela_uc_por_decisao_e_nao_por_tentativa(tmp_path, capsys):
    # GAP SEMANTICO DO LEGADO: em contrato MLA a coluna 'ODI' do Lote guarda numeros de UC.
    # Com o tipo do contrato declarado, a juncao TEM de ir pela UC mesmo quando a coluna
    # ODI do Anexo V tambem casaria - senao o programa precificaria a obra errada calado.
    _painel_ambiguo(tmp_path / "Anexo V.xlsx")
    escrever_lote(tmp_path / "Lote.xlsx", abas=(1,), odis=["5001"],
                  municipios={"5001": "GURINHEM"})
    amostras = ler_amostras(tmp_path / "Lote.xlsx")
    ucs = ler_painel(tmp_path / "Anexo V.xlsx")
    juntas = juntar_amostras_painel(amostras, ucs, tipo_contrato="MLA")
    # Casou pela UC: a linha A (latitude -7.12), nao a linha B.
    assert len(juntas[1]) == 1
    assert juntas[1].iloc[0]["LATITUDE"] == pytest.approx(-7.12)
    # E diz que fez isso, sem chamar de erro - e' o comportamento esperado do tipo.
    saida = capsys.readouterr().out
    assert "Contrato MLA" in saida and "AVISO" not in saida


def test_juntar_lpt_casa_pela_odi_no_mesmo_painel_ambiguo(tmp_path):
    # O par do teste acima: mesmo painel, mesmo Lote, tipo diferente -> linha diferente.
    # E' o que prova que quem decide e' o TIPO DO CONTRATO, nao o acaso dos dados.
    _painel_ambiguo(tmp_path / "Anexo V.xlsx")
    escrever_lote(tmp_path / "Lote.xlsx", abas=(1,), odis=["5001"],
                  municipios={"5001": "GURINHEM"})
    amostras = ler_amostras(tmp_path / "Lote.xlsx")
    ucs = ler_painel(tmp_path / "Anexo V.xlsx")
    juntas = juntar_amostras_painel(amostras, ucs, tipo_contrato="LPT")
    # Casou pela ODI: a linha B (latitude -7.13).
    assert juntas[1].iloc[0]["LATITUDE"] == pytest.approx(-7.13)


def test_juntar_avisa_quando_a_chave_declarada_falha(tmp_path, capsys):
    # Contrato declarado LPT mas as obras so casam pela UC: a rede de seguranca salva a
    # execucao, mas avisando - alguma premissa esta errada (contrato informado errado,
    # tipo errado na base, ou planilha fora do padrao do seu tipo).
    escrever_painel_anexo_v(tmp_path / "Anexo V.xlsx", odis=[9001, 9002, 9003], ucs_por_odi=1)
    escrever_lote(tmp_path / "Lote.xlsx", abas=(1,), odis=["4600000", "4600010", "4600020"],
                  municipios={o: "GURINHEM" for o in ["4600000", "4600010", "4600020"]})
    amostras = ler_amostras(tmp_path / "Lote.xlsx")
    ucs = ler_painel(tmp_path / "Anexo V.xlsx")
    juntas = juntar_amostras_painel(amostras, ucs, tipo_contrato="LPT")
    assert len(juntas[1]) == 3
    saida = capsys.readouterr().out
    assert "AVISO" in saida and "'ODI'" in saida and "'UC'" in saida


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

def test_ler_painel_anexo_v_cabecalho_na_segunda_linha(tmp_path):
    # Formato real: faixa mesclada na linha 1, cabecalho na 2, colunas por extenso.
    escrever_painel_anexo_v(tmp_path / "Anexo V - Painel de Monitoramento.xlsx")
    ucs = ler_painel(tmp_path / "Anexo V - Painel de Monitoramento.xlsx")
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
