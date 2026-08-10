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

## Placar (2026-08-10, pós-F10)

**74 testes passando. As 10 macrofases estão fechadas do lado do código, e o programa
roda ponta a ponta com dados REAIS de uma tranche.**

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

As 2 pendências restantes são de conferência humana com o olho — nenhuma depende de
escrever mais código:

1. F5 — conferir o `saida/Resumo_Custos.xlsx` contra o benchmark
   `minhas_notas/Tabela_Resumo_Extratos_Amostra.xlsx` (aba `Resumo`). Lembrando: a diferença
   de ~44% é **decisão** (equipe 1 × 2), não erro — com `TAMANHO_EQUIPE = 2.0` os números
   caem na fórmula da engenharia.
2. F6 — abrir `saida/Mapa_Estratos_3.html` no browser, ligar/desligar as camadas de amostra
   e conferir se a linha do roteiro faz sentido geográfico.

Pendência de **calibração** (aberta, não bloqueia): `VELOCIDADE_KMH` (45) e `FATOR_RODOVIARIO`
(1,40) continuam sendo chutes da F1 e são os dois parâmetros que mais mexem no resultado.

Roteiro em `planning/TESTES.md`, seções "Primeira execução com dados reais" e
"Roteiro do teste manual".
