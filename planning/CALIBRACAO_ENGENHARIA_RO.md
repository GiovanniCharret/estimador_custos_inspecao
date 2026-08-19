# Calibração contra o dimensionamento da engenharia — RO 3ª Tranche (`ECM 022/2025`)

Escrito em 2026-08-19. Companion HTML: `planning/html/CALIBRACAO_ENGENHARIA_RO.html`.

> **Fonte:** `suporte_contexto/Tabela_Resumo_Extratos_Amostra.xlsx` — dimensionamento real feito
> pela engenharia para a 3ª Tranche de Rondônia (MLA/SIGFI, base de 862 registros). Abas usadas:
> `Resumo` (o número que vale, segundo o humano) e `Dimensionamento_Inspecao` (o relatório de
> método, 241 linhas).
> **Contraparte:** `distribuicao/EstimadorCustos/saida/Resumo_Custos.xlsx`, gerado por esta
> ferramenta com a mesma tranche (`ECM 022-2025`, amostra 1, 4 estratificações).

Este documento existe porque a comparação produziu um resultado incomum: **a nossa fórmula de
custo está certa e mesmo assim o número sai diferente.** Registrar só o "deu diferente" perderia a
informação que importa — *onde* a diferença mora, e qual dela é parâmetro (barato de mudar) e qual
é método (decisão de projeto).

---

## O que já bate, e bate exato

**A leitura dos dados é idêntica.** Nas quatro estratificações, UCs e municípios coincidem:

| Estratos | UCs (nosso / eng.) | Municípios (nosso / eng.) |
| --- | --- | --- |
| 3 | 45 / 45 | 13 / 13 |
| 4 | 22 / 22 | 9 / 9 |
| 5 | 15 / 15 | 9 / 9 |
| 6 | 12 / 12 | 8 / 8 |

**A fórmula de custo é a mesma, com resíduo zero.** A aba `Resumo` deles obedece, nas quatro
linhas, a

```
custo = 8.640 + 4.800 × equipes × (dias + 1)
```

que é exatamente o modelo F16 para MLA (24 h × R$ 360 = R$ 8.640 de escritório) com
`TAMANHO_EQUIPE = 1` e `DIAS_MOBILIZACAO = 1`:

| Estratos | Eq. | Dias | Engenharia | Conferência |
| --- | --- | --- | --- | --- |
| 3 | 4 | 14 | 296.640 | 8.640 + 4.800 × 4 × 15 ✓ |
| 4 | 2 | 7 | 85.440 | 8.640 + 4.800 × 2 × 8 ✓ |
| 5 | 2 | 5 | 66.240 | 8.640 + 4.800 × 2 × 6 ✓ |
| 6 | 2 | 4 | 56.640 | 8.640 + 4.800 × 2 × 5 ✓ |

O `Custo fixo OS` da nossa execução saiu **R$ 8.640** sem nenhum ajuste — a regra do prefixo
(`ECM` → Geração Descentralizada) acertou o tipo sozinha, e com ele as 24 h de escritório da F16.

**Conclusão:** a divergência não está no preço. Está inteira no **dimensionamento** — quantas
equipes e quantos dias.

| Estratos | Nosso (oficial) | Engenharia | Δ |
| --- | --- | --- | --- |
| 3 | 2 eq × 15 dias · R$ 162.240 | 4 eq × 14 dias · R$ 296.640 | −45% |
| 4 | 2 eq × 10 dias · R$ 114.240 | 2 eq × 7 dias · R$ 85.440 | +34% |
| 5 | 2 eq × 9 dias · R$ 104.640 | 2 eq × 5 dias · R$ 66.240 | +58% |
| 6 | 2 eq × 7 dias · R$ 85.440 | 2 eq × 4 dias · R$ 56.640 | +51% |

Note que o sinal **muda**: subestimamos a amostra eleita e superestimamos as três alternativas.
Não é viés de calibração; são duas causas diferentes agindo em direções opostas (D1 e D7 abaixo).

---

## As dez divergências

Nomeadas `D1`–`D10` para poderem ser citadas. A ordem é de efeito, não de importância.

