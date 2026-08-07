# Estimador de Custos de Inspeção — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Estimar o custo de inspeção de cada amostra do SistemaAmostralPython, gerando tabela-resumo `.xlsx` e mapas folium `.html`, executável por duplo-clique em `.bat`.

> **Progresso (2026-08-07):** Tasks 0–7 (F0–F6) concluídas e commitadas — 26 testes passando.
> Task 8 (F7) em execução. Os checkboxes das Tasks 0–7 foram preenchidos retroativamente
> conferindo o código contra o git log (a sessão anterior foi interrompida por reboot do SO
> antes de marcar). **Onde o código difere do bloco escrito no plano, o código commitado vence** —
> as diferenças conhecidas estão listadas em "Divergências plano × código" no fim deste documento.

**Architecture:** Pipeline achatado no padrão do sistema canônico: módulos em `src/`, um único executável `src/estimar_custos.py`, entradas em `Entrada/`, saídas em `saida/`. O motor de custo (`custo.py`) tem contrato fixo e fórmula parametrizada em `config.py` — o modelo v0 deste plano será calibrado/ajustado na F1 com gate de aprovação humana.

**Tech Stack:** Python 3.12 (uv/Astral), pandas, numpy, openpyxl, folium, pytest.

## Global Constraints

- Python **3.12** fixado em `.python-version`; ambiente gerenciado por **uv**; venv em `.venv/`.
- Dependências mínimas: `pandas`, `numpy`, `openpyxl`, `folium`, `pytest`. Sem GeoPandas na v1 (haversine via numpy basta; decisão registrada no PLAN.md).
- Código, docstrings e comentários em **português sem acento**.
- **Toda função com docstring** no padrão do projeto: por que existe → lógica em fases numeradas (Entrada → Fase 1 → … → Saída). **Toda linha de código comentada**, inclusive as óbvias (CLAUDE.md).
- Erros **explícitos, nunca silenciosos**: exceção `EntradaInvalida` com mensagem para usuário final; o orquestrador imprime e sai com código 1.
- Nenhum teste depende de `minhas_notas/` (D6); fixtures sintéticas geradas pelo próprio teste em `tmp_path`.
- Caminhos sempre relativos a `RAIZ = Path(__file__).resolve().parent.parent` (o `.bat` roda de qualquer diretório).
- Parâmetros de custo **somente** em `src/config.py`, cada um com comentário de valor e fonte; zero números mágicos nas fórmulas.
- Entradas: `Entrada/Lote.xlsx` (abas `Amostra 1/2/3`, obras `STATUS = "Selecionado"`) e `Entrada/*Painel de Monitoramento*.xlsx` (D7).
- Rodar testes: `.venv\Scripts\python.exe -m pytest testes -v` (na raiz do projeto).
- Commits frequentes; mensagens `feat:`/`test:`/`docs:`/`chore:` em português. **NUNCA fazer `git push`** — o repositório permanece local; publicar no GitHub é decisão do humano.
- **Memória de cálculo para humanos**: a explicação em linguagem simples de como o custo é calculado (e por que se decidiu assim) vive DUPLICADA no topo de `src/config.py` e de `src/custo.py`, derivada do `MODELO_CUSTO.md` aprovado na F1. Quem abrir qualquer um dos dois arquivos entende o cálculo sem ler mais nada.
- Cada documento de planejamento novo ganha companion HTML em `planning/html/` (D4), autocontido, inspirado em `planning/html-effectiveness/`.

---

### Task 0: F0 — Infraestrutura do repositório

**Files:**
- Create: `.gitignore`, `.python-version`, `requirements.txt`, `src/__init__.py`, `testes/__init__.py`, `testes/test_smoke.py`, `Entrada/.gitkeep`, `saida/.gitkeep`, `instalar.ps1`, `_exec.ps1`, `executar.bat`, `planning/definition of done.md`

**Interfaces:**
- Produces: estrutura de pastas, venv 3.12 funcional, `pytest` rodando, ritual `.bat` idêntico ao canônico.

- [x] **Step 1: Inicializar git e criar .gitignore**

```powershell
git init
```

`.gitignore`:
```gitignore
.venv/
__pycache__/
*.pyc
saida/*
!saida/.gitkeep
Entrada/*
!Entrada/.gitkeep
```

(`Entrada/` e `saida/` ficam fora do git: conterão dados reais da distribuidora.)

- [x] **Step 2: Criar estrutura e arquivos de ambiente**

```powershell
New-Item -ItemType Directory -Force src, testes, Entrada, saida, planning\html
New-Item -ItemType File src\__init__.py, testes\__init__.py, Entrada\.gitkeep, saida\.gitkeep
Set-Content -Encoding utf8 .python-version "3.12"
Set-Content -Encoding utf8 requirements.txt "pandas`nnumpy`nopenpyxl`nfolium`npytest"
```

- [x] **Step 3: Criar venv e instalar dependências**

```powershell
uv venv --python 3.12
uv pip install -r requirements.txt
```

- [x] **Step 4: Teste smoke**

`testes/test_smoke.py`:
```python
# -*- coding: utf-8 -*-
"""Smoke test: garante que o ambiente e os imports base funcionam."""
def test_imports():
    # Importa as dependencias principais; falha = ambiente quebrado.
    import pandas, numpy, openpyxl, folium  # noqa: F401
```

Run: `.venv\Scripts\python.exe -m pytest testes -v` → Expected: `1 passed`.

- [x] **Step 5: Criar o ritual de execução (copiado do padrão canônico)**

`instalar.ps1`:
```powershell
# Setup unico: instala uv (se faltar), Python 3.12, cria .venv e instala dependencias.
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}
uv python install 3.12
uv venv --python 3.12
uv pip install -r requirements.txt
```

`_exec.ps1`:
```powershell
# Executa o estimador dentro da .venv; chama o setup se a venv nao existir.
Set-Location -Path $PSScriptRoot
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    powershell -ExecutionPolicy Bypass -File .\instalar.ps1
}
.\.venv\Scripts\python.exe src\estimar_custos.py
if ($LASTEXITCODE -ne 0) { Read-Host "ERRO - pressione Enter para fechar" }
```

`executar.bat`:
```bat
@echo off
powershell -ExecutionPolicy Bypass -File "%~dp0_exec.ps1"
pause
```

- [x] **Step 6: `planning/definition of done.md` inicial**

```markdown
# Definition of Done — por fase

`x` concluído · `[ ]` pendente (mesmo glossário do PLAN.md)

[ ] F0 — `pytest` passa; duplo-clique em `executar.bat` chega até a mensagem de
    "Lote nao encontrado" (comportamento correto sem entrada); repo git iniciado.
[ ] F1 — `planning/MODELO_CUSTO.md` escrito + companion HTML + APROVAÇÃO HUMANA registrada no PLAN.md.
[ ] F2 — `io_amostras` lê Lote.xlsx e Painel reais da Entrada/ sem erro (ou falha listando
    exatamente o que está errado); testes unitários passam.
[ ] F3 — distâncias validadas contra valores calculados à mão; testes passam.
[ ] F4 — custo por ODI/estrato/amostra conforme MODELO_CUSTO.md aprovado; testes passam.
[ ] F5 — saida/Resumo_Custos.xlsx no formato do gabarito; conferido pelo humano.
[ ] F6 — mapas HTML abrem no browser com camadas por estrato; conferido pelo humano.
[ ] F7 — e2e feliz + bordas passam; TESTES.md escrito; status report HTML gerado.
```

- [x] **Step 7: Commit**

```powershell
git add -A ; git commit -m "chore: F0 - infraestrutura (uv 3.12, pytest, ritual .bat, definition of done)"
```

---

### Task 1: F1 — Estudo das referências e proposta do modelo de custo (GATE HUMANO)

**Files:**
- Create: `planning/MODELO_CUSTO.md`, `planning/html/MODELO_CUSTO.html`

**Interfaces:**
- Consumes: `minhas_notas/CalculoDistancias.xlsx` (abas `CALCULO_VR`, `Grupo`, `Planilha1/6`), `minhas_notas/Formulário de Ordem de Serviço...xlsx` (abas `Custos Inspeções`, `Composição Equipes Inspeção`, `IMR`), gabarito `20260224_Tabela_Resumo_Estratos_Amostra.xlsx`.
- Produces: fórmula de custo aprovada + valores calibrados dos parâmetros de `config.py` (Task 4 consome).

- [x] **Step 1: Extrair das referências os ingredientes do custo**

Ler com pandas (via `uv run --no-project --with pandas --with openpyxl`) e documentar:
tarifas R$/hora por perfil (com/sem deslocamento) da aba `Custos Inspeções`; composição
de equipe típica; como `CalculoDistancias.xlsx` transforma distância em custo (aba
`CALCULO_VR` e `Grupo`); que grandezas o gabarito de resumo reporta por estrato.

- [x] **Step 2: Escrever `planning/MODELO_CUSTO.md`** com: (a) o que as referências fazem;
(b) o modelo v0 proposto abaixo, com cada parâmetro, valor sugerido e fonte;
(c) alternativas descartadas e por quê; (d) o que fica para v1 (ex.: diárias, pernoite);
(e) **a memória de cálculo**: um texto curto, em linguagem simples para humanos, explicando
como o custo é calculado e por que se decidiu assim — este texto será embutido literalmente
no topo de `src/config.py` e `src/custo.py` na Task 5.

Modelo v0 (ponto de partida — a calibrar neste estudo):
```
por ODI sorteado:
  dist_acesso_km = 2 * haversine(base_regional, centroide_odi) * FATOR_RODOVIARIO
  dist_interna_km = rota_vizinho_mais_proximo(ucs_do_odi)
  horas_desloc   = (dist_acesso_km + dist_interna_km) / VELOCIDADE_KMH
  horas_inspecao = n_ucs * HORAS_POR_UC
  custo_odi      = horas_desloc * TARIFA_HORA_DESLOC + horas_inspecao * TARIFA_HORA_INSP
por estrato: soma dos ODIs · por amostra: soma dos estratos
```

- [x] **Step 3: Companion HTML** `planning/html/MODELO_CUSTO.html` (estilo explicador de
pesquisa, como `14-research-feature-explainer.html`): a fórmula em diagrama, tabela de
parâmetros com fontes, perguntas abertas para o humano decidir.

- [x] **Step 4: GATE — apresentar ao humano e registrar a decisão**

Parar e pedir aprovação. Registrar no `PLAN.md` (seção Decisões) o modelo aprovado e
ajustes pedidos. **Não iniciar a Task 4 sem este registro.**

- [x] **Step 5: Commit**

```powershell
git add planning ; git commit -m "docs: F1 - modelo de custo proposto (MODELO_CUSTO.md + html)"
```

---

### Task 2: F2 — `io_amostras`: localizar entradas

**Files:**
- Create: `src/io_amostras.py`, `testes/test_io_amostras.py`

