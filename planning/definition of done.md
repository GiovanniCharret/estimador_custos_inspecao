# Definition of Done — por fase

`x` concluído · `[ ]` pendente (mesmo glossário do PLAN.md)

Atualizado em 2026-08-10. Onde há uma parte automática (teste) e uma parte humana
(conferir com o olho), as duas estão separadas — o agente só marca a que ele mesmo
pode verificar.

x F0 — `pytest` passa; duplo-clique em `executar.bat` chega até a mensagem de
    "Lote nao encontrado" (comportamento correto sem entrada); repo git iniciado.
x F1 — `planning/MODELO_CUSTO.md` escrito + companion HTML + APROVAÇÃO HUMANA registrada no PLAN.md.
x F2 — `io_amostras` falha listando exatamente o que está errado; testes unitários passam (20).
x F2-humano — rodado com `Lote.xlsx` + Anexo V REAIS (contrato `ECO 037/2025`, ENERGISA/PB)
    em 2026-08-10: exit 0, 26 ODIs por amostra, 0 órfãos, 0 coordenada descartada.
    Três bloqueios e dois defeitos latentes corrigidos — ver F8 abaixo.
x F3 — distâncias validadas contra valores calculados à mão; testes passam (4).
x F4 — custo por ODI/estrato/amostra conforme MODELO_CUSTO.md aprovado; testes passam (4).
x F5 — `saida/Resumo_Custos.xlsx` gerado com Leia-me + `Amostra K` + `Detalhe K`; testes passam (2).
    [ ] **Falta a parte humana:** comparar o layout com o gabarito
        `minhas_notas/20260224_Tabela_Resumo_Estratos_Amostra.xlsx`.
x F6 — mapas HTML gerados com camadas por estrato e popup de custo; teste passa (1).
    [ ] **Falta a parte humana:** abrir um `Mapa_Amostra_K.html` no browser e conferir.
x F7 — e2e feliz + 8 bordas passam (16 testes); `planning/TESTES.md` escrito;
    status report `planning/html/STATUS_F7.html` gerado; `executar.bat` validado
    (sem entrada → "Lote.xlsx nao encontrado", exit 1, sem traceback).
x F18 — produtividade como terceira dimensão da grade (2026-08-19). Critérios:
    - a aba `Cenarios` tem a coluna `Produtividade (UCs/dia)` **antes** de `Equipes`, e no MLA
      traz dois blocos: 3,0 (oficial) e 1,5 (o número da engenharia);
    - a aba `Resumo` **não muda um centavo** ao se declarar uma alternativa — testado
      comparando as duas execuções linha a linha;
    - **exatamente uma** linha `calculado` por estratificação, sempre na produtividade oficial;
    - os km de cada nº de equipes são **idênticos** nos dois blocos (a geometria não sabe de
      produtividade); só as horas de inspeção mudam;
    - o bloco de 1,5 tem **menos** linhas (combinações que cabiam em 20 dias deixam de caber), e
      o `Leia-me` explica por quê;
    - 122 testes passando (115 → 122);
    - execução real (`ECM 022/2025`, amostra 1): a 1,5 UC/dia, o mínimo viável do estrato 3 com
      4 equipes é **14 dias / R$ 296.640** — a recomendação da engenharia, ao centavo.
    [ ] **Falta a parte humana:** abrir a aba `Cenarios` e conferir se os dois blocos ficaram
        legíveis lado a lado (613 linhas na tranche real, contra 343 antes).
x F17 — aba `Resumo beneficiarios` (2026-08-14). Critérios:
    - **transposta**: uma linha por categoria do domínio do Anexo V (`Dominios` D e E —
      24 categorias no arquivo real, lidas por posição) e uma coluna por estratificação;
    - **categoria com zero ocorrências aparece mesmo assim**, e nenhuma célula é nula
      (`int(0)` é o piso) — inclusive numa estratificação sem UC nenhuma;
    - a soma da coluna de uma estratificação é `2 × UCs`, porque cada UC entra em uma
      categoria de cada bloco;
    - as três fugas avisam em vez de sumir: categoria fora do domínio, classificação vazia
      e rótulo repetido nos dois domínios;
    - sem a aba `Dominios` e sem as colunas de classificação, a aba não é gerada;
    - 115 testes passando (101 → 115) e execução real (`ECO 037/2025`) com 27 linhas,
      4 colunas (rótulo + 3 estratificações) e zero nulos.
