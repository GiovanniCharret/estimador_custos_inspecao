# -*- coding: utf-8 -*-
"""Parametros do modelo de custo - TODOS os numeros do estimador vivem aqui.

Cada parametro nasce de uma decisao do gate F1 (G1-G5, ver PLAN.md) e pode ser
ajustado sem rebuild. Cada constante tem valor e FONTE.

=== MEMORIA DE CALCULO (para humanos) ===
O custo e' calculado POR AMOSTRA (nao por estrato) e soma duas parcelas:

1) ESCRITORIO (fixo, UMA vez por amostra): planejamento + relatorio + apresentacao =
   HORAS_ESCRITORIO_POR_OS x tarifa de escritorio (36h x R$360 = R$12.960).

2) CAMPO: dias faturados x TAMANHO_EQUIPE x HORAS_DIA_CAMPO x tarifa de campo
   (R$600/h => R$4.800 por pessoa-dia). Os dias saem da geometria:
   - ROTEIRO: a equipe sai da CAPITAL da UF do contrato, encadeia TODAS as paradas
     numa viagem so (vizinho mais proximo, municipio a municipio e obra a obra
     dentro do municipio) e volta a capital UMA vez no fim. Nao ha ida-e-volta por
     obra nem por municipio. Km em linha reta viram km de estrada pelo
     FATOR_RODOVIARIO; km viram horas pela VELOCIDADE_KMH.
   - INSPECAO: cada UC consome HORAS_DIA_CAMPO / UCS_POR_DIA[tipo] horas.
     LPT (rede/postes): 30 UCs/dia. MLA (fotovoltaico remoto): 3 UCs/dia.
   - DIAS: (horas de roteiro + horas de inspecao) / HORAS_DIA_CAMPO, ARREDONDADO
     PARA CIMA (a equipe nao vende meio dia), mais DIAS_MOBILIZACAO.

BENCHMARK (minhas_notas/Tabela_Resumo_Extratos_Amostra.xlsx, aba 'Resumo'): a
engenharia da PB 7a Tranche estimou 3 amostras e as tres obedecem, ao centavo, a
   custo = 12.960 + 9.600 x (dias + 1),  onde 9.600 = 2 pessoas x 8h x R$600.
Ou seja: mesma formula desta memoria, com TAMANHO_EQUIPE = 2. Aqui o parametro fica
em 1 por decisao G1 do gate F1 (so engenheiro estima; nao sobe em poste quem estima),
o que deixa a estimativa ~44% abaixo do benchmark. Para reproduzir o benchmark, basta
mudar TAMANHO_EQUIPE para 2 - sem tocar em codigo.

Por que assim: mantem a camada de preco que o orgao ja usa e troca o julgamento
"condicoes logisticas" por geometria reprodutivel (coordenadas das UCs), sem
depender de malha rodoviaria externa. Detalhes e alternativas: planning/MODELO_CUSTO.md.
=== FIM DA MEMORIA DE CALCULO ===
"""
# --- Equipe (decisao G1 do gate) ---
# Perfil usado na estimativa. Tecnico raramente e' usado (nao sobe em poste quem estima).
PERFIL_EQUIPE = "ENGENHEIRO"
# Tarifas R$/hora por perfil (Formulario de OS, aba 'Custos Inspecoes').
# 'campo' = COM deslocamento; 'escritorio' = SEM deslocamento.
TARIFAS_HORA = {
    "ENGENHEIRO": {"campo": 600.0, "escritorio": 360.0},
    "TECNICO": {"campo": 513.22, "escritorio": 273.22},
}
# Diaria/pernoite em R$ por equipe-dia de campo (decisao G2: tarifa ja embute -> 0).
CUSTO_DIARIA = 0.0
# Pessoas na equipe de campo. G1 fixou 1 (so o engenheiro estima). O benchmark da
# engenharia da PB 7a Tranche usa 2 - mudar para 2.0 aqui reproduz aquele valor.
TAMANHO_EQUIPE = 1.0

