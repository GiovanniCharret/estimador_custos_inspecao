# MODELO DE CUSTO — Estimador de custos de inspeção das amostras

> Fase **F1** do `planning/PLAN.md`. Documento de **pesquisa e proposta**.
> Nada aqui vira código antes da aprovação humana (gate D1 do `planning/DESIGN.md`).
> Companion visual: `planning/html/MODELO_CUSTO.html`.
>
> Todos os números deste documento foram extraídos com pandas/openpyxl dos arquivos de
> `minhas_notas/` em 2026-08-06. Onde há chute, está escrito "chute".

---

## Sumário executivo (leia isto se só tiver 2 minutos)

1. **A fórmula de custo do órgão já existe e foi decifrada.** Ela é:
   `Custo = R$ 12.960 + R$ 4.800 × (equipes × dias de campo)`.
   Essa fórmula reproduz **exatamente** (centavo a centavo) 7 das 11 estimativas
   publicadas na apresentação à Diretoria, e as outras 4 com um resíduo fixo de ~R$ 4.000.
2. **O que ninguém sabe calcular é o "dias de campo".** A própria apresentação admite:
   os dias vêm de "condições logísticas dos municípios" — ou seja, do julgamento de quem planeja.
3. **É exatamente esse buraco que este projeto preenche**: substituir o julgamento por
   geometria (haversine + centroide por ODI + rota vizinho-mais-próximo), mantendo a
   fórmula contratual de preço intacta.
4. **Constante empírica mais robusta encontrada**: **≈ 20 UCs inspecionadas por equipe por dia**
   (mediana 20,2; 11 amostras de 2 distribuidoras diferentes). É a âncora para calibrar o modelo.

---

## (a) O que as referências fazem

### a.1 `Formulário de Ordem de Serviço Equatorial-PA 4ª Tranche` — a fonte canônica do preço

Esta planilha **é o contrato virando conta**. Ela tem 11 abas; três importam.

**Aba `Custos Inspeções`** — a tabela de tarifas do Edital:

| Área de conhecimento | Perfil | R$/h **sem** deslocamento | R$/h **com** deslocamento |
|---|---|---|---|
| Extensão de Redes de Distribuição | Eng. Eletricista | 360,00 | **600,00** |
| Extensão de Redes de Distribuição | Eletrotécnico | 250,00 | 593,00 |
| Sistemas de Geração Descentralizada | Eng. Generalista | 360,00 | **600,00** |
| Sistemas de Geração Descentralizada | Técnico | 273,22 | 513,22 |

E a tabela de **tempo previsto por etapa (h)**:

| Etapa | Extensão de Rede | Geração | Tarifa aplicada |
|---|---|---|---|
| Planejamento | 8 | 4 | 360 (sem deslocamento) |
| **Desenvolvimento (campo)** | 112 | 56 | **600 (com deslocamento)** |
| Relatório | 24 | 16 | 360 (sem deslocamento) |
| Apresentação | 4 | 4 | 360 (sem deslocamento) |

> **Descoberta-chave nº 1:** a etapa "Desenvolvimento" é a única que usa a tarifa
> **com deslocamento**. A planilha não tem nenhuma linha de diária, hotel, combustível,
> pedágio ou aluguel de veículo. Logo, **a tarifa de R$ 600/h já é "cheia"**: viagem,
> hospedagem, alimentação e veículo estão embutidos no diferencial de R$ 240/h
> (600 − 360). Isso resolve, de saída, a pergunta "diárias entram no modelo?": **não
> entram como linha separada** — a menos que o humano queira modelar por fora do contrato.

**Aba `Composição Equipes Inspeção`** — como as horas de campo viram dinheiro. As fórmulas reais:

```excel
horas_equipe_i  = (data_fim − data_inicio + 1) × 8            ' 8 h por dia corrido
custo_equipe_i  = (600 × n_engenheiros + 513,22 × n_tecnicos) × horas_equipe_i
```

Na 4ª tranche real: 6 equipes, 1 engenheiro eletricista cada, 0 técnicos.
Períodos de 03/08 a 08/08 (6 dias = 48 h), exceto a EQUIPE 03 (5 dias = 40 h) e a
EQUIPE 06 (1 dia = 8 h). Total: **240 h · R$ 144.000**.

> **Descoberta-chave nº 2:** a unidade de cobrança é a **hora-profissional**, e cada
> equipe é **1 profissional**. Portanto "equipe-dia" = 8 horas faturáveis. Como a
> conta é uma soma de horas, **o número de equipes não muda o custo total** — muda
> só quantos dias de calendário a campanha dura. Isso é importante: o nosso modelo
> deve estimar **HORAS** (que definem o custo) e derivar os **DIAS** como um segundo
> resultado (que define a agenda).

**Aba `Ordem de Serviço Emissão`** — a nota fechada da 4ª tranche PA:

| Profissional | Etapa | Nº prof. | Horas | R$/h | Total |
|---|---|---|---|---|---|
| Engenheiro | Planejamento | 1 | 4 | 360 | 1.440 |
| Engenheiro | **Desenvolvimento** | 6 | **240** | **600** | **144.000** |
| Engenheiro | Relatório | 1 | 16 | 360 | 5.760 |
| Engenheiro | Apresentação | 1 | 4 | 360 | 1.440 |
| | | | | **TOTAL** | **152.640** |

Depois há um desconto por qualidade: **IMR** (aba própria) — 12 critérios com pesos de
glosa de 5% a 20%, `TOTAL A PAGAR = TOTAL × (1 − glosa)`, glosa limitada a 35%.
Na OS real a glosa foi 0%.

> **Descoberta-chave nº 3:** as etapas de escritório (planejamento + relatório +
> apresentação) são **fixas por Ordem de Serviço**, não por ODI. Para "Geração":
> 4 + 16 + 4 = 24 h × 360 = **R$ 8.640** (é exatamente o que sobra em 152.640 − 144.000).
> Para "Extensão de Redes" (que é o caso do LPT Rural, nosso caso):
> 8 + 24 + 4 = 36 h × 360 = **R$ 12.960**.

