# Definition of Done — por fase

`x` concluído · `[ ]` pendente (mesmo glossário do PLAN.md)

Atualizado em 2026-08-07. Onde há uma parte automática (teste) e uma parte humana
(conferir com o olho), as duas estão separadas — o agente só marca a que ele mesmo
pode verificar.

x F0 — `pytest` passa; duplo-clique em `executar.bat` chega até a mensagem de
    "Lote nao encontrado" (comportamento correto sem entrada); repo git iniciado.
x F1 — `planning/MODELO_CUSTO.md` escrito + companion HTML + APROVAÇÃO HUMANA registrada no PLAN.md.
x F2 — `io_amostras` falha listando exatamente o que está errado; testes unitários passam (12).
    [ ] **Falta a parte humana:** rodar com `Lote.xlsx` + Painel REAIS na `Entrada/`.
        `Entrada/` está vazia — nenhum arquivo real foi lido até hoje.
x F3 — distâncias validadas contra valores calculados à mão; testes passam (4).
x F4 — custo por ODI/estrato/amostra conforme MODELO_CUSTO.md aprovado; testes passam (4).
x F5 — `saida/Resumo_Custos.xlsx` gerado com Leia-me + `Amostra K` + `Detalhe K`; testes passam (2).
    [ ] **Falta a parte humana:** comparar o layout com o gabarito
        `minhas_notas/20260224_Tabela_Resumo_Estratos_Amostra.xlsx`.
x F6 — mapas HTML gerados com camadas por estrato e popup de custo; teste passa (1).
    [ ] **Falta a parte humana:** abrir um `Mapa_Amostra_K.html` no browser e conferir.
x F7 — e2e feliz + 8 bordas passam (12 testes); `planning/TESTES.md` escrito;
    status report `planning/html/STATUS_F7.html` gerado; `executar.bat` validado
    (sem entrada → "Lote.xlsx nao encontrado", exit 1, sem traceback).

---

## Placar (2026-08-07)

**38 testes passando. As 7 macrofases estão fechadas do lado do código.**

As 3 pendências restantes são todas de conferência humana com dados reais — nenhuma
depende de escrever mais código:

1. F2 — rodar com `Lote.xlsx` + Painel REAIS na `Entrada/` (hoje vazia).
2. F5 — comparar o `Resumo_Custos.xlsx` gerado com o gabarito de 24/02.
3. F6 — abrir um `Mapa_Amostra_K.html` no browser.

Roteiro passo a passo em `planning/TESTES.md`, seção "Teste manual com dados reais".
