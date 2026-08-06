# DESIGN — Estimador de custos de inspeção das amostras

> Design aprovado em conversa de brainstorming em 2026-08-06.
> Documento-pai: `planning/PLAN.md`. Companion visual: `planning/html/DESIGN.html`.

## 1. Objetivo

Estimar o custo de inspeção de cada amostra gerada pelo `SistemaAmostralPython`,
produzindo (a) uma tabela-resumo de custos por estrato/amostra no formato do gabarito
`minhas_notas/20260224_Tabela_Resumo_Estratos_Amostra.xlsx` e (b) mapas interativos
dos pontos das amostras. Executável por duplo-clique em `.bat`, no mesmo ritual do
sistema canônico.

## 2. Decisões tomadas (com o humano, 2026-08-06)

| # | Decisão | Escolha |
|---|---------|---------|
| D1 | Modelo de custo | **Explorar e propor**: Claude estuda as referências e propõe o modelo em `planning/MODELO_CUSTO.md`; gate de aprovação humana antes de codificar `custo.py` (Fase F1) |
| D2 | Entrada do estimador | **Planilhas de amostras prontas** — o estimador NÃO roda o sistema amostral |
| D3 | Formato dos mapas | **HTML interativo (folium)** — sem PNG |
| D4 | HTMLs de acompanhamento | **1 HTML companion por documento de planejamento**, inspirados em `planning/html-effectiveness/` |
| D5 | Arquitetura | **Abordagem A**: pipeline achatado no padrão canônico, scripts em `src/` |
| D6 | Dados de `minhas_notas/` | **Pesquisa apenas** — testes usarão arquivos reais colocados em `Entrada/` pelo humano; nenhum teste depende de `minhas_notas/` |
| D7 | Nomes dos arquivos de entrada | Amostras: **`Entrada/Lote.xlsx`** (abas `Amostra 1/2/3`). Geolocalização: arquivo cujo nome **contém "Painel de Monitoramento"** |
| D8 | Ordem dos documentos | `ADVERSARIAL_REVIEW.md` só DEPOIS do plano escrito |

## 3. Fatos descobertos na exploração (moldam o design)

- **Um ODI não é um ponto.** No arquivo de coordenadas de referência (7ª TR PA):
  580 ODIs distintos ↔ ~22.585 UCs; cada ODI é um cluster de UCs, cada UC com
  lat/long própria. O custo de inspecionar 1 ODI = chegar ao cluster + percorrer as UCs.
