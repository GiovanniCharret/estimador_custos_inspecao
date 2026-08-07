# -*- coding: utf-8 -*-
"""E2E: Entrada/ sintetica completa -> pipeline inteiro -> confere saidas.

Cobre o caminho feliz e as bordas que o DESIGN §7 elegeu como os erros mais
provaveis do usuario final: tranche errada, entrada ausente, ODI orfa (nos dois
ramos da regra do orfao) e Resumo_Custos.xlsx travado pelo Excel.
"""
import json

import pandas as pd
import pytest

from src import config
from src.estimar_custos import executar
from testes.fixtures import escrever_lote, escrever_painel, ODIS


def _monta_entrada(raiz, odis_painel=ODIS, **kwargs_lote):
    """Cria a arvore Entrada/ + saida/ com Lote e Painel sinteticos dentro de um tmp_path.

    Por que existe: todos os testes e2e precisam da mesma arvore de entrada; centralizar
    evita repetir a montagem e mantem os testes legiveis (cada um so muda o que testa).

    Logica: Entrada (raiz, ODIs do painel, overrides do lote) -> Fase 1: cria as pastas
    -> Fase 2: grava Lote.xlsx com 2 amostras -> Fase 3: grava o Painel com os ODIs
    pedidos -> Saida: nada (efeito colateral em disco).
    """
    # Fase 1: as duas pastas que o orquestrador espera encontrar/usar.
    (raiz / "Entrada").mkdir(exist_ok=True)
    (raiz / "saida").mkdir(exist_ok=True)
    # Fase 2: Lote com as amostras 1 e 2 (o pipeline processa as que existirem).
    escrever_lote(raiz / "Entrada" / "Lote.xlsx", abas=(1, 2), **kwargs_lote)
    # Fase 3: Painel com os ODIs pedidos (por padrao, os mesmos do Lote = caso feliz).
    escrever_painel(raiz / "Entrada" / "Painel de Monitoramento T.xlsx", odis=odis_painel)


def _base_contratos(raiz, monkeypatch, contratos):
    """Grava uma base de contratos sintetica e aponta o config para ela.

    Por que existe: D6 proibe teste que dependa de minhas_notas/; a resolucao de
    contrato precisa de uma base, entao cada teste monta a sua dentro do tmp_path.

    Logica: Entrada (raiz, monkeypatch, dict de contratos) -> Fase 1: grava o JSON
    -> Fase 2: aponta config.ARQUIVO_BASE_CONTRATOS para ele -> Saida: nada.
    """
    # Fase 1: JSON no mesmo formato do minhas_notas/base_contratos.json real.
    (raiz / "base_contratos.json").write_text(json.dumps(contratos), encoding="utf-8")
    # Fase 2: caminho relativo a raiz (o orquestrador resolve com raiz / ARQUIVO_BASE_CONTRATOS).
    monkeypatch.setattr(config, "ARQUIVO_BASE_CONTRATOS", "base_contratos.json")


def test_e2e_feliz(tmp_path, capsys):
    # Caminho feliz sem contrato informado: usa UF_PADRAO/TIPO_CONTRATO_PADRAO com aviso.
    _monta_entrada(tmp_path)
    assert executar(tmp_path) == 0
    # O aviso de contrato nao informado precisa aparecer (limitacao nunca silenciosa).
    assert "AVISO" in capsys.readouterr().out
    # Saidas existem: um resumo e um mapa por amostra.
    assert (tmp_path / "saida" / "Resumo_Custos.xlsx").exists()
    assert (tmp_path / "saida" / "Mapa_Amostra_1.html").exists()
    assert (tmp_path / "saida" / "Mapa_Amostra_2.html").exists()


