# TESTES — mapa da suíte do estimador

Atualizado em 2026-08-11 (F13 — chave de junção declarada). **Hoje são 122 testes, todos
passando** (`.venv\Scripts\python.exe -m pytest testes -q`).

> **Aviso de validade:** a tabela de cobertura abaixo está congelada na F13. As fases F14–F18
> acrescentaram testes que ela não lista — mapa sem itinerário (F14), grade equipes × prazo e
> divisão real entre equipes (F15), horas de escritório por tipo (F16), aba
> `Resumo beneficiarios` transposta (F17) e a **produtividade como terceira dimensão da grade**
> (F19: espectro inteiro de prazos com `Cabe no prazo?`, `Ocupacao` que
> nao decide se cabe, uma linha por combinacao sem duplicata; a F18 e' a fase revertida pela
> F20, e os testes dela sairam junto). Os números por arquivo
> valem como mapa de *onde procurar*, não como contagem.

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
| `test_io_amostras.py` | 29 | F2/F8/F9/F12/F13 | a **chave de junção por tipo de contrato** (ver abaixo), o erro de `Anexo V` ausente listando os arquivos presentes, descoberta de **N estratificações** na `Entrada/` (ordem, duplicata, N do Leia-me → nome → contagem), painel ausente/ambíguo, ler abas `Amostra K`, filtro `STATUS`, `Cons` ausente, bbox do Brasil, os **3 ramos da regra do órfão**, e o **formato real do Anexo V** (cabeçalho na 2ª linha, apelidos de coluna, ODI texto × numérica, município com acento) |
| `test_distancias.py` | 14 | F3/F9/F11 | haversine contra valor conhecido (Belém→Castanhal ≈ 62 km), ponto igual = 0, centroide/rota interna, ODI com 1 UC, o **roteiro encadeado** (permutação completa, município não é revisitado, km fecha com trechos + volta, determinismo, amostra vazia) e a **divisão entre equipes** (toda obra tem dono, dividir soma mais km, 1 equipe = roteiro inteiro, mais equipes que obras, determinismo) |
| `test_custo.py` | 20 | F4/F9/F10/F15/F16 | **horas de escritório por tipo de obra** (36h LPT × 24h MLA, amarradas contra a planilha fonte, sem monkeypatch), tarifa do técnico mudando com o tipo e a do engenheiro não, | fórmula da amostra com parâmetros redondos, roteiro < ida-e-volta, **fixo independente do nº de estratos**, LPT × MLA, arredondamento de dias, **dobrar a equipe (pessoas) = metade dos dias e não metade do custo**, **duas equipes rodam mais km e custam mais**, **prazo ditado pela equipe mais lenta**, detalhe com a equipe dona, a **grade equipes × prazo** (limites, ordem, monotonia do custo, linha `calculado`), o **descarte do inviável** e a prova de que ele **não roteia**, **reprodução da fórmula do benchmark**, diária diluída |
| `test_resumo.py` | 5 | F5/F9/F10/F15 | as 4 abas fixas, `Equipes` × `Pessoas por equipe` como colunas distintas, a grade casando com o `Resumo`, equipe + ordem no detalhe, Leia-me com os parâmetros vigentes, `PermissionError` → mensagem amigável |
| `test_beneficiarios.py` | 10 | F17 | leitura do domínio pelas colunas D/E (e a ausência da aba `Dominios` não sendo erro), **categoria vazia virando linha de zeros**, espaço sobrando e acento não perdendo a UC, categoria fora do domínio contada à parte com aviso, UC sem classificação, a **transposição** (categoria na linha, estratificação na coluna) e a garantia de que **nenhuma célula sai nula** — nem numa estratificação sem UC |
| `test_mapas.py` | 4 | F6/F14 | um ponto por UC (obra de 3 UCs = 3 pontos), popup com ODI/município/nº de UCs, marcador da base, amostra vazia sem ponto — e um teste da **ausência**: nada de polilinha, parada ou radio de equipes |
| `test_e2e.py` | 30 | F7/F8/F9/F10/F11/F15/F16/F17 | pipeline inteiro `Entrada/` → `saida/` (abaixo) |

## O que o e2e cobre (F7)

Caminho feliz e as bordas que o `DESIGN.md` §7 elegeu como os erros mais prováveis:

| Teste | Verifica |
| --- | --- |
| `test_e2e_feliz` | exit 0, aviso de contrato não informado, `Resumo_Custos.xlsx` + 1 mapa por estratificação |
| `test_e2e_custo_e_por_amostra_nao_por_estrato` | **o invariante central do modelo** (ver abaixo) |
| `test_e2e_varias_estratificacoes_numa_planilha_so` | Estratos 3 e 5 na `Entrada/` → 4 linhas na mesma aba `Resumo`, 2 mapas |
| `test_e2e_roteiro_encadeado_derruba_a_quilometragem` | o roteiro gravado é menor que a soma das idas-e-voltas do modelo antigo, mesmo já somando os roteiros das duas equipes do padrão |
| `test_e2e_padrao_sao_duas_equipes_independentes` | a aba `Resumo` diz 2 equipes, `Equipes` e `Pessoas por equipe` não se confundem, e as duas equipes aparecem no `Detalhe` com cada obra tendo um dono só |
| `test_e2e_aba_de_beneficiarios` | a aba sai do pipeline inteiro **transposta** (lida com `header=None, index_col=0`), com a categoria de zero ocorrências presente, zero nulos, e a soma da coluna igual a `2 × UCs` |
| `test_e2e_sem_dominios_nao_gera_a_aba` | Anexo V antigo (sem classificação) → a planilha volta a ter exatamente as 4 abas |
| `test_e2e_tipo_de_obra_muda_as_horas_de_escritorio` | contrato MLA → 24h e R$ 8.640 de fixo na aba `Resumo`, e o `Leia-me` nomeando "Geração Descentralizada" com o desdobramento das etapas |
| `test_e2e_tipo_vem_do_prefixo_do_contrato` | `ECM`→MLA e `ECO`/`ECFS`/`ECOT`→LPT, com a base **sem** o campo `tipo_contrato` — o prefixo basta |
| `test_e2e_prefixo_vence_o_cadastro_mas_avisa` | o caso real `ECM 001/2020` (cadastrado como LPT): o prefixo vence, o aviso sai, e o custo usa mesmo as 24h |
| `test_e2e_grade_de_cenarios_respeita_os_limites` | a grade fica dentro de 1–7 equipes e do teto de 20 dias, tem mais de um valor em cada eixo (é grade, não lista), o km cresce com o nº de equipes, e a linha `calculado` bate com o `Resumo` |
| `test_e2e_estratificacoes_duplicadas_avisam` | dois arquivos com o mesmo N → aviso e uma linha só |
| `test_e2e_escolha_da_amostra` | a amostra escolhida manda em `Resumo`, `Cenarios`, `Detalhe` e no mapa |
| `test_e2e_mapa_localiza_as_obras_sem_propor_itinerario` | o mapa da execução inteira tem pontos e base, e **não** tem polilinha, parada nem radio — enquanto a aba `Cenarios` da planilha continua cheia (o que saiu foi o desenho, não o cálculo) |
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
   (`Lote.xlsx`, `Estratos 4 - Python.xlsx`, ...) e o arquivo cujo nome contenha
   **`Anexo V`**, **do mesmo certame** (tranches diferentes → o programa aborta avisando).
2. Duplo-clique em `executar.bat`.
3. Informar o contrato **como está na base** (`ECO 037/2025`) — hífen no lugar da barra
   também serve. Enter usa os padrões `PA`/`LPT`. Depois, escolher a **amostra**
   (1 = principal, 2 e 3 = reservas; Enter = 1).
4. Conferir na tela: UF e tipo resolvidos, as estratificações encontradas, a aba/linha de
   cabeçalho que o Painel usou, e a linha de cada amostra (ODIs, municípios, UCs, km, dias,
   R$), mais avisos de coordenada descartada, pseudo-UC ou estratificação duplicada.
5. Conferir em `saida/`: a aba `Resumo` do `Resumo_Custos.xlsx` contra o benchmark
   `minhas_notas/Tabela_Resumo_Extratos_Amostra.xlsx`, e abrir um `Mapa_Estratos_N.html`
   no browser para ver se os pontos caem onde as obras deveriam estar — município certo,
   dentro da UF, nada no oceano. O mapa **não** desenha rota (F14): ele localiza as obras.

Sinais de que a entrada é que está errada, não o programa: `ERRO DE ENTRADA:` e `AVISO:`.
Se aparecer **traceback**, é bug do programa — a planilha nunca deve produzir um.

Ruído conhecido e inofensivo: `UserWarning: Data Validation extension is not supported`
(o openpyxl não entende as listas suspensas do Anexo V; ele só as descarta na leitura).

## O painel ambíguo — o teste que separa decisão de palpite

O gap semântico do legado (em MLA a coluna `ODI` do Lote guarda número de **UC**) poderia ser
resolvido de dois jeitos: adivinhando (tenta a ODI, se falhar tenta a UC) ou **declarando**
(a chave vem do tipo do contrato). Os dois funcionam nos dados reais — e é por isso que o
teste precisa de um caso construído.

`_painel_ambiguo` monta um Anexo V em que a ODI de uma linha é o número de UC de **outra**:

```
Linha A: ODI 7001, UC 5001, latitude -7.12
Linha B: ODI 5001, UC 9001, latitude -7.13
```

Uma obra do Lote com `ODI = 5001` casa com as **duas** — na linha B pela ODI, na linha A pela UC.
Quem adivinha casa pela primeira que funcionar e precifica a obra errada em silêncio.

Dois testes usam esse mesmo painel e o mesmo Lote, mudando só o tipo do contrato:

| Teste | `tipo_contrato` | Linha esperada |
| --- | --- | --- |
| `test_juntar_mla_casa_pela_uc_por_decisao_e_nao_por_tentativa` | `MLA` | A (`-7.12`) |
| `test_juntar_lpt_casa_pela_odi_no_mesmo_painel_ambiguo` | `LPT` | B (`-7.13`) |

E mais dois cobrem a rede de segurança: `test_juntar_avisa_quando_a_chave_declarada_falha`
(tipo declarado errado → casa pela outra coluna, **com AVISO**) e
`test_juntar_sem_contrato_informado_ainda_acha_a_chave` (usuário apertou Enter).

## Parâmetros nos testes

Os testes de custo fixam valores redondos com `monkeypatch.setattr(config, ...)`
(`FATOR_RODOVIARIO=1.0`, `VELOCIDADE_KMH=50`, tarifas 100/50) para a fórmula ser
conferível à mão. Os testes e2e usam os valores **reais** de `config.py` de propósito:
é o que faz `test_e2e_tipo_contrato_muda_o_custo` medir o efeito real de LPT × MLA.