### D1 — O número de equipes é constante aqui e derivado lá `MÉTODO`

Nosso oficial é sempre `config.N_EQUIPES_PADRAO = 2`. O deles sai da geografia:
`equipes = número de clusters logísticos ativos` — 4 em Rondônia (A Norte/Capital, B
Oeste/Mamoré, C BR-364, D Vale do Guaporé), com a regra explícita de **uma equipe por cluster**.

O detalhe que salva a nossa aba: a linha `4 equipes × 14 dias` **existe** na nossa grade e está
precificada em **R$ 296.640** — o número deles, ao centavo. Não falta conta; falta a **regra que
aponta qual célula é a resposta**.

### D2 — A produtividade do MLA está pela metade `PARÂMETRO`

`config.UCS_POR_DIA["MLA"] = 3,0`. Eles usam **1,50 UC/equipe/dia**, derivada de histórico real
(`ECM 015/2024`, RO 2ª tranche: 18 UCs ÷ (2 equipes × 6 dias efetivos), expurgando 2 dias de
deslocamento dos 8 do prazo).

**É o achado mais forte do documento.** Trocando só esse parâmetro e forçando 4 equipes, o nosso
motor devolve **14 dias e R$ 296.640** — resíduo zero contra a amostra eleita, por um caminho
completamente independente do deles (roteiro guloso sobre coordenadas × clusters e raios).

> **Fechado em 2026-08-19 (F18):** a aba `Cenarios` passou a varrer **também** 1,5 UC/dia
> (`config.UCS_POR_DIA_ALTERNATIVAS`). A aba `Resumo` continua no default de 3,0 — decisão do
> humano. Ver § "O que a F18 fez".

### D3 — O modelo de deslocamento é estruturalmente outro `MÉTODO`

| | Nós | Engenharia |
| --- | --- | --- |
| Forma | roteiro guloso município a município, **uma** volta única | por cluster: `2 × dist. rodoviária do município mais distante × 1,30` |
| Conversão | × 1,40 ÷ 45 km/h → **360 km/dia** | ÷ **480 km/dia** (60 km/h × 8 h) |
| Comportamento ao dividir | **cresce** | **constante** |

A consequência é a que mais confunde na mesa: o deslocamento deles é de 12–14 equipe-dias
*qualquer que seja o número de equipes*, porque cada cluster paga sua ida-e-volta de todo jeito. O
nosso cresce com a divisão — no estrato 3, de 9,5 para 12,0 para 16,4 equipe-dias com 1, 2 e 4
equipes. Por isso **"mais equipes encarece" aqui e é praticamente neutro lá**.

Curiosidade que desmonta a leitura fácil: os km deles são **maiores** (5.534 contra nossos 4.323
no estrato 3). Eles não andam menos — cada dia deles rende mais.

### D4 — O arredondamento acontece em granularidades diferentes `MÉTODO`

Eles aplicam teto **por cluster**, e duas vezes: `Σ ARRED.EXCESSO(UCs ÷ 1,5)` para inspeção e
`Σ ARRED.EXCESSO(rota ÷ 480)` para deslocamento. No estrato 3 isso dá 31 equipe-dias de inspeção
onde a conta pura daria 30. Nós aplicamos **um único** teto no fim, sobre a equipe mais lenta.

### D5 — Fator explícito de desbalanceamento de +10% `PARÂMETRO`

Eles multiplicam o esforço total por 1,10 antes de dividir pelas equipes — "realocação imperfeita
e retrabalho de rota". Nós não temos nenhum. É a lacuna **L9** de `LACUNAS_CENARIOS.md`, ainda
aberta, e agora com um valor de referência vindo de fora.

### D6 — Eles realocam trabalho entre equipes; nós proibimos `MÉTODO`

O prazo deles é `ARRED.EXCESSO(carga total × 1,10 ÷ equipes)` — divisibilidade perfeita, com a
recomendação escrita de "realocar a equipe que concluir primeiro". O nosso é o da **equipe mais
lenta**, sobre blocos geográficos contíguos que nunca se ajudam.

