# PLAN — Estimador de custos de inspeção das amostras 

Construir um estimador realista dos custos de inspeção das amostras geradas através do script `minhas_notas\SistemaAmostralPython\gerar_planilhas.py`
Cada estrato gera 3 amostras, cada amostra tem uma ODIs e um geolocalização correpondente acessível no `minhas_notas\Coordenadas_UCs_7ªTR_PA.xlsx`

O executável, em liguagem python, dos cálculos precisa ser acessível via um arquivo .bat

Referências de formas de cálculo, não canônico, apenas sugerido estão disponíveis `minhas_notas\CalculoDistancias.xlsx` e `minhas_notas\Formulário de Ordem de Serviço Equatorial-PA 4ª Tranche - ECM 013-A-2023 (1).xlsx`

Output do scripts são os mapas e a tabela com os cálculos, como exemplificado em `minhas_notas\20260224_Tabela_Resumo_Estratos_Amostra` e `minhas_notas\Apresentação amostra COELBA 11a _ PA 7a_PA 4a_e_PI 8a e TO 2a_3a.pptx`, slide  3 e 4 somente. O restante dos slides, ignore. 

Os mapas com os pontos das coordenadas são parte do output. Originalmente são feitas através do QGIS. 
Sugestão de biblioteca para cálculos de geolocalização -> GeoPandas

> `PROJECT_BUILDING.md` não é alterado (checklist do humano). O controle do projeto do humano vive aqui.

## Glossário de status

`x` concluído · `f` revisão futura · `a` anulado · `n` não se aplica · `r` rollback (falhou) · `[ ]` pendente

## Macrofases

> Design aprovado: `planning/DESIGN.md` · Plano executável passo a passo: `planning/PLANO_IMPLEMENTACAO.md`
> Companions visuais: `planning/html/DESIGN.html` · `planning/html/PLANO_IMPLEMENTACAO.html`

x F0 — Infraestrutura: `src/`, venv uv 3.12, requirements, ritual `.bat`, git, `definition of done.md` — commit `cc15119`
x F1 — Estudo das referências → `MODELO_CUSTO.md` + companion HTML → **GATE: aprovação humana do modelo** — aprovado 2026-08-06, commits `26aa7f6`/`224719d`/`c2533de`
x F2 — `io_amostras`: localizar `Entrada/Lote.xlsx` + `*Painel de Monitoramento*`, ler amostras/UCs, juntar por ODI com validações — commits `0e3ec0c`/`e944905`/`a9f8ec8`
x F3 — `distancias`: haversine, centroide por ODI, rota interna (vizinho mais próximo) — commit `2e02acd`
x F4 — `custo.py`: fórmula aprovada na F1, parâmetros só em `config.py` — commit `bb50c25`
x F5 — `resumo.py`: `saida/Resumo_Custos.xlsx` (agregado por estrato + detalhe por ODI, por amostra) — commit `3ec9bdf`
x F6 — `mapas.py`: `saida/Mapa_Amostra_K.html` (folium, camadas por estrato, popup com custo) — commit `eb627ad`
x F7 — Orquestrador + e2e (feliz e bordas) + `TESTES.md` + status report HTML — 2026-08-07
x F8 — Adequação ao formato REAL de entrada (Anexo V do projeto irmão) após a 1ª execução
    com dados de verdade — 2026-08-10
x F9 — Reconstrução do modelo contra o benchmark da engenharia: roteiro encadeado, custo por
    amostra (não por estrato), dias inteiros, N estratificações numa planilha só — 2026-08-10
x F10 — Escolha da amostra (1/2/3, padrão 1) e aba `Cenarios` com prazos alternativos
    (dado o prazo, quantas equipes cabem) — 2026-08-10
x F11 — Mapa com a divisão real das obras entre equipes e painel de radio por nº de
    equipes (`dividir_roteiro` + `GroupedLayerControl`) — 2026-08-10
x F12 — Convenção `Anexo V`, chave de junção alternativa (MLA casa pela UC) e pacote
    autoinstalável para os usuários de teste (`_exec.ps1` + `empacotar.ps1`) — 2026-08-11
x F13 — Chave de junção **declarada** pelo tipo do contrato (`CHAVE_JUNCAO_POR_TIPO`),
    em vez de descoberta por tentativa-e-erro — 2026-08-11