### a.2 `CalculoDistancias.xlsx` — **não** é um modelo de custo (achado negativo importante)

O nome engana. Investigadas todas as 10 abas e todas as fórmulas:

- A aba `CALCULO_VR` é da **Energisa TO 2ª Tranche**, 450 linhas (1 por ODI/UC).
- A coluna **`KM`** é uma haversine pura entre o **centroide do município** e a **UC**:
  ```excel
  =6371*ACOS(COS(PI()*(90-P4)/180)*COS((90-N4)*PI()/180)
    +SIN((90-P4)*PI()/180)*SIN((90-N4)*PI()/180)*COS((Q4-O4)*PI()/180))
  ```
  Raio da Terra **R = 6.371 km**. Estatística da coluna: média 46,8 km, mediana 46,1 km,
  mín 7,2 km, máx 468,3 km.
- A coluna **`Custo`** é `XLOOKUP(SIGFI; Grupo!F:F; Grupo!G:G)` — uma tabela de 3 linhas:
  SIGFI 45 → R$ 39.252,62 · SIGFI 80 → R$ 46.440,22 · SIGFI 160 → R$ 79.888,47.

> **Descoberta-chave nº 4 (achado negativo):** esse `Custo` é o **valor da obra**
> (o sistema de geração instalado), usado para montar o **VR — Valor de Referência**
> que estratifica a amostra. **Não tem nada a ver com custo de inspeção.**
> A distância calculada ali **nunca é convertida em dinheiro** — fica como coluna
> descritiva. Portanto: *não existe, em nenhuma das referências, uma taxa R$/km.*
> Qualquer R$/km que aparecesse no nosso modelo seria invenção nossa.

O que essa planilha **de fato** contribui para o projeto:
1. A **fórmula de distância da casa** (haversine, R = 6371) — vamos usar a mesma.
2. A prática de usar o **centroide do município como polo logístico**.
3. Tabelas IBGE de lat/long de 5.565 municípios (abas `Planilha6`/`Planilha4`) e de
   529 municípios com população (aba `Planilha1`) — úteis se algum dia faltar coordenada de UC.

### a.3 O gabarito de saída — `20260224_Tabela_Resumo_Estratos_Amostra.xlsx`

Duas abas de resumo (`Resumo` e `Resumo (2)`) e três abas de detalhe
(`Amostra2_Err_9%_Estr_4/5/6`, 650 linhas cada = o quadro amostral inteiro de 580 ODIs,
com `STATUS = "Selecionado"` marcando os sorteados).

**Grandezas reportadas por estrato** (é o layout que o `resumo.py` terá de produzir):

| Coluna | Origem |
|---|---|
| Lote / nº de Estratos | parâmetro do desenho amostral |
| **ODI** | contagem de ODIs selecionados |
| **Municípios** | contagem distinta de municípios |
| **UC** | soma da coluna `Cons.` (consumidores) |
| **Trafos** | soma de `Trafo` |
| **Postes** | soma de `Poste` |
| **km AT** / **km BT** | soma de `Rede AT km` / `Rede BT km` — **extensão da rede construída, não distância percorrida** |
| **Custo Estimado (R$)** | o que este projeto vai calcular |
| **Dias** | duração de calendário da campanha |
| **Equipe** | nº de equipes de campo |
| Amostra Sugerida | marcação "X" manual |

Valores publicados (EQTL PA 7ª Tranche, 2ª amostra):

| Estratos | ODI | Mun | UC | Trafos | Postes | km AT | km BT | Custo (R$) | Dias | Equipes |
|---|---|---|---|---|---|---|---|---|---|---|
| 6 | 19 | 11 | 1.341 | 564 | 5.771 | 449,0 | 26,0 | 348.176 | 16 | 6 |
| 5 | 28 | 21 | 1.543 | 694 | 7.960 | 672,8 | 32,6 | 410.576 | 18 | 6 |
| 4 | 44 | 30 | 2.163 | 1.036 | 12.728 | 1.067,1 | 45,9 | 472.920 | 22 | 6 |
| 3 | 71 | 36 | 3.026 | 1.405 | 16.203 | 1.332,1 | 53,5 | 520.864 | 25 | 6 |

### a.4 A apresentação à Diretoria — a metodologia declarada

O slide 2 (`Critérios de Dimensionamento`) diz, textualmente:

> "O valor da hora técnica (engenheiro e técnico) é **pré-definido no Edital**";
> "Os custos apresentados são **estimativos**, pois o valor final depende da logística
> definida pelo Agente Executor, incluindo **o roteiro das inspeções** e o número de
> profissionais necessários";
> "A estimativa de custos foi elaborada com base na **previsão da quantidade de equipes
> de campo**, no **volume de Unidades Consumidoras** e nas **condições logísticas dos
> municípios**, que impactam diretamente o **número de dias de inspeção**."

Ou seja, o próprio órgão declara a cadeia: `UCs + logística → dias → equipes × dias → custo`.
O elo fraco declarado é "condições logísticas dos municípios" — hoje, julgamento humano.

### a.5 Engenharia reversa: a fórmula exata do gabarito

Testando `(Custo − 12.960) / 4.800` nas 11 estimativas publicadas (2 distribuidoras):

