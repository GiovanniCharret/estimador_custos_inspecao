# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> `PROJECT_BUILDING.md` não é alterado (checklist do humano). O controle do projeto do humano vive aqui.
> toda a documentação estará em `planning` directory e o key document is PLAN.md

> `SistemaAmostralPython` é para consulta e não deve ser alterado, a princípio. A menos que encontre uma rota com muita economia de recursos fazendo alteração no código canônico, use-o somente como consulta. Avise antes e solicite alteração se for alterar esse código.

> **NUNCA fazer `git push`** — o repositório permanece local; publicar no GitHub é decisão do humano. Commits locais frequentes, mensagens `feat:`/`fix:`/`test:`/`docs:`/`chore:` em português.

## O que é este repositório (leia primeiro)

Estimador dos custos de inspeção das amostras geradas pelo `SistemaAmostralPython`
(sistema amostral canônico, em `minhas_notas/SistemaAmostralPython/`, **somente consulta**).

```
Lote.xlsx  ──►  SistemaAmostralPython (upstream, NAO alterar)
                  └► abas Amostra 1/2/3 = ODIs sorteadas por estrato (STATUS="Selecionado")
                                    │
Entrada/Lote.xlsx ──────────────────┤  join pela chave ODI
Entrada/*Painel de Monitoramento*.xlsx (LATITUDE/LONGITUDE por UC)
                                    ▼
             ESTE PROJETO: geometria → horas → R$ por ODI/estrato/amostra
                                    │
                       ┌────────────┴────────────┐
                       ▼                         ▼
        saida/Resumo_Custos.xlsx      saida/Mapa_Amostra_K.html
```

Cada estrato gera 3 amostras (1 principal + 2 reservas). **`ODI` é a chave de junção**
entre amostras, coordenadas e custos; uma ODI tem N UCs (unidades consumidoras).

## Estado atual (2026-08-07)

Fases F0–F6 implementadas e commitadas; **26 testes passando**. Falta a **F7**:
`src/estimar_custos.py` (orquestrador) + `testes/test_e2e.py` + `planning/TESTES.md`.

Consequência prática: `_exec.ps1` já aponta para `src\estimar_custos.py`, que ainda **não
existe** — `executar.bat` falha até a F7 ser concluída. A interface esperada do orquestrador
(`executar(raiz, contrato=None) -> int`, resolução de UF/tipo pelo contrato, `__main__`
interativo) está especificada em `planning/PLANO_IMPLEMENTACAO.md` Task 8.

**Não são código do produto** (não trate como fontes a manter):
`ecc_dashboard.py` (GUI de outro contexto, import quebrado) · `claude resume.txt` (vazio) ·
`planning/html-effectiveness/` (clone de referência de modelos HTML, tem `.git` próprio) ·
`minhas_notas/*.xlsx`/`*.pptx` (insumos de pesquisa).

## Comandos

Windows + PowerShell. Gerenciador **`uv` (Astral)**, Python **3.12** (mesma versão do canônico).

```powershell
powershell -ExecutionPolicy Bypass -File .\instalar.ps1   # setup unico (uv + venv + deps)
.venv\Scripts\python.exe -m pytest testes -v              # suite completa
.venv\Scripts\python.exe -m pytest testes/test_custo.py -v            # um arquivo
.venv\Scripts\python.exe -m pytest testes/test_custo.py::test_custo_por_odi_formula -v  # um teste
.\executar.bat                                            # ritual de duplo-clique (pos-F7)
```

Inspecionar planilhas sem poluir o projeto (não exige `.venv`):

```powershell
uv run --no-project --with pandas --with openpyxl python -c "import pandas as pd; x=pd.ExcelFile(r'minhas_notas\Coordenadas_UCs_7ªTR_PA.xlsx'); print(x.sheet_names)"
```

Rodar o sistema amostral upstream (gera as amostras que este projeto precifica):

```powershell
cd minhas_notas\SistemaAmostralPython ; powershell -ExecutionPolicy Bypass -File .\_exec.ps1
```

## Arquitetura: o pipeline e os contratos entre módulos

Layout achatado (padrão do canônico): módulos em `src/`, um único executável, `.bat` na raiz.
Cada seta abaixo é um **contrato de dataframe** — mudar uma coluna quebra o módulo seguinte.

