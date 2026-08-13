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

## Estado atual (2026-08-10)

**Fases F0–F13 completas; 86 testes passando.** O pipeline roda ponta a ponta com **dados reais**
de duas tranches de tipos diferentes — `ECO 037/2025` (ENERGISA/PB, LPT, 3 estratificações) e
`ECM 022/2025` (ENERGISA/RO, MLA, 4 estratificações):
`executar.bat` → `_exec.ps1` → `src/estimar_custos.py` → `saida/`.

**`_exec.ps1` é autossuficiente:** na primeira execução instala uv + Python 3.12 + bibliotecas
dentro da própria pasta (`.venv`), com fallback para o Python do sistema. É o que permite mandar
`distribuicao/EstimadorCustos.zip` (gerado por `empacotar.ps1`) para uma máquina limpa.

O orquestrador expõe `executar(raiz, contrato=None, amostra=None) -> int` (0 sucesso / 1 erro de
entrada), puro e sem stdin — o `__main__` é quem pergunta contrato **e amostra**. Todo
`EntradaInvalida` é convertido ali, e só ali, em mensagem + exit 1.

Saída atual (`saida/`): **um** `Resumo_Custos.xlsx` (`Leia-me`/`Resumo`/`Cenarios`/`Detalhe`)
com todas as estratificações da amostra escolhida + um `Mapa_Estratos_N.html` por estratificação.

**O que falta é conferência humana com o olho, não código:** conferir o `Resumo_Custos.xlsx`
contra o benchmark da engenharia (F5) e abrir um mapa no browser (F6). Ver
`planning/definition of done.md` § Placar e `planning/TESTES.md`.

Armadilha de leitura da saída: **somar a coluna de custo da aba `Detalhe K` não dá o custo da
amostra** — o detalhe é só campo; o fixo de escritório entra por estrato. O número válido é a
linha `TOTAL` da aba `Amostra K`. O plano original tinha uma asserção e2e errada nisso (erro de
R$ 38.880); o teste corrigido está em `test_e2e_total_bate_com_detalhe_mais_fixo`.

**Não são código do produto** (não trate como fontes a manter):
`ecc_dashboard.py` (GUI de outro contexto, import quebrado) · `claude resume.txt` (vazio) ·
`planning/html-effectiveness/` (clone de referência de modelos HTML, tem `.git` próprio) ·
`minhas_notas/*.xlsx`/`*.pptx` (insumos de pesquisa).

## Comandos

Windows + PowerShell. Gerenciador **`uv` (Astral)**, Python **3.12** (mesma versão do canônico).

