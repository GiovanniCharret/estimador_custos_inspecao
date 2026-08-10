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
x F8 — adequação ao formato REAL de entrada (2026-08-10). Critérios:
    - `ler_painel` lê o Anexo V (1ª linha mesclada → cabeçalho na 2ª) e traduz
      `Número ODI`/`Número da Unidade Consumidora` por `ALIAS_PAINEL`;
    - o nome do contrato aceita `-` ou `/` (`ECO 037-2025` = `ECO 037/2025`);
    - a chave ODI casa entre Lote (texto com zeros) e Painel (número), via `_norm_odi`;
    - município compara sem acento (`GURINHEM` = `GURINHÉM`);
    - `.xlsx` extra com abas `Amostra K` na `Entrada/` gera AVISO em vez de silêncio;
    - 10 testes novos (48 no total) e execução real com exit 0.

---

## Placar (2026-08-10)

**48 testes passando. As 8 macrofases estão fechadas do lado do código, e o programa
já rodou ponta a ponta com dados REAIS de uma tranche.**

As 2 pendências restantes são de conferência humana com o olho — nenhuma depende de
escrever mais código:

1. F5 — comparar o `saida/Resumo_Custos.xlsx` gerado (contrato `ECO 037/2025`) com o
   gabarito `minhas_notas/20260224_Tabela_Resumo_Estratos_Amostra.xlsx`.
2. F6 — abrir `saida/Mapa_Amostra_1.html` no browser e ligar/desligar as camadas de estrato.

E uma **decisão de modelo** que os dados reais tornaram visível (não é bug): ~88% do custo
da Amostra 1 é deslocamento, porque a decisão G3 faz uma ida-e-volta da capital **por
município** e as 26 ODIs estão em 25 municípios. Vale confirmar se é assim que a inspeção
acontece na prática, ou se convém encadear municípios numa viagem só.

Roteiro em `planning/TESTES.md`, seções "Primeira execução com dados reais" e
"Roteiro do teste manual".
