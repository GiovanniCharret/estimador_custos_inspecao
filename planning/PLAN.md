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
x F14 — Mapa reduzido a pontos: saíram a polilinha, a numeração das paradas e o radio de
    equipes (decisão G7). O mapa localiza, não propõe itinerário — 2026-08-13
x F15 — **Equipes independentes** (decisão G8): padrão de 2 equipes, cada uma com o seu
    roteiro; aba `Cenarios` vira grade equipes × prazo, só com o viável — 2026-08-13
x F16 — **Horas de escritório por tipo de obra** (decisão G9): 36h no LPT, 24h no MLA,
    conforme o parâmetro `E48` do Formulário de OS — 2026-08-13
x F17 — **Aba `Resumo beneficiarios`** (decisão G11): perfil das UCs sorteadas por
    categoria do domínio do Anexo V, **transposta** (categoria por linha, estratificação
    por coluna) — 2026-08-14
x F18 — **Produtividade como terceira dimensão da grade** (decisão G12): a aba `Cenarios`
    varre também `UCS_POR_DIA_ALTERNATIVAS` (hoje MLA 1,5 UC/equipe/dia, o número da
    engenharia); a aba `Resumo` continua no default de 3,0 — 2026-08-19.
    Motivação e memória da comparação: `planning/CALIBRACAO_ENGENHARIA_RO.md`

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
- **G7 — O MAPA LOCALIZA, NÃO PROPÕE ITINERÁRIO (F14, decisão do humano em 2026-08-13):** saem do
  mapa a polilinha do roteiro, a numeração das paradas e o radio por nº de equipes; fica um ponto
  por UC, todos iguais, mais a base. O motivo é de leitura, não de código: a rota é **hipótese do
  modelo** (gulosa, linha reta, sem estrada real) e estava desenhada com a mesma tinta dos fatos
  (as coordenadas), o que a fazia parecer recomendação operacional. Sem rota não há o que
  repartir entre equipes, então o radio saiu junto e `gravar_mapa` voltou a
  `(df_ucs, lat0, lon0, caminho)`. O cálculo de custo **não muda** — `montar_roteiro` segue
  intacto em `distancias.py`.
- **G8 — DUAS EQUIPES INDEPENDENTES, E A GRADE DE CENÁRIOS (F15, decisão do humano em
  2026-08-13):** o cálculo oficial passa a assumir **2 equipes** (`config.N_EQUIPES_PADRAO`), não
  mais uma. Equipes são **independentes**: `custo.repartir_entre_equipes` corta o itinerário em N
  blocos contíguos e roteia cada um da capital, de modo que o km de dividir entra no número — a
  antiga L1 deixou de ser ressalva. O prazo é o da **equipe mais lenta**; todas são faturadas por
  ele. A aba `Cenarios` deixa de ser uma faixa de prazos e vira **grade equipes × prazo**, de
  `N_EQUIPES_MIN` a `N_EQUIPES_MAX` (1 a 7) e até `MAX_DIAS_POR_EQUIPE` (20) dias por equipe.
  **Combinação inviável não aparece nem é calculada** — um pré-filtro pelo limite inferior (só
  horas de inspeção) descarta antes de rotear. O caso que fixou a regra, dado pelo humano: 80 UCs
  de MLA a 3 UCs/dia são 213h = 27 dias só de inspeção para uma equipe; não há o que apresentar.
  Efeito no número: **o padrão ficou mais caro**, porque duas equipes pagam dois deslocamentos —
  na sondagem de 26 obras na PB, R$ 41.760 (1 equipe, 1.220 km) → R$ 60.960 (2 equipes, 1.663 km).
  Isso fecha as lacunas L1, L2, L3, L4 e L7 de `LACUNAS_CENARIOS.md`.
