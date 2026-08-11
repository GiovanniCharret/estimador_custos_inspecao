# -*- coding: utf-8 -*-
"""E2E: Entrada/ sintetica completa -> pipeline inteiro -> confere saidas.

Cobre o caminho feliz e as bordas que o DESIGN §7 elegeu como os erros mais
provaveis do usuario final: tranche errada, entrada ausente, ODI orfa (nos dois
ramos da regra do orfao) e Resumo_Custos.xlsx travado pelo Excel.
"""
import json
import re

import pandas as pd
import pytest

from src import config
from src.distancias import haversine_km
from src.estimar_custos import executar
from testes.fixtures import (escrever_lote, escrever_painel, escrever_painel_anexo_v,
                             ODIS, ODIS_LOTE_TEXTO)


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
    escrever_painel(raiz / "Entrada" / "Anexo V - Painel de Monitoramento T.xlsx", odis=odis_painel)


def _base_contratos(raiz, monkeypatch, contratos):
    """Grava uma base de contratos sintetica e aponta o config para ela.

    Por que existe: D6 proibe teste que dependa de minhas_notas/; a resolucao de
    contrato precisa de uma base, entao cada teste monta a sua dentro do tmp_path.

    Logica: Entrada (raiz, monkeypatch, dict de contratos) -> Fase 1: grava o JSON
    -> Fase 2: aponta config.ARQUIVO_BASE_CONTRATOS para ele -> Saida: nada.
    """
    # Fase 1: JSON no mesmo formato do dados/base_contratos.json real.
    (raiz / "base_contratos.json").write_text(json.dumps(contratos), encoding="utf-8")
    # Fase 2: caminho relativo a raiz (o orquestrador resolve com raiz / ARQUIVO_BASE_CONTRATOS).
    monkeypatch.setattr(config, "ARQUIVO_BASE_CONTRATOS", "base_contratos.json")


def test_e2e_feliz(tmp_path, capsys):
    # Caminho feliz sem contrato informado: usa UF_PADRAO/TIPO_CONTRATO_PADRAO com aviso.
    _monta_entrada(tmp_path)
    assert executar(tmp_path) == 0
    # O aviso de contrato nao informado precisa aparecer (limitacao nunca silenciosa).
    assert "AVISO" in capsys.readouterr().out
    # Saidas: UMA planilha com tudo + um mapa por estratificacao (decisao da F9).
    assert (tmp_path / "saida" / "Resumo_Custos.xlsx").exists()
    assert (tmp_path / "saida" / "Mapa_Estratos_3.html").exists()
    # Sem escolha explicita, so a amostra padrao (1) e' precificada: uma linha, nao duas.
    resumo = pd.read_excel(tmp_path / "saida" / "Resumo_Custos.xlsx", sheet_name="Resumo")
    assert list(resumo["Amostra"]) == [config.AMOSTRA_PADRAO]


def test_e2e_escolha_da_amostra(tmp_path):
    # A amostra escolhida manda na planilha INTEIRA - resumo, cenarios, detalhe e mapa.
    # As reservas (2 e 3) nem chegam a ser processadas.
    _monta_entrada(tmp_path)
    assert executar(tmp_path, amostra=2) == 0
    caminho = tmp_path / "saida" / "Resumo_Custos.xlsx"
    for aba in ("Resumo", "Cenarios", "Detalhe"):
        assert set(pd.read_excel(caminho, sheet_name=aba)["Amostra"]) == {2}
    # O mapa nao rotula mais camadas por amostra - a amostra e' unica na execucao inteira.
    html = (tmp_path / "saida" / "Mapa_Estratos_3.html").read_text(encoding="utf-8")
    assert "Amostra 1" not in html and "Amostra 2" not in html


def test_e2e_amostra_inexistente(tmp_path, capsys):
    # Lote so com as abas 1 e 2: pedir a 3 e' erro de entrada com mensagem, nao traceback.
    _monta_entrada(tmp_path)
    assert executar(tmp_path, amostra=3) == 1
    assert "Amostra 3" in capsys.readouterr().out


def test_e2e_amostra_faltando_em_uma_estratificacao(tmp_path, capsys):
    # Uma estratificacao sem a aba pedida e' pulada COM aviso; as outras seguem normalmente.
    _monta_entrada(tmp_path)                                          # Lote.xlsx: abas 1 e 2
    escrever_lote(tmp_path / "Entrada" / "Estratos 5 - Python.xlsx", abas=(1,))
    assert executar(tmp_path, amostra=2) == 0
    saida = capsys.readouterr().out
    assert "Estratos 5 - Python.xlsx" in saida and "Amostra 2" in saida
    resumo = pd.read_excel(tmp_path / "saida" / "Resumo_Custos.xlsx", sheet_name="Resumo")
    assert list(resumo["Estratos"]) == [3]


