# -*- coding: utf-8 -*-
"""Orquestrador do estimador: le Entrada/, calcula custos e grava saida/.

Unico executavel do projeto (padrao do sistema canonico): rode via executar.bat
ou `.venv\\Scripts\\python.exe src\\estimar_custos.py`.

O pipeline inteiro em uma linha:
  Entrada/Lote.xlsx + Painel -> juncao por ODI -> geometria -> custo -> saida/
"""
from pathlib import Path
import json
import sys

# Garante que 'src' e' importavel quando rodado como script (python src/estimar_custos.py):
# sem isso o import 'from src.io_amostras import ...' falha, pois o diretorio do script
# (src/) entra no sys.path, mas a raiz do projeto - que contem o pacote src/ - nao.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.io_amostras import (EntradaInvalida, achar_entradas, ler_amostras,   # noqa: E402
                             ler_painel, juntar_amostras_painel)
from src.distancias import resumo_por_odi                                     # noqa: E402
from src.custo import custo_por_odi                                           # noqa: E402
from src.resumo import gravar_resumo                                          # noqa: E402
from src.mapas import gravar_mapa                                             # noqa: E402
from src import config                                                        # noqa: E402


def _resolver_contrato(raiz, contrato):
    """Resolve (uf, tipo_contrato) a partir do contrato informado (decisoes G3/G5).

    Por que existe: a base de partida do deslocamento (capital da UF) e a produtividade
    da inspecao (LPT 30 UCs/dia x MLA 3 UCs/dia) dependem do contrato. Concentrar a
    resolucao aqui deixa executar() testavel sem stdin e sem base real.

    Logica: Entrada (raiz, contrato ou None) -> Fase 1: sem contrato, usa os padroes de
    config com AVISO -> Fase 2: carrega a base de contratos (caminho relativo a raiz)
    -> Fase 3: busca a chave exata; ausente = erro com sugestoes parecidas -> Saida:
    tupla (uf, tipo_contrato).
    """
    # Fase 1: sem contrato informado, cai nos padroes de config - mas nunca em silencio.
    if not contrato:
        print(f"AVISO: contrato nao informado; usando UF={config.UF_PADRAO}, "
              f"tipo={config.TIPO_CONTRATO_PADRAO}.")
        return config.UF_PADRAO, config.TIPO_CONTRATO_PADRAO
    # Fase 2: a base e' resolvida contra a RAIZ (nao contra o cwd), para o .bat funcionar
    # de qualquer diretorio; ARQUIVO_BASE_CONTRATOS e' relativo por design.
    caminho = Path(raiz) / config.ARQUIVO_BASE_CONTRATOS
    # Base ausente e' erro de ENTRADA: o usuario pediu resolucao por contrato e nao da pra atender.
    if not caminho.exists():
        raise EntradaInvalida(
            f"Base de contratos nao encontrada: {caminho}\n"
            f"Ela e' necessaria para resolver a UF e o tipo do contrato '{contrato}'.\n"
            f"Rode sem informar contrato para usar os padroes "
            f"({config.UF_PADRAO}/{config.TIPO_CONTRATO_PADRAO})."
        )
    # Le o JSON de contratos (chave = nome do contrato; campos uf/tipo_contrato/vigente).
    base = json.loads(caminho.read_text(encoding="utf-8"))
    # Fase 3: exige chave exata; digitacao aproximada nao vale para nao precificar o contrato errado.
    if contrato not in base:
        # Sugere chaves que compartilham o primeiro token (ex.: 'ECM'); se nada casar, mostra as 5 primeiras.
        parecidas = [c for c in base if contrato.split()[0] in c][:5] or list(base)[:5]
        raise EntradaInvalida(
            f"Contrato '{contrato}' nao encontrado na base ({len(base)} contratos).\n"
            f"Parecidos: {parecidas}"
        )
    dados = base[contrato]
    # Imprime o que foi resolvido: o usuario confere UF/tipo antes de confiar nos numeros.
    print(f"Contrato {contrato}: UF={dados['uf']}, tipo={dados['tipo_contrato']}, "
          f"vigente={dados.get('vigente', '?')}")
    # Saida: os dois parametros que o motor de custo precisa do contrato.
    return dados["uf"], dados["tipo_contrato"]