- **G11 — PERFIL DOS BENEFICIÁRIOS (F17, pedido do humano em 2026-08-14):** nova aba
  `Resumo beneficiarios` no `Resumo_Custos.xlsx`, **transposta** — uma **linha** por categoria
  das duas listas suspensas do Anexo V e uma **coluna** por estratificação. As categorias são
  `Tipo de Comunidade` (domínio na coluna **D** da aba `Dominios`, 12 opções) e
  `Enquadramento do beneficiário` (coluna **E**, 12 opções).
  A transposição foi pedida depois de ver a versão horizontal: 24 categorias de rótulo longo
  contra 3 estratificações não cabem na tela em colunas. Consequência técnica: a aba é gravada
  com `index=True, header=False` e lida com `header=None, index_col=0` — a primeira linha
  (`Estratos | 3 | 4 | 5`) já é o cabeçalho de fato. Responde a pergunta que o resto da planilha não responde: *quem* são as pessoas
  que a amostra vai visitar. **Não entra em nenhuma conta de custo** — por isso vive num módulo
  próprio, `src/beneficiarios.py`.
  Regras que o humano fixou: nenhuma célula nula, `int(0)` pode. Daí a lista de colunas vir do
  **domínio da planilha** e não dos valores presentes — categoria com zero ocorrências é
  informação, coluna ausente seria ambiguidade.
  **Correção de premissa feita na conversa:** o humano descreveu as colunas `D`/`E` como fonte
  das binárias `O:AZ`. São coisas diferentes: `D`/`E` são os domínios das colunas `M`/`N`
  (escolha única por UC), enquanto `O:AZ` são 38 flags `Sim`/`Não` cujo domínio é a coluna `F`
  (`CODIGO_TIPOLOGIA_BENEFICIO`). Ele escolheu `D`+`E`. As duas visões se sobrepõem — as 16 UCs
  com `2 - Comunidade quilombola` são as mesmas com `Sim` em `IV.2 - Família quilombola` —, então
  as tipologias `O:AZ` ficam disponíveis para uma fase futura sem retrabalho.
- **G12 — A PRODUTIVIDADE É A TERCEIRA DIMENSÃO DA GRADE (F18, decisão do humano em
  2026-08-19):** comparando o `Resumo_Custos.xlsx` com o dimensionamento que a engenharia fez
  para a 3ª tranche de RO (`ECM 022/2025`), a **fórmula de custo bateu ao centavo** — o que
  divergia era o dimensionamento, e a única diferença de parâmetro que explicava o prazo era a
  produtividade do MLA: **1,5 UC/equipe/dia** lá (histórico do `ECM 015/2024`), 3,0 aqui.
  Decisão: a aba `Cenarios` passa a varrer **as duas**; a aba `Resumo` **continua no default de
  3,0**. Implementado como `config.UCS_POR_DIA_ALTERNATIVAS` (produtividades *adicionais* — a
  oficial entra sempre e não se repete lá, para a tabela não envelhecer se alguém mudar o valor
  oficial) + `custo.produtividades_da_grade` + nova coluna `Produtividade (UCs/dia)`.
  **Só a produtividade oficial marca o cenário `calculado`**, senão a planilha teria dois números
  oficiais. Confirmação forte do valor: a 1,5 UC/dia, o **mínimo viável** do estrato 3 com 4
  equipes é **14 dias, R$ 296.640** — exatamente a recomendação da engenharia, por um caminho
  independente (roteiro guloso sobre coordenadas × clusters e raios).
  As nove divergências restantes estão catalogadas em `planning/CALIBRACAO_ENGENHARIA_RO.md`.
