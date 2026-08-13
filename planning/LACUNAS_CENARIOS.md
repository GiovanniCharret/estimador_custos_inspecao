# O que a aba `Cenarios` ainda NÃO modela

Escrito em 2026-08-13. Companion HTML: `planning/html/LACUNAS_CENARIOS.html`.

Este documento existe porque a aba `Cenarios` é a que vai para a mesa de decisão — é ela que
responde *"e se eu precisar terminar antes?"* — e é também a que mais assume coisas sem dizer.
O `Leia-me` da planilha avisa da principal em duas linhas; aqui estão **todas**, com o efeito
esperado em R$, para que a decisão de quais fechar seja sua e não do acaso.

Nada aqui é bug: o programa faz o que foi especificado. São **limites conhecidos do modelo**.

---

## O que a aba faz hoje (o piso do qual as lacunas partem)

`custo.cenarios_por_prazo` inverte o cálculo principal. Em vez de "dada a equipe, quantos dias",
ela pergunta "dado o prazo, quantas equipes cabem":

```
para cada dias em [calculado − 2 ... calculado + 2]:
    equipes        = teto(horas_campo / (8h × dias))
    dias_faturados = dias + DIAS_MOBILIZACAO
    custo_campo    = equipes × dias_faturados × 8h × R$600
    custo_total    = custo_campo + R$12.960
```

`horas_campo` vem do cálculo de **uma** equipe e nunca é recalculado. Essa única frase é a raiz
de três das lacunas abaixo.

---

## L1 — O quilômetro de dividir não entra no custo

**A maior, e a única já avisada ao usuário.**

A aba trata o trabalho como **perfeitamente divisível**: assume que N equipes rodam os mesmos km
que uma. Na prática cada equipe sai da capital e volta a ela, então a quilometragem **somada**
cresce. `distancias.dividir_roteiro` faz a divisão real e mede quanto:

| Estratificação (PB, LPT, Amostra 1) | 1 equipe | 2 equipes | 3 equipes |
| --- | --- | --- | --- |
| 3 estratos | 1.536 km | 2.100 km (**+37%**) | 2.501 km (+63%) |
| 4 estratos | 1.560 km | 1.838 km (**+18%**) | 2.426 km (+56%) |
| 5 estratos | 1.059 km | 1.301 km (**+23%**) | 1.832 km (+73%) |

(km em linha reta, antes do fator rodoviário — medidos em execução real.)

**Efeito:** os cenários multi-equipe são **otimistas**. O custo real de encurtar o prazo é maior
que o da tabela, e a diferença cresce com o número de equipes. Como encurtar o prazo já encarece
no modelo atual, fechar esta lacuna **acentua** a conclusão que a aba já entrega — não a inverte.

**Por que ainda não foi fechada:** exige realimentar `cenarios_por_prazo` com a geometria de
`dividir_roteiro` (hoje ele só recebe `numeros`, um dicionário sem geometria), e isso torna o
cálculo iterativo — mais km significa mais horas, que podem exigir mais um dia, que muda a
divisão. Precisa de uma decisão sobre onde parar a iteração.

**Custo de não fechar:** um prazo curto aprovado com base num número que subestima o próprio
prazo curto.

---

## L2 — A coluna `Equipes` conta PESSOAS, não equipes

Só aparece se `TAMANHO_EQUIPE` deixar de ser `1`. Como o benchmark da engenharia usa `2` e esse
é o valor que reproduz os números dela ao centavo, é um cenário provável, não hipotético.

`cenarios_por_prazo` **não usa `config.TAMANHO_EQUIPE` em lugar nenhum**: nem em
`equipes = teto(horas / (8 × dias))`, nem em `custo_campo = equipes × dias × 8 × tarifa`. A
variável `equipes` conta, na verdade, *unidades de uma pessoa*.

Sondagem com `TAMANHO_EQUIPE = 2.0` (amostra sintética de 12 obras):

| Cenário | Dias | "Equipes" | Custo | Leitura correta |
| --- | --- | --- | --- | --- |
| −2 dias | 1 | 5 | R$ 60.960 | 5 **pessoas**, não 5 duplas |
| calculado | 3 | 2 | R$ 51.360 | 1 dupla — bate com o `Resumo` |
| +2 dias | 5 | 1 | R$ 41.760 | **1 pessoa sozinha**, quebrando a dupla |