**Interfaces:**
- Produces: `EntradaInvalida(Exception)`; `achar_entradas(pasta: Path) -> tuple[Path, Path]` (caminho do Lote, caminho do Painel).

- [x] **Step 1: Testes que falham**

`testes/test_io_amostras.py`:
```python
# -*- coding: utf-8 -*-
"""Testes de localizacao dos arquivos de entrada."""
from pathlib import Path
import pytest
from src.io_amostras import achar_entradas, EntradaInvalida

def _cria(pasta, *nomes):
    # Cria arquivos vazios com os nomes dados dentro de pasta.
    for n in nomes:
        (pasta / n).write_bytes(b"")

def test_acha_lote_e_painel(tmp_path):
    # Caso feliz: um Lote.xlsx e um arquivo contendo "Painel de Monitoramento".
    _cria(tmp_path, "Lote.xlsx", "2026 Painel de Monitoramento PA.xlsx")
    lote, painel = achar_entradas(tmp_path)
    assert lote.name == "Lote.xlsx"
    assert "Painel de Monitoramento" in painel.name

def test_erro_sem_lote(tmp_path):
    # Sem Lote.xlsx: erro dizendo o que colocar na pasta.
    _cria(tmp_path, "Painel de Monitoramento.xlsx")
    with pytest.raises(EntradaInvalida, match="Lote.xlsx"):
        achar_entradas(tmp_path)

def test_erro_sem_painel(tmp_path):
    _cria(tmp_path, "Lote.xlsx")
    with pytest.raises(EntradaInvalida, match="Painel de Monitoramento"):
        achar_entradas(tmp_path)

def test_erro_dois_paineis(tmp_path):
    # Dois arquivos casando o padrao: aborta listando ambos.
    _cria(tmp_path, "Lote.xlsx", "Painel de Monitoramento A.xlsx", "Painel de Monitoramento B.xlsx")
    with pytest.raises(EntradaInvalida, match="A.xlsx"):
        achar_entradas(tmp_path)
```

- [x] **Step 2: Rodar e ver falhar**

Run: `.venv\Scripts\python.exe -m pytest testes/test_io_amostras.py -v` → Expected: FAIL (`ModuleNotFoundError` / `ImportError`).

- [x] **Step 3: Implementar**

`src/io_amostras.py`:
```python
# -*- coding: utf-8 -*-
"""Leitura e validacao das entradas do estimador (Lote de amostras + Painel de coordenadas)."""
from pathlib import Path


class EntradaInvalida(Exception):
    """Erro de entrada com mensagem pronta para o usuario final.

    Por que existe: separa erros de dados (culpa da entrada, mensagem amigavel,
    exit 1 sem traceback) de bugs do programa (traceback normal).
    """


def achar_entradas(pasta):
    """Localiza os dois arquivos de entrada dentro de Entrada/.

    Por que existe: o usuario deposita arquivos por convencao de nome (D7);
    centralizar a busca da um unico lugar para mensagens de erro claras.

    Logica: Entrada (pasta) -> Fase 1: valida Lote.xlsx -> Fase 2: procura
    *Painel de Monitoramento*.xlsx e exige exatamente 1 -> Saida: (lote, painel).
    """
    # Fase 1: o Lote.xlsx tem nome fixo; sem ele nao ha amostras a precificar.
    lote = Path(pasta) / "Lote.xlsx"
    # Se nao existe, aborta ja dizendo onde colocar o arquivo.
    if not lote.exists():
        raise EntradaInvalida(f"Lote.xlsx nao encontrado.\nColoque o arquivo com as amostras em: {pasta}\\Lote.xlsx")
    # Fase 2: o painel e localizado por nome contendo o padrao (D7), ignorando temporarios do Excel (~$).
    paineis = [p for p in Path(pasta).glob("*Painel de Monitoramento*.xlsx") if not p.name.startswith("~$")]
    # Nenhum painel: aborta explicando a convencao de nome.
    if not paineis:
        raise EntradaInvalida(f"Arquivo de coordenadas nao encontrado.\nColoque em {pasta}\\ um .xlsx cujo nome contenha 'Painel de Monitoramento'.")
    # Mais de um painel: ambiguidade — aborta listando para o usuario remover o excedente.
    if len(paineis) > 1:
        nomes = "\n  - ".join(p.name for p in paineis)
        raise EntradaInvalida(f"Mais de um Painel de Monitoramento em {pasta}:\n  - {nomes}\nDeixe apenas um.")
    # Saida: os dois caminhos validados.
    return lote, paineis[0]
```

- [x] **Step 4: Rodar e ver passar**

Run: `.venv\Scripts\python.exe -m pytest testes/test_io_amostras.py -v` → Expected: `4 passed`.

- [x] **Step 5: Commit**

```powershell
git add src testes ; git commit -m "feat: F2 - achar_entradas com validacao de nomes (io_amostras)"
```

---

### Task 3: F2 — `io_amostras`: ler amostras, ler painel e juntar por ODI

**Files:**
- Modify: `src/io_amostras.py`
- Test: `testes/test_io_amostras.py` (acrescentar), `testes/fixtures.py` (novo)

**Interfaces:**
- Consumes: `EntradaInvalida`, `achar_entradas` (Task 2).
- Produces:
  - `ler_amostras(caminho: Path) -> dict[int, pd.DataFrame]` — chave = nº da amostra (1/2/3); df com colunas `ODI` (str), `Estrato` (int), `Municipio` (str), `Cons` (int; nº de UCs da obra — 0 quando a coluna não existir no Lote); apenas `STATUS == "Selecionado"`.
  - `ler_painel(caminho: Path) -> pd.DataFrame` — colunas `ODI` (str), `UC` (str), `LATITUDE` (float), `LONGITUDE` (float); UCs com lat/long inválida removidas com aviso.
  - `juntar_amostras_painel(amostras, ucs) -> dict[int, pd.DataFrame]` — df por amostra com as UCs de cada ODI sorteada; levanta `EntradaInvalida` para órfãos com `Cons > 0` e para interseção zero.
  - `BBOX_BRASIL` — dict com limites lat/long do Brasil.

> **REGRA DO ÓRFÃO (decisão do gate F1, registrada no PLAN.md):** ODI sorteada sem
> nenhuma UC no painel: (a) se `Cons > 0` → erro `EntradaInvalida` listando os órfãos
> (comportamento original); (b) se `Cons == 0` (obra sem UC, ex.: reforço de rede) →
> AVISO impresso e fallback: gera-se para a ODI uma pseudo-UC no **centroide do
> município** (média de lat/long das UCs do mesmo município no painel; se o município
> não tem UC nenhuma no painel, aí sim é erro). A pseudo-UC leva `UC = "<ODI>-MUNICIPIO"`.
> Testes da Task 3 devem cobrir os dois ramos: órfão `Cons>0` aborta; órfão `Cons==0`
> vira 1 linha no df com o centroide municipal e conta como `n_ucs = 1` a inspecionar.

- [x] **Step 1: Fixture sintética compartilhada**

`testes/fixtures.py`:
```python
# -*- coding: utf-8 -*-
"""Fabrica de planilhas sinteticas de Entrada/ para os testes (nao depende de minhas_notas/)."""
import pandas as pd

# ODIs e coordenadas conhecidas (regiao de Belem-PA, dentro da bbox do Brasil).
ODIS = ["PA001", "PA002", "PA003", "PA004", "PA005"]

def escrever_lote(caminho, abas=(1, 2), odis=ODIS):
    """Grava um Lote.xlsx sintetico com abas 'Amostra K' no formato do sistema amostral.

    Logica: Entrada (caminho, abas) -> Fase 1: monta df com ODI/Estrato/Municipio/STATUS,
    incluindo linhas NAO selecionadas (que o leitor deve filtrar) -> Saida: .xlsx gravado.
    """
    # Fase 1: duas linhas por ODI — uma Selecionado, uma nao (o leitor filtra).
    with pd.ExcelWriter(caminho) as xls:
        for k in abas:
            df = pd.DataFrame({
                "ODI": odis + ["PA_NAO_SEL"],
                "Estrato": [1, 1, 2, 2, 3, 3],
                "Município": ["BARCARENA"] * 6,
                "STATUS": ["Selecionado"] * 5 + [""],
            })
            df.to_excel(xls, sheet_name=f"Amostra {k}", index=False)

def escrever_painel(caminho, odis=ODIS, ucs_por_odi=2):
    """Grava um Painel sintetico: aba com ODI/UC/LATITUDE/LONGITUDE + uma aba de enfeite."""
    linhas = []
    # Fase 1: gera ucs_por_odi UCs por ODI com coordenadas proximas de Belem.
    for i, odi in enumerate(odis):
        for j in range(ucs_por_odi):
            linhas.append({"ODI": odi, "UC": f"{odi}-UC{j}", "MUNICÍPIO": "BARCARENA",
                           "LATITUDE": -1.60 - i * 0.01, "LONGITUDE": -48.65 - j * 0.01})
    with pd.ExcelWriter(caminho) as xls:
        # Aba de enfeite primeiro: o leitor deve detectar a aba certa pelas colunas.
        pd.DataFrame({"qualquer": [1]}).to_excel(xls, sheet_name="Capa", index=False)
        pd.DataFrame(linhas).to_excel(xls, sheet_name="Base_UC", index=False)
```

- [x] **Step 2: Testes que falham** (acrescentar a `testes/test_io_amostras.py`)