- **Chave de junção = ODI** entre amostras e coordenadas.
- **Entradas de tranches diferentes não casam** (interseção de ODIs = zero). O leitor
  precisa detectar isso e falhar com mensagem específica ("amostra de uma tranche ×
  painel de outra").
- Referências de custo disponíveis (não canônicas, sugeridas): tarifas R$/hora por
  perfil profissional com/sem deslocamento (Formulário de OS, aba `Custos Inspeções`)
  e distâncias/custos por município (`CalculoDistancias.xlsx`).

## 4. Estrutura do repositório (a criar)

```
Entrada/Lote.xlsx                          <- amostras (abas Amostra 1/2/3, STATUS="Selecionado")
Entrada/*Painel de Monitoramento*.xlsx     <- geolocalização (ODI -> UCs, lat/long)
saida/                                     <- resumo .xlsx + mapas .html (gerado)
src/estimar_custos.py                      <- ÚNICO executável
src/io_amostras.py                         <- leitura + validação das entradas
src/distancias.py                          <- geometria: clusters de UCs, distâncias
src/custo.py                               <- motor de custo (modelo da F1)
src/resumo.py                              <- tabela-resumo no formato do gabarito
src/mapas.py                               <- mapas folium
src/config.py                              <- parâmetros explícitos (tarifas, velocidades, tempos)
executar.bat / _exec.ps1 / instalar.ps1    <- raiz (duplo-clique), chamam src/ (uv + Python 3.12)
testes/                                    <- pytest: unitários + e2e com fixtures sintéticas
planning/                                  <- docs + planning/html/ (companions)
```

## 5. Componentes e contratos

- **`io_amostras`** — localiza `Entrada/Lote.xlsx` e `Entrada/*Painel de Monitoramento*.xlsx`
  (detecção da aba de coordenadas pelas colunas ODI/latitude/longitude); extrai das abas
  `Amostra 1/2/3` as obras `STATUS = "Selecionado"`; junta com coordenadas por ODI.
  Processa as abas que existirem. Devolve `Amostra(k_amostra, df_odis, df_ucs)`.
- **`distancias`** — por ODI: centroide das UCs + métrica de dispersão intra-ODI.
  Entre ODIs/municípios: distância geodésica (haversine) × fator de correção rodoviário
  (parâmetro em `config.py`, calibrável contra `CalculoDistancias.xlsx`).
- **`custo`** — recebe distâncias + parâmetros de `config.py`; devolve custo por
  ODI → estrato → amostra. Fórmula interna definida na F1; o CONTRATO (entrada/saída)
  fica fixo desde já, para o pipeline não depender dessa decisão.
- **`resumo`** — agrega no formato do gabarito e grava `saida/Resumo_Custos.xlsx`.
- **`mapas`** — um `saida/Mapa_Amostra_K.html` por amostra: UCs coloridas por estrato,
  popup com ODI/município/custo, camadas ligáveis por estrato.
- **`estimar_custos.py`** — orquestra lê → calcula → grava; perguntas interativas no
  início se houver escolha (padrão do canônico).

## 6. Fluxo de dados

```
Entrada/Lote.xlsx (Amostra 1/2/3, STATUS=Selecionado)
Entrada/*Painel de Monitoramento*.xlsx (ODI -> UCs lat/long)
        |  join por ODI (validação ruidosa: ODI sem coordenada = erro listado)
        v
ODIs sorteadas + UCs --> distancias --> custo --> resumo (saida/*.xlsx)
                            |               \--> mapas  (saida/*.html)
                            \-- parâmetros de config.py (tudo explícito)
```

## 7. Tratamento de erros (explícito, nunca silencioso)

| Situação | Comportamento |
|---|---|
| `Lote.xlsx` ou `*Painel de Monitoramento*` ausente | Aborta dizendo o que colocar em `Entrada\` |
| Dois arquivos casando o padrão do painel | Aborta listando-os |
| ODI sem coordenada | Lista os órfãos (contagem + amostra de códigos) e aborta |
| Interseção de ODIs = zero | Mensagem específica de tranche errada |
| Lat/long vazia, zero ou fora da bounding box do Brasil | Reporta por UC; ODI sem UC válida = erro |
| Planilha de saída aberta no Excel | Mensagem "feche o arquivo" (como o canônico) |
| Parâmetros de custo | Todos em `config.py` com valor e fonte comentados; zero números mágicos |

## 8. Testes

- **Unitários por módulo** — fixtures sintéticas minúsculas (5–10 ODIs, coordenadas
  conhecidas): haversine contra valores à mão; custo contra planilha de conferência;
  leitura contra xlsx gerados no próprio teste.
- **E2E feliz** — `Entrada/` sintética completa → pipeline → resumo e mapas existem,
  totais batem com gabarito manual.
- **E2E de borda** — ODI órfão; interseção zero; coordenada inválida; aba `Amostra 2`
  ausente (processa as existentes); arquivo de saída travado.
- Nenhum teste depende de `minhas_notas/`.

## 9. Macrofases (a detalhar no plano de implementação)

Cada fase termina com: critério em `definition of done.md`, testes passando e, quando
produz documento de planejamento, o companion HTML em `planning/html/`.

| Fase | Entrega | Gate | HTML companion (inspiração) |
|---|---|---|---|
| F0 | Infra: `src/`, venv uv 3.12, `requirements.txt`, `.bat`, esqueleto de testes | — | — |
| F1 | Estudo das referências + `planning/MODELO_CUSTO.md` | **Aprovação humana do modelo** | explicador de pesquisa (14/15) |
| F2 | `io_amostras` + validações + testes | — | — |
| F3 | `distancias` + testes | — | explicador de conceito, se necessário |
| F4 | `custo.py` conforme modelo aprovado + testes | — | — |
| F5 | `resumo` no formato do gabarito + testes | — | — |
| F6 | `mapas` folium + testes | — | — |
| F7 | E2E completo + `TESTES.md` + revisão final | — | status report (11) |

## 10. Riscos e pendências conhecidas

- **Formato real das planilhas de entrada**: o design assume o formato do output do
  `SistemaAmostralPython` (abas `Amostra 1/2/3`, coluna `STATUS`) e uma aba de
  coordenadas com ODI/lat/long. Será validado com os arquivos reais que o humano
  colocará em `Entrada/` — a F2 começa por essa verificação e o leitor falha
  ruidosamente em qualquer divergência.
- **Modelo de custo** ainda não definido — é exatamente a entrega da F1 (D1).
- **Fator de correção rodoviário** (geodésica → estrada) precisa de calibração;
  referência inicial: `CalculoDistancias.xlsx`.

## 11. Convenções

Herdadas do canônico (ver `CLAUDE.md`): formato BR (`;`, `,`, latin-1) em CSV/TXT;
código/comentários em português sem acento; determinismo (seed fixa se houver sorteio);
docstrings no padrão do projeto (por quê → fases numeradas); caminhos relativos via
`Path(__file__)` para o `.bat` funcionar de qualquer diretório.
