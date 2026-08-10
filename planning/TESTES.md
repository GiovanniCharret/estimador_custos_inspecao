# TESTES — mapa da suíte do estimador

Atualizado em 2026-08-10 (F11 — rotas por equipe no mapa). **82 testes, todos passando.**

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
| `test_io_amostras.py` | 25 | F2/F8/F9 | descoberta de **N estratificações** na `Entrada/` (ordem, duplicata, N do Leia-me → nome → contagem), painel ausente/ambíguo, ler abas `Amostra K`, filtro `STATUS`, `Cons` ausente, bbox do Brasil, os **3 ramos da regra do órfão**, e o **formato real do Anexo V** (cabeçalho na 2ª linha, apelidos de coluna, ODI texto × numérica, município com acento) |
| `test_distancias.py` | 14 | F3/F9/F11 | haversine contra valor conhecido (Belém→Castanhal ≈ 62 km), ponto igual = 0, centroide/rota interna, ODI com 1 UC, o **roteiro encadeado** (permutação completa, município não é revisitado, km fecha com trechos + volta, determinismo, amostra vazia) e a **divisão entre equipes** (toda obra tem dono, dividir soma mais km, 1 equipe = roteiro inteiro, mais equipes que obras, determinismo) |
| `test_custo.py` | 10 | F4/F9/F10 | fórmula da amostra com parâmetros redondos, roteiro < ida-e-volta, **fixo independente do nº de estratos**, LPT × MLA, arredondamento de dias, **dobrar a equipe = metade dos dias e não metade do custo**, **cenários de prazo**, **reprodução da fórmula do benchmark**, diária diluída |
| `test_resumo.py` | 5 | F5/F9/F10 | as 4 abas fixas, ordem por estratificação, aba `Cenarios` casando com o `Resumo`, ordem do roteiro no detalhe, Leia-me com os parâmetros vigentes, `PermissionError` → mensagem amigável |
| `test_mapas.py` | 4 | F6/F9/F11 | **radio por nº de equipes** (`GroupedLayerControl`) com o km no rótulo, uma polilinha por equipe, marcador da base, popup com equipe + ordem da parada, amostra vazia sem camada |
| `test_e2e.py` | 23 | F7/F8/F9/F10/F11 | pipeline inteiro `Entrada/` → `saida/` (abaixo) |

## O que o e2e cobre (F7)

Caminho feliz e as bordas que o `DESIGN.md` §7 elegeu como os erros mais prováveis:

| Teste | Verifica |
| --- | --- |
| `test_e2e_feliz` | exit 0, aviso de contrato não informado, `Resumo_Custos.xlsx` + 1 mapa por estratificação |
| `test_e2e_custo_e_por_amostra_nao_por_estrato` | **o invariante central do modelo** (ver abaixo) |
| `test_e2e_varias_estratificacoes_numa_planilha_so` | Estratos 3 e 5 na `Entrada/` → 4 linhas na mesma aba `Resumo`, 2 mapas |
| `test_e2e_roteiro_encadeado_derruba_a_quilometragem` | o roteiro gravado é menor que a soma das idas-e-voltas do modelo antigo |
| `test_e2e_estratificacoes_duplicadas_avisam` | dois arquivos com o mesmo N → aviso e uma linha só |
| `test_e2e_escolha_da_amostra` | a amostra escolhida manda em `Resumo`, `Cenarios`, `Detalhe` e no mapa |
| `test_e2e_mapa_oferece_os_mesmos_cenarios_de_equipe_da_planilha` | o radio do mapa cobre exatamente os nºs de equipe da aba `Cenarios` — os dois artefatos não podem oferecer opções diferentes |
| `test_e2e_amostra_inexistente` | pedir a amostra 3 num lote com abas 1 e 2 → exit 1 com mensagem |
| `test_e2e_amostra_faltando_em_uma_estratificacao` | estratificação sem a aba pedida é pulada com aviso; as outras seguem |
| `test_e2e_amostra_vazia_nao_derruba_o_pipeline` | aba `Amostra K` sem obra sorteada vira linha de zeros e zero cenários, não traceback nem "tranche errada" |
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

### O invariante central e os dois testes que o amarram

**O custo é por AMOSTRA.** O estrato não participa: ele identifica de onde a obra veio na
estratificação e sobrevive só como coluna informativa. Dois testes seguram isso:

- `test_e2e_custo_e_por_amostra_nao_por_estrato` — o fixo de escritório é o **mesmo valor
  único** em toda linha do resumo (nunca `N × 12.960`), e `total == campo + fixo`, com
  `campo == dias_faturados × equipe × jornada × tarifa`.
- `test_custo_fixo_nao_depende_do_numero_de_estratos` — a MESMA geometria com rótulos de
  estrato `[1,1,1]` e `[1,2,3]` tem de custar exatamente igual.

