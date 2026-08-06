# Estimador de Custos de Inspeção — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Estimar o custo de inspeção de cada amostra do SistemaAmostralPython, gerando tabela-resumo `.xlsx` e mapas folium `.html`, executável por duplo-clique em `.bat`.

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

- [ ] **Step 1: Inicializar git e criar .gitignore**

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

- [ ] **Step 2: Criar estrutura e arquivos de ambiente**

```powershell
New-Item -ItemType Directory -Force src, testes, Entrada, saida, planning\html
New-Item -ItemType File src\__init__.py, testes\__init__.py, Entrada\.gitkeep, saida\.gitkeep
Set-Content -Encoding utf8 .python-version "3.12"
Set-Content -Encoding utf8 requirements.txt "pandas`nnumpy`nopenpyxl`nfolium`npytest"
```

- [ ] **Step 3: Criar venv e instalar dependências**

```powershell
uv venv --python 3.12
uv pip install -r requirements.txt
```

- [ ] **Step 4: Teste smoke**

`testes/test_smoke.py`:
```python
# -*- coding: utf-8 -*-
"""Smoke test: garante que o ambiente e os imports base funcionam."""
def test_imports():
    # Importa as dependencias principais; falha = ambiente quebrado.
    import pandas, numpy, openpyxl, folium  # noqa: F401
```

Run: `.venv\Scripts\python.exe -m pytest testes -v` → Expected: `1 passed`.

- [ ] **Step 5: Criar o ritual de execução (copiado do padrão canônico)**

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

- [ ] **Step 6: `planning/definition of done.md` inicial**

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

- [ ] **Step 7: Commit**

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

- [ ] **Step 1: Extrair das referências os ingredientes do custo**

Ler com pandas (via `uv run --no-project --with pandas --with openpyxl`) e documentar:
tarifas R$/hora por perfil (com/sem deslocamento) da aba `Custos Inspeções`; composição
de equipe típica; como `CalculoDistancias.xlsx` transforma distância em custo (aba
`CALCULO_VR` e `Grupo`); que grandezas o gabarito de resumo reporta por estrato.

- [ ] **Step 2: Escrever `planning/MODELO_CUSTO.md`** com: (a) o que as referências fazem;
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

- [ ] **Step 3: Companion HTML** `planning/html/MODELO_CUSTO.html` (estilo explicador de
pesquisa, como `14-research-feature-explainer.html`): a fórmula em diagrama, tabela de
parâmetros com fontes, perguntas abertas para o humano decidir.

- [ ] **Step 4: GATE — apresentar ao humano e registrar a decisão**

Parar e pedir aprovação. Registrar no `PLAN.md` (seção Decisões) o modelo aprovado e
ajustes pedidos. **Não iniciar a Task 4 sem este registro.**

- [ ] **Step 5: Commit**

```powershell
git add planning ; git commit -m "docs: F1 - modelo de custo proposto (MODELO_CUSTO.md + html)"
```

---

### Task 2: F2 — `io_amostras`: localizar entradas

**Files:**
- Create: `src/io_amostras.py`, `testes/test_io_amostras.py`

**Interfaces:**
- Produces: `EntradaInvalida(Exception)`; `achar_entradas(pasta: Path) -> tuple[Path, Path]` (caminho do Lote, caminho do Painel).

- [ ] **Step 1: Testes que falham**

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

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv\Scripts\python.exe -m pytest testes/test_io_amostras.py -v` → Expected: FAIL (`ModuleNotFoundError` / `ImportError`).

- [ ] **Step 3: Implementar**

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

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv\Scripts\python.exe -m pytest testes/test_io_amostras.py -v` → Expected: `4 passed`.

- [ ] **Step 5: Commit**

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
  - `ler_amostras(caminho: Path) -> dict[int, pd.DataFrame]` — chave = nº da amostra (1/2/3); df com colunas `ODI` (str), `Estrato` (int), `Municipio` (str); apenas `STATUS == "Selecionado"`.
  - `ler_painel(caminho: Path) -> pd.DataFrame` — colunas `ODI` (str), `UC` (str), `LATITUDE` (float), `LONGITUDE` (float); UCs com lat/long inválida removidas com aviso.
  - `juntar_amostras_painel(amostras, ucs) -> dict[int, pd.DataFrame]` — df por amostra com as UCs de cada ODI sorteada; levanta `EntradaInvalida` para órfãos/interseção zero.
  - `BBOX_BRASIL` — dict com limites lat/long do Brasil.