def test_e2e_custo_e_por_amostra_nao_por_estrato(tmp_path):
    # INVARIANTE CENTRAL DO MODELO F9: o custo fixo de escritorio entra UMA vez por
    # amostra. Antes ele entrava uma vez por ESTRATO, o que multiplicava R$12.960 pelo
    # numero de estratos (na amostra real da PB isso sozinho inflava R$25.920).
    _monta_entrada(tmp_path)
    assert executar(tmp_path) == 0
    resumo = pd.read_excel(tmp_path / "saida" / "Resumo_Custos.xlsx", sheet_name="Resumo")
    fixo_esperado = config.HORAS_ESCRITORIO_POR_OS * config.TARIFAS_HORA[config.PERFIL_EQUIPE]["escritorio"]
    # Uma linha por amostra, e o fixo e' o mesmo valor unico em todas (nunca N x 12.960).
    assert resumo["Custo fixo OS (R$)"].tolist() == pytest.approx([fixo_esperado] * len(resumo))
    # O total fecha com campo + fixo, sem nenhum termo escondido.
    assert resumo["Custo total (R$)"].tolist() == pytest.approx(
        (resumo["Custo campo (R$)"] + resumo["Custo fixo OS (R$)"]).tolist())
    # E o campo fecha com a formula de dias (o que amarra o modelo ao benchmark).
    esperado_campo = (resumo["Dias faturados"] * config.TAMANHO_EQUIPE
                      * config.HORAS_DIA_CAMPO * config.TARIFAS_HORA[config.PERFIL_EQUIPE]["campo"])
    assert resumo["Custo campo (R$)"].tolist() == pytest.approx(esperado_campo.tolist())


def test_e2e_varias_estratificacoes_numa_planilha_so(tmp_path, capsys):
    # A Entrada/ recebe uma planilha por numero de estratos; todas viram linhas da MESMA
    # aba Resumo, para o humano comparar Estratos 3 x 4 x 5 lado a lado.
    _monta_entrada(tmp_path)
    escrever_lote(tmp_path / "Entrada" / "Estratos 5 - Python.xlsx", abas=(1, 2))
    assert executar(tmp_path) == 0
    resumo = pd.read_excel(tmp_path / "saida" / "Resumo_Custos.xlsx", sheet_name="Resumo")
    # 2 estratificacoes x 1 amostra escolhida = 2 linhas, ordenadas por estratificacao.
    assert list(resumo["Estratos"]) == [3, 5]
    # E os cenarios de prazo existem para as duas.
    cenarios = pd.read_excel(tmp_path / "saida" / "Resumo_Custos.xlsx", sheet_name="Cenarios")
    assert set(cenarios["Estratos"]) == {3, 5}
    # Um mapa por estratificacao, nao um por amostra.
    assert (tmp_path / "saida" / "Mapa_Estratos_3.html").exists()
    assert (tmp_path / "saida" / "Mapa_Estratos_5.html").exists()
    assert not (tmp_path / "saida" / "Mapa_Amostra_1.html").exists()


def test_e2e_roteiro_encadeado_derruba_a_quilometragem(tmp_path):
    # REGRESSAO DA F9: com o modelo antigo (ida e volta da capital por municipio) o
    # deslocamento era ~7x maior. O roteiro gravado tem de ser menor que essa soma.
    # Cada ODI num municipio proprio - e' assim que a amostra real se comporta (26 ODIs
    # em 25 municipios) e e' o cenario em que o modelo antigo explodia.
    _monta_entrada(tmp_path, municipios={odi: f"MUNICIPIO {i}" for i, odi in enumerate(ODIS)})
    assert executar(tmp_path) == 0
    resumo = pd.read_excel(tmp_path / "saida" / "Resumo_Custos.xlsx", sheet_name="Resumo")
    detalhe = pd.read_excel(tmp_path / "saida" / "Resumo_Custos.xlsx", sheet_name="Detalhe")
    a1 = resumo[resumo["Amostra"] == 1].iloc[0]
    obras = detalhe[detalhe["Amostra"] == 1]
    lat_cap, lon_cap = config.CAPITAIS_UF[config.UF_PADRAO]
    # Modelo antigo: 2 x (capital -> obra) para cada municipio distinto.
    por_municipio = obras.groupby("Municipio")[["Latitude", "Longitude"]].mean()
    ida_e_volta = sum(2 * haversine_km(lat_cap, lon_cap, r.Latitude, r.Longitude)
                      for r in por_municipio.itertuples()) * config.FATOR_RODOVIARIO
    assert a1["Roteiro (km estrada)"] < ida_e_volta
    # A ordem do roteiro e' uma numeracao completa das obras da amostra.
    assert sorted(obras["Ordem"]) == list(range(1, len(obras) + 1))