def executar(raiz, contrato=None):
    """Roda o pipeline completo a partir da raiz do projeto.

    Por que existe: separa a ORQUESTRACAO (esta funcao, testavel com tmp_path e sem
    stdin) do ponto de entrada __main__ (que pergunta o contrato e fixa o exit code).
    E' o unico lugar que converte EntradaInvalida em mensagem + codigo 1: erro de DADOS
    nao vira traceback: bug de programa continua estourando normalmente.

    Logica: Entrada (raiz, contrato) -> Fase 1: resolve UF/tipo -> Fase 2: localiza e le
    as duas planilhas -> Fase 3: junta por ODI (orfaos/tranche errada abortam aqui)
    -> Fase 4: por amostra, reduz a ODI e calcula o custo -> Fase 5: grava resumo e
    mapas -> Saida: 0 (sucesso) ou 1 (erro de entrada).
    """
    # Normaliza para Path: o chamador pode passar str (ex.: do .bat) ou Path (dos testes).
    raiz = Path(raiz)
    try:
        # Fase 1: UF (base de partida do deslocamento) e tipo (produtividade da inspecao).
        uf, tipo = _resolver_contrato(raiz, contrato)
        # Fase 2: localiza os dois arquivos por convencao de nome (D7) e le cada um.
        lote, painel = achar_entradas(raiz / "Entrada")
        print(f"Lendo amostras : {lote.name}")
        amostras = ler_amostras(lote)
        print(f"Lendo painel   : {painel.name}")
        ucs = ler_painel(painel)
        # Fase 3: juncao validada por ODI - aqui morrem tranche errada e ODI orfa com Cons>0.
        juntas = juntar_amostras_painel(amostras, ucs)
        # Fase 4: uma passada por amostra; resumo_por_odi reduz UC -> ODI, custo_por_odi precifica.
        custos = {}
        for k, df_ucs in juntas.items():
            print(f"Amostra {k}: {df_ucs['ODI'].nunique()} ODIs / {len(df_ucs)} UCs")
            custos[k] = custo_por_odi(resumo_por_odi(df_ucs), uf=uf, tipo_contrato=tipo)
        # Fase 5: garante a pasta de saida e grava os dois produtos (tabela + mapas).
        saida = raiz / "saida"
        saida.mkdir(exist_ok=True)
        # A tabela-resumo recebe o DETALHE por ODI e agrega por dentro (contrato de resumo.py).
        gravar_resumo(custos, saida / "Resumo_Custos.xlsx")
        # Um mapa por amostra: UCs (para os pontos) + custos por ODI (para o popup).
        for k, df_ucs in juntas.items():
            gravar_mapa(df_ucs, custos[k], saida / f"Mapa_Amostra_{k}.html")
        print(f"OK: saidas gravadas em {saida}")
        # Saida: sucesso.
        return 0
    except EntradaInvalida as erro:
        # Erro de DADOS (culpa da entrada): mensagem pronta para o usuario final, sem traceback.
        print(f"\nERRO DE ENTRADA:\n{erro}")
        return 1


# Ponto de entrada: raiz = a pasta acima de src/, para o .bat rodar de qualquer diretorio.
if __name__ == "__main__":
    # Pergunta interativa no estilo do sistema canonico (Enter = padroes de config).
    resposta = input(
        f"Contrato (ex.: ECM 013-A-2023; Enter = {config.UF_PADRAO}/{config.TIPO_CONTRATO_PADRAO}): "
    ).strip()
    # O exit code propaga para o _exec.ps1, que so mantem a janela aberta quando != 0.
    sys.exit(executar(Path(__file__).resolve().parent.parent, contrato=resposta or None))