É a causa isolada de, com as **mesmas 2 equipes**, darmos 10/9/7 dias onde eles dão 7/5/4.

### D7 — Nos estratos 4, 5 e 6 o `Resumo` deles ignora o deslocamento `DADO`

Os dias saem de `UCs ÷ (1,5 × 2 equipes)` — 22→7, 15→5, 12→4 — com resíduo zero e **zero**
componente de viagem. Mas a aba `Dimensionamento_Inspecao`, no mesmo arquivo, calcula 13/12/13
equipe-dias de deslocamento para essas mesmas amostras e recomenda **4 equipes com 9, 8 e 8 dias**.

**As duas abas do arquivo deles discordam entre si.** Nenhuma calibração nossa reproduz essas três
linhas, porque elas não saíram de modelo nenhum: são o efetivo histórico de RO (2 equipes) vezes
uma regra de bolso de produtividade. Só a amostra eleita recebeu dimensionamento de verdade — as
outras três são referência de comparação.

Isso não é defeito a corrigir do lado deles nem do nosso: é **o motivo pelo qual o alvo de
calibração é a linha do estrato 3, e só ela**.

### D8 — "1 equipe por cluster" trava o prazo no caminho crítico `MÉTODO`

Com 4 equipes, o prazo de campo deles (13 dias) coincide exatamente com o cluster mais pesado
(C — eixo BR-364). É uma âncora geográfica que não temos: nossa `dividir_roteiro` equilibra km
acumulado, não regiões operacionais.

### D9 — Eles escolhem a amostra; nós listamos as quatro `ESCOPO`

Há uma matriz de decisão ponderada — robustez amostral 30%, eficiência logística 25%, prazo 20%,
esforço total 15%, concentração geográfica 10% — que elege o estrato 3 com score 0,650. O `Resumo`
deles **não é um comparativo de quatro alternativas**: é uma recomendação mais três referências.
O nosso apresenta as quatro em pé de igualdade.

### D10 — Parâmetros menores, todos na mesma direção `PARÂMETRO`

| Parâmetro | Nosso | Engenharia |
| --- | --- | --- |
| `VELOCIDADE_KMH` | 45 | 60 |
| `FATOR_RODOVIARIO` | 1,40 | 1,35 |

Sozinhos derrubam nosso prazo do estrato 3 de 15 para 13 dias — pouco perto de D2 e D6. É a
lacuna **L8** (velocidade/fator nunca calibrados), agora com um segundo par de valores para
comparar.

**Idênticos nos dois modelos:** base em Porto Velho (capital da UF), jornada de 8 h, 1 dia de
mobilização, e as 24 h de escritório do MLA.

---

## Uma ressalva de unidade, ainda aberta

R$ 4.800 por equipe-dia é `8 h × R$ 600` = **uma pessoa**. Nosso `TAMANHO_EQUIPE = 1` casa com
isso. Mas o texto deles chama o cenário de 2 de *"réplica do efetivo de Rondônia — 2 equipes"*, e
no benchmark da PB (LPT) a mesma engenharia usou R$ 9.600/dia, que é **dupla**.

Se em campo a equipe for uma dupla, os preços de RO estão para **metade** do efetivo. Confirmar
antes de calibrar qualquer coisa — a resposta muda o custo por um fator de 2, mais do que todas as
dez divergências somadas.

---

## O que a F18 fez (2026-08-19)

Decisão do humano, depois desta análise: **os cenários passam a considerar também
`UCS_POR_DIA["MLA"] = 1,5`; o `Resumo` continua no default de 3,0.**

Implementação:

- `config.UCS_POR_DIA_ALTERNATIVAS = {"MLA": [1.5]}` — produtividades **adicionais** varridas na
  grade. A oficial de `UCS_POR_DIA` entra sempre e não se repete aqui, para a tabela de
  alternativas não envelhecer quando alguém mudar o valor oficial.
- `custo.produtividades_da_grade(tipo)` — oficial primeiro, alternativas depois, sem repetidas.
- `custo.grade_cenarios` ganhou uma **terceira dimensão**: produtividade × equipes × prazo. Só a
  produtividade oficial pode marcar o cenário `calculado` (a ponte com o `Resumo`).