| Amostra | Custo (R$) | (Custo−12.960)/4.800 | Resultado |
|---|---|---|---|
| COELBA 11ª, estr. 6 | 200.160 | 39,0000 | **EXATO** |
| COELBA 11ª, estr. 5 | 204.960 | 40,0000 | **EXATO** |
| COELBA 11ª, estr. 4 | 267.360 | 53,0000 | **EXATO** |
| PA 7ª 1ª amostra, estr. 6 | 396.960 | 80,0000 | **EXATO** |
| PA 7ª 1ª amostra, estr. 5 | 502.560 | 102,0000 | **EXATO** |
| PA 7ª 1ª amostra, estr. 4 | 612.960 | 125,0000 | **EXATO** |
| PA 7ª 1ª amostra, estr. 3 | 684.960 | 140,0000 | **EXATO** |
| PA 7ª 2ª amostra, estr. 6 | 348.176 | 69,8367 | resíduo R$ 4.016 |
| PA 7ª 2ª amostra, estr. 5 | 410.576 | 82,8367 | resíduo R$ 4.016 |
| PA 7ª 2ª amostra, estr. 4 | 472.920 | 95,8250 | resíduo R$ 3.960 |
| PA 7ª 2ª amostra, estr. 3 | 520.864 | 105,8133 | resíduo R$ 3.904 |

**Conclusão: `Custo = 12.960 + 4.800 × equipe-dias`**, onde
`12.960 = 36 h × R$ 360` (etapas de escritório, "Extensão de Redes") e
`4.800 = 8 h × R$ 600` (um dia de campo de um engenheiro com deslocamento).

Sete acertos ao centavo em duas distribuidoras diferentes não é coincidência: a fórmula
está confirmada. O bloco "PA 7ª 2ª amostra" carrega um adicional fixo de ~R$ 3,9–4,0 mil
que não fecha com nenhuma combinação das tarifas do Edital — provável ajuste manual do
planejador (**pergunta aberta P6**).

**E o "equipe-dias"?** Convertendo em UCs por equipe por dia:

| Amostra | UC | equipe-dias | **UC/equipe-dia** |
|---|---|---|---|
| COELBA estr. 6 / 5 / 4 | 786 / 798 / 1.266 | 39 / 40 / 53 | 20,2 / 19,9 / 23,9 |
| PA 1ª amostra estr. 6 / 5 / 4 / 3 | 930 / 1.555 / 2.841 / 2.941 | 80 / 102 / 125 / 140 | 11,6 / 15,2 / 22,7 / 21,0 |
| PA 2ª amostra estr. 6 / 5 / 4 / 3 | 1.341 / 1.543 / 2.163 / 3.026 | 69,8 / 82,8 / 95,8 / 105,8 | 19,2 / 18,6 / 22,6 / 28,6 |

**Mediana 20,2 UC/equipe-dia · média 20,3 · desvio 4,2.** Notavelmente estável.
É a melhor âncora de calibração que os dados oferecem.

### a.6 Geometria real da 7ª tranche PA (calculada, não estimada)

De `Coordenadas_UCs_7ªTR_PA.xlsx` (22.585 UCs, 580 ODIs, 69 municípios, 4 regionais):

| Regional | ODIs | UCs | Municípios | Dist. base→centroide ODI (km, mediana) |
|---|---|---|---|---|
| MARABA (SUMAR) | 273 | 6.615 | 20 | 264,8 (máx 529) |
| CASTANHAL (SUCAS) | 125 | 5.113 | 18 | 96,2 (máx 300) |
| SANTAREM (SUSAN) | 98 | 6.568 | 18 | 151,0 (máx 620) |
| METROPOLITANA (SUMET) | 84 | 4.289 | 13 | 160,9 (máx 263) |

- **UCs por ODI**: média 38,9 · mediana 20,5 · mín 1 · máx 682.
- **Raio médio do cluster de UCs dentro de um ODI**: média 4,1 km · mediana ~2,3 km.
- **Rota vizinho-mais-próximo dentro do ODI**: média 30,0 km · mediana 16,8 km · máx 949 km.
- **Distância geodésica base regional → centroide do ODI**: mediana 163 km · média 205 km.

> **Descoberta-chave nº 5:** somar `2 × distância(base, ODI)` para **cada** ODI
> estoura tudo. Para a amostra de 4 estratos (44 ODIs em 30 municípios), isso dá
> 10.525 km só de ida — × 2 × 1,4 = 31.795 km rodoviários = **636 h de estrada**,
> quando a campanha inteira planejada tem 1.056 h. Motivo: **a equipe não volta à
> base entre ODIs**, e vários ODIs dividem o mesmo município. O modelo v0 do brief
> precisa ser corrigido nesse ponto — ver seção (b).

---

## (b) O modelo proposto (v0.1)

### b.1 A ideia em uma frase

> Mantemos **intacta a fórmula contratual de preço** (ela é auditável e já foi aceita
> pela Diretoria) e substituímos apenas a caixa-preta "quantos dias?" por uma conta
> de geometria explícita e reprodutível.

### b.2 A estrutura em três camadas

```
                       ┌─────────────────────────────────────┐
   AMOSTRA (k)   ──►   │  1. GEOMETRIA  (src/distancias.py)  │
   UCs + lat/long      │     km de estrada por ODI           │
                       └──────────────┬──────────────────────┘
                                      ▼
                       ┌─────────────────────────────────────┐
                       │  2. ESFORÇO  (src/custo.py)         │
                       │     km → horas ; UCs → horas        │
                       └──────────────┬──────────────────────┘
                                      ▼
                       ┌─────────────────────────────────────┐
                       │  3. PREÇO  (fórmula contratual)     │
                       │     horas × tarifa + etapas fixas   │
                       └─────────────────────────────────────┘
```

### b.3 Camada 1 — Geometria (por ODI)

O agrupamento é **por município dentro de cada regional**, não por ODI solto.
Isso corrige a descoberta nº 5.

```
Para cada (REGIONAL, MUNICÍPIO) presente na amostra:
    centroide_mun     = média das lat/long dos centroides dos ODIs do município
    km_mobilizacao    = 2 × haversine(base_regional, centroide_mun) × FATOR_RODOVIARIO
    km_entre_odis     = rota_vizinho_mais_proximo(centroides dos ODIs do município) × FATOR_RODOVIARIO

Para cada ODI:
    centroide_odi     = média das lat/long das suas UCs
    km_internos       = rota_vizinho_mais_proximo(UCs do ODI) × FATOR_RODOVIARIO

km_totais(amostra) = Σ_municipios (km_mobilizacao + km_entre_odis) + Σ_odis km_internos
```