- [ ] **Step 1: Fixture sintética compartilhada**

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

- [ ] **Step 2: Testes que falham** (acrescentar a `testes/test_io_amostras.py`)

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

- [ ] **Step 3: Rodar e ver falhar** — Run: `.venv\Scripts\python.exe -m pytest testes/test_io_amostras.py -v` → Expected: FAIL (`ImportError: ler_amostras`).

- [ ] **Step 4: Implementar** (acrescentar a `src/io_amostras.py`)

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

- [ ] **Step 5: Rodar e ver passar** — Run: `.venv\Scripts\python.exe -m pytest testes -v` → Expected: todos passam.

- [ ] **Step 6: Commit**

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

- [ ] **Step 1: Testes que falham**

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

- [ ] **Step 2: Rodar e ver falhar** — Expected: `ModuleNotFoundError: src.distancias`.

- [ ] **Step 3: Implementar**

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

- [ ] **Step 4: Rodar e ver passar** — Run: `.venv\Scripts\python.exe -m pytest testes/test_distancias.py -v` → Expected: `4 passed`.

- [ ] **Step 5: Commit**

```powershell
git add src testes ; git commit -m "feat: F3 - haversine, centroides e rota interna por ODI (distancias)"
```

---

### Task 5: F4 — `config.py` + `custo.py` (modelo aprovado na F1)

> **Pré-condição:** modelo aprovado e registrado no PLAN.md (gate da Task 1). Os valores
> abaixo são o v0 proposto; substituir pelos aprovados/calibrados antes de codificar.

**Files:**
- Create: `src/config.py`, `src/custo.py`, `testes/test_custo.py`

**Interfaces:**
- Consumes: `resumo_por_odi` (Task 4), `haversine_km` (Task 4).
- Produces:
  - `src/config.py` — constantes: `FATOR_RODOVIARIO`, `VELOCIDADE_KMH`, `HORAS_POR_UC`, `TARIFA_HORA_DESLOC`, `TARIFA_HORA_INSP`, `BASES_REGIONAIS: dict[str, tuple[float, float]]`, `BASE_PADRAO: str`.
  - `custo_por_odi(df_odis: pd.DataFrame) -> pd.DataFrame` — acrescenta colunas `dist_acesso_km`, `horas_desloc`, `horas_inspecao`, `custo_desloc`, `custo_insp`, `custo_total`.
  - `agregar_por_estrato(df_custos: pd.DataFrame) -> pd.DataFrame` — uma linha por estrato somando ODIs + linha `TOTAL`.

- [ ] **Step 1: Testes que falham**