def test_e2e_total_bate_com_detalhe_mais_fixo(tmp_path):
    # Invariante central do modelo: o TOTAL do agregado NAO e' a soma do detalhe -
    # o detalhe so tem custo de CAMPO; o fixo de escritorio entra uma vez por estrato.
    _monta_entrada(tmp_path)
    assert executar(tmp_path) == 0
    agg = pd.read_excel(tmp_path / "saida" / "Resumo_Custos.xlsx", sheet_name="Amostra 1")
    det = pd.read_excel(tmp_path / "saida" / "Resumo_Custos.xlsx", sheet_name="Detalhe 1")
    total = agg[agg["Estrato"].astype(str) == "TOTAL"].iloc[0]
    # (a) o campo do agregado bate com a soma do detalhe por ODI (tolerancia de arredondamento).
    assert total["Custo campo (R$)"] == pytest.approx(det["Custo total (R$)"].sum(), abs=0.05)
    # (b) o total = campo + fixo, e o fixo e' contado uma vez por estrato (3 estratos aqui).
    estratos = agg[agg["Estrato"].astype(str) != "TOTAL"]
    assert len(estratos) == 3
    assert total["Custo fixo OS (R$)"] == pytest.approx(
        config.HORAS_ESCRITORIO_POR_OS * config.TARIFAS_HORA[config.PERFIL_EQUIPE]["escritorio"] * 3, abs=0.05)
    assert total["Custo total (R$)"] == pytest.approx(
        total["Custo campo (R$)"] + total["Custo fixo OS (R$)"], abs=0.05)
    # (c) somar o detalhe direto NAO da o total - o teste registra a diferenca esperada.
    assert total["Custo total (R$)"] > det["Custo total (R$)"].sum()


def test_e2e_tranche_errada(tmp_path, capsys):
    # Painel de outra tranche: codigo de saida 1 e mensagem especifica, sem traceback.
    _monta_entrada(tmp_path, odis_painel=["TO900", "TO901", "TO902", "TO903", "TO904"])
    assert executar(tmp_path) == 1
    assert "tranche" in capsys.readouterr().out.lower()


def test_e2e_sem_entrada(tmp_path, capsys):
    # Sem Lote.xlsx: erro de usuario dizendo onde colocar o arquivo, nao traceback.
    (tmp_path / "Entrada").mkdir()
    (tmp_path / "saida").mkdir()
    assert executar(tmp_path) == 1
    assert "Lote.xlsx" in capsys.readouterr().out


def test_e2e_odi_orfa_com_uc_aborta(tmp_path, capsys):
    # Regra do orfao, ramo (a): ODI sorteada com Cons>0 e sem UC no painel aborta.
    _monta_entrada(tmp_path, odis_painel=ODIS[:3])   # PA004/PA005 ficam sem coordenada
    assert executar(tmp_path) == 1
    saida = capsys.readouterr().out
    # A mensagem lista os orfaos para o usuario corrigir o painel.
    assert "PA004" in saida and "PA005" in saida


def test_e2e_odi_orfa_cons_zero_vira_pseudo_uc(tmp_path, capsys):
    # Regra do orfao, ramo (b): Cons==0 (obra sem UC) nao aborta - vira pseudo-UC no
    # centroide do municipio e o pipeline completa normalmente.
    _monta_entrada(tmp_path, odis_painel=ODIS[:4], cons={"PA005": 0})
    assert executar(tmp_path) == 0
    saida = capsys.readouterr().out
    # O fallback e' anunciado (nunca silencioso) e nomeia a ODI afetada.
    assert "pseudo-UC" in saida and "PA005" in saida
    # A ODI orfa aparece no detalhe com exatamente 1 UC (a pseudo-UC).
    det = pd.read_excel(tmp_path / "saida" / "Resumo_Custos.xlsx", sheet_name="Detalhe 1")
    linha = det[det["ODI"] == "PA005"].iloc[0]
    assert linha["Qtd UCs"] == 1


