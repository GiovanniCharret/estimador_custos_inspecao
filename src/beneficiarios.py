# -*- coding: utf-8 -*-
"""Perfil dos beneficiarios de uma amostra: quantas UCs em cada categoria do Anexo V.

Por que existe como modulo proprio: e' a UNICA parte do programa que nao fala de custo.
As duas classificacoes ('Tipo de Comunidade' e 'Enquadramento do beneficiario') nao entram
em nenhuma conta de R$, dia ou km - elas respondem a outra pergunta, "QUEM sao as pessoas
que essa amostra vai visitar". Misturar isso em custo.py faria o motor de custo carregar
colunas que ele nunca usa.
"""
from src.io_amostras import _norm


def _chave(valor):
    """Reduz um rotulo de categoria a uma forma comparavel.

    Por que existe: o MESMO rotulo chega diferente das duas pontas. Na aba 'Dominios' vem
    '11 - Rural geral / demais comunidades rurais'; na aba 'Preenchimento' vem com espaco
    sobrando no fim e, as vezes, com acentuacao digitada de outro jeito. Comparar cru
    perderia a UC, e perder em silencio e' o pior desfecho possivel numa contagem.

    Logica: Entrada (rotulo) -> Fase 1: _norm (minusculas, sem acento) -> Fase 2: colapsa
    espacos internos -> Saida: chave canonica.
    """
    # Fase 1: minusculas e sem acento, a mesma normalizacao dos cabecalhos.
    s = _norm(valor)
    # Fase 2: '1  -  Familias' e '1 - Familias' sao o mesmo rotulo.
    return " ".join(s.split())


def contar_por_dominio(df_ucs, dominios):
    """Conta as UCs da amostra em cada categoria declarada no dominio do Anexo V.

    Por que existe: a aba 'Resumo beneficiarios' precisa de uma coluna por categoria
    POSSIVEL, nao por categoria presente. Uma categoria com zero e' informacao ('a amostra
    nao pegou nenhuma familia indigena'); a coluna ausente seria ambiguidade. Por isso a
    contagem parte do dominio lido da planilha e nao dos valores encontrados.

    Cada UC entra em exatamente UMA categoria de cada classificacao (sao listas suspensas
    de escolha unica), entao a soma das colunas de um bloco e' o numero de UCs - menos as
    nao classificadas, que sao contadas a parte para a diferenca nunca ficar escondida.

    Logica: Entrada (df de UCs da amostra, dominios) -> Fase 1: indexa o dominio pela
    chave canonica -> Fase 2: conta as UCs por chave -> Fase 3: escreve uma entrada por
    categoria do dominio, zerada quando ninguem caiu nela -> Fase 4: soma o que sobrou
    fora do dominio -> Saida: (dict {rotulo: contagem}, n de UCs sem classificacao valida).
    """
    # Mapeia a classificacao interna para a coluna correspondente no df de UCs.
    colunas = {"tipo_comunidade": "TipoComunidade", "enquadramento": "Enquadramento"}
    contagens = {}
    fora_do_dominio = 0
    for interno, coluna in colunas.items():
        rotulos = dominios.get(interno, [])
        # Fase 1: do rotulo canonico de volta ao rotulo de apresentacao (o da planilha).
        indice = {_chave(r): r for r in rotulos}
        # Fase 2: quantas UCs em cada chave presente nos dados.
        presentes = {}
        if coluna in df_ucs.columns:
            for valor in df_ucs[coluna]:
                chave = _chave(valor)
                # Vazio nao e' categoria: e' UC sem classificacao (pseudo-UC, celula em branco).
                if not chave:
                    continue
                presentes[chave] = presentes.get(chave, 0) + 1
        # Fase 3: uma entrada por categoria DO DOMINIO, na ordem da planilha, zerada quando
        # ninguem caiu nela. E' aqui que "nenhuma celula pode ser null" fica garantido.
        for chave, rotulo in indice.items():
            # Os dois dominios sao listas independentes e PODEM repetir um rotulo (hoje nao
            # repetem, mas 'Assentamento rural' aparece nos dois com numeros diferentes -
            # basta um deles mudar). Sem desempate, a segunda coluna sobrescreveria a
            # primeira e o numero sairia errado EM SILENCIO, que e' o pior desfecho.
            nome = rotulo
            if nome in contagens:
                nome = f"{rotulo} ({interno})"
                print(f"AVISO: a categoria '{rotulo}' aparece nos dois dominios do Anexo V; "
                      f"a segunda virou a coluna '{nome}' para nao sobrescrever a primeira.")
            contagens[nome] = int(presentes.pop(chave, 0))
        # Sem dominio declarado (Anexo V antigo, sem a aba 'Dominios'): cai para as
        # categorias que aparecerem nos dados - degradado, mas melhor que aba vazia.
        for chave, quantidade in list(presentes.items()):
            if not rotulos:
                contagens[str(chave)] = int(quantidade)
                presentes.pop(chave)
        # Fase 4: o que sobrou existe nos dados mas nao no dominio - nao some em silencio.
        fora_do_dominio += sum(presentes.values())
    # Saida: as contagens na ordem do dominio + o que nao coube nele.
    return contagens, fora_do_dominio


def perfil_da_amostra(df_ucs, dominios, n_estratos, amostra):
    """Monta a linha da aba 'Resumo beneficiarios' de UMA estratificacao.

    Por que existe: o orquestrador nao deveria saber como a linha e' montada, e a aba tem
    de ter as MESMAS colunas em todas as linhas - inclusive quando uma estratificacao nao
    tem nenhuma UC classificada. Concentrar a montagem aqui e' o que garante isso.

    Logica: Entrada (UCs da amostra, dominios, identificacao) -> Fase 1: conta por
    categoria -> Fase 2: prefixa as colunas de identificacao -> Fase 3: avisa se alguma UC
    ficou fora do dominio -> Saida: dict pronto para virar linha de DataFrame.
    """
    # Fase 1: as contagens por categoria (ja com os zeros das categorias vazias).
    contagens, fora = contar_por_dominio(df_ucs, dominios)
    # Fase 2: identificacao primeiro, para a aba casar visualmente com a aba 'Resumo'.
    linha = {"n_estratos": n_estratos, "amostra": amostra, "n_ucs": len(df_ucs)}
    linha.update(contagens)
    # Fase 3: UC com categoria que nao existe no dominio e' erro de preenchimento do Anexo V -
    # nao entra em nenhuma coluna, entao precisa ser dita (limitacao nunca silenciosa).
    if fora:
        print(f"AVISO: {n_estratos} estratos - {fora} classificacao(oes) de beneficiario fora "
              f"da lista da aba 'Dominios'; nao entraram em nenhuma coluna da aba "
              f"'Resumo beneficiarios'.")
    # Saida: a linha completa.
    return linha