- `horas_por_uc` e `repartir_entre_equipes` aceitam `ucs_por_dia` opcional, para a varredura não
  tocar em `config` — o que vazaria para o custo oficial e para as outras estratificações da mesma
  execução.
- Nova coluna `Produtividade (UCs/dia)` na aba `Cenarios`, antes de `Equipes`, porque é a chave
  mais externa da grade.

**Por que uma coluna e não uma segunda planilha:** a pergunta que a aba responde deixou de ser
"quantas equipes e quantos dias" e passou a ser "quantas equipes, quantos dias **e sob qual
premissa de produtividade**". Separar em dois arquivos obrigaria a comparar duas planilhas para
responder a uma pergunta só.

O que a grade mostra na tranche real (amostra 1, `ECM 022/2025`):

| Estratos | Linhas 3,0 | Linhas 1,5 | Prazo mínimo com 4 equipes, a 1,5 |
| --- | --- | --- | --- |
| 3 | 64 | 37 | **14 dias → R$ 296.640** ← o número da engenharia |
| 4 | 87 | 71 | 8 |
| 5 | 93 | 75 | 8 |
| 6 | 99 | 87 | 7 |

A linha destacada é o resultado que dá confiança: **a 1,5 UC/equipe/dia, 14 dias com 4 equipes é
o mínimo viável do bloco** — o nosso modelo chega ao prazo recomendado pela engenharia por um
caminho independente, e não por ajuste.

O bloco alternativo tem sempre **menos** linhas: metade da produtividade dobra as horas de
inspeção, e combinações que cabiam em 20 dias deixam de caber. A grade encolher numa produtividade
e não na outra é informação, não defeito — e o `Leia-me` diz isso.

---

## Placar: o que fechar, em ordem de retorno

| # | Ação | Divergências que fecha | Esforço | Status |
| --- | --- | --- | --- | --- |
| 1 | Varrer 1,5 UC/dia nos cenários | D2 (parcial) | 1 parâmetro + 1 laço | **feito (F18)** |
| 2 | Regra de nº de equipes derivada da geografia | D1, D8 | precisa de clusterização | aberta |
| 3 | Fator de desbalanceamento (+10%) | D5 (= L9) | 1 parâmetro | aberta |
| 4 | Decidir a forma do deslocamento: por cluster ou por roteiro dividido | D3, D6 | decisão de modelo | aberta |
| 5 | Calibrar `VELOCIDADE_KMH` / `FATOR_RODOVIARIO` | D10 (= L8) | 2 parâmetros | aberta |
| 6 | Confirmar se "equipe" é 1 ou 2 pessoas | ressalva de unidade | 1 pergunta | **bloqueia tudo** |

O item 6 vem antes de todos na prática, mesmo estando por último na tabela: ele multiplica ou
divide o resultado dos outros cinco por 2.

D7 e D9 **não entram no placar**. D7 porque não há o que reproduzir (as três linhas alternativas
não vieram de modelo); D9 porque escolher a amostra é decisão de escopo, não de custo — se um dia
entrar, entra como funcionalidade nova, não como calibração.

---

## Como refazer esta comparação

```powershell
# 1. Entrada/ com a tranche certa (Anexo V + as N planilhas de estratificacao)
# 2. rodar o estimador
.\executar.bat            # contrato: ECM 022-2025 · amostra: 1

# 3. abrir lado a lado
#    saida/Resumo_Custos.xlsx                              abas Resumo + Cenarios
#    suporte_contexto/Tabela_Resumo_Extratos_Amostra.xlsx  abas Resumo + Dimensionamento_Inspecao
```

As abas de amostra do arquivo da engenharia (`Amostra 1_K_extrato_erro_5%`) trazem
`Latitude_UC`/`Longitude_UC` e `STATUS`, então dá para alimentar `distancias.resumo_por_odi`
direto delas, sem o Anexo V — foi assim que a primeira rodada desta análise foi feita, antes de a
tranche certa estar em `Entrada/`. Os dois caminhos produzem os mesmos km, dígito por dígito.