`testes/test_custo.py`:
```python
# -*- coding: utf-8 -*-
"""Testes do motor de custo com valores conferidos em planilha manual."""
import pandas as pd
import pytest
from src import config
from src.custo import custo_por_odi, agregar_por_estrato

def _odis_teste():
    # 2 ODIs no estrato 1, 1 no estrato 2; centroides e rotas conhecidos.
    return pd.DataFrame({
        "ODI": ["A", "B", "C"], "Estrato": [1, 1, 2], "Municipio": ["X", "X", "Y"],
        "n_ucs": [2, 1, 3],
        "lat_centro": [-1.60, -1.70, -1.80], "lon_centro": [-48.65, -48.70, -48.75],
        "dist_interna_km": [2.0, 0.0, 5.0],
    })

def test_custo_por_odi_formula(monkeypatch):
    # Fixa parametros redondos para conferencia manual da formula.
    monkeypatch.setattr(config, "FATOR_RODOVIARIO", 1.0)
    monkeypatch.setattr(config, "VELOCIDADE_KMH", 50.0)
    monkeypatch.setattr(config, "HORAS_POR_UC", 1.0)
    monkeypatch.setattr(config, "TARIFA_HORA_DESLOC", 100.0)
    monkeypatch.setattr(config, "TARIFA_HORA_INSP", 200.0)
    r = custo_por_odi(_odis_teste())
    linha = r[r["ODI"] == "A"].iloc[0]
    # dist_acesso = 2 * haversine(base, centroide) * 1.0 (> 0, conferida por faixa).
    assert linha["dist_acesso_km"] > 0
    # horas_desloc = (acesso + interna) / 50; custo_desloc = horas * 100.
    assert linha["custo_desloc"] == pytest.approx(linha["horas_desloc"] * 100.0)
    # horas_inspecao = n_ucs * 1h -> custo_insp = 2 * 200.
    assert linha["custo_insp"] == pytest.approx(400.0)
    # total = desloc + inspecao.
    assert linha["custo_total"] == pytest.approx(linha["custo_desloc"] + 400.0)

def test_agregar_por_estrato():
    r = custo_por_odi(_odis_teste())
    agg = agregar_por_estrato(r)
    # 2 estratos + linha TOTAL.
    assert len(agg) == 3
    total = agg[agg["Estrato"] == "TOTAL"].iloc[0]
    assert total["n_odis"] == 3 and total["n_ucs"] == 6
    assert total["custo_total"] == pytest.approx(r["custo_total"].sum())
```

- [ ] **Step 2: Rodar e ver falhar** — Expected: `ModuleNotFoundError: src.config`.

- [ ] **Step 3: Implementar**

`src/config.py`:
```python
# -*- coding: utf-8 -*-
"""Parametros do modelo de custo — TODOS os numeros do estimador vivem aqui.

Cada constante tem valor e FONTE. Substituir os valores v0 pelos aprovados na F1
(planning/MODELO_CUSTO.md) antes do uso em producao.

=== MEMORIA DE CALCULO (para humanos) ===
[Na Task 5, substituir este bloco pelo texto aprovado no MODELO_CUSTO.md. Estrutura v0:]
O custo de inspecionar uma ODI soma duas parcelas:
1) DESLOCAMENTO: a equipe parte da base regional, vai ate o centro da obra (ida e
   volta; a distancia em linha reta e' convertida em distancia de estrada pelo
   FATOR_RODOVIARIO) e percorre as UCs da obra. Km viram horas dividindo pela
   VELOCIDADE_KMH; horas viram R$ pela TARIFA_HORA_DESLOC (Formulario de OS).
2) INSPECAO: cada UC visitada consome HORAS_POR_UC; horas viram R$ pela
   TARIFA_HORA_INSP (Formulario de OS).
Por que assim: reproduz a logica das referencias (tarifa horaria com/sem
deslocamento) usando a unica geometria disponivel (coordenadas das UCs), sem
depender de malha rodoviaria externa. Detalhes e alternativas: planning/MODELO_CUSTO.md.
=== FIM DA MEMORIA DE CALCULO ===
"""
# Fator que converte distancia geodesica (linha reta) em distancia rodoviaria.
# FONTE: calibrar contra minhas_notas/CalculoDistancias.xlsx na F1 (v0: literatura ~1.3).
FATOR_RODOVIARIO = 1.3
# Velocidade media de deslocamento em km/h (estradas regionais do PA).
# FONTE: proposta F1 (v0: 60 km/h).
VELOCIDADE_KMH = 60.0
# Horas de inspecao por UC visitada.
# FONTE: proposta F1 (v0: 0.5 h/UC).
HORAS_POR_UC = 0.5
# Tarifa R$/hora COM deslocamento (Formulario de OS, aba 'Custos Inspecoes': Eng. 600).
TARIFA_HORA_DESLOC = 600.0
# Tarifa R$/hora SEM deslocamento (Formulario de OS: Eng. 360).
TARIFA_HORA_INSP = 360.0
# Sede de partida da equipe por REGIONAL (lat, long) — v0: sedes das 4 regionais do PA.
BASES_REGIONAIS = {
    "METROPOLITANA": (-1.4558, -48.4902),   # Belem
    "CASTANHAL": (-1.2939, -47.9264),       # Castanhal
    "MARABA": (-5.3687, -49.1178),          # Maraba
    "SANTAREM": (-2.4431, -54.7083),        # Santarem
}
# Base usada quando a regional da ODI nao e' conhecida (v0: Belem).
BASE_PADRAO = "METROPOLITANA"
```

