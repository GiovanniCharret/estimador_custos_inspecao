# -*- coding: utf-8 -*-
"""Leitura e validacao das entradas do estimador (Lote de amostras + Painel de coordenadas)."""
from pathlib import Path


class EntradaInvalida(Exception):
    """Erro de entrada com mensagem pronta para o usuario final.

    Por que existe: separa erros de dados (culpa da entrada, mensagem amigavel,
    exit 1 sem traceback) de bugs do programa (traceback normal).
    """


def achar_entradas(pasta):
    """Localiza os dois arquivos de entrada dentro de Entrada/.

    Por que existe: o usuario deposita arquivos por convencao de nome (D7);
    centralizar a busca da um unico lugar para mensagens de erro claras.

    Logica: Entrada (pasta) -> Fase 1: valida Lote.xlsx -> Fase 2: procura
    *Painel de Monitoramento*.xlsx e exige exatamente 1 -> Saida: (lote, painel).
    """
    # Fase 1: o Lote.xlsx tem nome fixo; sem ele nao ha amostras a precificar.
    lote = Path(pasta) / "Lote.xlsx"
    # Se nao existe, aborta ja dizendo onde colocar o arquivo.
    if not lote.exists():
        raise EntradaInvalida(f"Lote.xlsx nao encontrado.\nColoque o arquivo com as amostras em: {pasta}\\Lote.xlsx")
    # Fase 2: o painel e localizado por nome contendo o padrao (D7), ignorando temporarios do Excel (~$).
    paineis = [p for p in Path(pasta).glob("*Painel de Monitoramento*.xlsx") if not p.name.startswith("~$")]
    # Nenhum painel: aborta explicando a convencao de nome.
    if not paineis:
        raise EntradaInvalida(f"Arquivo de coordenadas nao encontrado.\nColoque em {pasta}\\ um .xlsx cujo nome contenha 'Painel de Monitoramento'.")
    # Mais de um painel: ambiguidade — aborta listando para o usuario remover o excedente.
    if len(paineis) > 1:
        nomes = "\n  - ".join(p.name for p in paineis)
        raise EntradaInvalida(f"Mais de um Painel de Monitoramento em {pasta}:\n  - {nomes}\nDeixe apenas um.")
    # Saida: os dois caminhos validados.
    return lote, paineis[0]