> **Nota de acompanhamento (2026-08-07):** a sessão que executou F2–F6 foi interrompida por
> reboot do SO antes de marcar o progresso; os `x` de F0–F6 foram preenchidos retroativamente
> conferindo código + git log. A F7 foi executada em seguida na mesma sessão.
> **Estado verificado: 38 testes passando; `executar.bat` roda ponta a ponta.**
>
> **Nota de acompanhamento (2026-08-10):** o humano colocou os arquivos reais na `Entrada/`
> e a execução travou. Três bloqueios de formato + dois defeitos latentes foram corrigidos
> na **F8**; o programa agora roda ponta a ponta com dados de verdade (contrato `ECO 037/2025`,
> ENERGISA/PB, 26 ODIs por amostra, 0 órfãos). **48 testes passando.**
> Detalhes em `planning/TESTES.md` § "Primeira execução com dados reais".
>
> **Nota de acompanhamento (2026-08-10, F9):** o humano apontou que o custo estava
> superestimado e forneceu o benchmark da engenharia
> (`minhas_notas/Tabela_Resumo_Extratos_Amostra.xlsx`, aba `Resumo`). A engenharia reversa
> mostrou que o benchmark obedece **exatamente** à fórmula já aprovada no `MODELO_CUSTO.md`
> da F1 — quem tinha desviado era o **código**, em três pontos (fixo por estrato, ida-e-volta
> por município, horas fracionárias), somando **+141%** na amostra real. Reconstruído.
> **68 testes passando.**
>
> **Falta só conferência humana com o olho:** F5 (conferir o `Resumo_Custos.xlsx` contra o
> benchmark) e F6 (abrir um mapa no browser) — ver `definition of done.md`.

## Decisões e pendências

- Decisões D1–D8 registradas em `planning/DESIGN.md` §2 (modelo a propor; entrada = planilhas prontas; mapas folium; 1 HTML por doc de planejamento; arquitetura achatada em `src/`; `minhas_notas/` = pesquisa; nomes `Lote.xlsx` + "Painel de Monitoramento"; adversarial review depois do plano).
- Sem GeoPandas na v1: haversine via numpy cobre centroides/distâncias; GeoPandas só se surgir necessidade geoespacial real (shapefiles, projeções).
- Memória de cálculo para humanos: explicação simples do cálculo de custo (e do porquê) duplicada no topo de `src/config.py` e `src/custo.py`, derivada do `MODELO_CUSTO.md` aprovado.
- Git: commits locais regulares; **sem push** para o GitHub (publicação é decisão do humano).
- **GATE F1 APROVADO (2026-08-06)** — modelo de `MODELO_CUSTO.md` aprovado com as decisões abaixo; **cada decisão vira parâmetro em `config.py`** (ajustes futuros sem rebuild):
  - **G1 (equipe):** só engenheiro na estimativa (técnico raramente usado; não sobe em poste quem estima). Tarifas por perfil ficam parametrizadas, perfil ativo = ENGENHEIRO.
  - **G2 (diárias):** não entram — a tarifa horária "com deslocamento" já embute. Parâmetro `CUSTO_DIARIA = 0` existe para testes futuros.
  - **G3 (base de partida):** capital do estado (UF) do contrato. Multi-UF: `dados/base_contratos.json` (113 contratos, 23 UFs, tipo LPT/MLA, vigência) é a base; `config.py` carrega dicionário de capitais por UF. *(O arquivo morava em `minhas_notas/` até 2026-08-11; virou `dados/` por ser insumo de execução, não pesquisa.)*
  - **G4 (velocidade/fator rodoviário):** mantidos como parâmetros a calibrar (`VELOCIDADE_KMH = 45`, `FATOR_RODOVIARIO = 1.40`); aprimoramento futuro.
  - **G5 (produtividade):** substitui HORAS_POR_UC único por **`UCS_POR_DIA = {"LPT": 30, "MLA": 3}`** (LPT = obras com rede/transformador; MLA = fotovoltaico remoto) × `HORAS_DIA_CAMPO = 8`. O tipo do contrato vem do `base_contratos.json`.
- **Regra do órfão (assumida, não contestada no gate):** ODI sem coordenada no painel aborta SÓ se tiver UCs (`Cons. > 0`); com `Cons. = 0` (obra sem UC, ex.: reforço de rede) → aviso + fallback centroide do município. Afeta T3.
- **RESOLVIDO (F2/F8, 2026-08-10):** o formato real foi validado. O `Lote.xlsx` passou sem
  alteração; o Painel real é o **"Anexo V - Painel de Monitoramento"**, saída do projeto irmão
  `monitoramentolpt_producao_enbpar`, cujos cabeçalhos são **pétreos** (decisão do humano:
  tabela de apelidos fixa, sem varredura de layout). Exigiu: cabeçalho na 2ª linha (1ª é faixa
  mesclada), `ALIAS_PAINEL` (`Número ODI`, `Número da Unidade Consumidora`), normalização da
  chave ODI (Lote texto × Painel número) e comparação de município sem acento.
- **RESOLVIDO (F9, 2026-08-10):** a ida-e-volta por município foi substituída por um **itinerário
  único** (`distancias.montar_roteiro`): capital → todas as obras, município a município e obra a
  obra → capital, uma volta só. Nos dados reais: 1.529 km em vez de 10.521 km.
