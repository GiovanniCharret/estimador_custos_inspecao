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

[ ] F0 — Infraestrutura: `src/`, venv uv 3.12, requirements, ritual `.bat`, git, `definition of done.md`
[ ] F1 — Estudo das referências → `MODELO_CUSTO.md` + companion HTML → **GATE: aprovação humana do modelo**
[ ] F2 — `io_amostras`: localizar `Entrada/Lote.xlsx` + `*Painel de Monitoramento*`, ler amostras/UCs, juntar por ODI com validações
[ ] F3 — `distancias`: haversine, centroide por ODI, rota interna (vizinho mais próximo)
[ ] F4 — `custo.py`: fórmula aprovada na F1, parâmetros só em `config.py`
[ ] F5 — `resumo.py`: `saida/Resumo_Custos.xlsx` (agregado por estrato + detalhe por ODI, por amostra)
[ ] F6 — `mapas.py`: `saida/Mapa_Amostra_K.html` (folium, camadas por estrato, popup com custo)
[ ] F7 — Orquestrador + e2e (feliz e bordas) + `TESTES.md` + status report HTML

## Decisões e pendências

- Decisões D1–D8 registradas em `planning/DESIGN.md` §2 (modelo a propor; entrada = planilhas prontas; mapas folium; 1 HTML por doc de planejamento; arquitetura achatada em `src/`; `minhas_notas/` = pesquisa; nomes `Lote.xlsx` + "Painel de Monitoramento"; adversarial review depois do plano).
- Sem GeoPandas na v1: haversine via numpy cobre centroides/distâncias; GeoPandas só se surgir necessidade geoespacial real (shapefiles, projeções).
- Memória de cálculo para humanos: explicação simples do cálculo de custo (e do porquê) duplicada no topo de `src/config.py` e `src/custo.py`, derivada do `MODELO_CUSTO.md` aprovado.
- Git: commits locais regulares; **sem push** para o GitHub (publicação é decisão do humano).
- **GATE F1 APROVADO (2026-08-06)** — modelo de `MODELO_CUSTO.md` aprovado com as decisões abaixo; **cada decisão vira parâmetro em `config.py`** (ajustes futuros sem rebuild):
  - **G1 (equipe):** só engenheiro na estimativa (técnico raramente usado; não sobe em poste quem estima). Tarifas por perfil ficam parametrizadas, perfil ativo = ENGENHEIRO.
  - **G2 (diárias):** não entram — a tarifa horária "com deslocamento" já embute. Parâmetro `CUSTO_DIARIA = 0` existe para testes futuros.
  - **G3 (base de partida):** capital do estado (UF) do contrato. Multi-UF: `minhas_notas/base_contratos.json` (113 contratos, 23 UFs, tipo LPT/MLA, vigência) é a base; `config.py` carrega dicionário de capitais por UF.
  - **G4 (velocidade/fator rodoviário):** mantidos como parâmetros a calibrar (`VELOCIDADE_KMH = 45`, `FATOR_RODOVIARIO = 1.40`); aprimoramento futuro.
  - **G5 (produtividade):** substitui HORAS_POR_UC único por **`UCS_POR_DIA = {"LPT": 30, "MLA": 3}`** (LPT = obras com rede/transformador; MLA = fotovoltaico remoto) × `HORAS_DIA_CAMPO = 8`. O tipo do contrato vem do `base_contratos.json`.
- **Regra do órfão (assumida, não contestada no gate):** ODI sem coordenada no painel aborta SÓ se tiver UCs (`Cons. > 0`); com `Cons. = 0` (obra sem UC, ex.: reforço de rede) → aviso + fallback centroide do município. Afeta T3.
- **Pendência (F2):** validar o formato real de `Lote.xlsx`/Painel quando o humano colocar os arquivos em `Entrada/`.
- **Pendência (pós-plano):** escrever `planning/ADVERSARIAL_REVIEW.md` (D8).