```python
import pandas as pd
from src.io_amostras import ler_amostras, ler_painel, juntar_amostras_painel
from testes.fixtures import escrever_lote, escrever_painel, ODIS

def test_ler_amostras_filtra_selecionado(tmp_path):
    escrever_lote(tmp_path / "Lote.xlsx", abas=(1, 2))
    amostras = ler_amostras(tmp_path / "Lote.xlsx")
    assert set(amostras) == {1, 2}                      # uma entrada por aba existente
    assert len(amostras[1]) == 5                        # linha nao-selecionada filtrada
    assert list(amostras[1].columns) == ["ODI", "Estrato", "Municipio"]

def test_ler_amostras_sem_aba_amostra(tmp_path):
    # Lote sem nenhuma aba 'Amostra K': erro claro.
    pd.DataFrame({"x": [1]}).to_excel(tmp_path / "Lote.xlsx", sheet_name="Outra", index=False)
    with pytest.raises(EntradaInvalida, match="Amostra"):
        ler_amostras(tmp_path / "Lote.xlsx")

def test_ler_painel_detecta_aba_e_descarta_invalidas(tmp_path):
    escrever_painel(tmp_path / "Painel de Monitoramento.xlsx")
    ucs = ler_painel(tmp_path / "Painel de Monitoramento.xlsx")
    assert {"ODI", "UC", "LATITUDE", "LONGITUDE"} <= set(ucs.columns)
    assert len(ucs) == 10                               # 5 ODIs x 2 UCs

def test_ler_painel_reporta_coordenada_fora_do_brasil(tmp_path):
    escrever_painel(tmp_path / "Painel de Monitoramento.xlsx")
    # Corrompe uma UC com longitude positiva (fora da bbox do Brasil).
    df = pd.read_excel(tmp_path / "Painel de Monitoramento.xlsx", sheet_name="Base_UC")
    df.loc[0, "LONGITUDE"] = 48.65
    with pd.ExcelWriter(tmp_path / "Painel de Monitoramento.xlsx") as xls:
        df.to_excel(xls, sheet_name="Base_UC", index=False)
    ucs = ler_painel(tmp_path / "Painel de Monitoramento.xlsx")
    assert len(ucs) == 9                                # UC invalida removida (com aviso impresso)

def test_juntar_erro_odi_orfao(tmp_path):
    escrever_lote(tmp_path / "Lote.xlsx", abas=(1,))
    escrever_painel(tmp_path / "Painel.xlsx", odis=ODIS[:3])   # faltam PA004/PA005
    amostras = ler_amostras(tmp_path / "Lote.xlsx")
    ucs = ler_painel(tmp_path / "Painel.xlsx")
    with pytest.raises(EntradaInvalida, match="PA004"):
        juntar_amostras_painel(amostras, ucs)

def test_juntar_erro_intersecao_zero(tmp_path):
    escrever_lote(tmp_path / "Lote.xlsx", abas=(1,))
    escrever_painel(tmp_path / "Painel.xlsx", odis=["TO900", "TO901", "TO902", "TO903", "TO904"])
    amostras = ler_amostras(tmp_path / "Lote.xlsx")
    ucs = ler_painel(tmp_path / "Painel.xlsx")
    with pytest.raises(EntradaInvalida, match="tranche"):
        juntar_amostras_painel(amostras, ucs)
```

- [x] **Step 3: Rodar e ver falhar** — Run: `.venv\Scripts\python.exe -m pytest testes/test_io_amostras.py -v` → Expected: FAIL (`ImportError: ler_amostras`).

- [x] **Step 4: Implementar** (acrescentar a `src/io_amostras.py`)

```python
import re
import pandas as pd

# Bounding box aproximada do Brasil: coordenada fora daqui e' erro de digitacao/projecao.
BBOX_BRASIL = {"lat_min": -34.0, "lat_max": 5.5, "lon_min": -74.0, "lon_max": -34.0}

def _norm(nome):
    """Normaliza nome de coluna (minusculas, sem acento) para deteccao robusta."""
    # Traduz acentos comuns e baixa a caixa; suficiente para os cabecalhos reais.
    tabela = str.maketrans("áàâãéêíóôõúç", "aaaaeeiooouc")
    return str(nome).strip().lower().translate(tabela)

def ler_amostras(caminho):
    """Le as abas 'Amostra K' do Lote.xlsx e devolve so as obras selecionadas.

    Por que existe: o Lote.xlsx traz TODAS as obras com coluna STATUS; o estimador
    so precifica as sorteadas. Isolar a leitura permite validar o formato num lugar so.

    Logica: Entrada (caminho) -> Fase 1: lista abas 'Amostra K' -> Fase 2: por aba,
    filtra STATUS=='Selecionado' e projeta ODI/Estrato/Municipio -> Saida: dict {k: df}.
    """
    # Fase 1: abre o workbook e localiza abas cujo nome casa 'Amostra <numero>'.
    xls = pd.ExcelFile(caminho)
    abas = {int(m.group(1)): a for a in xls.sheet_names if (m := re.fullmatch(r"Amostra\s*(\d+)", a.strip()))}
    # Sem nenhuma aba de amostra: o arquivo nao e' o esperado — erro claro.
    if not abas:
        raise EntradaInvalida(f"Nenhuma aba 'Amostra 1/2/3' em {caminho.name}.\nAbas encontradas: {xls.sheet_names}")
    resultado = {}
    # Fase 2: processa cada aba de amostra existente (processa as que existirem — D7).
    for k, aba in sorted(abas.items()):
        df = xls.parse(aba)
        # Normaliza os nomes de coluna para achar ODI/Estrato/Municipio/STATUS com robustez.
        colmap = {_norm(c): c for c in df.columns}
        # Valida colunas obrigatorias; lista as ausentes na mensagem.
        faltam = [c for c in ("odi", "estrato", "status") if c not in colmap]
        if faltam:
            raise EntradaInvalida(f"Aba '{aba}' sem colunas obrigatorias: {faltam}.\nColunas: {list(df.columns)}")
        # Filtra apenas as obras sorteadas (STATUS == 'Selecionado').
        sel = df[df[colmap["status"]].astype(str).str.strip() == "Selecionado"]
        # Projeta e renomeia para o contrato interno (ODI como str preserva zeros a esquerda).
        resultado[k] = pd.DataFrame({
            "ODI": sel[colmap["odi"]].astype(str).str.strip(),
            "Estrato": sel[colmap["estrato"]].astype(int),
            "Municipio": sel[colmap["municipio"]].astype(str).str.strip() if "municipio" in colmap else "",
        }).reset_index(drop=True)
    # Saida: uma entrada por aba de amostra encontrada.
    return resultado

def ler_painel(caminho):
    """Le o Painel de Monitoramento e devolve as UCs geolocalizadas.

    Por que existe: o painel real tem varias abas; detectar a aba certa pelas colunas
    (ODI + latitude + longitude) evita depender do nome da aba, que varia entre tranches.

    Logica: Entrada (caminho) -> Fase 1: acha a primeira aba com as colunas necessarias
    -> Fase 2: projeta ODI/UC/lat/long -> Fase 3: descarta coordenadas invalidas com
    aviso -> Saida: df de UCs validas.
    """
    xls = pd.ExcelFile(caminho)
    # Fase 1: varre as abas procurando uma que tenha ODI, latitude e longitude.
    for aba in xls.sheet_names:
        df = xls.parse(aba)
        colmap = {_norm(c): c for c in df.columns}
        if {"odi", "latitude", "longitude"} <= set(colmap):
            break
    else:
        raise EntradaInvalida(f"Nenhuma aba de {caminho.name} tem colunas ODI/LATITUDE/LONGITUDE.")
    # Fase 2: projeta para o contrato interno; UC pode nao existir (usa o indice como id).
    ucs = pd.DataFrame({
        "ODI": df[colmap["odi"]].astype(str).str.strip(),
        "UC": df[colmap["uc"]].astype(str).str.strip() if "uc" in colmap else df.index.astype(str),
        "LATITUDE": pd.to_numeric(df[colmap["latitude"]], errors="coerce"),
        "LONGITUDE": pd.to_numeric(df[colmap["longitude"]], errors="coerce"),
    })
    # Fase 3: marca invalidas — NaN, zero exato ou fora da bounding box do Brasil.
    b = BBOX_BRASIL
    validas = (ucs["LATITUDE"].between(b["lat_min"], b["lat_max"])
               & ucs["LONGITUDE"].between(b["lon_min"], b["lon_max"])
               & (ucs["LATITUDE"] != 0) & (ucs["LONGITUDE"] != 0))
    # Reporta as descartadas (limitacao explicita, nunca silenciosa).
    if (~validas).any():
        print(f"AVISO: {(~validas).sum()} UC(s) com coordenada invalida descartada(s) de {caminho.name}.")
    # Saida: somente UCs com coordenada valida.
    return ucs[validas].reset_index(drop=True)

def juntar_amostras_painel(amostras, ucs):
    """Junta cada amostra com as UCs do painel pela chave ODI, validando o casamento.

    Por que existe: e' o detector do erro 'amostra de uma tranche x painel de outra'
    (intersecao zero) e de ODIs orfaos — os dois erros de dados mais provaveis.

    Logica: Entrada (amostras, ucs) -> Fase 1: intersecao global de ODIs (zero = tranche
    errada) -> Fase 2: por amostra, lista ODIs sem UC valida -> Fase 3: merge por ODI
    -> Saida: dict {k: df} com uma linha por UC de ODI sorteada.
    """
    # Fase 1: intersecao zero indica arquivos de tranches diferentes — mensagem especifica.
    odis_painel = set(ucs["ODI"])
    odis_amostras = set().union(*[set(df["ODI"]) for df in amostras.values()])
    if not odis_amostras & odis_painel:
        raise EntradaInvalida(
            "Nenhuma ODI das amostras existe no Painel: os arquivos parecem ser de "
            "tranche/UF diferentes.\nConfira se Lote.xlsx e o Painel sao do MESMO certame."
        )
    juntas = {}
    for k, df in amostras.items():
        # Fase 2: ODIs sorteadas sem nenhuma UC no painel = orfaos; aborta listando.
        orfaos = sorted(set(df["ODI"]) - odis_painel)
        if orfaos:
            mostra = ", ".join(orfaos[:10]) + ("..." if len(orfaos) > 10 else "")
            raise EntradaInvalida(f"Amostra {k}: {len(orfaos)} ODI(s) sem coordenada no Painel: {mostra}")
        # Fase 3: merge 1-para-N (cada ODI tem varias UCs).
        juntas[k] = df.merge(ucs, on="ODI", how="left")
    # Saida: amostras enriquecidas com as UCs geolocalizadas.
    return juntas
```

- [x] **Step 5: Rodar e ver passar** — Run: `.venv\Scripts\python.exe -m pytest testes -v` → Expected: todos passam.

- [x] **Step 6: Commit**

```powershell
git add src testes ; git commit -m "feat: F2 - leitura de amostras/painel e juncao por ODI com validacoes"
```

---

### Task 4: F3 — `distancias`: haversine, centroides, dispersão e rota interna

**Files:**
- Create: `src/distancias.py`, `testes/test_distancias.py`

**Interfaces:**
- Consumes: df de UCs por amostra (Task 3).
- Produces:
  - `haversine_km(lat1, lon1, lat2, lon2) -> float | np.ndarray` — distância geodésica em km (vetorizável).
  - `resumo_por_odi(df_ucs: pd.DataFrame) -> pd.DataFrame` — uma linha por ODI: `ODI`, `Estrato`, `Municipio`, `n_ucs`, `lat_centro`, `lon_centro`, `dist_interna_km` (rota vizinho-mais-próximo pelas UCs, determinística).

- [x] **Step 1: Testes que falham**