x F16 — horas de escritório por tipo de obra (2026-08-13). Critérios:
    - `config.HORAS_ESCRITORIO_POR_TIPO` traz o desdobramento por etapa do Formulário de OS
      (LPT 8+24+4 = 36h; MLA 4+16+4 = 24h), e não só o total;
    - o custo fixo de um contrato MLA cai de R$ 12.960 para R$ 8.640 por amostra;
    - `TARIFAS_HORA` passa a ser por tipo (só o técnico muda; o engenheiro é igual, então
      nenhum número muda hoje) e `tarifa_campo`/`tarifa_escritorio` recebem o tipo;
    - a aba `Resumo` ganha a coluna `Horas escritorio` e o `Leia-me` nomeia o tipo de obra
      como o formulário o chama, com o desdobramento das etapas;
    - o **tipo vem do prefixo do contrato** (`ECM` = Geração; qualquer outro = Extensão), e
      o `tipo_contrato` da base virou conferência: se discordar, sai `AVISO` e o prefixo
      vence — aplicado à base real, 112 dos 113 contratos ficam iguais;
    - 101 testes passando, com um teste que amarra as horas contra a planilha fonte (sem
      monkeypatch), um que garante que a diferença de tarifa do técnico não se perca, e um
      que reproduz o caso real `ECM 001/2020` (cadastro errado → aviso, prefixo vence).
x F15 — equipes independentes e grade de cenários (2026-08-13). Critérios:
    - o cálculo oficial assume `config.N_EQUIPES_PADRAO = 2` equipes **independentes**, e a
      aba `Resumo` traz `Equipes` e `Pessoas por equipe` como colunas distintas;
    - cada equipe tem o seu roteiro saindo da capital, então **o km de dividir entra no
      custo** (o número subiu: 26 obras na PB vão de R$ 41.760 com 1 equipe para R$ 60.960
      com 2) — a antiga ressalva do `Leia-me` virou conta;
    - o prazo é o da equipe **mais lenta**, e o `Detalhe` diz de qual equipe é cada obra;
    - a aba `Cenarios` é uma **grade** (1 a 7 equipes × até 20 dias por equipe) e mostra
      **só o viável**; o que não cabe não aparece e nem chega a ser roteado (pré-filtro
      pelas horas de inspeção — 80 UCs de MLA = 27 dias para 1 equipe, descartado antes);
    - o benchmark da engenharia continua reproduzido ao centavo, agora explicitamente como
      `TAMANHO_EQUIPE = 2` **com** `N_EQUIPES = 1` (uma dupla, um roteiro);
    - 95 testes passando (86 → 95), com testes novos para o km extra de dividir, o prazo da
      equipe crítica, os limites da grade e o descarte sem roteirizar.
x F14 — mapa reduzido a pontos (2026-08-13). Critérios:
    - `gravar_mapa(df_ucs, lat0, lon0, caminho)` — sem polilinha, sem número de parada,
      sem `GroupedLayerControl` e sem cor por equipe; um ponto por UC e o marcador da base;
    - o popup diz ODI, município e quantas UCs a obra tem — nada de ordem de visita;
    - o cálculo de custo **não muda**: `montar_roteiro` segue alimentando `custo.py`, e o
      `Resumo_Custos.xlsx` continua com as 4 abas e a aba `Cenarios` intacta;
    - o `Leia-me` da planilha passa a dizer que o mapa não recomenda rota;
    - 86 testes passando, com dois testes novos que provam a AUSÊNCIA de rota no HTML.
x F13 — chave de junção declarada pelo tipo do contrato (2026-08-11). Critérios:
    - `config.CHAVE_JUNCAO_POR_TIPO` (`LPT`→`ODI`, `MLA`→`UC`) decide a coluna do Anexo V
      **antes** de olhar os dados, e `juntar_amostras_painel` recebe `tipo_contrato`;
    - num painel **ambíguo** (a ODI de uma linha é a UC de outra) o mesmo Lote cai em linhas
      diferentes conforme o tipo — é o que prova que quem decide é o contrato, não o acaso;
    - contrato MLA imprime explicação (não é aviso de falha); a chave declarada falhando
      cai na reserva **com AVISO**, porque aí alguma premissa está errada;
    - 86 testes passando e a tranche RO (`ECM 022/2025`) rodando ponta a ponta.