Duas consequências:

1. A linha `calculado` bate com a aba `Resumo` por **coincidência aritmética** (`dias_trabalho` já
   foi dividido por `TAMANHO_EQUIPE`, então `teto(horas/(8×dias))` cai de volta em ≈ `TAMANHO_EQUIPE`).
   As demais linhas não têm essa proteção.
2. A aba propõe silenciosamente **desfazer a equipe** (a linha `+2 dias` acima manda 1 pessoa a
   campo), contradizendo a premissa de que a dupla é indivisível.

Agrava: o `Resumo` tem uma coluna **`Equipe`** (= `TAMANHO_EQUIPE`, pessoas por equipe) e o
`Cenarios` tem **`Equipes`** (contagem). Dois nomes quase idênticos, duas grandezas diferentes.

**Efeito:** hoje, zero — com `TAMANHO_EQUIPE = 1.0` as duas leituras coincidem. No dia em que
alguém mudar para `2.0` para conversar com a engenharia, a aba passa a mentir sem avisar.

---

## L3 — A ocupação da equipe está superestimada

`ocupacao = horas_campo / (8h × dias × equipes)` usa o `horas_campo` de **uma** equipe. Como o km
real cresce ao dividir (L1), a ocupação verdadeira dos cenários multi-equipe é **maior** que a
exibida — a equipe está mais ocupada do que a planilha diz, rodando estrada.

**Efeito:** a coluna que existe justamente para revelar desperdício (ocupação baixa = pagando por
gente parada) subestima o trabalho real. Uma ocupação de 59% pode ser folga aparente que na
prática é tempo de deslocamento não contabilizado.

Mesma raiz de L1: fecha junto.

---

## L4 — Não existe teto de equipes disponíveis

A aba propõe o número de equipes que a matemática pedir. Na sondagem acima ela chegou a **5** para
uma amostra de 12 obras. Nada no modelo pergunta se há 5 equipes, se a contratada consegue
mobilizá-las, ou se faz sentido operacional.

**Efeito:** cenários fisicamente impossíveis apresentados com a mesma autoridade dos viáveis.

**Custo de fechar:** baixo — um `MAX_EQUIPES` em `config.py` e o descarte (ou a marcação) dos
cenários acima do teto. É a lacuna de melhor relação esforço/benefício da lista.

---

## L5 — O custo fixo de escritório não varia com o número de equipes

Todos os cenários carregam os mesmos R$ 12.960 (36h × R$360), uma vez por amostra. A premissa é
que a Ordem de Serviço é uma só, independentemente de quantas equipes vão a campo.

É defensável — uma amostra, um relatório. Mas é **premissa não verificada**: coordenar 3 equipes,
consolidar 3 cadernos de campo e conciliar divergências plausivelmente custa mais horas de
escritório que coordenar uma.

**Efeito:** se a premissa for falsa, reforça L1 na mesma direção (cenários multi-equipe otimistas).

---

## L6 — Diária/pernoite continua zerada nos cenários longos

`CUSTO_DIARIA = 0.0` por decisão G2: a tarifa de R$600/h já embutiria hospedagem e alimentação.
A decisão foi tomada olhando o caso base.

Ela fica mais tensionada exatamente onde os cenários vivem: prazos longos no interior, com mais
equipes e mais pernoites. E a aba não tem como mostrar isso, porque o parâmetro é constante.

**Efeito:** se a tarifa não cobrir pernoite de fato, o erro cresce com o prazo — e a aba
`Cenarios` é a que mais varia prazo.

---

## L7 — A faixa é fixa em ±2 dias, não proporcional

`VARIACAO_DIAS_CENARIOS = 2` vale para qualquer amostra. Isso significa janelas muito diferentes:

| Amostra real | Prazo calculado | Faixa explorada | O que ±2 representa |
| --- | --- | --- | --- |
| RO, 3 estratos | 26 dias | 24–28 | ±8% — janela estreita demais para ser útil |
| PB, 5 estratos | 6 dias | 4–8 | ±33% — proporção razoável |
| amostra pequena | 2 dias | 1–4 | assimétrica: bate no piso de 1 dia |