`src/custo.py`:
```python
# -*- coding: utf-8 -*-
"""Motor de custo: transforma distancias em R$ conforme o modelo aprovado (F1).

=== MEMORIA DE CALCULO (para humanos) ===
[Mesmo bloco de src/config.py — duplicado de proposito: quem abrir qualquer um dos
dois arquivos entende o calculo sem ler mais nada. Na Task 5, colar aqui o texto
aprovado no MODELO_CUSTO.md.]
custo_odi = horas_desloc x TARIFA_HORA_DESLOC + horas_inspecao x TARIFA_HORA_INSP
  onde: horas_desloc   = (2 x dist(base, centro_da_obra) x FATOR_RODOVIARIO
                          + percurso_entre_UCs) / VELOCIDADE_KMH
        horas_inspecao = n_ucs x HORAS_POR_UC
Estrato = soma das suas ODIs; Amostra = soma dos estratos.
=== FIM DA MEMORIA DE CALCULO ===
"""
import pandas as pd
from src import config
from src.distancias import haversine_km

def custo_por_odi(df_odis):
    """Calcula o custo de inspecao de cada ODI a partir do resumo geometrico.

    Por que existe: e' o UNICO lugar onde a formula de custo vive; contrato estavel
    permite trocar o modelo (F1) sem tocar no resto do pipeline.

    Logica: Entrada (df por ODI) -> Fase 1: distancia de acesso (base->centroide,
    ida e volta, fator rodoviario) -> Fase 2: horas de deslocamento e de inspecao
    -> Fase 3: R$ = horas x tarifas -> Saida: df com as colunas de custo.
    """
    # Copia para nao mutar a entrada.
    r = df_odis.copy()
    # Fase 1: base de partida (v0: BASE_PADRAO para todas as ODIs).
    lat_b, lon_b = config.BASES_REGIONAIS[config.BASE_PADRAO]
    # Ida e volta ate o centroide, corrigida de linha reta para estrada.
    r["dist_acesso_km"] = [
        2 * haversine_km(lat_b, lon_b, la, lo) * config.FATOR_RODOVIARIO
        for la, lo in zip(r["lat_centro"], r["lon_centro"])
    ]
    # Fase 2: tempo = distancia / velocidade; inspecao = n_ucs x horas por UC.
    r["horas_desloc"] = (r["dist_acesso_km"] + r["dist_interna_km"]) / config.VELOCIDADE_KMH
    r["horas_inspecao"] = r["n_ucs"] * config.HORAS_POR_UC
    # Fase 3: custo = tempo x tarifa (tarifas distintas com/sem deslocamento).
    r["custo_desloc"] = r["horas_desloc"] * config.TARIFA_HORA_DESLOC
    r["custo_insp"] = r["horas_inspecao"] * config.TARIFA_HORA_INSP
    r["custo_total"] = r["custo_desloc"] + r["custo_insp"]
    # Saida: mesmo df, enriquecido com as colunas de custo.
    return r

def agregar_por_estrato(df_custos):
    """Agrega os custos por estrato e acrescenta a linha TOTAL.

    Por que existe: a tabela-resumo (F5) e o gabarito reportam por estrato; concentrar
    a agregacao aqui garante que resumo e mapas usem os MESMOS numeros.

    Logica: Entrada (df por ODI com custos) -> Fase 1: groupby Estrato somando ->
    Fase 2: linha TOTAL -> Saida: df por estrato + TOTAL.
    """
    # Fase 1: soma por estrato das grandezas aditivas.
    agg = (df_custos.groupby("Estrato", sort=True)
           .agg(n_odis=("ODI", "count"), n_ucs=("n_ucs", "sum"),
                dist_acesso_km=("dist_acesso_km", "sum"), dist_interna_km=("dist_interna_km", "sum"),
                horas_desloc=("horas_desloc", "sum"), horas_inspecao=("horas_inspecao", "sum"),
                custo_desloc=("custo_desloc", "sum"), custo_insp=("custo_insp", "sum"),
                custo_total=("custo_total", "sum"))
           .reset_index())
    # Fase 2: linha TOTAL = soma das colunas numericas.
    total = agg.drop(columns="Estrato").sum()
    total["Estrato"] = "TOTAL"
    # Saida: estratos ordenados + TOTAL ao final.
    return pd.concat([agg, total.to_frame().T], ignore_index=True)
```