*Rateio para exibir custo por ODI no mapa:* `km_mobilizacao` e `km_entre_odis` do
município são divididos entre os ODIs daquele município **proporcionalmente ao número
de UCs**. É só cosmético — o total da amostra não muda.

### b.4 Camada 2 — Esforço (km e UCs → horas)

```
horas_deslocamento = km_totais / VELOCIDADE_KMH
horas_inspecao     = n_ucs_total × HORAS_POR_UC
HORAS_CAMPO        = horas_deslocamento + horas_inspecao
```

### b.5 Camada 3 — Preço (fórmula contratual, não negociável)

```
CUSTO_CAMPO   = HORAS_CAMPO × TARIFA_HORA_COM_DESLOCAMENTO      (600,00)
CUSTO_FIXO    = HORAS_ETAPAS_ESCRITORIO × TARIFA_HORA_SEM_DESL  (36 h × 360 = 12.960)
CUSTO_AMOSTRA = CUSTO_FIXO + CUSTO_CAMPO

DIAS_CALENDARIO = teto( HORAS_CAMPO / (HORAS_POR_DIA × N_EQUIPES) )
```

Note: `CUSTO_FIXO` entra **uma vez por amostra** (é uma Ordem de Serviço), nunca por ODI.
E `N_EQUIPES` **não altera o custo** — só os dias.

### b.6 Tabela de parâmetros — valor sugerido, fonte e confiança

| Parâmetro | Valor sugerido | Fonte | Confiança |
|---|---|---|---|
| `TARIFA_HORA_COM_DESLOCAMENTO` | **600,00 R$/h** | `Custos Inspeções` D17 · Eng. Eletricista/Generalista, obra **com** deslocamento | **ALTA** — tabelado no Edital, confirmado em 7 estimativas |
| `TARIFA_HORA_SEM_DESLOCAMENTO` | **360,00 R$/h** | `Custos Inspeções` D19 · demais etapas | **ALTA** — idem |
| `HORAS_ETAPAS_ESCRITORIO` | **36 h** (8 planej. + 24 relat. + 4 apres.) | `Custos Inspeções` linha "Extensão Rede" | **ALTA** — 12.960 confirmado ao centavo em 7/11 casos |
| `CUSTO_FIXO_POR_AMOSTRA` | **R$ 12.960,00** (derivado) | 36 × 360 | **ALTA** |
| `HORAS_POR_DIA` | **8 h** | fórmula `(fim − início + 1) × 8` da aba `Composição Equipes` | **ALTA** |
| `N_EQUIPES` | **6** | 4ª tranche PA (OS real) e 7ª tranche PA (todas as amostras) | **MÉDIA** — decisão gerencial; não afeta o custo, só os dias |
| `RAIO_TERRA_KM` | **6.371** | fórmula da coluna `KM` de `CALCULO_VR` | **ALTA** — padrão da casa |
| `FATOR_RODOVIARIO` | **1,40** | *não existe nas referências* | **CHUTE A CALIBRAR** — literatura de logística usa 1,2–1,5 para malha densa; a Amazônia rural pede o topo da faixa ou mais |
| `VELOCIDADE_KMH` | **45 km/h** | *não existe nas referências* | **CHUTE A CALIBRAR** — média ponderada de asfalto (~70) e vicinal/ramal (~25) |
| `HORAS_POR_UC` | **0,30 h** (18 min) | ver b.7 | **CHUTE CALIBRADO** — faixa plausível 0,22–0,45 |
| `UC_POR_EQUIPE_DIA` (verificação) | **20** | mediana de 11 estimativas publicadas | **MÉDIA-ALTA** — usado como *sanity check*, não como entrada |
| `BASE_REGIONAL` (4 pontos) | METROPOLITANA (−1,4558; −48,4902) · CASTANHAL (−1,2969; −47,9264) · MARABA (−5,3686; −49,1178) · SANTAREM (−2,4431; −54,7083) | sedes municipais das 4 regionais da coluna `REGIONAL` | **MÉDIA** — são as sedes dos municípios que nomeiam as regionais; confirmar endereço real (**P3**) |
| `GLOSA_IMR` | **0 %** | aba `IMR` — na OS real a glosa foi zero | **ALTA** para estimativa *ex ante* (não se estima glosa) |

### b.7 De onde saiu `HORAS_POR_UC = 0,30`

Calculando a geometria real dos ODIs efetivamente sorteados nas três amostras do gabarito
(PA 7ª, 2ª amostra) e descontando as horas de deslocamento previstas pelo modelo:

| Estrato | ODIs sorteados | ODIs **com coordenada** | Mun (geometria) | UC | km rodov. (FR 1,4) | h desloc. (V 50) | h alvo (do custo) | h sobra / UC |
|---|---|---|---|---|---|---|---|---|
| 6 | 19 | 18 | 10 | 1.341 | 6.898 | 138 | 552 | 0,309 |
| 5 | 28 | 25 | 18 | 1.543 | 12.484 | 250 | 656 | 0,263 |
| 4 | 44 | 42 | 28 | 2.163 | 19.732 | 395 | 760 | 0,169 |

