# -*- coding: utf-8 -*-
"""Parametros do modelo de custo - TODOS os numeros do estimador vivem aqui.

Cada parametro nasce de uma decisao do gate F1 (G1-G5, ver PLAN.md) e pode ser
ajustado sem rebuild. Cada constante tem valor e FONTE.

=== MEMORIA DE CALCULO (para humanos) ===
O custo de um estrato soma duas parcelas (formula decifrada das estimativas reais
do orgao, MODELO_CUSTO.md a.5 - reproduz 7 de 11 estimativas ao centavo):
1) ESCRITORIO (fixo por estrato): planejamento + relatorio + apresentacao =
   HORAS_ESCRITORIO_POR_OS x tarifa de escritorio (36h x R$360 = R$12.960).
2) CAMPO: horas de campo x tarifa de campo (R$600/h = R$4.800/equipe-dia).
   As horas de campo somam:
   - DESLOCAMENTO: a equipe parte da CAPITAL do estado do contrato, vai ao municipio
     (ida e volta, UMA vez por municipio), salta entre as obras do municipio e
     percorre as UCs de cada obra. Km em linha reta viram km de estrada pelo
     FATOR_RODOVIARIO; km viram horas pela VELOCIDADE_KMH.
   - INSPECAO: cada UC consome HORAS_DIA_CAMPO / UCS_POR_DIA[tipo] horas.
     LPT (rede/postes): 30 UCs/dia. MLA (fotovoltaico remoto): 3 UCs/dia.
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

# --- Jornada e produtividade (decisao G5 do gate) ---
# Horas de um dia de campo (8h x 600 = 4.800/equipe-dia, formula decifrada do orgao).
HORAS_DIA_CAMPO = 8.0
# Horas de escritorio por OS: planejamento + relatorio + apresentacao, UMA vez por estrato
# (36h x 360 = 12.960, o termo fixo da formula decifrada em MODELO_CUSTO.md a.5).
HORAS_ESCRITORIO_POR_OS = 36.0
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
