# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> `PROJECT_BUILDING.md` não é alterado (checklist do humano). O controle do projeto do humano vive aqui.
> toda a documentação estará em `planning` directory e o key document is PLAN.md

> `SistemaAmostralPython` é para consulta e não deve ser alterado, a princípio. A menos que encontre uma rota com muita economia de recursos fazendo alteração no código canônico, use-o somente como consulta. Avise antes e solicite alteração se for alterar esse código.


## O que é este repositório (leia primeiro)

Projeto de estimação dos custos de inspeção de todas as amostras geradas pelo `SistemaAmostraPython`
(o sistema amostral canônico, que vive em `minhas_notas/SistemaAmostralPython/`).

Cadeia completa do problema:

```
Lote.xlsx  ──►  SistemaAmostralPython (upstream, NÃO alterar)
                  └► saida/Estratos N - Python.xlsx
                       └► abas Amostra 1/2/3 = ODIs sorteadas por estrato
                                    │
                                    │  join pela chave ODI
                                    ▼
                Coordenadas_UCs_7ªTR_PA.xlsx (LATITUDE/LONGITUDE por ODI)
                                    │
                                    ▼
             ESTE PROJETO: distâncias/roteirização → custo de inspeção por amostra
                                    │
                       ┌────────────┴────────────┐
                       ▼                         ▼
             tabela-resumo por estrato     mapas dos pontos
```

Regras de escopo vindas do `planning/PLAN.md`:

- Cada estrato gera 3 amostras (1 principal + 2 reservas); cada amostra tem uma ODI e uma
  geolocalização correspondente.
- O executável Python dos cálculos precisa ser acessível via um arquivo `.bat`
  (mesmo padrão de duplo-clique do `SistemaAmostralPython`: `executar.bat` → `_exec.ps1` → `.venv`).
- Os mapas com os pontos das coordenadas são parte do output (originalmente feitos no QGIS).
  Sugestão de biblioteca para geolocalização: **GeoPandas**.

## Estado atual do repositório

Projeto **greenfield**: ainda não há código de aplicação, `requirements.txt`, `.venv`, testes nem
`.git` na raiz. O que existe é planejamento + insumos. Ao criar a primeira estrutura de código,
siga o layout achatado do sistema canônico (módulos na raiz + um único script executável + `.bat`),
que é o formato que o humano já sabe operar.

**Arquivos que NÃO são entradas do projeto** (não os trate como código a manter):

- `ecc_dashboard.py` — GUI TkInter de outro contexto ("Everything Claude Code"); importa
  `scripts.lib.ecc_dashboard_runtime`, que não existe aqui. Está só de leitura/referência.
- `claude resume.txt` — vazio, uso do humano.
- `planning/html-effectiveness/` — clone do repo `ThariqS/html-effectiveness` (tem `.git` próprio).
  É biblioteca de **modelos de HTML** para comunicar tarefas/planos ao humano, não código do produto.
- `minhas_notas/*.pptx` e `*.xlsx` — insumos e gabaritos visuais, não fontes.

## Governança e documentação

- `planning/PLAN.md` — **documento-chave**. Fases, decisões e pendências vivem aqui; é onde o
  progresso é registrado.
- `planning/PROJECT_BUILDING.md` — checklist do humano, **somente leitura**.
- Glossário de status usado nos dois: `x` concluído · `f` revisão futura · `a` anulado ·
  `n` não se aplica · `r` rollback (falhou) · `[ ]` pendente.
- `suporte_contexto/` — pasta para contexto de apoio/bugfix (antiga `bug_fix`).
- Documentos previstos e ainda não escritos (rastreados no `PROJECT_BUILDING.md`):
  `planning/ADVERSARIAL_REVIEW.md`, `TESTES.md`, `definition of done.md`.

## Insumos de dados (`minhas_notas/`)

| Arquivo | Papel | Esquema útil |
| --- | --- | --- |
| `Coordenadas_UCs_7ªTR_PA.xlsx` | **Canônico** — geolocalização das amostras | aba `Base_UC`: `ODI`, `MUNICÍPIO`, `UC`, `REGIONAL`, `LATITUDE`, `LONGITUDE` |
| `CalculoDistancias.xlsx` | Referência **sugerida** (não canônica) de forma de cálculo | `Planilha3`: `ODI`, `Projeto`, `Municipio`, `Localidade`, `Data_*`, `Custo_ODI`, `Tipo_Sist`, `Quant_Cons/Kits/SIGFI` · `Planilha1`/`Planilha6`: lat/long por município (IBGE) · `Grupo`: `MUNICÍPIO`, `Grupo`, `lat`, `long`, `SIGFI`, `Custo` |
| `Formulário de Ordem de Serviço Equatorial-PA 4ª Tranche...xlsx` | Referência **sugerida** de custos | abas `Custos Inspeções`, `Composição Equipes Inspeção`, `Ordem de Serviço Emissão`, `IMR` |
| `20260224_Tabela_Resumo_Estratos_Amostra.xlsx` | **Gabarito do output** (formato da tabela final) | abas `Resumo`, `Amostra2_Err_9%_Estr_{4,5,6}` — cabeçalhos em linhas deslocadas, ler com `header=None` |
| `Apresentação amostra COELBA 11a ... .pptx` | Gabarito visual — **apenas slides 3 e 4** | ignore o restante |
| `Lote.xlsx` | Entrada do sistema amostral (formato legado) | cabeçalho na **linha 3**, ODI na 1ª coluna, Grupo na col. 10, VR na última; 2 últimas linhas são rodapé |