> **Nota — por que "ODIs sorteados" ≠ "ODIs com coordenada".**
> Seis ODIs sorteados não aparecem em `Coordenadas_UCs_7ªTR_PA.xlsx`, e **todos os seis
> têm `Cons. = 0`** (zero unidades consumidoras): `PA2200612LPT140005` (Novo Progresso,
> 296 postes), `PA2200612LPT140009` (Rurópolis), `PA2200612LPT150002` (Anapu, 287 postes),
> `PA2200612LPT140006` (Novo Progresso, 392 postes), `PA2100612LPT130113` (São Félix do Xingu)
> e novamente `PA2200612LPT150002` no estrato 4. São obras de **reforço de alimentador /
> rede de acesso**: têm postes e rede, mas nenhuma UC. Um painel indexado por UC não pode,
> por construção, conter um ODI sem UC.
>
> Efeitos, todos verificados:
> - **A calibração de `HORAS_POR_UC` não é afetada**: o total de UCs bate exatamente com o
>   gabarito nos três estratos (1.341 / 1.543 / 2.163), justamente porque os ausentes têm 0 UC.
> - **Os km de mobilização ficam subestimados**: 1, 3 e 2 municípios a menos entram no
>   circuito. Ou seja, `HORAS_POR_UC` calibrado nesta tabela é, se algo, ligeiramente
>   **conservador para cima**.
> - **Isso é uma lacuna real do modelo**, não só da calibração: um ODI com 0 UC ainda precisa
>   ser inspecionado (postes, rede) e ainda custa viagem. Tratamento previsto na
>   implementação e listado em (d): usar o **centroide do município** como localização do ODI
>   quando não houver nenhuma UC com coordenada, e contar seu tempo de inspeção por
>   quilômetro de rede em vez de por UC.

Média ponderada: **0,235 h/UC**. Com `V = 45` a média sobe para ~0,26.
A dispersão (0,17–0,31) mostra que **o gabarito não obedece a nenhuma regra geométrica
consistente** — é justamente o julgamento humano que queremos substituir.
Sugerimos **0,30 h/UC** por ficar no topo da faixa observada e por bater melhor com a
âncora "20 UC/equipe-dia" (que, líquida de deslocamento, implica ~0,30–0,40 h/UC).

**Erro esperado do modelo contra o gabarito: ±20%.** Isso é honesto e deve ser dito ao
leitor do relatório. O modelo não promete reproduzir o gabarito — promete ser
**reprodutível, auditável e sensível à geografia**, coisas que o gabarito não é.

### b.8 Exemplo numérico completo (PA 7ª, 6 estratos)

```
Sorteados no gabarito ..... 19 ODIs · 11 municípios · 1.341 UCs · 4 regionais
Com coordenada no painel .. 18 ODIs · 10 municípios · 1.341 UCs  <- base da geometria

  km mobilização (10 municípios, ida e volta) .... 4.327 km geodésicos
  km entre ODIs do mesmo município ................  110 km geodésicos
  km internos aos ODIs (vizinho + próximo) ........  491 km geodésicos
                                                    ─────────
  soma geodésica ..................................  4.928 km
  × FATOR_RODOVIARIO 1,40 .........................  6.898 km de estrada

  horas de deslocamento = 6.898 / 45 ..............  153,3 h
  horas de inspeção     = 1.341 × 0,30 ............  402,3 h
                                                    ─────────
  HORAS_CAMPO .....................................  555,6 h

  CUSTO_CAMPO = 555,6 × 600 .......................  R$ 333.356
  CUSTO_FIXO ......................................  R$  12.960
                                                    ────────────
  CUSTO_AMOSTRA ...................................  R$ 346.316
  DIAS = teto(555,6 / (8 × 6)) ....................  12 dias

  Gabarito publicado: R$ 348.176 · 16 dias
  Diferença de custo: −0,5 %
```

(O acerto de custo é bom; os dias divergem porque o gabarito já embute folgas de
calendário — fins de semana, deslocamento inicial. Ver pergunta **P5**.)

---

## (c) Alternativas descartadas e por quê

| # | Alternativa | Por que foi descartada |
|---|---|---|
| C1 | **Custo por quilômetro (R$/km rodado)** | Não existe tarifa R$/km em nenhuma referência. O Edital paga **hora-profissional**, não quilometragem. Inventar um R$/km criaria um número não auditável e faria a soma divergir do contrato. |
| C2 | **Usar a coluna `Custo` de `CalculoDistancias.xlsx`** | Aquilo é o **valor da obra** (SIGFI 45/80/160 → R$ 39k/46k/80k), insumo do Valor de Referência que estratifica a amostra. Usar como custo de inspeção seria erro conceitual grosseiro (a inspeção custaria mais que a obra). |
| C3 | **`2 × haversine(base, centroide_odi)` para cada ODI** (o v0 do brief) | Superestima brutalmente: 636 h de estrada numa campanha de 1.056 h. Ignora que a equipe faz circuito e que vários ODIs partilham município. Substituído pela mobilização por município (b.3). |
| C4 | **Custo por ODI com etapas de escritório rateadas** | As 36 h de escritório são **por Ordem de Serviço**, não por obra. Ratear inflaria amostras com muitos ODIs pequenos. Mantido como parcela fixa da amostra. |
| C5 | **Somar diárias / pernoite / veículo como linhas próprias** | O diferencial de R$ 240/h entre "com" e "sem" deslocamento já é a remuneração da logística. Somar diárias contaria duas vezes. (Se o humano discordar → **P2**.) |
| C6 | **TSP exato (caixeiro-viajante) para a rota interna** | ODIs chegam a 682 UCs; TSP exato é inviável e a precisão extra é ruído perto da incerteza de `FATOR_RODOVIARIO`. Vizinho-mais-próximo entrega ~25% acima do ótimo, o que é conservador e desejável. |
| C7 | **Roteamento real por API (OSRM / Google Directions)** | Melhor precisão, mas exige internet, chave e ~22.585 chamadas. O `.bat` de duplo-clique tem de rodar offline. Fica para v1 como calibrador do `FATOR_RODOVIARIO`. |
| C8 | **Estimar a glosa IMR** | Glosa é resultado de desempenho *ex post*. Estimativa *ex ante* assume 0%, como fez a OS real. |
| C9 | **Modelo puramente empírico `UC ÷ 20 = equipe-dias`** | Reproduz bem o histórico (±15%), mas é **cego à geografia** — daria o mesmo custo para 1.000 UCs concentradas em Belém e para 1.000 UCs espalhadas por Novo Progresso. Rejeitado como modelo principal; **mantido como coluna de verificação** no relatório de saída. |