x F12 — convenção `Anexo V`, chave MLA e pacote para os testadores (2026-08-11). Critérios:
    - o arquivo de coordenadas é localizado por `Anexo V`, e o erro de "não encontrado"
      lista os arquivos que existem na pasta (para o usuário ver que o nome está errado);
    - contrato MLA casa pela UC quando não casa pela ODI, com aviso — antes o programa
      recusava dados válidos dizendo "tranche errada" (verificado em `ECM 022/2025`);
    - `_exec.ps1` prepara o ambiente sozinho numa máquina sem Python, com fallback para o
      Python do sistema e mensagem acionável quando o proxy bloqueia;
    - `empacotar.ps1` gera `distribuicao/EstimadorCustos{,.zip}` com o mínimo + `LEIA-ME.txt`;
    - **validado**: pacote copiado para `C:\TesteEstimador` sem `.venv`, instalou-se sozinho
      e rodou a tranche RO ponta a ponta (exit 0, 4 estratificações, planilha + 4 mapas);
    - 83 testes passando.
x F11 — mapa com as rotas por equipe (2026-08-10). Critérios:
    - `dividir_roteiro` reparte as obras entre N equipes em blocos geográficos contíguos
      (nenhuma obra sem dono, nenhum município partido) e roteia cada bloco da capital;
    - o mapa traz um **radio** (`GroupedLayerControl`) com um cenário por nº de equipes,
      rotulado com o km somado — o painel "Amostra 1" deixou de existir;
    - uma cor e uma polilinha por equipe, popup dizendo equipe + ordem da parada;
    - o radio oferece exatamente os nºs de equipe que a aba `Cenarios` propõe;
    - 82 testes passando e execução real com exit 0.
x F10 — escolha da amostra + cenários de prazo (2026-08-10). Critérios:
    - o script pergunta qual amostra precificar (1/2/3, Enter = 1) e a escolha vale para a
      planilha inteira: `Resumo`, `Cenarios`, `Detalhe` e mapas;
    - estratificação sem a aba pedida é pulada com AVISO; nenhuma tendo, é erro de entrada;
    - aba `Cenarios` nova: para cada prazo de `calculado ± 2` dias, quantas equipes cabem,
      qual a ocupação e quanto custa — deixando visível que encurtar o prazo encarece;
    - `dias_trabalho` passa a dividir por `TAMANHO_EQUIPE` (Fase 6 do MODELO_CUSTO.md);
    - 74 testes passando e execução real com exit 0 nas amostras 1 e 2.
x F9 — reconstrução do modelo contra o benchmark da engenharia (2026-08-10). Critérios:
    - o roteiro é UM itinerário (capital → todas as obras → capital), não ida-e-volta por
      município: 1.529 km em vez de 10.521 km na amostra real;
    - o custo fixo de escritório entra **uma vez por amostra**, nunca por estrato;
    - dias arredondados para cima + 1 dia de mobilização (responde a pergunta P5 do gate);
    - `TAMANHO_EQUIPE` é parâmetro: em 1 (G1 reafirmado), em 2 reproduz o benchmark ao centavo
      (`test_reproduz_a_formula_do_benchmark_da_engenharia`);
    - `Resumo_Custos.xlsx` tem 3 abas fixas (`Leia-me`/`Resumo`/`Detalhe`), sem abertura por
      estrato, com TODAS as estratificações da `Entrada/` lado a lado;
    - um `Mapa_Estratos_N.html` por estratificação, camada por amostra, roteiro desenhado;
    - 68 testes passando e execução real com exit 0.
x F8 — adequação ao formato REAL de entrada (2026-08-10). Critérios:
    - `ler_painel` lê o Anexo V (1ª linha mesclada → cabeçalho na 2ª) e traduz
      `Número ODI`/`Número da Unidade Consumidora` por `ALIAS_PAINEL`;
    - o nome do contrato aceita `-` ou `/` (`ECO 037-2025` = `ECO 037/2025`);
    - a chave ODI casa entre Lote (texto com zeros) e Painel (número), via `_norm_odi`;
    - município compara sem acento (`GURINHEM` = `GURINHÉM`);
    - `.xlsx` extra com abas `Amostra K` na `Entrada/` gera AVISO em vez de silêncio;
    - 10 testes novos (48 no total) e execução real com exit 0.