"Canônico" = fonte de verdade. "Sugerido" = forma de cálculo de referência que pode ser
substituída por método melhor — se divergir, registre a decisão em `planning/PLAN.md`.

## Sistema upstream: `minhas_notas/SistemaAmostralPython/`

Consulta apenas (ver regra no topo). O que importa daqui para este projeto:

- Executável único: `gerar_planilhas.py` (os demais `.py` são módulos importados, sem CLI).
  Entrada `Entrada/Lote.xlsx`, saída `saida/Estratos N - Python.xlsx` para `N` em (3,4,5,6).
- Cada `.xlsx` de saída tem as abas: `Leia-me`, `Relatorio (Python)` (uma linha por estrato) e
  `Amostra 1/2/3` (obras com `STATUS = "Selecionado"`; 1 = principal, 2 e 3 = reservas).
- **`ODI` é a chave de junção** entre amostras, coordenadas e custos.
- O erro amostral é perguntado na execução: `0,05` urbano (o que os gabaritos usaram) ou
  `0,09` rural (intenção do método). O `9%` aparece nos nomes das abas do gabarito de resumo.
- O `CLAUDE.md` daquele repo detalha a matemática (SOM 1-D, `tamanho_amostra`, Neyman) e o
  princípio "equivalência com o legado em R vence simplicidade" — leia antes de mexer lá.

## Ambiente e comandos

Windows + PowerShell. Gerenciador: **`uv` (Astral)**; o sistema canônico fixa **Python 3.12**
(`.python-version`) — use a mesma versão aqui para evitar divergência de dependências.

```powershell
# ambiente (na raiz deste projeto, quando for criar o primeiro código)
uv venv --python 3.12
.venv\Scripts\activate
uv pip install <pacotes>
uv pip freeze > requirements.txt

# rodar o sistema amostral upstream (gera as amostras que este projeto precifica)
cd minhas_notas\SistemaAmostralPython
powershell -ExecutionPolicy Bypass -File .\instalar.ps1   # setup único
powershell -ExecutionPolicy Bypass -File .\_exec.ps1      # ou duplo-clique em executar.bat
```

Inspecionar planilhas sem poluir o projeto (não exige `.venv`):

```powershell
uv run --no-project --with pandas --with openpyxl python -c "import pandas as pd; x=pd.ExcelFile(r'minhas_notas\Coordenadas_UCs_7ªTR_PA.xlsx'); print(x.sheet_names)"
```

## Code development pace

- O desenvolvimentos dos módulos deve ser feito em pequenas partes para facilitar o acompanhamento e entendimento humano.
- Explica critérios de sucesso de cada fase em `definition of done.md` para humanos poderem acompanhar.,

## Documentation

- Toda função com docstring explicando, nesta ordem: por que a função existe (o problema que ela resolve / o motivo de ser função separada); a lógica do input ao output, em fases numeradas (Entrada → Fase 1 → Fase 2 → … → Saída), descrevendo o que cada bloco transforma. Além disso, toda linha de código comentada — inclusive as que parecem óbvias.

## Convenções herdadas do sistema canônico

Siga-as para que os dois códigos convivam sem atrito:

- **Formato BR** em CSV/TXT: `sep=";"`, `decimal=","`, `encoding="latin-1"`.
  Nomes de arquivo têm acento (`Coordenadas_UCs_7ªTR_PA.xlsx`) — sempre use caminhos com raw
  strings/`Path` e cuidado com o console do Windows (cp1252) ao imprimir.
- Código, docstrings e comentários em **português sem acento** (evita quebra de encoding).
- **Determinismo**: seed fixa; mesma entrada → mesma saída. Nada de aleatoriedade não semeada.
- **Limitações são explícitas, nunca silenciosas**: valide o esquema na leitura e levante erro
  (ex.: ODI sem coordenada, planilha de saída aberta no Excel) em vez de adivinhar.
- Caminhos relativos à raiz do script (`RAIZ = Path(__file__).resolve().parent`), para o `.bat`
  funcionar de qualquer diretório.

## Tests

- Always include e2e tests to cover important paths. You should always make sure that the plans include a test suite that covers the happy paths and edge cases. Your tests should be high quality and give confidence while covering most of the implementation.
- O e2e natural deste projeto: amostras de exemplo + coordenadas → tabela-resumo e mapas,
  comparados contra `20260224_Tabela_Resumo_Estratos_Amostra.xlsx`. Casos de borda a cobrir:
  ODI sem coordenada, coordenada inválida/fora do PA, estrato vazio, e as 3 amostras por estrato.
