# TESTES — mapa da suíte do estimador

Atualizado em 2026-08-07 (F7). **38 testes, todos passando.**

Nenhum teste depende de `minhas_notas/` nem de `Entrada/` (decisão D6): as planilhas
são geradas sinteticamente em `tmp_path` por `testes/fixtures.py`. Isso é o que permite
rodar a suíte numa máquina limpa, sem os dados reais da distribuidora.

## Como rodar

```powershell
.venv\Scripts\python.exe -m pytest testes -v                  # suite completa (38)
.venv\Scripts\python.exe -m pytest testes/test_e2e.py -v      # um arquivo
.venv\Scripts\python.exe -m pytest testes -k orfao -v         # por trecho do nome
.venv\Scripts\python.exe -m pytest testes/test_custo.py::test_custo_por_odi_formula -v   # um teste
```

> **Rode sempre a partir da raiz do projeto.** Não há `conftest.py` nem `pyproject.toml`:
> o `from src import ...` funciona porque `src/__init__.py` e `testes/__init__.py` existem
> (fazem o pytest inserir a raiz no `sys.path`). Apagar esses arquivos vazios quebra a suíte.

## Cobertura por arquivo

| Arquivo | Nº | Fase | O que cobre |
| --- | --- | --- | --- |
| `test_smoke.py` | 1 | F0 | ambiente: pandas/numpy/openpyxl/folium importam |
| `test_io_amostras.py` | 14 | F2 | achar entradas (ausente/ambígua), ler abas `Amostra K`, filtro `STATUS`, `Cons` ausente, detecção da aba do painel, bbox do Brasil, e os **3 ramos da regra do órfão** |
| `test_distancias.py` | 4 | F3 | haversine contra valor conhecido (Belém→Castanhal ≈ 62 km), ponto igual = 0, centroide/rota interna, ODI com 1 UC |
| `test_custo.py` | 4 | F4 | fórmula por ODI com parâmetros redondos, rateio municipal da mobilização, LPT × MLA, agregação por estrato + fixo de OS, diária diluída |
| `test_resumo.py` | 2 | F5 | abas geradas no `.xlsx` e `PermissionError` → mensagem amigável |
| `test_mapas.py` | 1 | F6 | HTML gerado com `FeatureGroup` por estrato e popup da ODI |
| `test_e2e.py` | 12 | F7 | pipeline inteiro `Entrada/` → `saida/` (abaixo) |

## O que o e2e cobre (F7)

Caminho feliz e as bordas que o `DESIGN.md` §7 elegeu como os erros mais prováveis:

| Teste | Verifica |
| --- | --- |
| `test_e2e_feliz` | exit 0, aviso de contrato não informado, `Resumo_Custos.xlsx` + 1 mapa por amostra |
| `test_e2e_total_bate_com_detalhe_mais_fixo` | **o invariante central do modelo** (ver abaixo) |
| `test_e2e_tranche_errada` | Painel de outra tranche → exit 1 com a mensagem específica |
| `test_e2e_sem_entrada` | `Entrada/` vazia → exit 1 dizendo onde pôr o `Lote.xlsx` |
| `test_e2e_odi_orfa_com_uc_aborta` | órfão com `Cons > 0` → aborta listando as ODIs |
| `test_e2e_odi_orfa_cons_zero_vira_pseudo_uc` | órfão com `Cons == 0` → aviso + pseudo-UC, `n_ucs = 1`, pipeline completa |
| `test_e2e_resumo_aberto_no_excel` | `PermissionError` → "Feche o arquivo no Excel", exit 1 |
| `test_e2e_contrato_conhecido_usa_uf_e_tipo` | contrato da base manda sobre os padrões |
| `test_e2e_tipo_contrato_muda_o_custo` | MLA sai mais caro que LPT na MESMA amostra (prova que o tipo chega ao motor) |
| `test_e2e_contrato_desconhecido` | contrato inexistente → exit 1 sugerindo chaves parecidas |
| `test_e2e_base_de_contratos_ausente` | base faltando → erro claro, não traceback |
| `test_e2e_determinismo` | rodar duas vezes na mesma entrada dá exatamente os mesmos números |

### O invariante que quase virou bug

O `PLANO_IMPLEMENTACAO.md` (Task 8, Step 1) propunha assertar que o `TOTAL` da aba
agregada é igual à soma da aba de detalhe, com tolerância de R$ 0,05. **Isso está errado
e o teste teria falhado por R$ 38.880.**

O detalhe por ODI traz **só o custo de campo**; o custo fixo de escritório
(`36h × R$360 = R$12.960`) entra **uma vez por estrato** em `agregar_por_estrato` e não
pertence a nenhuma ODI. Na fixture (3 estratos) a diferença é exatamente `3 × 12.960`.

O teste correto, implementado, checa as três relações reais:

```
TOTAL["Custo campo (R$)"]  ==  soma do detalhe          (tolerância de arredondamento)
TOTAL["Custo fixo OS (R$)"] ==  n_estratos × 36h × R$360
TOTAL["Custo total (R$)"]  ==  campo + fixo             e  >  soma do detalhe
```

## Teste manual com dados reais (o que a suíte NÃO cobre)

A suíte inteira roda sobre planilhas sintéticas. **Nenhum arquivo real foi lido até hoje** —
a `Entrada/` está vazia. O roteiro para o humano fechar essa lacuna:

1. Copiar para `Entrada/` o `Lote.xlsx` da tranche e o `*Painel de Monitoramento*.xlsx`
   **do mesmo certame** (tranches diferentes → o programa aborta avisando).
2. Duplo-clique em `executar.bat`.
3. Informar o contrato (ex.: `ECM 013-A-2023`) ou Enter para os padrões `PA`/`LPT`.
4. Conferir na tela: UF e tipo resolvidos, contagem de ODIs/UCs por amostra, avisos de
   coordenada descartada ou pseudo-UC.
5. Conferir em `saida/`: `Resumo_Custos.xlsx` contra o gabarito
   `minhas_notas/20260224_Tabela_Resumo_Estratos_Amostra.xlsx`, e abrir um
   `Mapa_Amostra_K.html` no browser ligando/desligando as camadas de estrato.

O que provavelmente aparece primeiro com dados reais: cabeçalhos fora do previsto no
`Lote.xlsx` legado (cabeçalho na linha 3, duas linhas de rodapé) e o volume de UCs
descartadas por coordenada inválida. Ambos aparecem como `AVISO:` ou `ERRO DE ENTRADA:`,
nunca como traceback — se aparecer traceback, é bug do programa, não da planilha.

## Parâmetros nos testes

Os testes de custo fixam valores redondos com `monkeypatch.setattr(config, ...)`
(`FATOR_RODOVIARIO=1.0`, `VELOCIDADE_KMH=50`, tarifas 100/50) para a fórmula ser
conferível à mão. Os testes e2e usam os valores **reais** de `config.py` de propósito:
é o que faz `test_e2e_tipo_contrato_muda_o_custo` medir o efeito real de LPT × MLA.