| Módulo | Entrada → Saída |
| --- | --- |
| `io_amostras.py` | `Entrada/` → `achar_entradas` (Lote.xlsx + 1 Painel) → `ler_amostras` `{k: df[ODI,Estrato,Municipio,Cons]}` · `ler_painel` `df[ODI,UC,Municipio,LATITUDE,LONGITUDE]` → `juntar_amostras_painel` `{k: df 1 linha por UC}` |
| `distancias.py` | df de UCs → `resumo_por_odi` → **1 linha por ODI**: `n_ucs`, `lat_centro`, `lon_centro`, `dist_interna_km` (rota vizinho-mais-próximo, determinística) |
| `config.py` | **todos** os números do modelo (G1–G5 do gate F1). Zero números mágicos fora daqui |
| `custo.py` | `custo_por_odi(df, uf, tipo_contrato)` → colunas de custo de **campo**; `agregar_por_estrato` → 1 linha por estrato + `custo_fixo_os` + linha `TOTAL` |
| `resumo.py` | `gravar_resumo({k: df por ODI}, caminho)` → `saida/Resumo_Custos.xlsx` (Leia-me + `Amostra K` agregado + `Detalhe K` por ODI). Recebe o **detalhe** e chama `agregar_por_estrato` por dentro — não passe agregados prontos |
| `mapas.py` | `gravar_mapa(df_ucs, custos, caminho)` → `saida/Mapa_Amostra_K.html` (folium, FeatureGroup por estrato). Duas granularidades no mesmo call: `df_ucs` 1 linha/UC para os marcadores, `custos` 1 linha/ODI para o popup |

Detalhes que não se deduzem lendo um arquivo só:

- **`custo.py` lê `config` na chamada, nunca no import** — é o que faz `monkeypatch.setattr(config, ...)`
  nos testes e o ajuste sem rebuild funcionarem. Não faça `from src.config import X`.
- **Custo de ODI ≠ custo de estrato.** `custo_por_odi` devolve só o campo (deslocamento + inspeção);
  o termo fixo de escritório (`HORAS_ESCRITORIO_POR_OS × tarifa_escritorio`) entra **uma vez por
  estrato** em `agregar_por_estrato`. Somar `custo_total` das ODIs ≠ total do estrato.
- **A mobilização é por MUNICÍPIO, não por ODI**: capital da UF → centroide municipal, ida e volta,
  uma vez; mais saltos entre as ODIs do município. O rateio igual entre as ODIs do município é
  **só para exibição** — o total do estrato não depende dele.
- **Regra do órfão** (`juntar_amostras_painel`): ODI sorteada sem UC no painel aborta se `Cons > 0`;
  com `Cons == 0` (obra sem UC, ex.: reforço de rede) vira pseudo-UC no centroide do município,
  com aviso. A função **coleta todos os inválidos antes de abortar** e só aplica fallbacks depois
  de a amostra inteira passar — não imprima progresso que possa ser abortado depois.
- **Interseção zero de ODIs** tem mensagem própria: é o sintoma de "Lote de uma tranche × Painel de outra".
- **`dist_interna_km` troca de significado entre níveis**: por ODI é linha reta (`resumo_por_odi`);
  no agregado por estrato é `dist_interna_corrigida_km` (já × `FATOR_RODOVIARIO`) renomeada de volta
  para `dist_interna_km`. Mesmo nome, escala diferente — não compare os dois níveis direto.
- **`custo.py` importa `_rota_vizinho_mais_proximo` (privada) de `distancias.py`**: a mesma rota gulosa
  serve o percurso entre UCs de uma ODI e os saltos entre ODIs de um município. Renomeá-la quebra `custo.py`.
- **`ler_painel` para na PRIMEIRA aba** que tenha `ODI` + `LATITUDE` + `LONGITUDE` — a ordem das abas
  do painel importa. `ler_amostras`, por outro lado, processa todas as abas `Amostra K` que existirem.
- **`Cons` é opcional no Lote**: ausente vira `0`, o que joga *toda* ODI órfã na regra do fallback
  (pseudo-UC no centroide municipal) em vez do caminho de erro. Painel incompleto passa despercebido.
- **A linha `TOTAL` soma `custo_fixo_os` de todos os estratos** (N estratos × 36h × tarifa), o que é o
  comportamento correto — o fixo é por estrato, não por amostra.
- **Memória de cálculo duplicada de propósito** no topo de `src/config.py` e `src/custo.py`: quem
  abrir qualquer um dos dois entende o custo sem ler mais nada. Mantenha as duas cópias em sincronia.