**E um teste amarra o motor ao benchmark da engenharia:**
`test_reproduz_a_formula_do_benchmark_da_engenharia` roda com `TAMANHO_EQUIPE = 2` e os
parâmetros reais de `config` e exige `custo == 12.960 + 9.600 × (dias + 1)`. Se alguém
reintroduzir qualquer um dos três desvios da F9 (fixo por estrato, ida-e-volta por município,
dias fracionários), esse teste cai.

> **História anterior, mantida como registro:** antes da F9 o resumo era agregado por estrato
> e existia uma armadilha famosa — somar a coluna de custo do detalhe não dava o total da
> amostra, porque o fixo entrava por estrato (diferença de R$ 38.880 na fixture de 3 estratos).
> A F9 eliminou a armadilha na raiz: não há mais agregação por estrato nem custo por ODI.

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

Sobrou uma leitura de **modelo**: os R$ 239.799 da Amostra 1 eram ~88% deslocamento (14.737 km),
porque a implementação fazia uma ida-e-volta da capital por município. Isso foi corrigido na F9
(abaixo).

## Reconstrução F9 (2026-08-10) — calibração contra o benchmark da engenharia

O humano apontou a superestimativa e forneceu o benchmark:
`minhas_notas/Tabela_Resumo_Extratos_Amostra.xlsx`, aba `Resumo` — as 3 estratificações da
PB 7ª Tranche com o custo estimado à mão. Regressão nos 3 pontos, **resíduo zero**:

```
custo = 12.960 + 9.600 × (dias + 1)      9.600 = 2 pessoas × 8h × R$600
```

Que é **exatamente** a fórmula já aprovada no `MODELO_CUSTO.md` da F1. Quem tinha desviado era
o código, em três pontos que somavam +141% na amostra real:

| Desvio | Correção | Testes que seguram |
| --- | --- | --- |
| fixo de R$12.960 por **estrato** | uma vez por **amostra** | `test_custo_fixo_nao_depende_do_numero_de_estratos`, `test_e2e_custo_e_por_amostra_nao_por_estrato` |
| ida-e-volta da capital por **município** (10.521 km) | itinerário **único** encadeado (1.529 km) | `test_roteiro_*` (5), `test_e2e_roteiro_encadeado_derruba_a_quilometragem` |
| horas fracionárias | dias inteiros + 1 de mobilização | `test_dias_arredondam_para_cima` |

Resultado com `TAMANHO_EQUIPE = 2` (para comparar maçã com maçã): −9,7% / +27,2% / −21,4% por
amostra, **−3,7% no agregado**. O erro por amostra é limite do benchmark, não do modelo — os dias
da engenharia não seguem a geometria (a amostra de 5 estratos tem a rota mais curta e ganhou mais
dias que a de 4). Em produção o parâmetro fica em **1** por decisão G1.

## Roteiro do teste manual (para as próximas tranches)

1. Copiar para `Entrada/` **todas** as planilhas de estratificação da tranche
   (`Lote.xlsx`, `Estratos 4 - Python.xlsx`, ...) e o `*Painel de Monitoramento*.xlsx`
   **do mesmo certame** (tranches diferentes → o programa aborta avisando).
2. Duplo-clique em `executar.bat`.
3. Informar o contrato **como está na base** (`ECO 037/2025`) — hífen no lugar da barra
   também serve. Enter usa os padrões `PA`/`LPT`. Depois, escolher a **amostra**
   (1 = principal, 2 e 3 = reservas; Enter = 1).
4. Conferir na tela: UF e tipo resolvidos, as estratificações encontradas, a aba/linha de
   cabeçalho que o Painel usou, e a linha de cada amostra (ODIs, municípios, UCs, km, dias,
   R$), mais avisos de coordenada descartada, pseudo-UC ou estratificação duplicada.
5. Conferir em `saida/`: a aba `Resumo` do `Resumo_Custos.xlsx` contra o benchmark
   `minhas_notas/Tabela_Resumo_Extratos_Amostra.xlsx`, e abrir um `Mapa_Estratos_N.html`
   no browser, alternando o radio "Equipes em campo" e seguindo a linha de cada equipe.
   O km no rótulo do radio mostra quanto se roda a mais ao dividir o trabalho.

Sinais de que a entrada é que está errada, não o programa: `ERRO DE ENTRADA:` e `AVISO:`.
Se aparecer **traceback**, é bug do programa — a planilha nunca deve produzir um.

Ruído conhecido e inofensivo: `UserWarning: Data Validation extension is not supported`
(o openpyxl não entende as listas suspensas do Anexo V; ele só as descarta na leitura).

## Parâmetros nos testes

Os testes de custo fixam valores redondos com `monkeypatch.setattr(config, ...)`
(`FATOR_RODOVIARIO=1.0`, `VELOCIDADE_KMH=50`, tarifas 100/50) para a fórmula ser
conferível à mão. Os testes e2e usam os valores **reais** de `config.py` de propósito:
é o que faz `test_e2e_tipo_contrato_muda_o_custo` medir o efeito real de LPT × MLA.
