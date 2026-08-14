# -*- coding: utf-8 -*-
"""Orquestrador do estimador: le Entrada/, calcula custos e grava saida/.

Unico executavel do projeto (padrao do sistema canonico): rode via executar.bat
ou `.venv\\Scripts\\python.exe src\\estimar_custos.py`.

O pipeline inteiro em uma linha:
  Entrada/Lote.xlsx + Painel -> juncao por ODI -> geometria -> custo -> saida/
"""
from pathlib import Path
import difflib
import json
import re
import sys

# Garante que 'src' e' importavel quando rodado como script (python src/estimar_custos.py):
# sem isso o import 'from src.io_amostras import ...' falha, pois o diretorio do script
# (src/) entra no sys.path, mas a raiz do projeto - que contem o pacote src/ - nao.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.io_amostras import (EntradaInvalida, achar_entradas, ler_amostras,   # noqa: E402
                             ler_dominios, ler_painel, juntar_amostras_painel)
from src.beneficiarios import perfil_da_amostra                               # noqa: E402
from src.distancias import resumo_por_odi                                     # noqa: E402
from src.custo import custo_amostra, grade_cenarios                           # noqa: E402
from src.resumo import gravar_resumo                                          # noqa: E402
from src.mapas import gravar_mapa                                             # noqa: E402
from src import config                                                        # noqa: E402


def _chave_contrato(texto):
    """Reduz o nome de um contrato a uma chave comparavel (maiusculas, separadores unificados).

    Por que existe: o MESMO contrato aparece com separadores diferentes conforme a fonte.
    A base grafa 'ECO 037/2025' (formato do contrato), enquanto o nome do arquivo do Anexo V
    traz 'ECO 037-2025' - e e' dali que o usuario copia. Exigir a barra faz o programa recusar
    um contrato que ele tem. Normalizar os DOIS lados com esta funcao resolve sem afrouxar a
    exigencia de chave exata: continua sendo casamento 1-para-1, so que insensivel ao separador.

    Logica: Entrada (texto) -> Fase 1: tira o BOM (que o terminal do Windows cola no inicio de
    texto colado/canalizado), espacos das pontas e sobe a caixa -> Fase 2: colapsa qualquer
    corrida de espaco, hifen ou barra num unico espaco -> Saida: chave canonica.
    """
    # Fase 1: BOM fora, espacos das pontas fora, caixa alta.
    s = str(texto).replace("﻿", "").strip().upper()
    # Fase 2: hifen, barra e espacos sao o MESMO separador para efeito de comparacao.
    # (Verificado contra a base real: as 113 chaves continuam unicas apos esta reducao,
    # inclusive a unica com hifen no prefixo, 'ECFS-332/2013'.)
    return re.sub(r"[\s\-/]+", " ", s).strip()


def _tipo_pelo_prefixo(nome_do_contrato):
    """Deduz o tipo de obra do PREFIXO do contrato (regra do humano).

    Por que existe: o 'Tipo de obra' que a Ordem de Servico pede - e que decide horas de
    escritorio, produtividade da inspecao e a coluna de juncao do Anexo V - esta no proprio
    nome do contrato. A regra e' binaria e foi declarada pelo humano em 2026-08-13:
    'ECM' e' Geracao Descentralizada (MLA); qualquer outro prefixo (ECO, ECFS, ECOT, ...)
    e' Extensao de Redes (LPT).

    Por que o prefixo e nao o campo da base: a base e' cadastro e pode ter erro - foi o
    caso de 'ECM 001/2020', gravado como LPT. O nome do contrato e' o proprio documento.

    Logica: Entrada (nome do contrato) -> Fase 1: reduz a chave canonica (a mesma de
    _chave_contrato, para 'ECM-001/2020' e 'ecm 001 2020' caírem no mesmo lugar) ->
    Fase 2: compara o primeiro token com o prefixo de Geracao -> Saida: 'MLA' ou 'LPT'.
    """
    # Fase 1: mesma normalizacao do casamento de contrato (caixa alta, separadores unificados).
    chave = _chave_contrato(nome_do_contrato)
    # Fase 2: so o PRIMEIRO token conta - 'ECMX 01/2020' nao e' ECM, e 'ECM-001/2020' e'.
    primeiro = chave.split()[0] if chave.split() else ""
    if primeiro == config.PREFIXO_GERACAO_DESCENTRALIZADA:
        return "MLA"
    # Saida: todo o resto e' Extensao de Redes.
    return "LPT"