`testes/test_distancias.py`:
```python
# -*- coding: utf-8 -*-
"""Testes de geometria: valores conferidos a mao/na calculadora geodesica."""
import pandas as pd
import pytest
from src.distancias import haversine_km, resumo_por_odi

def test_haversine_valor_conhecido():
    # Belem (-1.4558, -48.4902) -> Castanhal (-1.2939, -47.9264): ~62.4 km em linha reta.
    d = haversine_km(-1.4558, -48.4902, -1.2939, -47.9264)
    assert d == pytest.approx(62.4, abs=1.5)

def test_haversine_zero():
    # Mesmo ponto: distancia zero.
    assert haversine_km(-1.5, -48.5, -1.5, -48.5) == pytest.approx(0.0, abs=1e-9)

def test_resumo_por_odi():
    # 1 ODI com 3 UCs em linha (0.01 grau de lat ~ 1.11 km entre vizinhas).
    df = pd.DataFrame({
        "ODI": ["A"] * 3, "Estrato": [1] * 3, "Municipio": ["X"] * 3,
        "UC": ["u1", "u2", "u3"],
        "LATITUDE": [-1.60, -1.61, -1.62], "LONGITUDE": [-48.65] * 3,
    })
    r = resumo_por_odi(df)
    assert len(r) == 1 and r.loc[0, "n_ucs"] == 3
    assert r.loc[0, "lat_centro"] == pytest.approx(-1.61)
    # Rota u1->u2->u3 = ~2.22 km (2 x 1.11).
    assert r.loc[0, "dist_interna_km"] == pytest.approx(2.22, abs=0.05)

def test_resumo_odi_uma_uc_dist_zero():
    # ODI com 1 UC: sem percurso interno.
    df = pd.DataFrame({"ODI": ["A"], "Estrato": [1], "Municipio": ["X"], "UC": ["u1"],
                       "LATITUDE": [-1.6], "LONGITUDE": [-48.65]})
    assert resumo_por_odi(df).loc[0, "dist_interna_km"] == 0.0
```

- [x] **Step 2: Rodar e ver falhar** — Expected: `ModuleNotFoundError: src.distancias`.

- [x] **Step 3: Implementar**

`src/distancias.py`:
```python
# -*- coding: utf-8 -*-
"""Geometria do estimador: distancias geodesicas, centroides e percurso interno por ODI."""
import numpy as np
import pandas as pd

# Raio medio da Terra em km (esfera equivalente) — constante da formula de haversine.
RAIO_TERRA_KM = 6371.0088

def haversine_km(lat1, lon1, lat2, lon2):
    """Distancia geodesica (grande circulo) entre dois pontos, em km.

    Por que existe: todo o modelo de custo se apoia em distancias; concentrar a formula
    aqui permite valida-la uma unica vez contra valores conhecidos.

    Logica: Entrada (graus) -> Fase 1: converte para radianos -> Fase 2: formula de
    haversine -> Saida: km (float ou array, e' vetorizada via numpy).
    """
    # Fase 1: graus -> radianos (numpy aceita escalares e arrays).
    la1, lo1, la2, lo2 = map(np.radians, (lat1, lon1, lat2, lon2))
    # Fase 2: formula de haversine sobre as diferencas.
    dlat = la2 - la1
    dlon = lo2 - lo1
    a = np.sin(dlat / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin(dlon / 2) ** 2
    # Saida: arco * raio da Terra = distancia em km.
    return float(2 * RAIO_TERRA_KM * np.arcsin(np.sqrt(a))) if np.isscalar(lat1) else 2 * RAIO_TERRA_KM * np.arcsin(np.sqrt(a))

def _rota_vizinho_mais_proximo(lats, lons):
    """Percurso guloso pelas UCs: sempre vai a UC nao visitada mais proxima.

    Por que existe: aproxima o deslocamento interno do inspetor dentro do ODI sem
    resolver TSP; deterministico (comeca na primeira UC na ordem de entrada).

    Logica: Entrada (arrays lat/lon) -> Fase 1: parte do indice 0 -> Fase 2: repete
    'vai ao mais proximo' ate visitar todos -> Saida: soma dos trechos em km.
    """
    # Fase 1: menos de 2 pontos nao tem percurso.
    n = len(lats)
    if n < 2:
        return 0.0
    # Estado: conjunto de nao-visitados e posicao atual (indice 0 = primeira UC).
    restam = set(range(1, n))
    atual = 0
    total = 0.0
    # Fase 2: passo guloso ate esgotar os pontos.
    while restam:
        # Distancia da posicao atual a todos os que restam.
        dists = {j: haversine_km(lats[atual], lons[atual], lats[j], lons[j]) for j in restam}
        # Escolhe o mais proximo (desempate pelo menor indice, para determinismo).
        prox = min(dists, key=lambda j: (dists[j], j))
        total += dists[prox]
        restam.remove(prox)
        atual = prox
    # Saida: km totais do percurso guloso.
    return total

def resumo_por_odi(df_ucs):
    """Reduz o df de UCs a uma linha por ODI com centroide e percurso interno.

    Por que existe: o custo e' calculado por ODI; esta funcao faz a ponte entre a
    granularidade UC (entrada) e ODI (modelo de custo).

    Logica: Entrada (df com ODI/Estrato/Municipio/UC/lat/long) -> Fase 1: agrupa por
    ODI -> Fase 2: centroide (media simples) e rota interna -> Saida: df por ODI.
    """
    linhas = []
    # Fase 1: um grupo por ODI, preservando a ordem de entrada (determinismo).
    for odi, g in df_ucs.groupby("ODI", sort=False):
        # Fase 2: centroide = media das coordenadas; rota = guloso sobre as UCs do grupo.
        linhas.append({
            "ODI": odi,
            "Estrato": int(g["Estrato"].iloc[0]),
            "Municipio": g["Municipio"].iloc[0],
            "n_ucs": len(g),
            "lat_centro": float(g["LATITUDE"].mean()),
            "lon_centro": float(g["LONGITUDE"].mean()),
            "dist_interna_km": _rota_vizinho_mais_proximo(g["LATITUDE"].to_numpy(), g["LONGITUDE"].to_numpy()),
        })
    # Saida: uma linha por ODI, pronta para o motor de custo.
    return pd.DataFrame(linhas)
```

- [x] **Step 4: Rodar e ver passar** — Run: `.venv\Scripts\python.exe -m pytest testes/test_distancias.py -v` → Expected: `4 passed`.

- [x] **Step 5: Commit**

```powershell
git add src testes ; git commit -m "feat: F3 - haversine, centroides e rota interna por ODI (distancias)"
```

---

### Task 5: F4 — `config.py` + `custo.py` (modelo aprovado na F1)

> **GATE APROVADO (2026-08-06, ver PLAN.md):** modelo de `MODELO_CUSTO.md` com as decisões
> G1–G5. Fórmula de preço decifrada do órgão: `custo = CUSTO_FIXO_OS + tarifa_campo × horas
> de campo` (12.960 = 36h×360 de escritório por OS; 600/h de campo ⇔ 4.800/equipe-dia).
> Geometria: mobilização POR MUNICÍPIO (capital → centroide do município, ida e volta, UMA
> vez) + saltos entre ODIs do município + rota interna às UCs — NÃO ida-e-volta por ODI.
> **Cada decisão do gate é um parâmetro em `config.py` — ajustes futuros sem rebuild.**

**Files:**
- Create: `src/config.py`, `src/custo.py`, `testes/test_custo.py`

**Interfaces:**
- Consumes: `resumo_por_odi` (Task 4), `haversine_km`, `_rota_vizinho_mais_proximo` (Task 4).
- Produces:
  - `src/config.py` — parâmetros: `PERFIL_EQUIPE`, `TARIFAS_HORA` (por perfil, campo/escritório), `CUSTO_DIARIA`, `HORAS_DIA_CAMPO`, `HORAS_ESCRITORIO_POR_OS`, `UCS_POR_DIA` (LPT/MLA), `TIPO_CONTRATO_PADRAO`, `FATOR_RODOVIARIO`, `VELOCIDADE_KMH`, `CAPITAIS_UF` (23 UFs), `UF_PADRAO`, `ARQUIVO_BASE_CONTRATOS`.
  - `tarifa_campo() -> float` / `tarifa_escritorio() -> float` — tarifas do perfil ativo (campo soma `CUSTO_DIARIA/HORAS_DIA_CAMPO`).
  - `custo_por_odi(df_odis: pd.DataFrame, uf: str, tipo_contrato: str) -> pd.DataFrame` — acrescenta `dist_acesso_km` (rateio municipal: mobilização + saltos), `dist_interna_corrigida_km`, `horas_desloc`, `horas_inspecao`, `custo_desloc`, `custo_insp`, `custo_total` (só campo; o fixo entra por estrato).
  - `agregar_por_estrato(df_custos: pd.DataFrame) -> pd.DataFrame` — uma linha por estrato somando ODIs + `equipe_dias` + `custo_fixo_os` (uma vez por estrato) + linha `TOTAL`.

- [x] **Step 1: Testes que falham**

