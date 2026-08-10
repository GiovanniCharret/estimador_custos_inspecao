# TESTES — mapa da suíte do estimador

Atualizado em 2026-08-10 (F8 — primeira execução com dados reais). **48 testes, todos passando.**

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
| `test_io_amostras.py` | 20 | F2/F8 | achar entradas (ausente/ambígua), ler abas `Amostra K`, filtro `STATUS`, `Cons` ausente, detecção da aba do painel, bbox do Brasil, os **3 ramos da regra do órfão**, e o **formato real do Anexo V** (cabeçalho na 2ª linha, apelidos de coluna, ODI texto × numérica, município com acento, lote alternativo ignorado) |
| `test_distancias.py` | 4 | F3 | haversine contra valor conhecido (Belém→Castanhal ≈ 62 km), ponto igual = 0, centroide/rota interna, ODI com 1 UC |
| `test_custo.py` | 4 | F4 | fórmula por ODI com parâmetros redondos, rateio municipal da mobilização, LPT × MLA, agregação por estrato + fixo de OS, diária diluída |
| `test_resumo.py` | 2 | F5 | abas geradas no `.xlsx` e `PermissionError` → mensagem amigável |
| `test_mapas.py` | 1 | F6 | HTML gerado com `FeatureGroup` por estrato e popup da ODI |
| `test_e2e.py` | 16 | F7/F8 | pipeline inteiro `Entrada/` → `saida/` (abaixo) |

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
| `test_e2e_contrato_aceita_hifen_no_lugar_da_barra` | `ECO 037-2025` (do nome do arquivo) resolve `ECO 037/2025` (da base) |
| `test_e2e_contrato_ignora_bom_e_caixa` | BOM colado pelo terminal + caixa baixa não impedem a resolução |
| `test_e2e_painel_no_formato_anexo_v` | pipeline inteiro sobre o formato REAL do Painel (a combinação que travou a 1ª execução) |
| `test_e2e_lote_alternativo_na_entrada_gera_aviso` | `Estratos 5 - Python.xlsx` esquecido na `Entrada/` → aviso, nunca silêncio |
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

## Primeira execução com dados reais (2026-08-10)

**Feita.** Contrato `ECO 037/2025` (ENERGISA/PB, LPT, 7ª Tranche), com o `Lote.xlsx` da tranche e
o `Anexo V - Painel de Monitoramento preenchido - ECO 037-2025.xlsx`. Resultado: exit 0,
26 ODIs por amostra, 0 órfãos, 0 coordenada descartada, `Resumo_Custos.xlsx` + 3 mapas gerados.

Três coisas quebraram na primeira tentativa, todas corrigidas com teste de regressão:

| Sintoma | Causa real | Correção |
| --- | --- | --- |
| `Contrato 'ECO 037-2025' nao encontrado` | a base grafa `ECO 037/2025`; o usuário copia o nome do arquivo, com hífen | `_chave_contrato` unifica ` `, `-` e `/` nos dois lados (as 113 chaves seguem únicas) |
| `Nenhuma aba ... tem colunas ODI/LATITUDE/LONGITUDE` | a aba `Preenchimento` tem a 1ª linha **mesclada** (faixa de grupos); o cabeçalho está na 2ª | `ler_painel` testa `header=0` e `header=1` |
| (idem) | o Anexo V nomeia `Número ODI` / `Número da Unidade Consumidora` | `ALIAS_PAINEL` traduz para `odi`/`uc` |

E dois defeitos latentes que só apareceriam mais tarde, também corrigidos:

- **Chave ODI casava por sorte:** Lote guarda `'0012500186'` (texto), Painel guarda `12500186`
  (número). Só casava porque o pandas converteu a coluna inteira para `int64` — uma célula suja
  no Lote deixaria a coluna como texto, a interseção daria zero e o programa acusaria
  "tranche errada", um erro **falso**. `_norm_odi` normaliza os dois lados.
- **Município com acento de um lado só:** Lote `GURINHEM` × Painel `GURINHÉM`. A regra do órfão
  comparava só com `upper()/strip()` e acusaria "município sem nenhuma UC no Painel". Agora usa `_norm`.

Sobra uma leitura para o humano, **de modelo e não de código**: os R$ 239.799 da Amostra 1 são
~88% deslocamento (14.737 km de acesso), porque as 26 ODIs estão em 25 municípios distintos e a
decisão G3 faz **uma ida-e-volta da capital por município**, sem encadear municípios numa viagem
só. É o comportamento aprovado na F1, mas com dado real ele fica grande e visível.

## Roteiro do teste manual (para as próximas tranches)

1. Copiar para `Entrada/` o `Lote.xlsx` da tranche e o `*Painel de Monitoramento*.xlsx`
   **do mesmo certame** (tranches diferentes → o programa aborta avisando).
2. Duplo-clique em `executar.bat`.
3. Informar o contrato **como está na base** (`ECO 037/2025`) — hífen no lugar da barra
   também serve. Enter usa os padrões `PA`/`LPT`.
4. Conferir na tela: UF e tipo resolvidos, a aba/linha de cabeçalho que o Painel usou,
   contagem de ODIs/UCs por amostra, avisos de coordenada descartada, pseudo-UC ou
   lote alternativo ignorado.
5. Conferir em `saida/`: `Resumo_Custos.xlsx` contra o gabarito
   `minhas_notas/20260224_Tabela_Resumo_Estratos_Amostra.xlsx`, e abrir um
   `Mapa_Amostra_K.html` no browser ligando/desligando as camadas de estrato.

Sinais de que a entrada é que está errada, não o programa: `ERRO DE ENTRADA:` e `AVISO:`.
Se aparecer **traceback**, é bug do programa — a planilha nunca deve produzir um.

Ruído conhecido e inofensivo: `UserWarning: Data Validation extension is not supported`
(o openpyxl não entende as listas suspensas do Anexo V; ele só as descarta na leitura).

## Parâmetros nos testes

Os testes de custo fixam valores redondos com `monkeypatch.setattr(config, ...)`
(`FATOR_RODOVIARIO=1.0`, `VELOCIDADE_KMH=50`, tarifas 100/50) para a fórmula ser
conferível à mão. Os testes e2e usam os valores **reais** de `config.py` de propósito:
é o que faz `test_e2e_tipo_contrato_muda_o_custo` medir o efeito real de LPT × MLA.