def _resolver_contrato(raiz, contrato):
    """Resolve (uf, tipo_contrato) a partir do contrato informado (decisoes G3/G5).

    Por que existe: a base de partida do deslocamento (capital da UF) e a produtividade
    da inspecao (LPT 30 UCs/dia x MLA 3 UCs/dia) dependem do contrato. Concentrar a
    resolucao aqui deixa executar() testavel sem stdin e sem base real.

    A UF vem da base (so ela tem esse dado). O TIPO vem do PREFIXO do contrato, por regra
    do humano - ver _tipo_pelo_prefixo. O campo 'tipo_contrato' da base sobrou como
    conferencia: se discordar do prefixo, sai AVISO e o prefixo vence.

    Logica: Entrada (raiz, contrato ou None) -> Fase 1: sem contrato, usa os padroes de
    config com AVISO -> Fase 2: carrega a base de contratos (caminho relativo a raiz)
    -> Fase 3: busca a chave exata; ausente = erro com sugestoes parecidas -> Fase 4:
    tipo pelo prefixo, com aviso se o cadastro discordar -> Saida: tupla (uf, tipo).
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
    # Fase 3: indexa a base pela chave canonica e busca o contrato informado pela mesma regra -
    # continua sendo casamento exato, so que 'ECO 037-2025' e 'ECO 037/2025' viram a mesma chave.
    indice = {_chave_contrato(c): c for c in base}
    procurado = _chave_contrato(contrato)
    if procurado not in indice:
        # Sugestoes por semelhanca sobre as chaves canonicas (o filtro antigo, por primeiro token
        # literal, devolvia 'ECFS...' para quem digitou 'ECO' - sugestao inutil).
        parecidas = [indice[c] for c in difflib.get_close_matches(procurado, indice, n=5, cutoff=0.5)]
        # Sem nenhuma parecida, cai no primeiro token (ex.: todas as 'ECO') e por fim nas 5 primeiras.
        if not parecidas:
            primeiro = procurado.split()[0] if procurado.split() else ""
            parecidas = [c for c in base if _chave_contrato(c).startswith(primeiro)][:5] or list(base)[:5]
        raise EntradaInvalida(
            f"Contrato '{contrato}' nao encontrado na base ({len(base)} contratos).\n"
            f"Parecidos: {parecidas}"
        )
    # Nome como esta gravado na base (pode diferir do digitado no separador).
    nome_na_base = indice[procurado]
    dados = base[nome_na_base]
    # O tipo de obra vem do PREFIXO do contrato, nao do cadastro (regra do humano). A base
    # segue sendo lida e conferida: divergencia e' erro de cadastro e sai como AVISO, para
    # o humano corrigir o JSON - escolher em silencio esconderia o defeito nos dois lados.
    tipo = _tipo_pelo_prefixo(nome_na_base)
    cadastrado = dados.get("tipo_contrato")
    # Imprime o que foi resolvido: o usuario confere UF/tipo antes de confiar nos numeros.
    print(f"Contrato {nome_na_base}: UF={dados['uf']}, tipo={tipo}, "
          f"vigente={dados.get('vigente', '?')}")
    if cadastrado and cadastrado != tipo:
        print(f"AVISO: a base de contratos diz tipo_contrato='{cadastrado}' para "
              f"{nome_na_base}, mas o prefixo do contrato indica '{tipo}'. Usando '{tipo}' "
              f"(o nome do contrato manda). Convem corrigir "
              f"{config.ARQUIVO_BASE_CONTRATOS}.")
    # Saida: os dois parametros que o motor de custo precisa do contrato.
    return dados["uf"], tipo


def executar(raiz, contrato=None, amostra=None):
    """Roda o pipeline completo a partir da raiz do projeto, para UMA amostra.

    Por que existe: separa a ORQUESTRACAO (esta funcao, testavel com tmp_path e sem
    stdin) do ponto de entrada __main__ (que pergunta contrato e amostra e fixa o exit
    code). E' o unico lugar que converte EntradaInvalida em mensagem + codigo 1: erro de
    DADOS nao vira traceback; bug de programa continua estourando normalmente.

    Por que UMA amostra: as amostras 2 e 3 sao reservas da 1. Precificar as tres juntas
    enchia o resumo de linhas que nunca sao usadas ao mesmo tempo. O usuario escolhe qual
    quer (padrao 1) e a planilha inteira - resumo, cenarios, detalhe e mapas - fala dela.

    Logica: Entrada (raiz, contrato, amostra) -> Fase 1: resolve UF/tipo -> Fase 2:
    localiza as planilhas (uma por estratificacao) e le o painel uma unica vez -> Fase 3:
    por estratificacao, junta por ODI (orfaos/tranche errada abortam aqui), precifica a
    amostra escolhida e monta os cenarios de prazo -> Fase 4: grava a planilha unica de
    resumo e um mapa por estratificacao -> Saida: 0 (sucesso) ou 1 (erro de entrada).
    """
    # Normaliza para Path: o chamador pode passar str (ex.: do .bat) ou Path (dos testes).
    raiz = Path(raiz)
    # Amostra escolhida (padrao de config quando o chamador nao decide).
    amostra = config.AMOSTRA_PADRAO if amostra is None else int(amostra)
    try:
        # Fase 1: UF (base de partida do roteiro) e tipo (produtividade da inspecao).
        uf, tipo = _resolver_contrato(raiz, contrato)
        # Fase 2: descobre TODAS as estratificacoes da pasta + o painel de coordenadas.
        lotes, painel = achar_entradas(raiz / "Entrada")
        print(f"Lendo painel   : {painel.name}")
        # O painel serve a todas as estratificacoes - lido uma vez so.
        ucs = ler_painel(painel)
        # Dominios das listas suspensas de classificacao do beneficiario: definem as COLUNAS
        # da aba 'Resumo beneficiarios'. Aba opcional - painel antigo simplesmente nao a tem.
        dominios = ler_dominios(painel)
        print(f"Estratificacoes: {', '.join(f'{n} estratos ({c.name})' for n, c in lotes)}")
        print(f"Amostra escolhida: {amostra}")
        # Fase 3: uma passada por estratificacao, precificando so a amostra escolhida.
        resultados = []
        perfis = []
        mapas = {}
        for n_estratos, caminho in lotes:
            amostras = ler_amostras(caminho)
            # A estratificacao pode nao ter a amostra pedida (Lote com menos abas):
            # avisa e segue com as outras, em vez de derrubar a execucao inteira.
            if amostra not in amostras:
                print(f"AVISO: {caminho.name} nao tem aba 'Amostra {amostra}' "
                      f"(tem {sorted(amostras)}); estratificacao ignorada.")
                continue
            # Juncao validada - aqui morrem tranche errada e ODI orfa com Cons>0. O tipo do
            # contrato entra porque ele decide COM QUAL coluna do Anexo V o 'ODI' do Lote
            # casa (LPT pela ODI, MLA pela UC - ver escolher_chave_juncao).
            # So a amostra escolhida e' juntada: as reservas nem chegam a ser processadas.
            juntas = juntar_amostras_painel({amostra: amostras[amostra]}, ucs, tipo_contrato=tipo)
            df_ucs = juntas[amostra]
            # resumo_por_odi reduz UC -> ODI; custo_amostra reparte entre as equipes,
            # roteia cada uma a partir da capital e precifica.
            odis = resumo_por_odi(df_ucs)
            numeros, roteiro = custo_amostra(odis, uf=uf, tipo_contrato=tipo)
            # Grade de combinacoes viaveis (aba Cenarios): quantas equipes x qual prazo.
            cenarios = grade_cenarios(odis, uf=uf, tipo_contrato=tipo)
            print(f"  {n_estratos} estratos: {numeros['n_odis']} ODIs, "
                  f"{numeros['n_municipios']} municipios, {numeros['n_ucs']} UCs, "
                  f"{numeros['n_equipes']:g} equipe(s), {numeros['km_roteiro']:,.0f} km, "
                  f"{numeros['dias_faturados']:g} dias -> R$ {numeros['custo_total']:,.2f}")
            # Amostra COM obras e sem nenhuma combinacao viavel: o silencio da aba
            # Cenarios seria lido como "esqueceram", entao o motivo vai para a tela.
            # Amostra vazia nao entra aqui - ali a aba vazia e' obvia, nao um mistero.
            if numeros["n_odis"] and not cenarios:
                print(f"AVISO: {n_estratos} estratos - nenhuma combinacao cabe em "
                      f"{config.MAX_DIAS_POR_EQUIPE:g} dias por equipe com ate "
                      f"{config.N_EQUIPES_MAX:g} equipes; a aba 'Cenarios' fica sem linhas "
                      f"para esta estratificacao.")
            # Perfil dos beneficiarios desta estratificacao: conta as UCs sorteadas em cada
            # categoria do dominio. Nao entra em nenhuma conta de custo - e' outra pergunta.
            perfis.append(perfil_da_amostra(df_ucs, dominios, n_estratos, amostra))
            # Guarda os numeros (para o resumo) e as UCs (para o mapa, que so as localiza).
            resultados.append({"n_estratos": n_estratos, "amostra": amostra,
                               "roteiro": roteiro, "cenarios": cenarios, **numeros})
            mapas[n_estratos] = df_ucs
        # Nenhuma estratificacao tinha a amostra pedida: erro de entrada, nao saida vazia.
        if not resultados:
            raise EntradaInvalida(
                f"Nenhuma planilha da Entrada/ tem a aba 'Amostra {amostra}'.\n"
                f"Escolha outra amostra ou confira os arquivos."
            )
        # Fase 4: garante a pasta de saida e grava os dois produtos (uma tabela + um mapa por N).
        saida = raiz / "saida"
        saida.mkdir(exist_ok=True)
        # Uma planilha so, com todas as estratificacoes lado a lado (decisao do humano na F9).
        gravar_resumo(resultados, saida / "Resumo_Custos.xlsx", perfis=perfis)
        # A capital entra no mapa como base da equipe (de onde ela parte), nao como obra.
        lat_cap, lon_cap = config.CAPITAIS_UF[uf]
        for n_estratos, df_ucs in mapas.items():
            gravar_mapa(df_ucs, lat_cap, lon_cap, saida / f"Mapa_Estratos_{n_estratos}.html")
        print(f"OK: saidas gravadas em {saida}")
        # Saida: sucesso.
        return 0
    except EntradaInvalida as erro:
        # Erro de DADOS (culpa da entrada): mensagem pronta para o usuario final, sem traceback.
        print(f"\nERRO DE ENTRADA:\n{erro}")
        return 1


def _perguntar_amostra():
    """Pergunta qual amostra precificar, insistindo ate receber algo valido.

    Por que existe: o numero da amostra entra no calculo inteiro; aceitar um lixo digitado
    e cair no padrao em silencio faria o usuario levar embora a planilha da amostra errada
    sem perceber. Como e' interativo, insistir e' melhor que abortar.

    Logica: Entrada (stdin) -> Fase 1: le a resposta; vazia = padrao -> Fase 2: aceita
    1, 2 ou 3; qualquer outra coisa reexplica e pergunta de novo -> Saida: int.
    """
    while True:
        # Fase 1: Enter aceita o padrao (amostra 1 = principal).
        resposta = input(f"Amostra a precificar [1/2/3, Enter = {config.AMOSTRA_PADRAO}]: ").strip()
        if not resposta:
            return config.AMOSTRA_PADRAO
        # Fase 2: so 1, 2 e 3 existem (1 = principal, 2 e 3 = reservas).
        if resposta in ("1", "2", "3"):
            return int(resposta)
        print("  Responda 1, 2 ou 3 (a 1 e' a amostra principal; 2 e 3 sao as reservas).")


# Ponto de entrada: raiz = a pasta acima de src/, para o .bat rodar de qualquer diretorio.
if __name__ == "__main__":
    # Perguntas interativas no estilo do sistema canonico (Enter = padroes de config).
    contrato_digitado = input(
        f"Contrato (ex.: ECM 013-A-2023; Enter = {config.UF_PADRAO}/{config.TIPO_CONTRATO_PADRAO}): "
    ).strip()
    amostra_escolhida = _perguntar_amostra()
    # O exit code propaga para o _exec.ps1, que so mantem a janela aberta quando != 0.
    sys.exit(executar(Path(__file__).resolve().parent.parent,
                      contrato=contrato_digitado or None, amostra=amostra_escolhida))