```powershell
powershell -ExecutionPolicy Bypass -File .\instalar.ps1   # setup de DEV (uv + venv + requirements-dev)
powershell -ExecutionPolicy Bypass -File .\empacotar.ps1  # monta distribuicao/EstimadorCustos{,.zip}
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
| `io_amostras.py` | `Entrada/` → `achar_entradas` → `([(n_estratos, caminho), ...], painel)` (descobre **todas** as estratificações pelo conteúdo) · `ler_n_estratos` · `ler_amostras` `{k: df[ODI,Estrato,Municipio,Cons]}` · `ler_painel` `df[ODI,UC,Municipio,LATITUDE,LONGITUDE]` → `juntar_amostras_painel` `{k: df 1 linha por UC}` |
| `distancias.py` | df de UCs → `resumo_por_odi` → **1 linha por ODI** (colunas fixas, mesmo vazio): `n_ucs`, `lat_centro`, `lon_centro`, `dist_interna_km` · `montar_roteiro(df_odis, lat0, lon0)` → `(df com ordem/km_trecho, km_total)` = **itinerário único** · `dividir_roteiro(..., n_equipes)` → `[(roteiro, km), ...]`, um por equipe |
| `config.py` | **todos** os números do modelo (G1–G5 do gate F1 + F9). Zero números mágicos fora daqui |
| `custo.py` | `repartir_entre_equipes(df_odis, uf, tipo, n)` → lista com o campo de **cada equipe** (km, UCs, horas) · `custo_amostra(df_odis, uf, tipo_contrato, n_equipes=None)` → `(dict com os números da AMOSTRA, df do detalhe por obra com a coluna `equipe`)` · `grade_cenarios(df_odis, uf, tipo)` → **grade equipes × prazo**, só as combinações viáveis |
| `resumo.py` | `gravar_resumo([{n_estratos, amostra, roteiro, cenarios, **números}, ...], caminho)` → `saida/Resumo_Custos.xlsx` com **4 abas fixas**: `Leia-me` + `Resumo` (1 linha por estratificação) + `Cenarios` (grade equipes × prazo) + `Detalhe` (1 linha por obra, com a equipe dona e a ordem dela) |
| `mapas.py` | `gravar_mapa(df_ucs, lat0, lon0, caminho)` → `saida/Mapa_Estratos_N.html` (folium; **um ponto por UC**, todos iguais, mais o marcador da base. Sem rota, sem camadas) |

Detalhes que não se deduzem lendo um arquivo só:

- **`custo.py` lê `config` na chamada, nunca no import** — é o que faz `monkeypatch.setattr(config, ...)`
  nos testes e o ajuste sem rebuild funcionarem. Não faça `from src.config import X`.
- **O ESTRATO não entra no custo** (desde a F9). Ele identifica de onde a obra veio na
  estratificação e sobrevive só como coluna informativa do `Detalhe` — saiu do popup do mapa em
  2026-08-12 (poluía sem agregar: em campo a equipe não decide nada com essa informação). O custo
  é por **amostra**: um roteiro, um fixo de escritório.
- **A equipe faz UMA viagem, não ida-e-volta por município.** `montar_roteiro` sai da capital,
  escolhe o município mais próximo, varre **todas** as obras dele antes de sair, e só retorna à
  capital no fim. A hierarquia município→obra é deliberada: uma rota gulosa direta sobre as obras
  entraria e sairia do mesmo município. Nos dados reais isso é 1.529 km contra 10.521 km do
  modelo antigo — a correção que motivou a F9.
- **O TIPO DE CONTRATO muda as horas de escritório, não só a produtividade** (desde a F16). O
  Formulário de OS tem um parâmetro binário — `Tipo de obra`, célula `E48` da aba `Ordem de
  Serviço Emissão` — que as fórmulas `E26:E29` da aba `Custos Inspeções` leem: **Extensão de
  Redes** (LPT) usa 8+24+4 = **36h**; **Geração Descentralizada** (MLA) usa 4+16+4 = **24h**.
  Até 2026-08-13 o modelo tinha 36h fixas — o valor da Extensão —, então **todo contrato MLA
  levava 12h a mais de escritório (R$ 4.320 por amostra)**. Achado pelo humano, lendo o
  formulário. As tarifas também são tabeladas por tipo, mas só o **técnico** muda
  (Eletrotécnico 593/250 no LPT × Técnico 513,22/273,22 no MLA); o engenheiro é 600/360 nos dois,
  então com `PERFIL_EQUIPE = ENGENHEIRO` isso não altera número nenhum hoje.
- **A regra ECO/ECM do usuário e o `tipo_contrato` da base dizem o mesmo, mas a base cobre mais.**
  O humano descreve o tipo de obra pelo prefixo do contrato (`ECO` = Extensão, `ECM` = Geração).
  O código usa `tipo_contrato` (LPT/MLA) de `base_contratos.json`, que é equivalente e cobre os
  **113** contratos — inclusive os prefixos `ECFS` (28) e `ECOT` (16), que a regra não menciona e
  são todos LPT. Há **uma** divergência conhecida: `ECM 001/2020` (Equatorial PA, 1ª Tranche,
  encerrado) está na base como `LPT`. Não foi alterada — é dado do humano, não do código.
- **`N_EQUIPES` e `TAMANHO_EQUIPE` são grandezas DIFERENTES e não se somam.** `N_EQUIPES_PADRAO`
  (= 2 desde a F15) são equipes **independentes**: cada uma tem seu bloco de obras, sai da capital
  e volta — logo **N roteiros**. `TAMANHO_EQUIPE` (= 1) são as pessoas **dentro** de uma equipe;
  uma dupla viaja junta, em **um** roteiro. Custo = `N_EQUIPES × TAMANHO_EQUIPE × dias × 8h ×
  tarifa`. O benchmark da engenharia é `TAMANHO_EQUIPE=2, N_EQUIPES=1` (uma dupla, um roteiro) —
  o padrão daqui tem a mesma mão de obra e custa **mais**, porque são dois roteiros.
  Na planilha as duas viram colunas vizinhas: `Equipes` e `Pessoas por equipe`.
- **O prazo é o da equipe MAIS LENTA**, não a média: `ceil(horas_da_crítica / (HORAS_DIA_CAMPO ×
  TAMANHO_EQUIPE)) + DIAS_MOBILIZACAO`. Todas as equipes são faturadas por esse prazo — o
  trabalho não é perfeitamente divisível, e quem sobra espera.
- **Mais equipes não barateia — encarece**, agora por três motivos somados: o km extra de cada
  ida-e-volta, o dia de mobilização de cada equipe, e o arredondamento para dia inteiro. Na
  sondagem de 26 obras na PB: 1 equipe R$ 41.760 (1.220 km) → 2 equipes R$ 60.960 (1.663 km) →
  3 equipes R$ 70.560 (2.010 km).
- **A aba `Cenarios` é uma GRADE (equipes × prazo)**, não uma faixa de prazos. Varre
  `N_EQUIPES_MIN..N_EQUIPES_MAX` (1 a 7) e, para cada, os prazos do mínimo viável até
  `MAX_DIAS_POR_EQUIPE` (20). **Combinação inviável não aparece nem é calculada**: um pré-filtro
  descarta pelo limite inferior (só horas de inspeção, divididas igualmente) *antes* de rotear,
  que é a parte cara. Caso que motivou a regra: 80 UCs de MLA a 3 UCs/dia são 213h = 27 dias só
  de inspeção para uma equipe — não há o que apresentar.
- **O mapa NÃO desenha itinerário** (desde 2026-08-13, decisão do humano). Ele marca um ponto por
  UC, todos da mesma cor, mais a base. A rota gulosa continua existindo em `distancias.py` e
  alimentando o custo — o que saiu foi o **desenho**: a linha era hipótese do modelo traçada com a
  mesma tinta dos fatos (as coordenadas), e ninguém decidia nada com a ordem das paradas. Sem
  rota não há o que repartir entre equipes, então o radio `GroupedLayerControl` saiu junto e o
  mapa voltou a ter camada única.
- **`dividir_roteiro` voltou a ser o coração do cálculo na F15.** Ficou órfã na F14 (era o mapa
  quem a chamava) e agora é `custo.repartir_entre_equipes` quem a usa — o km de dividir deixou de
  ser ressalva no `Leia-me` e entrou no número. Ela corta o itinerário em blocos **contíguos**
  equilibrados por km acumulado (não por contagem de obras); como `montar_roteiro` já ordena
  município a município, nenhum município é partido entre duas equipes. Segue valendo que **o
  roteiro desenhado volta numa fase operacional** — a F14 tirou a rota do produto *gerencial*,
  não do escopo.
- **Dentro de um mesmo nº de equipes, mais dias custa mais** (folga = dias faturados a mais), e
  isso é monótono na grade da F15 — a não-monotonicidade da versão anterior era artefato de o nº
  de equipes se ajustar sozinho ao prazo. A coluna `Ocupação da equipe` mostra o desperdício.
- **Só UMA amostra é precificada por execução** (a 2 e a 3 são reservas da 1). `executar(raiz,
  contrato, amostra)` — o `__main__` pergunta, padrão `config.AMOSTRA_PADRAO`. Estratificação sem
  a aba pedida é pulada com aviso; se nenhuma tiver, é `EntradaInvalida`.
- **Interseção zero de ODIs só é "tranche errada" se a amostra tiver obras.** Uma aba
  `Amostra K` legitimamente vazia também dá interseção zero — acusá-la seria erro falso.
- **A chave de junção é DECLARADA pelo tipo do contrato, não adivinhada** —
  `config.CHAVE_JUNCAO_POR_TIPO = {"LPT": "ODI", "MLA": "UC"}`, aplicada por
  `escolher_chave_juncao`. Existe um **gap semântico do sistema legado**: a coluna do Lote se
  chama `ODI` nos dois tipos, mas em **MLA** ela guarda o **número da UC** (cada obra é um
  sistema individual; o legado nunca criou número de ODI próprio e reaproveitou a coluna).
  Verificado na 3ª Tranche RO (`ECM 022/2025`): 862 de 862 casam pela UC, nenhuma pela ODI.
  Por isso `juntar_amostras_painel` recebe `tipo_contrato`.
- **Por que declarada e não por tentativa-e-erro:** se um número de UC coincidir com um número
  de ODI, uma heurística casaria pela linha errada **em silêncio**. A verificação contra os
  dados fica só como rede de segurança (contrato não informado, ou tipo errado na base) — e aí
  sai `AVISO`. Os dois testes que provam isso usam o MESMO painel ambíguo com tipos diferentes.
- **`ler_painel` normaliza a UC com `_norm_odi`**, não só a ODI — é o que permite a chave
  alternativa acima funcionar quando os formatos numéricos diferem entre as planilhas.
- **Regra do órfão** (`juntar_amostras_painel`): ODI sorteada sem UC no painel aborta se `Cons > 0`;
  com `Cons == 0` (obra sem UC, ex.: reforço de rede) vira pseudo-UC no centroide do município,
  com aviso. A função **coleta todos os inválidos antes de abortar** e só aplica fallbacks depois
  de a amostra inteira passar — não imprima progresso que possa ser abortado depois.
- **Interseção zero de ODIs** tem mensagem própria: é o sintoma de "Lote de uma tranche × Painel de outra".
- **Duas escalas de km convivem**: `dist_interna_km` e `km_trecho` são **linha reta**;
  `km_roteiro` e `km_trecho_estrada` já vêm × `FATOR_RODOVIARIO`. O nome com `estrada` é a marca.
- **`Entrada/` recebe VÁRIAS estratificações.** `achar_entradas` devolve uma lista: todo `.xlsx`
  com abas `Amostra K` vira uma estratificação, com `N` lido do `Leia-me` → nome do arquivo →
  contagem de estratos distintos (nessa ordem, a última com aviso). Dois arquivos com o mesmo `N`
  → o segundo é descartado com aviso, para não duplicar linha no resumo.
- **`ler_n_estratos` conta só as obras `Selecionado`**: a aba traz o lote inteiro, e as linhas
  não sorteadas carregam rótulos de estrato que não existem na amostra.
- **`resumo_por_odi` tem esquema fixo mesmo vazio.** Uma aba `Amostra K` sem obra sorteada é
  possível; sem as colunas garantidas, o pandas devolve um df sem coluna nenhuma e o que consome
  o roteiro quebra (aconteceu, no mapa da época). `mapas.py` hoje só centraliza na base e não
  desenha ponto nenhum nesse caso.
- **`ler_painel` para na PRIMEIRA combinação (aba × linha de cabeçalho)** que produza
  `odi` + `latitude` + `longitude` — a ordem das abas do painel importa. `ler_amostras`, por
  outro lado, processa todas as abas `Amostra K` que existirem.
- **O Painel real tem DUAS linhas de cabeçalho.** O `Anexo V - Painel de Monitoramento` (saída do
  projeto irmão `monitoramentolpt_producao_enbpar`) traz na 1ª linha da aba `Preenchimento` uma
  faixa **mesclada** de grupos (`Identificação mínima` / `Classificação geral`); o cabeçalho real
  está na 2ª. Por isso `LINHAS_CABECALHO_PAINEL = (0, 1)`. Os nomes de coluna daquele projeto são
  **pétreos** (confirmado pelo humano) — daí `ALIAS_PAINEL` ser uma tabela fixa (`Número ODI`,
  `Número da Unidade Consumidora`) em vez de uma varredura heurística de layout.
- **`_norm_odi` é o que faz a junção funcionar.** A mesma ODI é TEXTO com zeros à esquerda no Lote
  (`'0012500186'`) e NÚMERO no Painel (`12500186`, às vezes float). Sem normalizar os dois lados,
  basta uma célula suja no Lote para a interseção dar zero e o programa acusar "tranche errada" —
  um erro **falso** e desnorteante. IDs não numéricos (fixtures `PA001`) passam intactos.
- **Município compara com `_norm`, não com `upper()`**: Lote grava `GURINHEM`, Painel `GURINHÉM`.
  Só a comparação sem acento evita o falso "município sem nenhuma UC no Painel" na regra do órfão.
- **Outros `.xlsx` com abas `Amostra K` na `Entrada/` são ignorados com AVISO** (`_avisar_lotes_ignorados`).
  O sistema upstream gera `Estratos 4/5/6 - Python.xlsx` e é natural sobrar algum lá; sem o aviso,
  o programa precificaria a estratificação errada em silêncio.
- **O nome do contrato aceita `-` ou `/`** (`_chave_contrato` colapsa espaço/hífen/barra e remove BOM):
  a base grafa `ECO 037/2025`, mas o usuário copia `ECO 037-2025` do nome do arquivo do Anexo V.
  Continua sendo casamento exato — verificado que as 113 chaves seguem únicas após a redução.
- **`Cons` é opcional no Lote**: ausente vira `0`, o que joga *toda* ODI órfã na regra do fallback
  (pseudo-UC no centroide municipal) em vez do caminho de erro. Painel incompleto passa despercebido.
- **Memória de cálculo duplicada de propósito** no topo de `src/config.py` e `src/custo.py`: quem
  abrir qualquer um dos dois entende o custo sem ler mais nada. Mantenha as duas cópias em sincronia.

## Modelo de custo (gate F1 aprovado em 2026-08-06 · corrigido na F9 · N equipes na F15)

```
custo_amostra = horas_escritório(tipo) × R$360 (1× por AMOSTRA)
                  LPT 8+24+4 = 36h → R$ 12.960 · MLA 4+16+4 = 24h → R$ 8.640
              + N_EQUIPES × TAMANHO_EQUIPE × dias_faturados × 8h × R$600/h