---

## (d) O que fica para a v1

1. **Perfil misto de equipe** (engenheiro + técnico). Hoje o modelo assume 1 engenheiro
   por equipe (como a OS real da 4ª tranche). A tarifa de técnico com deslocamento
   (R$ 513,22) já está mapeada e entra fácil quando houver definição.
2. **`FATOR_RODOVIARIO` por regional**. Rota fluvial no Marajó/Baixo Amazonas não tem
   nada a ver com a PA-150. Provavelmente SANTAREM e METROPOLITANA (ilhas) precisam de
   fator próprio — ou de um modo "acesso fluvial" com velocidade separada.
3. **Calibração contra roteamento real** (OSRM offline ou uma amostra de consultas
   Google Directions) para fixar `FATOR_RODOVIARIO` com evidência em vez de chute.
4. **Diárias / pernoite explícitos**, se o humano decidir que o modelo deve enxergar
   custo econômico e não só o desembolso contratual.
5. **Cenários de nº de equipes**: hoje `N_EQUIPES` é fixo; poderia sair uma tabelinha
   "6 equipes → 12 dias · 4 equipes → 18 dias · 8 equipes → 9 dias" (custo idêntico).
6. **Glosa IMR como cenário**: mostrar o custo com glosa 0% / 15% / 35%.
7. **Tempo de inspeção variável por tipo de obra** (SIGFI/MIGDI vs. extensão de rede),
   já que o Edital separa "Geração" de "Extensão de Redes" com tempos diferentes.
8. **ODIs sem nenhuma UC** (`Cons. = 0`). Existem de fato: seis dos sorteados no gabarito
   são obras de reforço de alimentador / rede de acesso — têm postes e rede, zero UCs, e
   por isso **não aparecem no painel de coordenadas** (ver nota em b.7). O modelo v0 os
   ignora, subestimando a mobilização. Tratamento proposto para a v1: localizar o ODI pelo
   **centroide do município** e medir seu esforço de inspeção por **km de rede (AT+BT)**
   em vez de por UC — o `Lote.xlsx` já traz `Rede AT km` e `Rede BT km`.
   > ⚠ **Isto corrige uma regra do `planning/DESIGN.md` §7**, que manda *abortar* quando um
   > ODI não tem coordenada ("Lista os órfãos e aborta"). Um ODI com 0 UC é órfão
   > **legítimo** e não pode derrubar a execução. A regra deve virar: aborta só se o ODI tem
   > `Cons. > 0` e mesmo assim nenhuma coordenada; se `Cons. = 0`, avisa e usa o fallback
   > do município. Registrar no gate junto com o modelo.

---

## (e) MEMÓRIA DE CÁLCULO

> **Este é o texto que será embutido literalmente no topo de `src/config.py` e
> `src/custo.py` na Task 5.** Escrito para ser lido por quem não abriu o código.

```
==============================================================================
MEMORIA DE CALCULO — COMO O CUSTO DE INSPECAO E ESTIMADO E POR QUE ASSIM
==============================================================================

O QUE ESTAMOS ESTIMANDO
-----------------------
Uma amostra e um conjunto de obras (ODIs) sorteadas para inspecao fisica.
Inspecionar uma obra significa: uma equipe sai da base regional, dirige ate o
municipio da obra, percorre as unidades consumidoras (UCs) espalhadas pelo
campo e conferre cada uma. O que queremos saber e quanto isso custa.

DE ONDE VEM O PRECO (nao inventamos nada aqui)
----------------------------------------------
O Edital ja fixa quanto vale a hora de trabalho. Ha duas tarifas:
  - R$ 360/hora  -> trabalho de escritorio (planejar, escrever relatorio, apresentar)
  - R$ 600/hora  -> trabalho de campo, "com deslocamento"

A diferenca de R$ 240/hora e o que o contrato paga pela logistica: viagem,
veiculo, hospedagem, alimentacao. Por isso NAO somamos diaria, hotel nem
combustivel em separado — isso ja esta dentro dos R$ 600.

Toda Ordem de Servico tem, alem do campo, tres etapas fixas de escritorio:
planejamento (8h), relatorio (24h) e apresentacao (4h) = 36 horas.
36 x R$ 360 = R$ 12.960. Esse valor entra UMA VEZ por amostra, nunca por obra.

Conferimos essa formula contra 11 estimativas ja apresentadas a Diretoria
(Equatorial PA 7a Tranche e Coelba 11a Tranche). Em 7 delas o resultado bate
ao centavo:
        CUSTO = 12.960 + 4.800 x (numero de equipe-dias de campo)
onde 4.800 = 8 horas x R$ 600 = um dia de campo de um profissional.

O QUE O ORGAO NAO SABIA CALCULAR — E QUE ESTE PROGRAMA CALCULA
---------------------------------------------------------------
A apresentacao a Diretoria diz que os dias de campo saem "das condicoes
logisticas dos municipios". Na pratica, alguem olhava o mapa e chutava.
Nosso trabalho e trocar esse chute por geometria, mantendo o preco intacto.

COMO CONTAMOS AS HORAS DE CAMPO
--------------------------------
Fase 1 — Onde fica cada obra.
  Cada ODI vira um ponto: a media das coordenadas das suas UCs (o "centroide").

Fase 2 — Quanto se roda para chegar la.
  A equipe NAO volta a base a cada obra: ela viaja ate um municipio e trabalha
  todas as obras daquele municipio antes de voltar. Entao contamos:
    (a) ida e volta da base regional ate o municipio  — uma vez por municipio;
    (b) os saltos entre as obras dentro do municipio;
    (c) o percurso interno de cada obra, visitando as UCs sempre pela vizinha
        mais proxima ainda nao visitada.
  Todas as distancias sao em linha reta sobre a esfera (formula de haversine,
  raio da Terra = 6.371 km — a mesma usada nas planilhas da casa) e depois
  multiplicadas pelo FATOR RODOVIARIO, porque estrada nao e linha reta.

Fase 3 — Distancia vira tempo.
  horas de deslocamento = quilometros de estrada / velocidade media.

Fase 4 — Inspecao vira tempo.
  horas de inspecao = numero de UCs x tempo medio por UC.

Fase 5 — Tempo vira dinheiro.
  custo de campo = (horas de deslocamento + horas de inspecao) x R$ 600
  custo total    = custo de campo + R$ 12.960 (etapas de escritorio)

Fase 6 — Tempo vira agenda.
  dias de campo = arredonda para cima( horas de campo / (8 h x numero de equipes) )
  Atencao: mais equipes NAO barateiam a inspecao — o contrato paga por
  hora-profissional. Mais equipes so terminam mais rapido.

O QUE E SOLIDO E O QUE E CHUTE
-------------------------------
SOLIDO   (tabelado no Edital, conferido contra estimativas ja aprovadas):
         as tarifas de R$ 360 e R$ 600, as 36 horas de escritorio,
         as 8 horas por dia, o raio da Terra.
CHUTE    (calibravel, os dois parametros que mais mexem no resultado):
         FATOR RODOVIARIO e VELOCIDADE MEDIA — nenhuma referencia do orgao
         tem esses numeros, porque nenhuma referencia converte distancia em
         dinheiro.
MEIO-TERMO: o TEMPO MEDIO POR UC. Foi calibrado com a geometria real dos
         ODIs sorteados nas amostras ja publicadas; a faixa observada foi de
         0,17 a 0,31 hora por UC.

VERIFICACAO DE SANIDADE
-----------------------
Nas 11 estimativas historicas, uma equipe inspeciona em media 20 UCs por dia
(mediana 20,2; variacao de 12 a 29). O relatorio de saida traz essa razao
calculada para cada amostra: se der muito longe de 20, o parametro esta errado
ou aquela amostra e geograficamente atipica — vale conferir antes de assinar.

MARGEM DE ERRO HONESTA
----------------------
Contra o gabarito de fevereiro/2026, este modelo erra ate cerca de 20% por
estrato. Isso nao e defeito do modelo: o gabarito nao segue regra geometrica
nenhuma. O ganho aqui nao e "acertar o numero antigo" — e produzir um numero
reprodutivel, rastreavel ate cada parametro e sensivel a geografia real da
amostra sorteada.
==============================================================================
```