`testes/test_custo.py`:
```python
# -*- coding: utf-8 -*-
"""Testes do motor de custo com valores conferidos em planilha manual."""
import pandas as pd
import pytest
from src import config
from src.custo import custo_por_odi, agregar_por_estrato, tarifa_campo

def _odis_teste():
    # 2 ODIs no estrato 1 (mesmo municipio X), 1 no estrato 2 (municipio Y).
    return pd.DataFrame({
        "ODI": ["A", "B", "C"], "Estrato": [1, 1, 2], "Municipio": ["X", "X", "Y"],
        "n_ucs": [2, 1, 3],
        "lat_centro": [-1.60, -1.70, -1.80], "lon_centro": [-48.65, -48.70, -48.75],
        "dist_interna_km": [2.0, 0.0, 5.0],
    })

def _config_redonda(monkeypatch):
    # Fixa parametros redondos para conferencia manual da formula.
    monkeypatch.setattr(config, "FATOR_RODOVIARIO", 1.0)
    monkeypatch.setattr(config, "VELOCIDADE_KMH", 50.0)
    monkeypatch.setattr(config, "HORAS_DIA_CAMPO", 8.0)
    monkeypatch.setattr(config, "HORAS_ESCRITORIO_POR_OS", 10.0)
    monkeypatch.setattr(config, "UCS_POR_DIA", {"LPT": 4.0, "MLA": 1.0})
    monkeypatch.setattr(config, "PERFIL_EQUIPE", "ENGENHEIRO")
    monkeypatch.setattr(config, "TARIFAS_HORA",
                        {"ENGENHEIRO": {"campo": 100.0, "escritorio": 50.0}})
    monkeypatch.setattr(config, "CUSTO_DIARIA", 0.0)

def test_custo_por_odi_formula(monkeypatch):
    _config_redonda(monkeypatch)
    r = custo_por_odi(_odis_teste(), uf="PA", tipo_contrato="LPT")
    a = r[r["ODI"] == "A"].iloc[0]
    # Mobilizacao municipal e' rateada: A e B (mesmo municipio X) tem o MESMO acesso.
    b = r[r["ODI"] == "B"].iloc[0]
    assert a["dist_acesso_km"] == pytest.approx(b["dist_acesso_km"])
    assert a["dist_acesso_km"] > 0
    # horas_inspecao = n_ucs * (8h / 4 UCs por dia) = 2 * 2h = 4h -> custo = 4 * 100.
    assert a["horas_inspecao"] == pytest.approx(4.0)
    assert a["custo_insp"] == pytest.approx(400.0)
    # custo_desloc = horas_desloc * tarifa de campo (100).
    assert a["custo_desloc"] == pytest.approx(a["horas_desloc"] * 100.0)
    # total por ODI = so campo (desloc + inspecao); o fixo de OS entra por estrato.
    assert a["custo_total"] == pytest.approx(a["custo_desloc"] + a["custo_insp"])

def test_tipo_contrato_muda_produtividade(monkeypatch):
    _config_redonda(monkeypatch)
    lpt = custo_por_odi(_odis_teste(), uf="PA", tipo_contrato="LPT")
    mla = custo_por_odi(_odis_teste(), uf="PA", tipo_contrato="MLA")
    # MLA (1 UC/dia) consome 4x as horas de inspecao de LPT (4 UCs/dia).
    assert mla["horas_inspecao"].sum() == pytest.approx(4 * lpt["horas_inspecao"].sum())

def test_agregar_por_estrato_soma_e_fixo(monkeypatch):
    _config_redonda(monkeypatch)
    r = custo_por_odi(_odis_teste(), uf="PA", tipo_contrato="LPT")
    agg = agregar_por_estrato(r)
    # 2 estratos + linha TOTAL.
    assert len(agg) == 3
    e1 = agg[agg["Estrato"] == 1].iloc[0]
    # custo_fixo_os = 10h de escritorio * 50 = 500, UMA vez por estrato.
    assert e1["custo_fixo_os"] == pytest.approx(500.0)
    # equipe_dias = horas de campo do estrato / 8.
    assert e1["equipe_dias"] == pytest.approx((e1["horas_desloc"] + e1["horas_inspecao"]) / 8.0)
    # custo_total do estrato = campo (soma dos ODIs) + fixo.
    soma_campo = r[r["Estrato"] == 1]["custo_total"].sum()
    assert e1["custo_total"] == pytest.approx(soma_campo + 500.0)
    # TOTAL soma os estratos (fixo incluido 2x: uma vez por estrato).
    total = agg[agg["Estrato"] == "TOTAL"].iloc[0]
    assert total["custo_fixo_os"] == pytest.approx(1000.0)
    assert total["custo_total"] == pytest.approx(agg[agg["Estrato"] != "TOTAL"]["custo_total"].sum())

def test_tarifa_campo_inclui_diaria(monkeypatch):
    _config_redonda(monkeypatch)
    # CUSTO_DIARIA = 80 por dia de campo -> 80/8h = +10/h sobre a tarifa 100.
    monkeypatch.setattr(config, "CUSTO_DIARIA", 80.0)
    assert tarifa_campo() == pytest.approx(110.0)
```

- [x] **Step 2: Rodar e ver falhar** — Expected: `ModuleNotFoundError: src.config`.

- [x] **Step 3: Implementar**

`src/config.py`:
```python
# -*- coding: utf-8 -*-
"""Parametros do modelo de custo — TODOS os numeros do estimador vivem aqui.

Cada parametro nasce de uma decisao do gate F1 (G1-G5, ver PLAN.md) e pode ser
ajustado sem rebuild. Cada constante tem valor e FONTE.

=== MEMORIA DE CALCULO (para humanos) ===
O custo de um estrato soma duas parcelas (formula decifrada das estimativas reais
do orgao, MODELO_CUSTO.md a.5 — reproduz 7 de 11 estimativas ao centavo):
1) ESCRITORIO (fixo por estrato): planejamento + relatorio + apresentacao =
   HORAS_ESCRITORIO_POR_OS x tarifa de escritorio (36h x R$360 = R$12.960).
2) CAMPO: horas de campo x tarifa de campo (R$600/h = R$4.800/equipe-dia).
   As horas de campo somam:
   - DESLOCAMENTO: a equipe parte da CAPITAL do estado do contrato, vai ao municipio
     (ida e volta, UMA vez por municipio), salta entre as obras do municipio e
     percorre as UCs de cada obra. Km em linha reta viram km de estrada pelo
     FATOR_RODOVIARIO; km viram horas pela VELOCIDADE_KMH.
   - INSPECAO: cada UC consome HORAS_DIA_CAMPO / UCS_POR_DIA[tipo] horas.
     LPT (rede/postes): 30 UCs/dia. MLA (fotovoltaico remoto): 3 UCs/dia.
Por que assim: mantem a camada de preco que o orgao ja usa e troca o julgamento
"condicoes logisticas" por geometria reprodutivel (coordenadas das UCs), sem
depender de malha rodoviaria externa. Detalhes e alternativas: planning/MODELO_CUSTO.md.
=== FIM DA MEMORIA DE CALCULO ===
"""
# --- Equipe (decisao G1 do gate) ---
# Perfil usado na estimativa. Tecnico raramente e' usado (nao sobe em poste quem estima).
PERFIL_EQUIPE = "ENGENHEIRO"
# Tarifas R$/hora por perfil (Formulario de OS, aba 'Custos Inspecoes').
# 'campo' = COM deslocamento; 'escritorio' = SEM deslocamento.
TARIFAS_HORA = {
    "ENGENHEIRO": {"campo": 600.0, "escritorio": 360.0},
    "TECNICO": {"campo": 513.22, "escritorio": 273.22},
}
# Diaria/pernoite em R$ por equipe-dia de campo (decisao G2: tarifa ja embute -> 0).
CUSTO_DIARIA = 0.0

# --- Jornada e produtividade (decisao G5 do gate) ---
# Horas de um dia de campo (8h x 600 = 4.800/equipe-dia, formula decifrada do orgao).
HORAS_DIA_CAMPO = 8.0
# Horas de escritorio por OS: planejamento + relatorio + apresentacao, UMA vez por estrato
# (36h x 360 = 12.960, o termo fixo da formula decifrada em MODELO_CUSTO.md a.5).
HORAS_ESCRITORIO_POR_OS = 36.0
# UCs inspecionadas por equipe por dia, por tipo de contrato (decisao G5):
# LPT = obras com rede/postes/transformador; MLA = fotovoltaico em regioes remotas.
UCS_POR_DIA = {"LPT": 30.0, "MLA": 3.0}
# Tipo usado quando o contrato nao e' informado/encontrado.
TIPO_CONTRATO_PADRAO = "LPT"

# --- Deslocamento (decisao G4: parametros a calibrar, ajustaveis sem rebuild) ---
# Converte distancia geodesica (linha reta) em distancia rodoviaria. FONTE: chute F1.
FATOR_RODOVIARIO = 1.40
# Velocidade media em km/h no interior. FONTE: chute F1.
VELOCIDADE_KMH = 45.0

# --- Base de partida (decisao G3: capital do estado do contrato) ---
# Coordenadas (lat, long) das capitais das 23 UFs presentes em base_contratos.json.
CAPITAIS_UF = {
    "AC": (-9.9754, -67.8249),   # Rio Branco
    "AL": (-9.6660, -35.7350),   # Maceio
    "AM": (-3.1190, -60.0217),   # Manaus
    "AP": (0.0349, -51.0694),    # Macapa
    "BA": (-12.9718, -38.5011),  # Salvador
    "CE": (-3.7172, -38.5433),   # Fortaleza
    "GO": (-16.6869, -49.2648),  # Goiania
    "MA": (-2.5307, -44.3068),   # Sao Luis
    "MS": (-20.4697, -54.6201),  # Campo Grande
    "MT": (-15.6014, -56.0979),  # Cuiaba
    "PA": (-1.4558, -48.4902),   # Belem
    "PB": (-7.1195, -34.8450),   # Joao Pessoa
    "PE": (-8.0476, -34.8770),   # Recife
    "PI": (-5.0892, -42.8019),   # Teresina
    "PR": (-25.4284, -49.2733),  # Curitiba
    "RJ": (-22.9068, -43.1729),  # Rio de Janeiro
    "RN": (-5.7945, -35.2110),   # Natal
    "RO": (-8.7612, -63.9004),   # Porto Velho
    "RR": (2.8235, -60.6758),    # Boa Vista
    "RS": (-30.0346, -51.2177),  # Porto Alegre
    "SE": (-10.9472, -37.0731),  # Aracaju
    "SP": (-23.5505, -46.6333),  # Sao Paulo
    "TO": (-10.2400, -48.3558),  # Palmas
}
# UF usada quando o contrato nao e' informado.
UF_PADRAO = "PA"
# Caminho (relativo a raiz do projeto) da base de contratos: chave = contrato,
# campos uf / tipo_contrato / vigente. Fonte: minhas_notas/base_contratos.json.
ARQUIVO_BASE_CONTRATOS = "minhas_notas/base_contratos.json"
```

