# -*- coding: utf-8 -*-
"""Testes do perfil de beneficiarios: dominio manda nas colunas, e nada fica nulo."""
import pandas as pd

from src.beneficiarios import contar_por_dominio, perfil_da_amostra
from src.io_amostras import ler_dominios
from src.resumo import _tabela_beneficiarios
from testes.fixtures import (DOMINIO_COMUNIDADE, DOMINIO_ENQUADRAMENTO,
                             escrever_painel_anexo_v)


def _dominios():
    """Os dois dominios sinteticos, na forma que ler_dominios devolve."""
    return {"tipo_comunidade": list(DOMINIO_COMUNIDADE),
            "enquadramento": list(DOMINIO_ENQUADRAMENTO)}


def _ucs(pares):
    """df de UCs com (tipo de comunidade, enquadramento) por linha."""
    return pd.DataFrame({
        "ODI": [f"O{i}" for i in range(len(pares))],
        "UC": [f"u{i}" for i in range(len(pares))],
        "TipoComunidade": [c for c, _ in pares],
        "Enquadramento": [e for _, e in pares],
    })


def test_ler_dominios_pega_as_colunas_d_e_e(tmp_path):
    # As listas suspensas moram nas colunas D e E da aba 'Dominios', identificadas por
    # POSICAO - e' assim que o humano se refere a elas, e o titulo da linha 1 nao e' dado.
    caminho = tmp_path / "Anexo V teste.xlsx"
    escrever_painel_anexo_v(caminho, com_dominios=True)
    dominios = ler_dominios(caminho)
    assert dominios["tipo_comunidade"] == DOMINIO_COMUNIDADE
    assert dominios["enquadramento"] == DOMINIO_ENQUADRAMENTO


def test_ler_dominios_sem_a_aba_nao_e_erro(tmp_path):
    # Anexo V antigo (e todos os paineis sinteticos de custo) nao tem a aba 'Dominios'.
    # Isso nao pode derrubar o programa - so nao ha dominio declarado.
    caminho = tmp_path / "Anexo V antigo.xlsx"
    escrever_painel_anexo_v(caminho)
    assert ler_dominios(caminho) == {"tipo_comunidade": [], "enquadramento": []}


def test_contagem_traz_a_categoria_vazia_com_zero():
    # O CORACAO DA ABA: uma coluna por categoria POSSIVEL, nao por categoria presente.
    # 'Comunidade indigena' com zero e' um fato ('a amostra nao pegou nenhuma'); a coluna
    # ausente seria ambiguidade.
    ucs = _ucs([("2 - Comunidade quilombola", "4 - Povos tradicionais"),
                ("2 - Comunidade quilombola", "4 - Povos tradicionais")])
    contagens, fora = contar_por_dominio(ucs, _dominios())
    assert fora == 0
    # Todas as 6 categorias dos dois dominios aparecem...
    assert set(contagens) == set(DOMINIO_COMUNIDADE) | set(DOMINIO_ENQUADRAMENTO)
    # ...as que ninguem escolheu valem 0, e nenhuma vale None.
    assert contagens["1 - Comunidade indígena"] == 0
    assert contagens["0 - Não é prioridade"] == 0
    assert all(v is not None for v in contagens.values())
    # E as escolhidas contam certo.
    assert contagens["2 - Comunidade quilombola"] == 2
    assert contagens["4 - Povos tradicionais"] == 2


def test_contagem_ignora_espaco_sobrando_e_acento():
    # O Anexo V real grava '11 - Rural geral / demais comunidades rurais ' (com espaco no
    # fim). Sem normalizar, a UC nao casaria com o dominio e sumiria da conta EM SILENCIO.
    ucs = _ucs([("11 - Rural geral / demais comunidades rurais   ", "1 - Familias de baixa renda")])
    contagens, fora = contar_por_dominio(ucs, _dominios())
    assert fora == 0
    assert contagens["11 - Rural geral / demais comunidades rurais"] == 1
    # 'Familias' sem acento tambem casa com 'Famílias' do dominio.
    assert contagens["1 - Famílias de baixa renda"] == 1


def test_categoria_fora_do_dominio_e_contada_a_parte(capsys):
    # Preenchimento invalido no Anexo V: a UC nao entra em nenhuma coluna. Isso precisa
    # ser DITO - senao a soma das colunas nao fecha com o total e ninguem sabe por que.
    ucs = _ucs([("99 - Categoria inventada", "1 - Famílias de baixa renda")])
    contagens, fora = contar_por_dominio(ucs, _dominios())
    assert fora == 1
    assert "99 - Categoria inventada" not in contagens
    perfil_da_amostra(ucs, _dominios(), n_estratos=3, amostra=1)
    assert "AVISO" in capsys.readouterr().out


def test_uc_sem_classificacao_nao_conta_e_nao_quebra():
    # Pseudo-UC (ODI orfa com Cons=0) nao existe no Anexo V, entao vem sem classificacao.
    ucs = _ucs([("", ""), ("2 - Comunidade quilombola", "4 - Povos tradicionais")])
    contagens, fora = contar_por_dominio(ucs, _dominios())
    # Vazio nao e' categoria invalida - e' ausencia. Nao conta e nao vira aviso.
    assert fora == 0
    assert contagens["2 - Comunidade quilombola"] == 1
    # A soma de um bloco fica ABAIXO do total de UCs, e e' isso que revela a nao classificada.
    soma_comunidade = sum(contagens[c] for c in DOMINIO_COMUNIDADE)
    assert soma_comunidade == 1 and len(ucs) == 2


def test_perfil_tem_identificacao_e_total():
    # A linha precisa dizer de qual estratificacao/amostra ela e', para casar com o Resumo.
    ucs = _ucs([("2 - Comunidade quilombola", "4 - Povos tradicionais")])
    linha = perfil_da_amostra(ucs, _dominios(), n_estratos=4, amostra=2)
    assert linha["n_estratos"] == 4 and linha["amostra"] == 2 and linha["n_ucs"] == 1


def test_tabela_nunca_tem_celula_nula():
    # Exigencia explicita do humano: nenhuma celula nula; zero pode. Vale inclusive quando
    # uma estratificacao nao tem NENHUMA UC (nada a classificar).
    cheia = perfil_da_amostra(_ucs([("2 - Comunidade quilombola", "4 - Povos tradicionais")]),
                              _dominios(), n_estratos=3, amostra=1)
    vazia = perfil_da_amostra(_ucs([]), _dominios(), n_estratos=4, amostra=1)
    tabela = _tabela_beneficiarios([cheia, vazia])
    assert len(tabela) == 2
    assert int(tabela.isna().sum().sum()) == 0
    # As contagens sao inteiros, nao floats (o pandas viraria float ao encontrar buraco).
    contagens = [c for c in tabela.columns if c not in ("Estratos", "Amostra", "UCs na amostra")]
    assert all(str(tabela[c].dtype).startswith("int") for c in contagens)
    # A estratificacao vazia e' uma linha de zeros, nao uma linha ausente.
    assert tabela.iloc[1]["UCs na amostra"] == 0
    assert all(tabela.iloc[1][c] == 0 for c in contagens)


def test_tabela_de_perfis_vazia_nao_quebra():
    # Sem nenhuma estratificacao nao ha aba - e nao ha excecao.
    assert len(_tabela_beneficiarios([])) == 0