def test_e2e_mapa_oferece_os_mesmos_cenarios_de_equipe_da_planilha(tmp_path):
    # Mapa e planilha tem de falar das MESMAS opcoes: o radio do mapa cobre exatamente os
    # numeros de equipe que a aba Cenarios chegou a propor.
    _monta_entrada(tmp_path, municipios={odi: f"MUNICIPIO {i}" for i, odi in enumerate(ODIS)})
    assert executar(tmp_path) == 0
    cenarios = pd.read_excel(tmp_path / "saida" / "Resumo_Custos.xlsx", sheet_name="Cenarios")
    equipes = sorted(set(cenarios[cenarios["Estratos"] == 3]["Equipes"]))
    html = (tmp_path / "saida" / "Mapa_Estratos_3.html").read_text(encoding="utf-8")
    rotulos = re.findall(r"(\d+) equipes? - [\d,]+ km", html)
    assert sorted({int(n) for n in rotulos}) == equipes
    # E o painel e' de radio (um cenario por vez), com titulo proprio.
    assert "Equipes em campo" in html and "groupedlayers" in html.lower()


def test_e2e_tranche_errada(tmp_path, capsys):
    # Painel de outra tranche: codigo de saida 1 e mensagem especifica, sem traceback.
    _monta_entrada(tmp_path, odis_painel=["TO900", "TO901", "TO902", "TO903", "TO904"])
    assert executar(tmp_path) == 1
    assert "tranche" in capsys.readouterr().out.lower()


def test_e2e_sem_entrada(tmp_path, capsys):
    # Entrada/ so com o painel: erro de usuario dizendo o que falta, nao traceback.
    (tmp_path / "Entrada").mkdir()
    (tmp_path / "saida").mkdir()
    escrever_painel(tmp_path / "Entrada" / "Anexo V - Painel de Monitoramento T.xlsx")
    assert executar(tmp_path) == 1
    assert "Nenhuma planilha de amostras" in capsys.readouterr().out


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
    det = pd.read_excel(tmp_path / "saida" / "Resumo_Custos.xlsx", sheet_name="Detalhe")
    linha = det[(det["Amostra"] == 1) & (det["ODI"] == "PA005")].iloc[0]
    assert linha["UCs"] == 1


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
        resumo = pd.read_excel(raiz / "saida" / "Resumo_Custos.xlsx", sheet_name="Resumo")
        return resumo[resumo["Amostra"] == 1].iloc[0]["Custo total (R$)"]

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


def test_e2e_contrato_aceita_hifen_no_lugar_da_barra(tmp_path, capsys, monkeypatch):
    # A base grafa 'ECO 037/2025' (formato do contrato) mas o usuario copia 'ECO 037-2025'
    # do nome do arquivo do Anexo V. As duas formas tem de resolver o MESMO contrato.
    _monta_entrada(tmp_path)
    _base_contratos(tmp_path, monkeypatch,
                    {"ECO 037/2025": {"uf": "PB", "tipo_contrato": "LPT", "vigente": "Andamento"}})
    assert executar(tmp_path, contrato="ECO 037-2025") == 0
    saida = capsys.readouterr().out
    # Imprime o nome COMO ESTA NA BASE, nao como foi digitado (o usuario confere o que casou).
    assert "Contrato ECO 037/2025" in saida and "PB" in saida


def test_e2e_contrato_ignora_bom_e_caixa(tmp_path, monkeypatch):
    # O terminal do Windows cola um BOM no inicio do texto canalizado; caixa baixa e' erro
    # de digitacao trivial. Nenhum dos dois pode impedir a resolucao do contrato.
    _monta_entrada(tmp_path)
    _base_contratos(tmp_path, monkeypatch,
                    {"ECO 037/2025": {"uf": "PB", "tipo_contrato": "LPT", "vigente": "Andamento"}})
    assert executar(tmp_path, contrato="﻿eco 037-2025") == 0