**Efeito:** em amostras grandes a aba oferece cinco cenários quase idênticos; em amostras pequenas
ela trunca de um lado. Fechar seria trocar a variação absoluta por percentual (ou por uma faixa
declarada em `config.py` por porte de amostra).

---

## L8 — Velocidade e fator rodoviário continuam sendo chutes da F1

`VELOCIDADE_KMH = 45` e `FATOR_RODOVIARIO = 1,40` (decisão G4, nunca calibrados) entram em
`horas_roteiro`, que é metade de `horas_campo`, que é a entrada de **todos** os cenários.

Atenuante importante: como os dois parâmetros afetam todos os cenários igualmente, a **comparação
entre cenários** sobrevive. O que não sobrevive é o **valor absoluto**.

**Efeito:** a aba é confiável para escolher *entre* prazos, e não para prometer um número.

---

## L9 — Não há contingência, e há evidência de que a engenharia usa uma

A aba não reserva nada para chuva, acesso impedido, obra não localizada ou retrabalho. O modelo é
determinístico: mesma geometria, mesmo prazo, sempre.

Há um indício concreto de que isso importa. Ao calibrar contra o benchmark da engenharia (F9),
ficou registrado que os dias deles **não são geométricos**: a estratificação de 5 estratos tem o
roteiro mais curto e, ainda assim, o maior número de dias. Nenhum modelo determinístico reproduz
8/5/7 dias a partir da geometria — o que sobra é julgamento que o modelo não tem.

**Efeito:** os prazos da aba são **pisos técnicos**, não compromissos. Vale dizer isso ao lado da
tabela quando ela for apresentada.

---

## L10 — Os cenários variam só o prazo

Ficam fora todas as outras alavancas: perfil da equipe (`TECNICO` custa R$513,22/h de campo contra
R$600 do `ENGENHEIRO`), produtividade (`UCS_POR_DIA`), e a escolha da estratificação em si — que
hoje se compara na aba `Resumo`, mas nunca cruzada com prazo.

**Efeito:** a conversa de planejamento fica restrita a "mais rápido custa mais", quando existem
outras trocas a fazer. Não é lacuna de exatidão, é de escopo.

---

## Prioridade sugerida

| # | Lacuna | Erra o R$? | Esforço | Prioridade |
| --- | --- | --- | --- | --- |
| L4 | sem teto de equipes | não (erra a viabilidade) | baixo | **1º — melhor relação** |
| L2 | `Equipes` conta pessoas | sim, se `TAMANHO_EQUIPE ≠ 1` | baixo | **2º — armadilha armada** |
| L1+L3 | km de dividir e ocupação | **sim, subestima** | alto (iterativo) | **3º — a que mais importa** |
| L7 | faixa fixa ±2 dias | não | baixo | 4º |
| L9 | sem contingência | sim, subestima | decisão, não código | 5º |
| L8 | velocidade/fator | sim, no absoluto | médio (dados externos) | 6º |
| L5 | fixo constante | talvez | decisão | 7º |
| L6 | diária zerada | talvez | decisão | 8º |
| L10 | só varia prazo | não | médio | 9º |

**Recomendação:** L4 e L2 primeiro. São baratas, e L2 é uma armadilha já armada — dispara no dia
em que alguém mudar `TAMANHO_EQUIPE` para conversar com a engenharia, que é justamente quando a
planilha estará sob mais escrutínio. Só depois L1+L3, que é a correção de fundo.

---

## Onde cada coisa vive

| Assunto | Arquivo |
| --- | --- |
| a fórmula dos cenários | `src/custo.py::cenarios_por_prazo` |
| a medição do km real de dividir | `src/distancias.py::dividir_roteiro` |
| todos os parâmetros citados | `src/config.py` |
| o aviso que hoje chega ao usuário | `src/resumo.py::_texto_leia_me` |
| a decisão que originou L1 | `planning/PLAN.md`, pendência aberta pela F11 |
| o modelo de custo aprovado | `planning/MODELO_CUSTO.md` |