- [ ] **Step 4: Rodar e ver passar** — Run: `.venv\Scripts\python.exe -m pytest testes/test_custo.py -v` → Expected: `2 passed`.

- [ ] **Step 5: Commit**

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

- [ ] **Step 1: Testes que falham**

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

def test_gravar_resumo_estrutura(tmp_path):
    custos = {1: custo_por_odi(_odis_teste()), 2: custo_por_odi(_odis_teste())}
    destino = tmp_path / "Resumo_Custos.xlsx"
    gravar_resumo(custos, destino)
    xls = pd.ExcelFile(destino)
    # Abas esperadas: Leia-me + (resumo, detalhe) por amostra.
    assert xls.sheet_names == ["Leia-me", "Amostra 1", "Detalhe 1", "Amostra 2", "Detalhe 2"]
    # A aba de resumo tem a linha TOTAL.
    aba = xls.parse("Amostra 1")
    assert (aba["Estrato"].astype(str) == "TOTAL").any()

def test_gravar_resumo_arquivo_aberto(tmp_path):
    # Simula 'planilha aberta no Excel': arquivo destino travado para escrita.
    destino = tmp_path / "Resumo_Custos.xlsx"
    custos = {1: custo_por_odi(_odis_teste())}
    with open(destino, "w") as trava:  # handle aberto impede a regravacao no Windows
        with pytest.raises(EntradaInvalida, match="[Ff]eche"):
            gravar_resumo(custos, destino)
```

- [ ] **Step 2: Rodar e ver falhar** — Expected: `ModuleNotFoundError: src.resumo`.

- [ ] **Step 3: Implementar**

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
    "horas_desloc": "Horas desloc.", "horas_inspecao": "Horas inspecao",
    "custo_desloc": "Custo desloc. (R$)", "custo_insp": "Custo inspecao (R$)",
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

- [ ] **Step 4: Rodar e ver passar** — Run: `.venv\Scripts\python.exe -m pytest testes/test_resumo.py -v` → Expected: `2 passed`.

- [ ] **Step 5: Commit**

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

- [ ] **Step 1: Testes que falham**

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
    gravar_mapa(_ucs_teste(), custo_por_odi(_odis_teste()), destino)
    html = destino.read_text(encoding="utf-8")
    # HTML existe, tem os grupos por estrato e os popups com a ODI.
    assert destino.exists()
    assert "Estrato 1" in html and "Estrato 2" in html
    assert "ODI A" in html
```

- [ ] **Step 2: Rodar e ver falhar** — Expected: `ModuleNotFoundError: src.mapas`.

- [ ] **Step 3: Implementar**

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

- [ ] **Step 4: Rodar e ver passar** — Run: `.venv\Scripts\python.exe -m pytest testes/test_mapas.py -v` → Expected: `1 passed`.

- [ ] **Step 5: Commit**

```powershell
git add src testes ; git commit -m "feat: F6 - mapas folium por amostra com camadas por estrato"
```

---

### Task 8: F7 — `estimar_custos.py` (orquestrador) + testes e2e

**Files:**
- Create: `src/estimar_custos.py`, `testes/test_e2e.py`

**Interfaces:**
- Consumes: tudo das Tasks 2–7.
- Produces: `executar(raiz: Path) -> int` (0 = sucesso, 1 = erro de entrada) e bloco `__main__`; saídas em `saida/Resumo_Custos.xlsx` + `saida/Mapa_Amostra_K.html`.