`src/custo.py`:
```python
# -*- coding: utf-8 -*-
"""Motor de custo: transforma distancias em R$ conforme o modelo aprovado (F1).

=== MEMORIA DE CALCULO (para humanos) ===
[Mesmo bloco de src/config.py -- duplicado de proposito: quem abrir qualquer um dos
dois arquivos entende o calculo sem ler mais nada.]
custo_estrato = CUSTO_FIXO + custo_campo, onde:
  CUSTO_FIXO  = HORAS_ESCRITORIO_POR_OS x tarifa_escritorio  (36h x 360 = 12.960, 1x por estrato)
  custo_campo = (horas_desloc + horas_inspecao) x tarifa_campo (600/h = 4.800/equipe-dia)
  horas_desloc = km_estrada / VELOCIDADE_KMH, com km_estrada = FATOR_RODOVIARIO x
    (mobilizacao: capital da UF -> centro do municipio, ida e volta, UMA vez por municipio
     + saltos entre as obras do municipio + percurso entre as UCs de cada obra)
  horas_inspecao = n_ucs x (HORAS_DIA_CAMPO / UCS_POR_DIA[tipo])  (LPT: 30/dia; MLA: 3/dia)
Amostra = soma dos estratos. A mobilizacao municipal e' rateada igualmente entre as
obras do municipio so para exibir custo por obra; o total do estrato nao depende do rateio.
=== FIM DA MEMORIA DE CALCULO ===
"""
import pandas as pd
from src import config
from src.distancias import haversine_km, _rota_vizinho_mais_proximo

def tarifa_campo():
    """Tarifa horaria de campo do perfil ativo, com diaria diluida por hora.

    Por que existe: G1/G2 do gate viram parametros; le config NA CHAMADA (nao no
    import) para monkeypatch e ajustes sem rebuild funcionarem.

    Logica: Entrada (config) -> Fase 1: tarifa 'campo' do perfil ativo -> Fase 2:
    soma CUSTO_DIARIA diluida pela jornada -> Saida: R$/hora.
    """
    # Fase 1: tarifa de campo do perfil ativo (G1: ENGENHEIRO).
    base = config.TARIFAS_HORA[config.PERFIL_EQUIPE]["campo"]
    # Fase 2: diaria (G2: 0 por padrao) diluida pelas horas do dia de campo.
    return base + config.CUSTO_DIARIA / config.HORAS_DIA_CAMPO

def tarifa_escritorio():
    """Tarifa horaria de escritorio (sem deslocamento) do perfil ativo.

    Por que existe: par do tarifa_campo() para o termo fixo por OS; le config na
    chamada pelo mesmo motivo.

    Logica: Entrada (config) -> Fase 1: tarifa 'escritorio' do perfil -> Saida: R$/h.
    """
    # Fase 1/Saida: tarifa de escritorio do perfil ativo.
    return config.TARIFAS_HORA[config.PERFIL_EQUIPE]["escritorio"]

def custo_por_odi(df_odis, uf, tipo_contrato):
    """Calcula o custo de CAMPO de cada ODI a partir do resumo geometrico.

    Por que existe: e' o UNICO lugar onde a formula de custo vive; contrato estavel
    permite ajustar o modelo so por config.py, sem tocar no resto do pipeline.
    O termo fixo de escritorio NAO entra aqui (e' por estrato, ver agregar_por_estrato).

    Logica: Entrada (df por ODI, uf, tipo) -> Fase 1: por municipio, mobilizacao
    (capital -> centroide municipal, ida e volta, uma vez) + saltos entre ODIs,
    rateados igualmente entre as ODIs do municipio -> Fase 2: km -> horas (desloc)
    e produtividade do tipo -> horas (inspecao) -> Fase 3: horas x tarifa de campo
    -> Saida: df com as colunas de custo de campo.
    """
    # Copia para nao mutar a entrada.
    r = df_odis.copy()
    # Capital da UF do contrato (G3); KeyError aqui = UF invalida (bug, nao dado).
    lat_cap, lon_cap = config.CAPITAIS_UF[uf]
    # Fase 1: distancia de acesso rateada por municipio.
    acesso = {}
    # Um grupo por municipio: a equipe mobiliza uma vez por municipio, nao por ODI.
    for _mun, g in r.groupby("Municipio", sort=False):
        # Centroide municipal = media dos centroides das ODIs do municipio.
        lat_m, lon_m = float(g["lat_centro"].mean()), float(g["lon_centro"].mean())
        # Mobilizacao: capital -> municipio, ida e volta, UMA vez.
        mob = 2 * haversine_km(lat_cap, lon_cap, lat_m, lon_m)
        # Saltos: rota gulosa entre os centroides das ODIs do municipio.
        saltos = _rota_vizinho_mais_proximo(g["lat_centro"].to_numpy(), g["lon_centro"].to_numpy())
        # Rateio igual entre as ODIs do municipio (so para exibicao por ODI).
        for odi in g["ODI"]:
            acesso[odi] = (mob + saltos) / len(g)
    # Aplica o rateio e a correcao linha reta -> estrada em todas as distancias.
    r["dist_acesso_km"] = r["ODI"].map(acesso) * config.FATOR_RODOVIARIO
    r["dist_interna_corrigida_km"] = r["dist_interna_km"] * config.FATOR_RODOVIARIO
    # Fase 2: km -> horas; inspecao usa a produtividade do tipo de contrato (G5).
    r["horas_desloc"] = (r["dist_acesso_km"] + r["dist_interna_corrigida_km"]) / config.VELOCIDADE_KMH
    # Horas por UC derivadas da jornada e da produtividade do tipo (LPT 30, MLA 3).
    horas_por_uc = config.HORAS_DIA_CAMPO / config.UCS_POR_DIA[tipo_contrato]
    r["horas_inspecao"] = r["n_ucs"] * horas_por_uc
    # Fase 3: horas -> R$ pela tarifa de campo (G1/G2 via tarifa_campo()).
    r["custo_desloc"] = r["horas_desloc"] * tarifa_campo()
    r["custo_insp"] = r["horas_inspecao"] * tarifa_campo()
    r["custo_total"] = r["custo_desloc"] + r["custo_insp"]
    # Saida: mesmo df, enriquecido com as colunas de custo de campo.
    return r

def agregar_por_estrato(df_custos):
    """Agrega por estrato, acrescenta o custo fixo de OS e a linha TOTAL.

    Por que existe: a formula decifrada tem um termo FIXO por estrato (planejamento/
    relatorio/apresentacao) que nao pertence a nenhuma ODI; ele entra aqui, garantindo
    que resumo e mapas usem os mesmos numeros.

    Logica: Entrada (df por ODI com custos de campo) -> Fase 1: groupby Estrato
    somando -> Fase 2: equipe_dias e custo_fixo_os por estrato; total = campo + fixo
    -> Fase 3: linha TOTAL -> Saida: df por estrato + TOTAL.
    """
    # Fase 1: soma por estrato das grandezas aditivas de campo.
    agg = (df_custos.groupby("Estrato", sort=True)
           .agg(n_odis=("ODI", "count"), n_ucs=("n_ucs", "sum"),
                dist_acesso_km=("dist_acesso_km", "sum"),
                dist_interna_km=("dist_interna_corrigida_km", "sum"),
                horas_desloc=("horas_desloc", "sum"), horas_inspecao=("horas_inspecao", "sum"),
                custo_desloc=("custo_desloc", "sum"), custo_insp=("custo_insp", "sum"),
                custo_campo=("custo_total", "sum"))
           .reset_index())
    # Fase 2: equipe-dias (horas de campo / jornada) e o termo fixo de OS por estrato.
    agg["equipe_dias"] = (agg["horas_desloc"] + agg["horas_inspecao"]) / config.HORAS_DIA_CAMPO
    agg["custo_fixo_os"] = config.HORAS_ESCRITORIO_POR_OS * tarifa_escritorio()
    # Total do estrato = campo (soma dos ODIs) + fixo (uma vez).
    agg["custo_total"] = agg["custo_campo"] + agg["custo_fixo_os"]
    # Fase 3: linha TOTAL = soma das colunas numericas (fixo somado por estrato).
    total = agg.drop(columns="Estrato").sum()
    total["Estrato"] = "TOTAL"
    # Saida: estratos ordenados + TOTAL ao final.
    return pd.concat([agg, total.to_frame().T], ignore_index=True)
```

- [x] **Step 4: Rodar e ver passar** — Run: `.venv\Scripts\python.exe -m pytest testes/test_custo.py -v` → Expected: `4 passed`.

- [x] **Step 5: Commit**

```powershell
git add src testes ; git commit -m "feat: F4 - motor de custo parametrizado por config.py"
```

---

### Task 6: F5 — `resumo.py`: tabela-resumo em Excel

**Files:**
- Create: `src/resumo.py`, `testes/test_resumo.py`

**Interfaces:**
- Consumes: `agregar_por_estrato` (Task 5), `EntradaInvalida` (Task 2).
- Produces: `gravar_resumo(custos_por_amostra: dict[int, pd.DataFrame], caminho: Path) -> None` — grava `saida/Resumo_Custos.xlsx` com aba `Leia-me`, uma aba `Amostra K` (agregado por estrato) e uma `Detalhe K` (por ODI) por amostra.

- [x] **Step 1: Testes que falham**

`testes/test_resumo.py`:
```python
# -*- coding: utf-8 -*-
"""Testes da gravacao da tabela-resumo."""
import pandas as pd
import pytest
from src.custo import custo_por_odi
from src.resumo import gravar_resumo
from src.io_amostras import EntradaInvalida
from testes.test_custo import _odis_teste

def _custos():
    # Custos de campo calculados com a config real (valores nao importam aqui;
    # o teste confere ESTRUTURA da planilha, nao numeros).
    return custo_por_odi(_odis_teste(), uf="PA", tipo_contrato="LPT")

def test_gravar_resumo_estrutura(tmp_path):
    custos = {1: _custos(), 2: _custos()}
    destino = tmp_path / "Resumo_Custos.xlsx"
    gravar_resumo(custos, destino)
    xls = pd.ExcelFile(destino)
    # Abas esperadas: Leia-me + (resumo, detalhe) por amostra.
    assert xls.sheet_names == ["Leia-me", "Amostra 1", "Detalhe 1", "Amostra 2", "Detalhe 2"]
    # A aba de resumo tem a linha TOTAL e as colunas novas do modelo do gate.
    aba = xls.parse("Amostra 1")
    assert (aba["Estrato"].astype(str) == "TOTAL").any()
    assert "Equipe-dias" in aba.columns and "Custo fixo OS (R$)" in aba.columns

def test_gravar_resumo_arquivo_aberto(tmp_path):
    # Simula 'planilha aberta no Excel': arquivo destino travado para escrita.
    destino = tmp_path / "Resumo_Custos.xlsx"
    custos = {1: _custos()}
    with open(destino, "w") as trava:  # handle aberto impede a regravacao no Windows
        with pytest.raises(EntradaInvalida, match="[Ff]eche"):
            gravar_resumo(custos, destino)
```

- [x] **Step 2: Rodar e ver falhar** — Expected: `ModuleNotFoundError: src.resumo`.

- [x] **Step 3: Implementar**

`src/resumo.py`:
```python
# -*- coding: utf-8 -*-
"""Gravacao da tabela-resumo de custos em Excel (formato inspirado no gabarito 20260224)."""
import pandas as pd
from src.custo import agregar_por_estrato
from src.io_amostras import EntradaInvalida

# Renomeacao de apresentacao (apenas exibicao; nao afeta o calculo).
COLUNAS_PT = {
    "Estrato": "Estrato", "n_odis": "Qtd ODIs", "n_ucs": "Qtd UCs",
    "dist_acesso_km": "Dist. acesso (km)", "dist_interna_km": "Dist. interna (km)",
    "dist_interna_corrigida_km": "Dist. interna (km, estrada)",
    "horas_desloc": "Horas desloc.", "horas_inspecao": "Horas inspecao",
    "equipe_dias": "Equipe-dias",
    "custo_desloc": "Custo desloc. (R$)", "custo_insp": "Custo inspecao (R$)",
    "custo_campo": "Custo campo (R$)", "custo_fixo_os": "Custo fixo OS (R$)",
    "custo_total": "Custo total (R$)",
}

def gravar_resumo(custos_por_amostra, caminho):
    """Grava o Resumo_Custos.xlsx com uma aba de agregado e uma de detalhe por amostra.

    Por que existe: e' o produto principal do estimador — a tabela que o humano cola
    na apresentacao; isolar a gravacao permite ajustar formato sem tocar no calculo.

    Logica: Entrada (dict {k: df por ODI com custos}, caminho) -> Fase 1: Leia-me ->
    Fase 2: por amostra, agrega por estrato e grava agregado + detalhe -> Saida: .xlsx.
    """
    try:
        # Abre o writer; PermissionError aqui = arquivo aberto no Excel.
        with pd.ExcelWriter(caminho) as xls:
            # Fase 1: aba Leia-me com a explicacao minima do conteudo.
            pd.DataFrame({"Leia-me": [
                "Resumo de custos de inspecao por amostra/estrato.",
                "Aba 'Amostra K' = agregado por estrato; 'Detalhe K' = por ODI.",
                "Parametros do modelo: src/config.py (fontes comentadas).",
            ]}).to_excel(xls, sheet_name="Leia-me", index=False)
            # Fase 2: um par de abas por amostra, em ordem numerica.
            for k in sorted(custos_por_amostra):
                detalhe = custos_por_amostra[k]
                # Agrega por estrato (mesma funcao usada em todo o pipeline).
                agregado = agregar_por_estrato(detalhe)
                # Grava com nomes de coluna de apresentacao e 2 casas decimais.
                agregado.rename(columns=COLUNAS_PT).round(2).to_excel(xls, sheet_name=f"Amostra {k}", index=False)
                detalhe.rename(columns=COLUNAS_PT).round(2).to_excel(xls, sheet_name=f"Detalhe {k}", index=False)
    except PermissionError:
        # Arquivo travado (aberto no Excel): mensagem de usuario, nao traceback.
        raise EntradaInvalida(f"Nao consegui gravar {caminho}.\nFeche o arquivo no Excel e rode de novo.")
```

