# -*- coding: utf-8 -*-
"""Fabrica de planilhas sinteticas de Entrada/ para os testes (nao depende de minhas_notas/)."""
import pandas as pd

# ODIs e coordenadas conhecidas (regiao de Belem-PA, dentro da bbox do Brasil).
ODIS = ["PA001", "PA002", "PA003", "PA004", "PA005"]

# A MESMA ODI escrita dos dois jeitos que aparecem nas planilhas reais: o Lote guarda
# TEXTO com zeros a esquerda; o Painel guarda NUMERO. Servem aos testes de normalizacao
# da chave de juncao (_norm_odi).
ODIS_LOTE_TEXTO = ["0012500186", "0012500231", "0012500370", "0012500399", "0012500453"]
ODIS_PAINEL_NUMERO = [12500186, 12500231, 12500370, 12500399, 12500453]


def escrever_lote(caminho, abas=(1, 2), odis=ODIS, municipios=None, cons=None,
                  n_estratos_leia_me=None):
    """Grava um Lote.xlsx sintetico com abas 'Amostra K' no formato do sistema amostral.

    Por que existe: os testes de io_amostras precisam de um Lote.xlsx real em disco,
    com a coluna 'Cons.' (numero de UCs da obra) e linhas nao selecionadas, sem
    depender de arquivos reais de minhas_notas/.

    Logica: Entrada (caminho, abas, odis, municipios, cons, n_estratos_leia_me) -> Fase 1:
    aplica os defaults (municipio BARCARENA, Cons=3 - obra com UC) sobre os overrides
    recebidos -> Fase 2: monta, por aba, o df com ODI/Estrato/Municipio/Cons./STATUS,
    incluindo uma linha extra NAO selecionada (que o leitor deve filtrar) -> Fase 3: se
    pedido, grava a aba 'Leia-me' no formato do upstream (e' de la que sai o numero de
    estratos da estratificacao) -> Saida: .xlsx gravado.
    """
    # Fase 1a: municipio padrao e' BARCARENA para todo ODI que o chamador nao customizar.
    muni = {odi: "BARCARENA" for odi in odis}
    if municipios:
        muni.update(municipios)
    # Fase 1b: Cons padrao e' 3 (obra com UC) para todo ODI que o chamador nao customizar.
    cns = {odi: 3 for odi in odis}
    if cons:
        cns.update(cons)
    # Fase 2: grava uma aba 'Amostra K' por numero pedido, todas com os mesmos dados.
    with pd.ExcelWriter(caminho) as xls:
        # Fase 3: 'Leia-me' no formato do upstream (Campo | Valor), quando pedido.
        if n_estratos_leia_me is not None:
            pd.DataFrame([["Metodo desta planilha", "SEM regional"],
                          ["N (estratos por grupo)", n_estratos_leia_me]],
                         columns=["Campo", "Valor"]).to_excel(
                xls, sheet_name="Leia-me", index=False)
        for k in abas:
            df = pd.DataFrame({
                "ODI": list(odis) + ["PA_NAO_SEL"],
                # Estrato ciclico 1/2/3 por ODI, mais um estrato de enfeite na linha nao selecionada.
                "Estrato": [(i % 3) + 1 for i in range(len(odis))] + [9],
                "Município": [muni[odi] for odi in odis] + ["BARCARENA"],
                # Cons.=0 na linha nao selecionada e' irrelevante (ela e' descartada pelo leitor).
                "Cons.": [cns[odi] for odi in odis] + [0],
                "STATUS": ["Selecionado"] * len(odis) + [""],
            })
            df.to_excel(xls, sheet_name=f"Amostra {k}", index=False)


def escrever_painel(caminho, odis=ODIS, ucs_por_odi=2, municipio="BARCARENA"):
    """Grava um Painel sintetico: aba com ODI/UC/MUNICIPIO/LATITUDE/LONGITUDE + uma aba de enfeite.

    Logica: Entrada (caminho, odis, ucs_por_odi, municipio) -> Fase 1: gera ucs_por_odi
    UCs por ODI com coordenadas proximas de Belem, todas no municipio informado ->
    Saida: .xlsx gravado com a aba de dados apos uma aba de enfeite.
    """
    linhas = []
    # Fase 1: gera ucs_por_odi UCs por ODI com coordenadas proximas de Belem.
    for i, odi in enumerate(odis):
        for j in range(ucs_por_odi):
            linhas.append({"ODI": odi, "UC": f"{odi}-UC{j}", "MUNICÍPIO": municipio,
                           "LATITUDE": -1.60 - i * 0.01, "LONGITUDE": -48.65 - j * 0.01})
    with pd.ExcelWriter(caminho) as xls:
        # Aba de enfeite primeiro: o leitor deve detectar a aba certa pelas colunas.
        pd.DataFrame({"qualquer": [1]}).to_excel(xls, sheet_name="Capa", index=False)
        pd.DataFrame(linhas).to_excel(xls, sheet_name="Base_UC", index=False)


def escrever_painel_anexo_v(caminho, odis=ODIS_PAINEL_NUMERO, ucs_por_odi=2, municipio="GURINHÉM"):
    """Grava um Painel no formato REAL do 'Anexo V - Painel de Monitoramento'.

    Por que existe: o Painel real e' saida do projeto irmao (monitoramentolpt_producao_enbpar)
    e difere do sintetico simples em tres pontos que ja quebraram a leitura uma vez: a aba
    'Preenchimento' tem a PRIMEIRA linha mesclada com nomes de grupo (o cabecalho de verdade
    esta na segunda), as colunas se chamam 'Numero ODI'/'Numero da Unidade Consumidora' em vez
    de ODI/UC, e a ODI e' NUMERO (enquanto no Lote e' texto com zeros a esquerda). Reproduzir
    isso numa fixture e' o que impede a regressao sem depender de dados reais (D6).

    Logica: Entrada (caminho, odis, ucs_por_odi, municipio) -> Fase 1: monta as UCs com os
    cabecalhos por extenso -> Fase 2: grava a tabela a partir da SEGUNDA linha -> Fase 3:
    escreve e mescla a faixa de grupo na primeira linha -> Saida: .xlsx gravado.
    """
    linhas = []
    # Fase 1: ucs_por_odi UCs por ODI, com os nomes de coluna exatos do Anexo V.
    for i, odi in enumerate(odis):
        for j in range(ucs_por_odi):
            linhas.append({
                "Distribuidora": "EPB",
                "Número ODI": odi,
                "Número da Unidade Consumidora": 4600000 + i * 10 + j,
                "Município": municipio,
                "UF": "PB",
                # Coordenadas na Paraiba (dentro da bbox do Brasil).
                "Latitude": -7.12 - i * 0.01,
                "Longitude": -35.35 - j * 0.01,
            })
    df = pd.DataFrame(linhas)
    with pd.ExcelWriter(caminho, engine="openpyxl") as xls:
        # Fase 2: startrow=1 deixa a primeira linha livre para a faixa de grupo.
        df.to_excel(xls, sheet_name="Preenchimento", index=False, startrow=1)
        ws = xls.sheets["Preenchimento"]
        # Fase 3: faixa mesclada por cima do cabecalho real - e' ela que faz o pandas com
        # header=0 enxergar 'Identificacao minima' + varias colunas 'Unnamed'.
        ws.cell(row=1, column=1, value="Identificação mínima")
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=5)
        ws.cell(row=1, column=6, value="Classificação geral")
        ws.merge_cells(start_row=1, start_column=6, end_row=1, end_column=len(df.columns))