- [ ] **Step 1: Testes e2e que falham**

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
    assert executar(tmp_path) == 0
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
```

- [ ] **Step 2: Rodar e ver falhar** — Expected: `ModuleNotFoundError: src.estimar_custos`.

- [ ] **Step 3: Implementar**

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

def executar(raiz):
    """Roda o pipeline completo a partir da raiz do projeto.

    Por que existe: separa a ORQUESTRACAO (esta funcao, testavel com tmp_path) do
    ponto de entrada __main__ (que fixa a raiz real e o codigo de saida do processo).

    Logica: Entrada (raiz) -> Fase 1: localizar e ler entradas -> Fase 2: juntar por
    ODI -> Fase 3: geometria e custo por amostra -> Fase 4: gravar resumo e mapas ->
    Saida: 0 (sucesso) ou 1 (erro de entrada, mensagem impressa).
    """
    raiz = Path(raiz)
    try:
        # Fase 1: localizar os dois arquivos e le-los.
        lote, painel = achar_entradas(raiz / "Entrada")
        print(f"Lendo amostras : {lote.name}")
        amostras = ler_amostras(lote)
        print(f"Lendo painel   : {painel.name}")
        ucs = ler_painel(painel)
        # Fase 2: juncao validada por ODI (orfaos/tranche errada abortam aqui).
        juntas = juntar_amostras_painel(amostras, ucs)
        # Fase 3: por amostra, reduz a ODI, calcula custo e acumula para gravacao.
        custos = {}
        for k, df_ucs in juntas.items():
            print(f"Amostra {k}: {df_ucs['ODI'].nunique()} ODIs / {len(df_ucs)} UCs")
            custos[k] = custo_por_odi(resumo_por_odi(df_ucs))
        # Fase 4: grava a tabela-resumo e um mapa por amostra.
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
    sys.exit(executar(Path(__file__).resolve().parent.parent))
```

- [ ] **Step 4: Rodar TODA a suite** — Run: `.venv\Scripts\python.exe -m pytest testes -v` → Expected: todos passam.

- [ ] **Step 5: Validar o ritual de duplo-clique**

Rodar `executar.bat` sem `Entrada/Lote.xlsx` real → deve terminar com a mensagem
"Lote.xlsx nao encontrado... Coloque o arquivo..." (não traceback). Este é o critério
da F0/F7 no `definition of done.md`.

- [ ] **Step 6: Escrever `planning/TESTES.md`**

Mapa de testes por fase: o que cada arquivo de teste cobre, como rodar a suite inteira,
como rodar um teste só (`-k nome`), e o roteiro de teste manual com arquivos reais
(colocar Lote.xlsx + Painel na Entrada/, duplo-clique, conferir saida/).

- [ ] **Step 7: Status report HTML** — `planning/html/STATUS_F7.html` (estilo
`11-status-report.html`): o que foi construído, resultado da suite, como testar com
dados reais, pendências para v1.

- [ ] **Step 8: Commit**

```powershell
git add -A ; git commit -m "feat: F7 - orquestrador, e2e, TESTES.md e status report"
```

---

## Self-review (executado na escrita deste plano)

- **Cobertura do spec:** D1→Task 1 (gate); D2/D7→Tasks 2–3; D3→Task 7; D4→Tasks 1/8 (companions); D5→estrutura src/ em todas; D6→fixtures sintéticas (Tasks 3/8); D8→ADVERSARIAL_REVIEW fora deste plano (pós-PLAN.md, decisão do humano). Erros do DESIGN §7 → Tasks 2 (ausente/ambígua), 3 (órfão/interseção/bbox), 6 (arquivo aberto). Testes do DESIGN §8 → Tasks 2–8.
- **Placeholders:** nenhum "TBD"; a única dependência aberta (fórmula final) tem v0 concreto + gate explícito na Task 1/5.
- **Consistência de tipos:** `dict[int, DataFrame]` flui de `ler_amostras` → `juntar_amostras_painel` → `resumo_por_odi` (por amostra) → `custo_por_odi` → `gravar_resumo`/`gravar_mapa`; nomes de colunas conferidos entre Tasks 3–7 (`ODI/Estrato/Municipio/UC/LATITUDE/LONGITUDE` → `n_ucs/lat_centro/lon_centro/dist_interna_km` → colunas de custo).