## Modelo de custo (gate F1 aprovado em 2026-08-06)

`custo_estrato = 36h × R$360 (escritório, fixo)` + `horas_de_campo × R$600/h`, onde as horas de
campo somam deslocamento (km em linha reta × `FATOR_RODOVIARIO` ÷ `VELOCIDADE_KMH`) e inspeção
(`n_ucs × HORAS_DIA_CAMPO / UCS_POR_DIA[tipo]`; LPT 30 UCs/dia, MLA 3 UCs/dia).

Decisões G1–G5 (equipe = ENGENHEIRO; diárias 0 pois a tarifa já embute; base de partida = capital
da UF do contrato; velocidade/fator rodoviário a calibrar; produtividade por tipo de contrato) estão
em `planning/PLAN.md` e derivadas em `planning/MODELO_CUSTO.md`. **Cada decisão é um parâmetro em
`config.py`** — mudar o modelo é mudar `config.py`, não `custo.py`.

`config.ARQUIVO_BASE_CONTRATOS` aponta para `minhas_notas/base_contratos.json` (113 contratos,
23 UFs; chave = nome do contrato, valores `uf`/`tipo_contrato` ∈ {LPT, MLA}/`vigente` ∈
{Andamento, Encerramento, Encerrado}) — a F7 depende dele para resolver UF e tipo a partir do
contrato informado. Dois cuidados:

- O arquivo é **untracked mas NÃO está no `.gitignore`**: um `git add -A` o commitaria. Use
  `git add` explícito, ou ignore-o antes.
- O valor é uma **string relativa**, não um `Path`. A F7 precisa resolvê-lo contra `RAIZ`
  (não contra o cwd), senão `executar.bat` quebra quando chamado de outro diretório.

## Governança e documentação

- `planning/PLAN.md` — **documento-chave**: macrofases F0–F7, decisões e pendências. Registre progresso aqui.
- `planning/DESIGN.md` (D1–D8) · `planning/MODELO_CUSTO.md` (fórmula e fontes) ·
  `planning/PLANO_IMPLEMENTACAO.md` (plano passo a passo com código de cada task) ·
  `planning/definition of done.md` (critério de aceite por fase, para o humano acompanhar).
- Cada documento de planejamento novo ganha companion HTML autocontido em `planning/html/`
  (D4, inspirado em `planning/html-effectiveness/`). Existem hoje: `DESIGN.html`,
  `MODELO_CUSTO.html`, `PLANO_IMPLEMENTACAO.html` — `PLAN.md` ainda não tem companion.
- `planning/PROJECT_BUILDING.md` — checklist do humano, **somente leitura**.
- Glossário de status: `x` concluído · `f` revisão futura · `a` anulado · `n` não se aplica ·
  `r` rollback (falhou) · `[ ]` pendente.
- `suporte_contexto/` — contexto de apoio/bugfix; **hoje vazio**. Ainda não escritos:
  `planning/ADVERSARIAL_REVIEW.md` (D8), `planning/TESTES.md`.

## Insumos: `Entrada/` (runtime) vs `minhas_notas/` (pesquisa)

O programa lê **só de `Entrada/`** — dois arquivos por convenção de nome (D7):
`Lote.xlsx` (abas `Amostra K`, coluna `STATUS`) e um `*Painel de Monitoramento*.xlsx`
(qualquer aba com `ODI` + `LATITUDE` + `LONGITUDE`; a aba é detectada pelas colunas, não pelo nome).
`Entrada/` e `saida/` estão no `.gitignore` (conterão dados reais da distribuidora).

`minhas_notas/` é material de **pesquisa**, nunca entrada de execução:

| Arquivo | Papel |
| --- | --- |
| `Coordenadas_UCs_7ªTR_PA.xlsx` | exemplo do formato de coordenadas (aba `Base_UC`) |
| `base_contratos.json` | UF/tipo/vigência por contrato — consumido pela F7 via `config` |
| `CalculoDistancias.xlsx` | referência **sugerida** de forma de cálculo (não canônica) |
| `Formulário de Ordem de Serviço Equatorial-PA 4ª Tranche...xlsx` | fonte das tarifas (aba `Custos Inspeções`) |
| `20260224_Tabela_Resumo_Estratos_Amostra.xlsx` | **gabarito do output** — cabeçalhos deslocados, ler com `header=None` |
| `Apresentação amostra COELBA 11a ....pptx` | gabarito visual — **apenas slides 3 e 4** |
| `Lote.xlsx` | entrada do sistema amostral (formato legado: cabeçalho na linha 3, 2 últimas linhas são rodapé) |