- **G9 — O TIPO DE OBRA MUDA AS HORAS DE ESCRITÓRIO (F16, achado do humano em 2026-08-13):** o
  Formulário de OS tem um parâmetro binário que o modelo ignorava — `Tipo de obra` (célula `E48`
  da aba `Ordem de Serviço Emissão`), lido pelas fórmulas `E26:E29` da aba `Custos Inspeções`:

  | etapa | Extensão de Redes (LPT / ECO) | Geração Descentralizada (MLA / ECM) |
  | --- | --- | --- |
  | Planejamento | 8 h | 4 h |
  | Relatório | 24 h | 16 h |
  | Apresentação | 4 h | 4 h |
  | **total** | **36 h → R$ 12.960** | **24 h → R$ 8.640** |

  As 36h que valiam para tudo eram as da **Extensão**, então **todo contrato MLA vinha com
  R$ 4.320 a mais por amostra**. Vira `config.HORAS_ESCRITORIO_POR_TIPO`, com o desdobramento por
  etapa preservado — é assim que a OS é preenchida e conferida.
  A etapa `Desenvolvimento` do formulário (112h LPT / 56h MLA) **não** entra: é o tempo de campo,
  que este projeto calcula da geometria em vez de assumir por tabela.
  As tarifas também são tabeladas por tipo (`E3:F6`), mas só o técnico muda — o engenheiro é
  600/360 nos dois. `TARIFAS_HORA` passou a ser por tipo mesmo assim, para não guardar meia
  verdade; com `PERFIL_EQUIPE = ENGENHEIRO` (G1) nenhum número muda por isso.
- **G10 — O TIPO VEM DO PREFIXO DO CONTRATO (decisão do humano em 2026-08-13):** a regra é
  binária — **`ECM` → Geração Descentralizada (MLA); qualquer outro prefixo → Extensão de Redes
  (LPT)**. Vale para `ECO`, `ECFS` e `ECOT` sem precisar citá-los. Implementada em
  `estimar_custos._tipo_pelo_prefixo`, com `config.PREFIXO_GERACAO_DESCENTRALIZADA`.
  **Por que o prefixo e não o cadastro:** o nome do contrato é o próprio documento; o
  `base_contratos.json` é cadastro e pode ter erro de digitação. Foi assim que apareceu
  `ECM 001/2020`, gravado como `LPT` — o humano confirmou que é erro e vai corrigir o JSON.
  O campo `tipo_contrato` continua sendo lido como **conferência**: divergência sai como `AVISO`
  e o prefixo vence, para o erro de cadastro aparecer em vez de ser escolhido em silêncio.
  Aplicando a regra na base real: **112 de 113 contratos ficam iguais**. Da base, só a **UF**
  segue sendo autoritativa.
- **Cuidado que a G8 cria:** `N_EQUIPES` (quantas) e `TAMANHO_EQUIPE` (pessoas em cada) são
  grandezas distintas e ambas multiplicam o custo. O benchmark da engenharia é
  `TAMANHO_EQUIPE=2, N_EQUIPES=1` — uma dupla num roteiro só. Confundir os dois é o erro que a
  antiga L2 já tinha armado; por isso a planilha traz as colunas `Equipes` e `Pessoas por
  equipe` lado a lado, e o `Leia-me` abre explicando a diferença.
- **F-futura — o roteiro volta, numa fase OPERACIONAL** (humano, 2026-08-13). A supressão da F14
  é de **visualização para decisão gerencial**, não de escopo: o itinerário desenhado tem lugar
  num produto voltado a quem vai a campo, onde a rota é o assunto e o leitor sabe que ela é
  sugestão. Quando essa fase existir, o que hoje é ruído volta a ser o conteúdo — e aí vale
  reabrir o que a F14 tirou (polilinha, ordem das paradas, divisão por equipe) **com estrada
  real**, não em linha reta, já que o público operacional vai cobrar isso.
- **Correção (F10):** `dias_trabalho` passou a dividir por `TAMANHO_EQUIPE`, como a Fase 6 do
  `MODELO_CUSTO.md` sempre prescreveu. Era invisível com equipe = 1; com equipe = 2 o custo
  dobrava em vez de ficar aproximadamente estável.
- **Pendência (pós-plano):** escrever `planning/ADVERSARIAL_REVIEW.md` (D8).