def test_e2e_resumo_aberto_no_excel(tmp_path, capsys, monkeypatch):
    # Resumo_Custos.xlsx travado (aberto no Excel): mensagem amigavel, exit 1, sem traceback.
    _monta_entrada(tmp_path)

    def _trava(*args, **kwargs):
        # Simula o lock do Windows que o Excel poe no arquivo aberto.
        raise PermissionError(13, "Permission denied")

    # Intercepta a criacao do writer dentro do modulo resumo (onde o lock apareceria).
    monkeypatch.setattr("src.resumo.pd.ExcelWriter", _trava)
    assert executar(tmp_path) == 1
    assert "Feche o arquivo no Excel" in capsys.readouterr().out


def test_e2e_contrato_conhecido_usa_uf_e_tipo(tmp_path, capsys, monkeypatch):
    # Contrato valido na base: a UF e o tipo do contrato mandam sobre os padroes.
    _monta_entrada(tmp_path)
    _base_contratos(tmp_path, monkeypatch,
                    {"ECM TESTE-2026": {"uf": "PA", "tipo_contrato": "MLA", "vigente": "Andamento"}})
    assert executar(tmp_path, contrato="ECM TESTE-2026") == 0
    saida = capsys.readouterr().out
    # Confirma que a resolucao foi aplicada e impressa para conferencia do usuario.
    assert "PA" in saida and "MLA" in saida
    # Sem contrato nao ha aviso de padrao: o aviso so existe quando o contrato falta.
    assert "contrato nao informado" not in saida


def test_e2e_tipo_contrato_muda_o_custo(tmp_path, monkeypatch):
    # MLA (3 UCs/dia) e' muito mais caro que LPT (30 UCs/dia) para a MESMA amostra:
    # prova que o tipo resolvido pelo contrato chega de fato ao motor de custo.
    def _total(contrato, tipo):
        raiz = tmp_path / tipo
        raiz.mkdir()
        _monta_entrada(raiz)
        _base_contratos(raiz, monkeypatch,
                        {contrato: {"uf": "PA", "tipo_contrato": tipo, "vigente": "Andamento"}})
        assert executar(raiz, contrato=contrato) == 0
        agg = pd.read_excel(raiz / "saida" / "Resumo_Custos.xlsx", sheet_name="Amostra 1")
        return agg[agg["Estrato"].astype(str) == "TOTAL"].iloc[0]["Custo total (R$)"]

    # Mesma geometria, so o tipo muda: MLA tem de sair mais caro.
    assert _total("ECM LPT-2026", "LPT") < _total("ECM MLA-2026", "MLA")


def test_e2e_contrato_desconhecido(tmp_path, capsys, monkeypatch):
    # Contrato inexistente: erro de entrada listando chaves parecidas para o usuario.
    _monta_entrada(tmp_path)
    _base_contratos(tmp_path, monkeypatch,
                    {"ECM TESTE-2026": {"uf": "PA", "tipo_contrato": "LPT", "vigente": "Andamento"}})
    assert executar(tmp_path, contrato="ECM INEXISTENTE") == 1
    assert "ECM TESTE-2026" in capsys.readouterr().out


def test_e2e_base_de_contratos_ausente(tmp_path, capsys, monkeypatch):
    # Contrato informado mas base ausente: erro de entrada claro, nao traceback.
    _monta_entrada(tmp_path)
    monkeypatch.setattr(config, "ARQUIVO_BASE_CONTRATOS", "nao_existe.json")
    assert executar(tmp_path, contrato="ECM QUALQUER") == 1
    assert "Base de contratos nao encontrada" in capsys.readouterr().out


def test_e2e_determinismo(tmp_path):
    # Determinismo (convencao do canonico): mesma entrada -> mesmos numeros, sempre.
    _monta_entrada(tmp_path)
    assert executar(tmp_path) == 0
    primeiro = pd.read_excel(tmp_path / "saida" / "Resumo_Custos.xlsx", sheet_name="Amostra 1")
    # Roda de novo sobre a mesma Entrada/, sobrescrevendo as saidas.
    assert executar(tmp_path) == 0
    segundo = pd.read_excel(tmp_path / "saida" / "Resumo_Custos.xlsx", sheet_name="Amostra 1")
    pd.testing.assert_frame_equal(primeiro, segundo)
