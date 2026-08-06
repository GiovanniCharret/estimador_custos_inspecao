# -*- coding: utf-8 -*-
"""Fabrica de planilhas sinteticas de Entrada/ para os testes (nao depende de minhas_notas/)."""
import pandas as pd

# ODIs e coordenadas conhecidas (regiao de Belem-PA, dentro da bbox do Brasil).
ODIS = ["PA001", "PA002", "PA003", "PA004", "PA005"]


def escrever_lote(caminho, abas=(1, 2), odis=ODIS, municipios=None, cons=None):
    """Grava um Lote.xlsx sintetico com abas 'Amostra K' no formato do sistema amostral.

    Por que existe: os testes de io_amostras precisam de um Lote.xlsx real em disco,
    com a coluna 'Cons.' (numero de UCs da obra) e linhas nao selecionadas, sem
    depender de arquivos reais de minhas_notas/.

    Logica: Entrada (caminho, abas, odis, municipios, cons) -> Fase 1: aplica os
    defaults (municipio BARCARENA, Cons=3 - obra com UC) sobre os overrides recebidos
    -> Fase 2: monta, por aba, o df com ODI/Estrato/Municipio/Cons./STATUS, incluindo
    uma linha extra NAO selecionada (que o leitor deve filtrar) -> Saida: .xlsx gravado.
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