- [x] **Step 4: Rodar e ver passar** — Run: `.venv\Scripts\python.exe -m pytest testes/test_resumo.py -v` → Expected: `2 passed`.

- [x] **Step 5: Commit**

```powershell
git add src testes ; git commit -m "feat: F5 - tabela-resumo de custos em Excel"
```

---

### Task 7: F6 — `mapas.py`: mapas folium por amostra

**Files:**
- Create: `src/mapas.py`, `testes/test_mapas.py`

**Interfaces:**
- Consumes: df de UCs por amostra (Task 3) + custos por ODI (Task 5).
- Produces: `gravar_mapa(df_ucs: pd.DataFrame, custos: pd.DataFrame, caminho: Path) -> None` — grava um `.html` folium: `CircleMarker` por UC, cor por estrato, popup ODI/município/custo, `FeatureGroup` por estrato + `LayerControl`.

- [x] **Step 1: Testes que falham**

`testes/test_mapas.py`:
```python
# -*- coding: utf-8 -*-
"""Testes do mapa folium: existencia e conteudo minimo do HTML."""
import pandas as pd
from src.custo import custo_por_odi
from src.mapas import gravar_mapa
from testes.test_custo import _odis_teste

def _ucs_teste():
    # 2 UCs para o ODI A, 1 para B, 1 para C (estratos 1/1/2).
    return pd.DataFrame({
        "ODI": ["A", "A", "B", "C"], "Estrato": [1, 1, 1, 2], "Municipio": ["X"] * 4,
        "UC": ["a1", "a2", "b1", "c1"],
        "LATITUDE": [-1.60, -1.605, -1.70, -1.80],
        "LONGITUDE": [-48.65, -48.652, -48.70, -48.75],
    })

def test_gravar_mapa(tmp_path):
    destino = tmp_path / "Mapa_Amostra_1.html"
    gravar_mapa(_ucs_teste(), custo_por_odi(_odis_teste(), uf="PA", tipo_contrato="LPT"), destino)
    html = destino.read_text(encoding="utf-8")
    # HTML existe, tem os grupos por estrato e os popups com a ODI.
    assert destino.exists()
    assert "Estrato 1" in html and "Estrato 2" in html
    assert "ODI A" in html
```

- [x] **Step 2: Rodar e ver falhar** — Expected: `ModuleNotFoundError: src.mapas`.

- [x] **Step 3: Implementar**

`src/mapas.py`:
```python
# -*- coding: utf-8 -*-
"""Mapas interativos (folium) das amostras: UCs coloridas por estrato com popup de custo."""
import folium
import pandas as pd

# Paleta fixa por estrato (cores distinguiveis; cicla se houver mais estratos que cores).
CORES = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf"]

def gravar_mapa(df_ucs, custos, caminho):
    """Grava um mapa HTML da amostra com uma camada ligavel por estrato.

    Por que existe: substitui o mapa manual do QGIS (D3); um arquivo autocontido que o
    humano abre no browser e explora por camadas.

    Logica: Entrada (UCs, custos por ODI, caminho) -> Fase 1: centro do mapa = media
    das UCs -> Fase 2: FeatureGroup por estrato com CircleMarker por UC e popup
    ODI/municipio/custo -> Fase 3: LayerControl -> Saida: .html gravado.
    """
    # Fase 1: centraliza o mapa no centroide geral da amostra.
    mapa = folium.Map(location=[df_ucs["LATITUDE"].mean(), df_ucs["LONGITUDE"].mean()], zoom_start=8)
    # Indice de custo por ODI para preencher o popup.
    custo_odi = custos.set_index("ODI")["custo_total"].to_dict()
    # Fase 2: uma camada por estrato, na ordem crescente.
    for i, (estrato, g) in enumerate(df_ucs.groupby("Estrato", sort=True)):
        grupo = folium.FeatureGroup(name=f"Estrato {estrato}")
        # Um marcador por UC do estrato.
        for _, uc in g.iterrows():
            folium.CircleMarker(
                location=[uc["LATITUDE"], uc["LONGITUDE"]],
                radius=4,
                color=CORES[i % len(CORES)],   # cor estavel por estrato
                fill=True,
                popup=folium.Popup(
                    f"ODI {uc['ODI']}<br>{uc['Municipio']}<br>"
                    f"Custo ODI: R$ {custo_odi.get(uc['ODI'], float('nan')):,.2f}",
                    max_width=250),
            ).add_to(grupo)
        grupo.add_to(mapa)
    # Fase 3: controle para ligar/desligar estratos.
    folium.LayerControl(collapsed=False).add_to(mapa)
    # Saida: HTML autocontido.
    mapa.save(str(caminho))
```

- [x] **Step 4: Rodar e ver passar** — Run: `.venv\Scripts\python.exe -m pytest testes/test_mapas.py -v` → Expected: `1 passed`.

- [x] **Step 5: Commit**

```powershell
git add src testes ; git commit -m "feat: F6 - mapas folium por amostra com camadas por estrato"
```

---

### Task 8: F7 — `estimar_custos.py` (orquestrador) + testes e2e

**Files:**
- Create: `src/estimar_custos.py`, `testes/test_e2e.py`

**Interfaces:**
- Consumes: tudo das Tasks 2–7.
- Produces: `executar(raiz: Path, contrato: str | None = None) -> int` (0 = sucesso, 1 = erro de entrada) e bloco `__main__`; saídas em `saida/Resumo_Custos.xlsx` + `saida/Mapa_Amostra_K.html`.
- Resolução de UF/tipo (decisão G3/G5): se `contrato` informado, busca em `config.ARQUIVO_BASE_CONTRATOS` (chave exata; campos `uf` e `tipo_contrato`); contrato não encontrado → `EntradaInvalida` listando 5 chaves parecidas; sem contrato → usa `config.UF_PADRAO`/`config.TIPO_CONTRATO_PADRAO` com AVISO impresso. O `__main__` pergunta o contrato interativamente (Enter = padrão), no estilo do sistema canônico; `executar()` puro não lê stdin (testável).

- [x] **Step 1: Testes e2e que falham**

`testes/test_e2e.py`:
```python
# -*- coding: utf-8 -*-
"""E2E: Entrada/ sintetica completa -> pipeline inteiro -> confere saidas."""
import pandas as pd
from src.estimar_custos import executar
from testes.fixtures import escrever_lote, escrever_painel, ODIS

def _monta_entrada(raiz, odis_painel=ODIS):
    # Cria a arvore Entrada/ e saida/ dentro de um tmp_path.
    (raiz / "Entrada").mkdir()
    (raiz / "saida").mkdir()
    escrever_lote(raiz / "Entrada" / "Lote.xlsx", abas=(1, 2))
    escrever_painel(raiz / "Entrada" / "Painel de Monitoramento T.xlsx", odis=odis_painel)

def test_e2e_feliz(tmp_path, capsys):
    _monta_entrada(tmp_path)
    # Sem contrato informado: usa UF_PADRAO/TIPO_CONTRATO_PADRAO com aviso.
    assert executar(tmp_path) == 0
    assert "AVISO" in capsys.readouterr().out  # aviso de contrato nao informado
    # Saidas existem.
    assert (tmp_path / "saida" / "Resumo_Custos.xlsx").exists()
    assert (tmp_path / "saida" / "Mapa_Amostra_1.html").exists()
    assert (tmp_path / "saida" / "Mapa_Amostra_2.html").exists()
    # Totais consistentes: TOTAL da aba agregada = soma do detalhe.
    agg = pd.read_excel(tmp_path / "saida" / "Resumo_Custos.xlsx", sheet_name="Amostra 1")
    det = pd.read_excel(tmp_path / "saida" / "Resumo_Custos.xlsx", sheet_name="Detalhe 1")
    total = agg[agg["Estrato"].astype(str) == "TOTAL"]["Custo total (R$)"].iloc[0]
    assert abs(total - det["Custo total (R$)"].sum()) < 0.05  # tolerancia de arredondamento

def test_e2e_tranche_errada(tmp_path, capsys):
    # Painel de outra tranche: codigo de saida 1 e mensagem especifica, sem traceback.
    _monta_entrada(tmp_path, odis_painel=["TO900", "TO901", "TO902", "TO903", "TO904"])
    assert executar(tmp_path) == 1
    assert "tranche" in capsys.readouterr().out.lower()

def test_e2e_sem_entrada(tmp_path, capsys):
    # Sem pasta Entrada/ populada: erro de usuario, nao traceback.
    (tmp_path / "Entrada").mkdir()
    (tmp_path / "saida").mkdir()
    assert executar(tmp_path) == 1
    assert "Lote.xlsx" in capsys.readouterr().out

def test_e2e_contrato_conhecido(tmp_path, capsys, monkeypatch):
    # Contrato valido no base_contratos.json: usa a UF e o tipo do contrato.
    import json
    from src import config
    _monta_entrada(tmp_path)
    # Base de contratos sintetica dentro do tmp_path (teste nao depende de minhas_notas/).
    base = {"ECM TESTE-2026": {"uf": "PA", "tipo_contrato": "MLA", "vigente": "Andamento"}}
    (tmp_path / "base_contratos.json").write_text(json.dumps(base), encoding="utf-8")
    monkeypatch.setattr(config, "ARQUIVO_BASE_CONTRATOS", "base_contratos.json")
    assert executar(tmp_path, contrato="ECM TESTE-2026") == 0
    saida = capsys.readouterr().out
    # Confirma que a resolucao do contrato foi aplicada (UF/tipo impressos).
    assert "PA" in saida and "MLA" in saida

def test_e2e_contrato_desconhecido(tmp_path, capsys, monkeypatch):
    # Contrato inexistente: erro de entrada listando chaves parecidas.
    import json
    from src import config
    _monta_entrada(tmp_path)
    base = {"ECM TESTE-2026": {"uf": "PA", "tipo_contrato": "LPT", "vigente": "Andamento"}}
    (tmp_path / "base_contratos.json").write_text(json.dumps(base), encoding="utf-8")
    monkeypatch.setattr(config, "ARQUIVO_BASE_CONTRATOS", "base_contratos.json")
    assert executar(tmp_path, contrato="ECM INEXISTENTE") == 1
    assert "ECM TESTE-2026" in capsys.readouterr().out  # sugestao de chave parecida
```