"Canônico" = fonte de verdade. "Sugerido" = referência substituível por método melhor — se
divergir, registre a decisão em `planning/PLAN.md`.

## Sistema upstream: `minhas_notas/SistemaAmostralPython/`

Consulta apenas (ver regra no topo). É um gitlink sem `.gitmodules` — `git status` mostra `m` nele;
não tente resolvê-lo como submódulo. O que importa daqui:

- Executável único `gerar_planilhas.py`: `Entrada/Lote.xlsx` → `saida/Estratos N - Python.xlsx` (N em 3..6).
- Abas de saída: `Leia-me`, `Relatorio (Python)` (uma linha por estrato), `Amostra 1/2/3`
  (obras com `STATUS = "Selecionado"`; 1 = principal, 2 e 3 = reservas).
- Erro amostral perguntado na execução: `0,05` urbano (usado nos gabaritos) ou `0,09` rural
  (intenção do método) — o `9%` aparece nos nomes de aba do gabarito de resumo.
- O `CLAUDE.md` daquele repo detalha a matemática (SOM 1-D, `tamanho_amostra`, Neyman) e o
  princípio "equivalência com o legado em R vence simplicidade" — leia antes de mexer lá.

## Code development pace

- O desenvolvimentos dos módulos deve ser feito em pequenas partes para facilitar o acompanhamento e entendimento humano.
- Explica critérios de sucesso de cada fase em `definition of done.md` para humanos poderem acompanhar.

## Documentation

- Toda função com docstring explicando, nesta ordem: por que a função existe (o problema que ela resolve / o motivo de ser função separada); a lógica do input ao output, em fases numeradas (Entrada → Fase 1 → Fase 2 → … → Saída), descrevendo o que cada bloco transforma. Além disso, toda linha de código comentada — inclusive as que parecem óbvias.

## Convenções herdadas do sistema canônico

- Código, docstrings e comentários em **português sem acento** (evita quebra de encoding).
  Nomes de arquivo de insumo têm acento — use `Path`/raw strings e cuidado com o console cp1252.
- **Formato BR** em CSV/TXT: `sep=";"`, `decimal=","`, `encoding="latin-1"`.
- **Determinismo**: mesma entrada → mesma saída (rota gulosa desempata pelo menor índice,
  `groupby(sort=False)` preserva ordem). Nada de aleatoriedade não semeada.
- **Limitações são explícitas, nunca silenciosas**: `EntradaInvalida` com mensagem pronta para o
  usuário final (erro de dados → exit 1 sem traceback); `print("AVISO: ...")` para descartes e
  fallbacks. Bug de programa continua levantando traceback normal.
- Caminhos relativos à raiz (`RAIZ = Path(__file__).resolve().parent.parent` a partir de `src/`),
  para o `.bat` funcionar de qualquer diretório.

## Tests

- **Não há `conftest.py`, `pyproject.toml` nem `pytest.ini`.** Os testes fazem `from src import ...`,
  e isso só funciona porque `src/__init__.py` e `testes/__init__.py` existem (fazem o pytest inserir a
  raiz no `sys.path`) **e** o pytest roda a partir da raiz. Não apague os `__init__.py` vazios.
- Always include e2e tests to cover important paths. You should always make sure that the plans include a test suite that covers the happy paths and edge cases. Your tests should be high quality and give confidence while covering most of the implementation.
- **Nenhum teste depende de `minhas_notas/`** (D6): `testes/fixtures.py` gera Lote/Painel sintéticos
  em `tmp_path` (`escrever_lote`, `escrever_painel`, `ODIS` na região de Belém-PA).
- Parâmetros de custo em teste: `monkeypatch.setattr(config, ...)` com valores redondos, para a
  fórmula ser conferível à mão.
- O e2e natural (F7): `Entrada/` sintética → `Resumo_Custos.xlsx` + mapas. Casos de borda a cobrir:
  ODI sem coordenada (`Cons>0` aborta, `Cons==0` vira pseudo-UC), coordenada inválida/fora da
  bbox do Brasil, interseção zero (tranche errada), estrato vazio, as 3 amostras por estrato,
  e `Resumo_Custos.xlsx` aberto no Excel (`PermissionError` → mensagem amigável).