---

## Placar (2026-08-11, pós-F13)

**86 testes passando. As 13 macrofases estão fechadas do lado do código, e o programa
roda ponta a ponta com dados REAIS de duas tranches de tipos diferentes** — `ECO 037/2025`
(PB, LPT) e `ECM 022/2025` (RO, MLA) — **inclusive a partir do pacote de distribuição
numa pasta limpa, sem Python instalado.**

O que a tranche RO (MLA, equipe = 1) entrega hoje, Amostra 1:

| Estratos | Obras | Municípios | km | Dias | Custo |
| --- | --- | --- | --- | --- | --- |
| 3 | 45 | 13 | 3.433 | 26 | R$ 137.760 |
| 4 | 22 | 9 | 2.802 | 17 | R$ 94.560 |
| 5 | 15 | 9 | 2.902 | 15 | R$ 84.960 |
| 6 | 12 | 8 | 2.313 | 12 | R$ 70.560 |

O que o programa entrega hoje para o contrato `ECO 037/2025`, **Amostra 1**
(equipe = 1, decisão G1):

| Estratos | ODIs | Municípios | UCs | Dias | Custo | Benchmark eng. (equipe 2) |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | 26 | 25 | 27 | 8 | R$ 51.360 | R$ 99.360 |
| 4 | 19 | 18 | 19 | 8 | R$ 51.360 | R$ 70.560 |
| 5 | 15 | 14 | 21 | 6 | R$ 41.760 | R$ 89.760 |

E os prazos alternativos (aba `Cenarios`, exemplo de 3 estratos):

| Cenário | Dias/equipe | Equipes | Ocupação | Custo total |
| --- | --- | --- | --- | --- |
| −2 dias | 5 | 2 | 69% | R$ 70.560 |
| −1 dia | 6 | 2 | 57% | R$ 80.160 |
| **calculado** | **7** | **1** | **99%** | **R$ 51.360** |
| +1 dia | 8 | 1 | 86% | R$ 56.160 |
| +2 dias | 9 | 1 | 77% | R$ 60.960 |

Repare que **encurtar o prazo encarece** (o contrato paga por hora-profissional, e cada
equipe traz seu dia de mobilização) e que o custo **não é monótono**: 5 dias sai mais barato
que 6, porque ambos precisam de 2 equipes e 5 dias é menos dia-equipe.

E o que a tabela ainda não cobra — dividir custa quilometragem (medido por `dividir_roteiro`;
o mapa mostrava isso até a F14, hoje o número só existe aqui e no `Leia-me`):

| Estratos | 1 equipe | 2 equipes | 3 equipes |
| --- | --- | --- | --- |
| 3 | 1.536 km | 2.100 km (+37%) | 2.501 km (+63%) |
| 4 | 1.560 km | 1.838 km (+18%) | 2.426 km (+56%) |
| 5 | 1.059 km | 1.301 km (+23%) | 1.832 km (+73%) |

(km em linha reta, antes do fator rodoviário). Os cenários multi-equipe da aba `Cenarios`
são portanto **otimistas** — está avisado no `Leia-me` da planilha.

As 2 pendências restantes são de conferência humana com o olho — nenhuma depende de
escrever mais código:

1. F5 — conferir o `saida/Resumo_Custos.xlsx` contra o benchmark
   `minhas_notas/Tabela_Resumo_Extratos_Amostra.xlsx` (aba `Resumo`). Lembrando: a diferença
   de ~44% é **decisão** (equipe 1 × 2), não erro — com `TAMANHO_EQUIPE = 2.0` os números
   caem na fórmula da engenharia.
2. F6 — abrir `saida/Mapa_Estratos_3.html` no browser e conferir se os pontos caem onde as
   obras deveriam estar (município certo, dentro da UF, nada no oceano).

Pendência de **calibração** (aberta, não bloqueia): `VELOCIDADE_KMH` (45) e `FATOR_RODOVIARIO`
(1,40) continuam sendo chutes da F1 e são os dois parâmetros que mais mexem no resultado.

Roteiro em `planning/TESTES.md`, seções "Primeira execução com dados reais" e
"Roteiro do teste manual".