- [x] **Step 2: Rodar e ver falhar** — Expected: `ModuleNotFoundError: src.estimar_custos`.

- [x] **Step 3: Implementar**

`src/estimar_custos.py`:
```python
# -*- coding: utf-8 -*-
"""Orquestrador do estimador: le Entrada/, calcula custos e grava saida/.

Unico executavel do projeto (padrao do sistema canonico): rode via executar.bat
ou `.venv\\Scripts\\python.exe src\\estimar_custos.py`.
"""
from pathlib import Path
import sys

# Garante que 'src' e' importavel quando rodado como script (python src/estimar_custos.py).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.io_amostras import (EntradaInvalida, achar_entradas, ler_amostras,   # noqa: E402
                             ler_painel, juntar_amostras_painel)
from src.distancias import resumo_por_odi                                      # noqa: E402
from src.custo import custo_por_odi                                            # noqa: E402
from src.resumo import gravar_resumo                                           # noqa: E402
from src.mapas import gravar_mapa                                              # noqa: E402
from src import config                                                          # noqa: E402

def _resolver_contrato(raiz, contrato):
    """Resolve (uf, tipo_contrato) a partir do contrato informado (decisoes G3/G5).

    Por que existe: a base de partida (capital da UF) e a produtividade (LPT/MLA)
    dependem do contrato; concentrar a resolucao aqui deixa executar() testavel.

    Logica: Entrada (raiz, contrato ou None) -> Fase 1: sem contrato, usa padroes de
    config com AVISO -> Fase 2: carrega base de contratos e busca a chave exata ->
    Fase 3: chave ausente = erro com sugestoes parecidas -> Saida: (uf, tipo).
    """
    # Fase 1: sem contrato informado, usa os padroes de config e avisa.
    if not contrato:
        print(f"AVISO: contrato nao informado; usando UF={config.UF_PADRAO}, tipo={config.TIPO_CONTRATO_PADRAO}.")
        return config.UF_PADRAO, config.TIPO_CONTRATO_PADRAO
    # Fase 2: carrega a base de contratos (caminho relativo a raiz, vindo de config).
    caminho = Path(raiz) / config.ARQUIVO_BASE_CONTRATOS
    # Base ausente e' erro de entrada: o usuario pediu resolucao por contrato.
    if not caminho.exists():
        raise EntradaInvalida(f"Base de contratos nao encontrada: {caminho}")
    import json
    base = json.loads(caminho.read_text(encoding="utf-8"))
    # Fase 3: chave exata; se ausente, sugere as 5 chaves mais parecidas.
    if contrato not in base:
        parecidas = [c for c in base if contrato.split()[0] in c][:5] or list(base)[:5]
        raise EntradaInvalida(f"Contrato '{contrato}' nao encontrado na base.\nParecidos: {parecidas}")
    dados = base[contrato]
    # Saida: UF e tipo do contrato encontrado (impressos para conferencia do usuario).
    print(f"Contrato {contrato}: UF={dados['uf']}, tipo={dados['tipo_contrato']}, vigente={dados.get('vigente', '?')}")
    return dados["uf"], dados["tipo_contrato"]

def executar(raiz, contrato=None):
    """Roda o pipeline completo a partir da raiz do projeto.

    Por que existe: separa a ORQUESTRACAO (esta funcao, testavel com tmp_path) do
    ponto de entrada __main__ (que pergunta o contrato e fixa o codigo de saida).

    Logica: Entrada (raiz, contrato) -> Fase 1: resolver UF/tipo -> Fase 2: localizar
    e ler entradas -> Fase 3: juntar por ODI -> Fase 4: geometria e custo por amostra
    -> Fase 5: gravar resumo e mapas -> Saida: 0 (sucesso) ou 1 (erro de entrada).
    """
    raiz = Path(raiz)
    try:
        # Fase 1: resolve a UF (base de partida) e o tipo (produtividade) do contrato.
        uf, tipo = _resolver_contrato(raiz, contrato)
        # Fase 2: localizar os dois arquivos e le-los.
        lote, painel = achar_entradas(raiz / "Entrada")
        print(f"Lendo amostras : {lote.name}")
        amostras = ler_amostras(lote)
        print(f"Lendo painel   : {painel.name}")
        ucs = ler_painel(painel)
        # Fase 3: juncao validada por ODI (orfaos/tranche errada abortam aqui).
        juntas = juntar_amostras_painel(amostras, ucs)
        # Fase 4: por amostra, reduz a ODI, calcula custo e acumula para gravacao.
        custos = {}
        for k, df_ucs in juntas.items():
            print(f"Amostra {k}: {df_ucs['ODI'].nunique()} ODIs / {len(df_ucs)} UCs")
            custos[k] = custo_por_odi(resumo_por_odi(df_ucs), uf=uf, tipo_contrato=tipo)
        # Fase 5: grava a tabela-resumo e um mapa por amostra.
        (raiz / "saida").mkdir(exist_ok=True)
        gravar_resumo(custos, raiz / "saida" / "Resumo_Custos.xlsx")
        for k, df_ucs in juntas.items():
            gravar_mapa(df_ucs, custos[k], raiz / "saida" / f"Mapa_Amostra_{k}.html")
        print(f"OK: saidas gravadas em {raiz / 'saida'}")
        # Saida: sucesso.
        return 0
    except EntradaInvalida as erro:
        # Erro de DADOS (culpa da entrada): mensagem amigavel, sem traceback.
        print(f"\nERRO DE ENTRADA:\n{erro}")
        return 1

# Ponto de entrada: raiz = pasta acima de src/ (o .bat roda de qualquer diretorio).
if __name__ == "__main__":
    # Pergunta interativa no estilo do sistema canonico (Enter = padroes de config).
    resposta = input(f"Contrato (ex.: ECM 013-A-2023; Enter = {config.UF_PADRAO}/{config.TIPO_CONTRATO_PADRAO}): ").strip()
    sys.exit(executar(Path(__file__).resolve().parent.parent, contrato=resposta or None))
```

- [x] **Step 4: Rodar TODA a suite** — Run: `.venv\Scripts\python.exe -m pytest testes -v` → Expected: todos passam.

- [x] **Step 5: Validar o ritual de duplo-clique**

Rodar `executar.bat` sem `Entrada/Lote.xlsx` real → deve terminar com a mensagem
"Lote.xlsx nao encontrado... Coloque o arquivo..." (não traceback). Este é o critério
da F0/F7 no `definition of done.md`.

- [x] **Step 6: Escrever `planning/TESTES.md`**

Mapa de testes por fase: o que cada arquivo de teste cobre, como rodar a suite inteira,
como rodar um teste só (`-k nome`), e o roteiro de teste manual com arquivos reais
(colocar Lote.xlsx + Painel na Entrada/, duplo-clique, conferir saida/).

- [x] **Step 7: Status report HTML** — `planning/html/STATUS_F7.html` (estilo
`11-status-report.html`): o que foi construído, resultado da suite, como testar com
dados reais, pendências para v1.

- [x] **Step 8: Commit**

```powershell
git add -A ; git commit -m "feat: F7 - orquestrador, e2e, TESTES.md e status report"
```

---

## Self-review (executado na escrita deste plano)

- **Cobertura do spec:** D1→Task 1 (gate); D2/D7→Tasks 2–3; D3→Task 7; D4→Tasks 1/8 (companions); D5→estrutura src/ em todas; D6→fixtures sintéticas (Tasks 3/8); D8→ADVERSARIAL_REVIEW fora deste plano (pós-PLAN.md, decisão do humano). Erros do DESIGN §7 → Tasks 2 (ausente/ambígua), 3 (órfão/interseção/bbox), 6 (arquivo aberto). Testes do DESIGN §8 → Tasks 2–8.
- **Placeholders:** nenhum "TBD"; a única dependência aberta (fórmula final) tem v0 concreto + gate explícito na Task 1/5.
- **Consistência de tipos:** `dict[int, DataFrame]` flui de `ler_amostras` → `juntar_amostras_painel` → `resumo_por_odi` (por amostra) → `custo_por_odi` → `gravar_resumo`/`gravar_mapa`; nomes de colunas conferidos entre Tasks 3–7 (`ODI/Estrato/Municipio/UC/LATITUDE/LONGITUDE` → `n_ucs/lat_centro/lon_centro/dist_interna_km` → colunas de custo).

---

## Divergências plano × código (registradas em 2026-08-07)

Os blocos de código deste plano são o *plano*; o que está commitado é a *verdade*. As
diferenças abaixo são refinamentos deliberados feitos durante a execução das Tasks 3 e 5,
não desvios acidentais — todas cobertas por teste.

| Onde | Plano dizia | Código commitado | Por quê |
| --- | --- | --- | --- |
| T3 `ler_amostras` | projeta `ODI/Estrato/Municipio` | projeta também **`Cons`** (0 quando a coluna falta) | a regra do órfão precisa de `Cons` para escolher entre erro e fallback |
| T3 `_norm` | minúsculas + sem acento | também **remove ponto final** | o cabeçalho real é `Cons.`, não `Cons` |
| T3 `ler_painel` | projeta `ODI/UC/lat/long` | projeta também **`Municipio`** | o fallback do órfão `Cons==0` precisa do centroide municipal |
| T3 `juntar_amostras_painel` | aborta na primeira lista de órfãos | classifica em 3 baldes, **coleta todos os inválidos antes de abortar** e só aplica os fallbacks depois de a amostra inteira passar | não imprimir aviso de progresso que seria abortado depois (commit `a9f8ec8`) |
| T3 `fixtures.escrever_lote` | `(caminho, abas, odis)` | `(caminho, abas, odis, municipios, cons)` | testar os dois ramos da regra do órfão |
| T3 `fixtures.escrever_painel` | `(caminho, odis, ucs_por_odi)` | `(caminho, odis, ucs_por_odi, municipio)` | idem |
| T5 `agregar_por_estrato` | — | soma `dist_interna_corrigida_km` para dentro da coluna `dist_interna_km` do agregado | por ODI a coluna é linha reta; por estrato já é km de estrada. **Mesmo nome, escala diferente** |

Pendências que NÃO são código e continuam abertas (ver `definition of done.md`):
validação com `Lote.xlsx`/Painel **reais** na `Entrada/` (F2), conferência visual do
`Resumo_Custos.xlsx` contra o gabarito (F5) e dos mapas no browser (F6) pelo humano.