dias_faturados = teto(horas da equipe MAIS LENTA / (8h × TAMANHO_EQUIPE)) + DIAS_MOBILIZACAO

por equipe (o itinerário é cortado em N blocos contíguos, cada um roteado da capital):
  horas_campo    = horas_roteiro + horas_inspecao
  horas_roteiro  = (km do bloco + percursos internos) × FATOR_RODOVIARIO ÷ VELOCIDADE_KMH
  horas_inspecao = n_ucs do bloco × 8h / UCS_POR_DIA[tipo]   (LPT 30/dia, MLA 3/dia)
```

**O benchmark da engenharia** (`minhas_notas/Tabela_Resumo_Extratos_Amostra.xlsx`, aba `Resumo`,
PB 7ª Tranche) obedece a `12.960 + 9.600 × (dias+1)` com resíduo **zero** nos 3 pontos —
9.600 = 2 pessoas × 8h × R$600. É esta fórmula com `TAMANHO_EQUIPE = 2` e **`N_EQUIPES = 1`**
(uma dupla, um roteiro). O padrão daqui (`N_EQUIPES = 2`, `TAMANHO_EQUIPE = 1`) tem a mesma mão
de obra e custa **mais** — são dois roteiros, cada um pagando ida e volta.

A F9 corrigiu três desvios da implementação em relação ao `MODELO_CUSTO.md` já aprovado
(fixo por estrato em vez de por amostra; ida-e-volta por município em vez de itinerário único;
horas fracionárias em vez de dias inteiros). Juntos, superestimavam a amostra real em **+141%**.
A tabela do desvio está em `planning/MODELO_CUSTO.md` § "CORREÇÃO F9".

Decisões G1–G5 (equipe = ENGENHEIRO; diárias 0 pois a tarifa já embute; base de partida = capital
da UF do contrato; velocidade/fator rodoviário a calibrar; produtividade por tipo de contrato) estão
em `planning/PLAN.md` e derivadas em `planning/MODELO_CUSTO.md`. **Cada decisão é um parâmetro em
`config.py`** — mudar o modelo é mudar `config.py`, não `custo.py`.

`config.ARQUIVO_BASE_CONTRATOS` aponta para **`dados/base_contratos.json`** (113 contratos,
23 UFs; chave = nome do contrato, valores `uf`/`tipo_contrato` ∈ {LPT, MLA}/`vigente` ∈
{Andamento, Encerramento, Encerrado}) — a resolução de contrato depende dele para achar UF e tipo.
Três cuidados:

- **`dados/` é insumo de EXECUÇÃO, não pesquisa.** O arquivo morava em `minhas_notas/` até
  2026-08-11; saiu de lá porque o programa não roda sem ele e ele viaja no pacote enviado aos
  usuários — uma pasta "minhas_notas" não faz sentido na máquina de quem recebe.
- O arquivo **é versionado** (entrou no repo em `15bc69e`) e contém 113 contratos reais com
  valores. Está no git por decisão já tomada, não por acidente — e é o que permite o pacote
  funcionar em outra máquina.
- O valor é uma **string relativa**, não um `Path`. O orquestrador resolve contra `RAIZ`
  (não contra o cwd), senão `executar.bat` quebra quando chamado de outro diretório.

## Governança e documentação

- `planning/PLAN.md` — **documento-chave**: macrofases F0–F7, decisões e pendências. Registre progresso aqui.
- `planning/DESIGN.md` (D1–D8) · `planning/MODELO_CUSTO.md` (fórmula e fontes) ·
  `planning/PLANO_IMPLEMENTACAO.md` (plano passo a passo com código de cada task) ·
  `planning/definition of done.md` (critério de aceite por fase, para o humano acompanhar).
- `planning/LACUNAS_CENARIOS.md` — as 10 coisas que a aba `Cenarios` não modelava (L1–L10), com
  efeito em R$ e prioridade. **A F15 fechou cinco** (L1 km de dividir, L2 `Equipes` contando
  pessoas, L3 ocupação, L4 teto de equipes, L7 faixa fixa); as cinco abertas continuam ali, com
  o status marcado no topo de cada uma.
- Cada documento de planejamento novo ganha companion HTML autocontido em `planning/html/`
  (D4, inspirado em `planning/html-effectiveness/`). Existem hoje: `DESIGN.html`,
  `MODELO_CUSTO.html`, `PLANO_IMPLEMENTACAO.html`, `LACUNAS_CENARIOS.html` — `PLAN.md` ainda
  não tem companion.
- `planning/PROJECT_BUILDING.md` — checklist do humano, **somente leitura**.
- Glossário de status: `x` concluído · `f` revisão futura · `a` anulado · `n` não se aplica ·
  `r` rollback (falhou) · `[ ]` pendente.
- `suporte_contexto/` — contexto de apoio/bugfix; **hoje vazio**. Ainda não escritos:
  `planning/ADVERSARIAL_REVIEW.md` (D8), `planning/TESTES.md`.

## Insumos: `Entrada/` + `dados/` (runtime) vs `minhas_notas/` (pesquisa)

As três pastas de insumo, e a diferença entre elas:

| Pasta | Papel | Vai no pacote do usuário? |
| --- | --- | --- |
| `Entrada/` | planilhas que o usuário deposita a cada execução | sim, vazia |
| `dados/` | insumo fixo do programa (`base_contratos.json`) | sim, com o arquivo |
| `minhas_notas/` | material de **pesquisa**, nunca lido em execução | não |

O programa lê **só de `Entrada/`** (e de `dados/` para resolver o contrato):
- **N planilhas de amostra** — qualquer `.xlsx` com abas `Amostra K` (`Lote.xlsx`,
  `Estratos 4 - Python.xlsx`, ...). Todas são precificadas e comparadas no mesmo resumo.
- **1 arquivo de coordenadas** — nome contendo **`Anexo V`** (`io_amostras.PADRAO_ARQUIVO_COORDENADAS`,
  convenção D7); a aba é detectada pelas colunas, não pelo nome (ver as regras de cabeçalho/apelido
  acima). Na prática é o `Anexo V preenchido - <CONTRATO>.xlsx`. O padrão era
  `Painel de Monitoramento` até 2026-08-11 — mudou porque `Anexo V` é o rótulo do anexo no contrato,
  estável entre tranches e reconhecível pelo usuário.
`Entrada/` e `saida/` estão no `.gitignore` (conterão dados reais da distribuidora).

`minhas_notas/` é material de **pesquisa**, nunca entrada de execução:

| Arquivo | Papel |
| --- | --- |
| `Coordenadas_UCs_7ªTR_PA.xlsx` | exemplo do formato de coordenadas (aba `Base_UC`) |
| `CalculoDistancias.xlsx` | referência **sugerida** de forma de cálculo (não canônica) |
| `Formulário de Ordem de Serviço Equatorial-PA 4ª Tranche...xlsx` | **fonte canônica das tarifas E das horas de escritório** (aba `Custos Inspeções`: `E3:F6` tarifas, `E26:E29` horas por etapa — as duas keyed no `Tipo de obra` da célula `E48` da aba `Ordem de Serviço Emissão`) |
| `20260224_Tabela_Resumo_Estratos_Amostra.xlsx` | **gabarito do output** — cabeçalhos deslocados, ler com `header=None` |
| `Tabela_Resumo_Extratos_Amostra.xlsx` | **benchmark de CUSTO** (aba `Resumo`, ler com `header=None`): as 3 estratificações da PB 7ª Tranche com o custo estimado à mão pela engenharia. É o alvo de calibração da F9 |
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