---

## Perguntas que o humano precisa responder para aprovar

> Sem estas respostas o modelo fica com chutes onde poderia ter fatos.
> Marcadas com ⚠ as que **mudam o resultado em mais de 10%**.

**P1 — Perfil da equipe.** Confirmamos 1 **Engenheiro Eletricista** por equipe, tarifa
R$ 600/h com deslocamento (é o que a OS real da 4ª tranche fez: 6 equipes, 6 engenheiros,
0 técnicos)? Ou haverá equipes mistas engenheiro + técnico (R$ 513,22/h)? ⚠

**P2 — Diárias e pernoite.** Concorda que a tarifa "com deslocamento" já remunera viagem,
hospedagem e veículo, e que portanto **não** somamos diárias em separado? Se o objetivo
for custo econômico (e não desembolso contratual), isso muda. ⚠

**P3 — Base de partida.** Usamos a **sede do município que nomeia cada regional**
(Belém, Castanhal, Marabá, Santarém) como ponto de partida. Existe um endereço/coordenada
oficial das bases regionais da Equatorial? Ou a equipe credenciada parte sempre de Belém,
independentemente da regional? ⚠

**P4 — Tipo de obra.** A 7ª tranche PA é **LPT Rural / Extensão de Redes**, logo as etapas
de escritório são 36 h (R$ 12.960). Confirma? Se houver ODIs de **Geração Descentralizada**
(SIGFI/MIGDI) na mesma amostra, são 24 h (R$ 8.640) — e o modelo precisaria distinguir.

**P5 — Dias de calendário.** Nosso "dias" é puramente aritmético
(`horas ÷ 8 ÷ nº de equipes`, arredondado para cima). O gabarito reporta mais dias que isso
(ex.: 12 calculados vs. 16 publicados). Devemos acrescentar **dias de mobilização inicial**
e/ou **pular fins de semana**? Quantos?

**P6 — O resíduo de R$ 4.016.** As quatro estimativas da "2ª amostra PA 7ª" têm um
adicional fixo de R$ 3.904–4.016 que não fecha com nenhuma tarifa do Edital. Você sabe o
que é? (hora de apoio? deslocamento aéreo? ajuste manual?) Se for uma parcela legítima,
vira parâmetro.

**P7 — Nº de equipes.** Fixamos 6 (padrão histórico). Deve ser parâmetro fixo em
`config.py`, pergunta interativa no `.bat`, ou calculado a partir de um prazo-alvo
("preciso terminar em 15 dias")? *(Não afeta o custo, só os dias.)*

**P8 — Velocidade e fator rodoviário.** ⚠ São os dois chutes que mais mexem no resultado.
Você tem alguma referência operacional — quilometragem média rodada por dia por uma equipe
de inspeção no Pará, ou quanto tempo se leva de Marabá a Novo Repartimento? Qualquer
número real vale mais que a nossa estimativa de 45 km/h e 1,40.

**P9 — Acesso fluvial.** Marajó, Baixo Amazonas e as ilhas de Belém não têm estrada.
Devemos tratar essas regionais/municípios com velocidade e fator próprios já na v0, ou
aceitar a distorção e deixar para a v1?