- **G1 REAFIRMADO (2026-08-10):** o humano manteve equipe = 1 engenheiro, ciente de que o
  benchmark da engenharia usa 2 e de que isso deixa a estimativa ~44% abaixo dele. Virou o
  parâmetro `config.TAMANHO_EQUIPE = 1.0` — mudar para `2.0` reproduz o benchmark sem rebuild.
- **P5 RESPONDIDA (F9):** os dias incluem **1 dia de mobilização** (`config.DIAS_MOBILIZACAO`),
  que é o `+1` do benchmark, e são arredondados para cima (a equipe não vende meio dia).
- **Pendência (calibração, aberta):** os dias da engenharia **não seguem a geometria** (a amostra
  de 5 estratos tem a rota mais curta e ganhou mais dias que a de 4). O modelo acerta −3,7% no
  agregado mas erra ±25% por amostra. `VELOCIDADE_KMH` e `FATOR_RODOVIARIO` (G4) seguem sendo
  os dois chutes com maior efeito.
- **P7 RESPONDIDA (F10):** o número de equipes não é fixo nem perguntado — vira uma **faixa**.
  A aba `Cenarios` inverte o cálculo (`config.VARIACAO_DIAS_CENARIOS = 2`): para cada prazo de
  `calculado ± 2` dias, mostra quantas equipes cabem e quanto custa. Confirma o alerta da Fase 6
  do `MODELO_CUSTO.md`: mais equipes não barateiam — **encarecem**, pelo dia de mobilização de
  cada equipe e pelo desperdício de arredondar para dia inteiro.
- **Decisão (F10):** cada execução precifica **uma** amostra (1, 2 ou 3; padrão 1), porque 2 e 3
  são reservas da 1 e nunca são usadas ao mesmo tempo. `config.AMOSTRA_PADRAO`.
- **D7 REVISADO (F12, 2026-08-11):** o arquivo de coordenadas é localizado por **`Anexo V`**
  (antes: `Painel de Monitoramento`). `Anexo V` é o rótulo do anexo no contrato — estável entre
  tranches e o que o usuário reconhece. Parâmetro `io_amostras.PADRAO_ARQUIVO_COORDENADAS`.
- **G6 — GAP SEMÂNTICO DO LEGADO (F12/F13, decisão do humano em 2026-08-11):** a chave de junção
  **muda com o tipo de contrato**. Em LPT o `ODI` do Lote casa com `Número ODI` do Anexo V; em
  **MLA** cada obra é um sistema individual e o legado, sem número de ODI próprio, reaproveitou a
  coluna para guardar o **número da UC** — que casa com `Número da Unidade Consumidora`. Na 3ª
  Tranche RO (`ECM 022/2025`) 862 de 862 obras casam pela UC e nenhuma pela ODI; o programa
  acusava "tranche errada" em dados válidos.
  Vira o parâmetro `config.CHAVE_JUNCAO_POR_TIPO = {"LPT": "ODI", "MLA": "UC"}`. A escolha é
  **declarada**, não adivinhada: uma heurística de tentativa-e-erro casaria pela linha errada em
  silêncio se um número de UC coincidisse com um de ODI. A verificação contra os dados fica só
  como rede de segurança (contrato não informado / tipo errado na base), e aí emite `AVISO`.
- **Distribuição (F12):** `empacotar.ps1` monta `distribuicao/EstimadorCustos{,.zip}` com o mínimo
  para rodar. O `_exec.ps1` instala uv + Python 3.12 + bibliotecas na primeira execução (fallback
  para o Python do sistema). Exige internet; `distribuicao/` está no `.gitignore`.
- **Pendência aberta pela F11 — o custo de dividir não está no custo.** `dividir_roteiro`
  mediu a divisão real das obras entre equipes: 2 equipes rodam **+18% a +37%** mais km que
  uma, porque cada uma sai da capital e volta. A aba `Cenarios` ainda assume trabalho
  perfeitamente divisível, então seus cenários multi-equipe são **otimistas**. O mapa mostra
  o km real e o `Leia-me` avisa. Decidir se `cenarios_por_prazo` passa a usar a geometria real
  (encareceria os cenários de prazo curto e daria consistência total entre mapa e planilha).
- **Correção (F10):** `dias_trabalho` passou a dividir por `TAMANHO_EQUIPE`, como a Fase 6 do
  `MODELO_CUSTO.md` sempre prescreveu. Era invisível com equipe = 1; com equipe = 2 o custo
  dobrava em vez de ficar aproximadamente estável.
- **Pendência (pós-plano):** escrever `planning/ADVERSARIAL_REVIEW.md` (D8).