def test_e2e_painel_no_formato_anexo_v(tmp_path, capsys):
    # Pipeline inteiro sobre o formato REAL do Painel (faixa mesclada + cabecalhos por
    # extenso) com ODI texto-com-zeros no Lote e numerica no Painel: e' a combinacao que
    # travou a primeira execucao com dados reais.
    (tmp_path / "Entrada").mkdir()
    escrever_lote(tmp_path / "Entrada" / "Lote.xlsx", abas=(1, 2), odis=ODIS_LOTE_TEXTO,
                  municipios={odi: "GURINHEM" for odi in ODIS_LOTE_TEXTO})
    escrever_painel_anexo_v(tmp_path / "Entrada" / "Anexo V - Painel de Monitoramento T.xlsx")
    assert executar(tmp_path) == 0
    saida = capsys.readouterr().out
    # Diz de qual aba/linha leu (com duas linhas de cabecalho possiveis, isso precisa ser visivel).
    assert "cabecalho na linha 2" in saida
    # 5 ODIs x 2 UCs por amostra chegaram ate o motor de custo.
    assert "5 ODIs, 1 municipios, 10 UCs" in saida
    assert (tmp_path / "saida" / "Resumo_Custos.xlsx").exists()


def test_e2e_estratificacoes_duplicadas_avisam(tmp_path, capsys):
    # Duas planilhas declarando o mesmo N sao a mesma estratificacao: a segunda e'
    # descartada para nao duplicar a linha do resumo, mas nunca em silencio.
    _monta_entrada(tmp_path)
    escrever_lote(tmp_path / "Entrada" / "Estratos 3 - Python.xlsx", abas=(1, 2))
    assert executar(tmp_path) == 0
    assert "IGNORADO" in capsys.readouterr().out
    resumo = pd.read_excel(tmp_path / "saida" / "Resumo_Custos.xlsx", sheet_name="Resumo")
    assert len(resumo) == 1               # uma estratificacao so, uma linha so


def test_e2e_amostra_vazia_nao_derruba_o_pipeline(tmp_path):
    # Uma aba 'Amostra K' sem nenhuma obra sorteada e' possivel (estratificacao apertada).
    # Ela precisa virar uma linha de zeros no resumo, nunca um traceback.
    _monta_entrada(tmp_path)
    # Reescreve o Lote com a amostra 2 sem nenhum STATUS='Selecionado'.
    caminho = tmp_path / "Entrada" / "Lote.xlsx"
    cheia = pd.read_excel(caminho, sheet_name="Amostra 1")
    vazia = cheia.assign(STATUS="")
    with pd.ExcelWriter(caminho) as xls:
        cheia.to_excel(xls, sheet_name="Amostra 1", index=False)
        vazia.to_excel(xls, sheet_name="Amostra 2", index=False)
    # Pede justamente a amostra vazia: interseccao zero de ODIs nao pode ser confundida
    # com "tranche errada" (os arquivos estao certos; a amostra e' que nao sorteou nada).
    assert executar(tmp_path, amostra=2) == 0
    resumo = pd.read_excel(tmp_path / "saida" / "Resumo_Custos.xlsx", sheet_name="Resumo")
    linha = resumo[resumo["Amostra"] == 2].iloc[0]
    # Sem obras: zero geometria, zero dias de trabalho - mas o fixo de OS continua existindo.
    assert linha["ODIs"] == 0 and linha["UCs"] == 0
    assert linha["Roteiro (km estrada)"] == pytest.approx(0.0)
    assert linha["Dias trabalho"] == 0
    # E nao ha cenario de prazo a explorar para uma amostra sem trabalho.
    assert len(pd.read_excel(tmp_path / "saida" / "Resumo_Custos.xlsx", sheet_name="Cenarios")) == 0


def test_e2e_determinismo(tmp_path):
    # Determinismo (convencao do canonico): mesma entrada -> mesmos numeros, sempre.
    _monta_entrada(tmp_path)
    assert executar(tmp_path) == 0
    primeiro = pd.read_excel(tmp_path / "saida" / "Resumo_Custos.xlsx", sheet_name="Resumo")
    # Roda de novo sobre a mesma Entrada/, sobrescrevendo as saidas.
    assert executar(tmp_path) == 0
    segundo = pd.read_excel(tmp_path / "saida" / "Resumo_Custos.xlsx", sheet_name="Resumo")
    pd.testing.assert_frame_equal(primeiro, segundo)