**P10 — Tempo por UC.** Nossa calibração indireta deu 0,17–0,31 h/UC e sugerimos 0,30 h
(18 min). Faz sentido operacionalmente? Quanto tempo uma equipe realmente gasta conferindo
uma unidade consumidora (medidor, padrão, ramal, foto, formulário)? ⚠

---

*Documento gerado na F1. Após a aprovação, registrar a decisão em `planning/PLAN.md`
(seção "Decisões e pendências") e só então iniciar a Task 5 (`src/config.py` + `src/custo.py`).*

---

## DECISÕES DO GATE (2026-08-06) — modelo APROVADO

Registradas em `PLAN.md` (G1–G5); todas viram parâmetros em `src/config.py`:
G1 equipe = só engenheiro · G2 sem diárias (tarifa embute) · G3 base = capital da UF
do contrato (`dados/base_contratos.json`, 113 contratos/23 UFs) · G4 velocidade
45 km/h e fator 1,40 mantidos como parâmetros a calibrar · G5 produtividade por tipo:
LPT = 30 UCs/dia, MLA = 3 UCs/dia (substitui o HORAS_POR_UC único calibrado em b.7).
Regra do órfão: ODI sem coordenada aborta só se Cons>0; Cons=0 → aviso + centroide municipal.

---

## CORREÇÃO F9 (2026-08-10) — o código tinha desviado deste documento

A engenharia forneceu um benchmark novo: `minhas_notas/Tabela_Resumo_Extratos_Amostra.xlsx`,
aba `Resumo` — as três estratificações da **PB 7ª Tranche (ECO 037/2025)** com o custo
estimado à mão. Regressão linear nos três pontos, resíduo **zero**:

| Estratos | Dias | Equipe | Custo real | `12.960 + 4.800 × equipes × (dias+1)` |
|---|---|---|---|---|
| 5 | 7 | 2 | 89.760 | 89.760 |
| 4 | 5 | 2 | 70.560 | 70.560 |
| 3 | 8 | 2 | 99.360 | 99.360 |

**É exatamente a fórmula deste documento** (§ sumário executivo, item 1 e o bloco
"DE ONDE VEM O PREÇO": `CUSTO = 12.960 + 4.800 × equipe-dias`, com o fixo entrando
"UMA VEZ por amostra, nunca por obra"). O `+1` nos dias é a **mobilização** — a resposta
à pergunta **P5**, que ficara em aberto no gate.

O que desviou foi a **implementação** (F4), em três pontos:

| # | O documento aprovado dizia | O código fazia | Efeito nos dados reais |
|---|---|---|---|
| 1 | fixo de R$ 12.960 **uma vez por amostra** | uma vez por **estrato** | +R$ 25.920 numa amostra de 3 estratos |
| 2 | "a equipe **NÃO volta à base a cada obra**" (Fase 2) | ida e volta da capital **por município** | 10.521 km em vez de 1.529 km (**7×**) |
| 3 | "dias = arredonda para cima(horas / 8)" (Fase 6) | horas fracionárias direto em R$ | dias fracionários, sem mobilização |

Somados, faziam a Amostra 1 da PB custar R$ 239.799 contra R$ 99.360 da engenharia (**+141%**).

**Correções aplicadas** (`src/config.py`, `src/custo.py`, `src/distancias.py`):

- `montar_roteiro` monta **um itinerário único** — capital → todas as obras (município a
  município, obra a obra) → capital, uma volta só. Substitui a ida-e-volta por município.
- `HORAS_ESCRITORIO_POR_OS` passa a entrar **uma vez por amostra**; o estrato deixa de
  participar do custo e vira coluna informativa do detalhe.
- Dias arredondados para cima + `DIAS_MOBILIZACAO = 1` (responde P5).
- `TAMANHO_EQUIPE` vira parâmetro. Fica em **1** (decisão G1 reafirmada pelo humano em
  2026-08-10), enquanto o benchmark usa 2 — a estimativa sai ~44% abaixo dele **por decisão**,
  não por erro. Mudar para `2.0` reproduz o benchmark sem tocar em código.

**Complemento F10 (2026-08-10)** — duas coisas que faltavam:

- **A Fase 6 virou código de verdade.** `dias = ceil(horas / (jornada × equipes))` — o código
  não dividia pelo número de equipes. Era invisível com equipe = 1; com equipe = 2 o custo
  dobrava em vez de ficar aproximadamente estável, contrariando o alerta desta seção
  (*"mais equipes NÃO barateiam a inspeção... só terminam mais rápido"*).
- **P7 respondida:** o nº de equipes não é fixo nem perguntado — vira uma **faixa**. A aba
  `Cenarios` inverte o cálculo: para cada prazo de `calculado ± 2` dias, mostra quantas equipes
  cabem, a ocupação delas e o custo. Com isso o alerta acima fica *visível* na planilha —
  encurtar o prazo **encarece**, pelo dia de mobilização de cada equipe nova e pelo desperdício
  de arredondar para dia inteiro em mais equipes. A aba assume o trabalho perfeitamente
  divisível entre equipes; na prática cada equipe teria seu próprio roteiro saindo da capital.

Também na F10: cada execução precifica **uma** amostra (1, 2 ou 3; padrão 1), porque a 2 e a 3
são reservas da 1 e nunca são usadas ao mesmo tempo.

**Margem honesta contra o benchmark** (com `TAMANHO_EQUIPE = 2`, para comparar maçã com maçã):
−9,7% / +27,2% / −21,4% por amostra; **−3,7% no agregado**. O erro por amostra não é do
modelo: os dias da engenharia **não seguem a geometria** (a amostra de 5 estratos tem a rota
mais curta — 1.456 km — e ganhou 7 dias; a de 4 estratos tem a rota mais longa e ganhou 5).
Isso confirma o diagnóstico de b.1: os dias vinham de julgamento. Nenhum modelo determinístico
reproduz 8/5/7 — e é justamente esse julgamento que este projeto substitui.