# --- Jornada e produtividade (decisao G5 do gate) ---
# Horas de um dia de campo (8h x 600 = 4.800/equipe-dia, formula decifrada do orgao).
HORAS_DIA_CAMPO = 8.0
# Horas de escritorio por OS: planejamento + relatorio + apresentacao, UMA vez por AMOSTRA
# (36h x 360 = 12.960, o termo fixo da formula decifrada em MODELO_CUSTO.md a.5 e confirmado
# pelo benchmark da engenharia). Antes da F9 este termo entrava uma vez por ESTRATO, o que
# multiplicava o fixo pelo numero de estratos - erro corrigido na reconstrucao.
HORAS_ESCRITORIO_POR_OS = 36.0
# Dias cobrados alem dos dias de trabalho, para a mobilizacao (sair da capital / voltar).
# O benchmark da engenharia cobra exatamente 1 (custo = 12.960 + 9.600 x (dias + 1)).
DIAS_MOBILIZACAO = 1.0
# UCs inspecionadas por equipe por dia, por tipo de contrato (decisao G5):
# LPT = obras com rede/postes/transformador; MLA = fotovoltaico em regioes remotas.
UCS_POR_DIA = {"LPT": 30.0, "MLA": 3.0}
# Tipo usado quando o contrato nao e' informado/encontrado.
TIPO_CONTRATO_PADRAO = "LPT"

# --- Deslocamento (decisao G4: parametros a calibrar, ajustaveis sem rebuild) ---
# Converte distancia geodesica (linha reta) em distancia rodoviaria. FONTE: chute F1.
FATOR_RODOVIARIO = 1.40
# Velocidade media em km/h no interior. FONTE: chute F1.
VELOCIDADE_KMH = 45.0

# --- Base de partida (decisao G3: capital do estado do contrato) ---
# Coordenadas (lat, long) das capitais das 23 UFs presentes em base_contratos.json.
CAPITAIS_UF = {
    "AC": (-9.9754, -67.8249),   # Rio Branco
    "AL": (-9.6660, -35.7350),   # Maceio
    "AM": (-3.1190, -60.0217),   # Manaus
    "AP": (0.0349, -51.0694),    # Macapa
    "BA": (-12.9718, -38.5011),  # Salvador
    "CE": (-3.7172, -38.5433),   # Fortaleza
    "GO": (-16.6869, -49.2648),  # Goiania
    "MA": (-2.5307, -44.3068),   # Sao Luis
    "MS": (-20.4697, -54.6201),  # Campo Grande
    "MT": (-15.6014, -56.0979),  # Cuiaba
    "PA": (-1.4558, -48.4902),   # Belem
    "PB": (-7.1195, -34.8450),   # Joao Pessoa
    "PE": (-8.0476, -34.8770),   # Recife
    "PI": (-5.0892, -42.8019),   # Teresina
    "PR": (-25.4284, -49.2733),  # Curitiba
    "RJ": (-22.9068, -43.1729),  # Rio de Janeiro
    "RN": (-5.7945, -35.2110),   # Natal
    "RO": (-8.7612, -63.9004),   # Porto Velho
    "RR": (2.8235, -60.6758),    # Boa Vista
    "RS": (-30.0346, -51.2177),  # Porto Alegre
    "SE": (-10.9472, -37.0731),  # Aracaju
    "SP": (-23.5505, -46.6333),  # Sao Paulo
    "TO": (-10.2400, -48.3558),  # Palmas
}
# UF usada quando o contrato nao e' informado.
UF_PADRAO = "PA"
# Caminho (relativo a raiz do projeto) da base de contratos: chave = contrato,
# campos uf / tipo_contrato / vigente. Fonte: minhas_notas/base_contratos.json.
ARQUIVO_BASE_CONTRATOS = "minhas_notas/base_contratos.json"
