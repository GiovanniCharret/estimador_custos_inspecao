# -*- coding: utf-8 -*-
"""Parametros do modelo de custo - TODOS os numeros do estimador vivem aqui.

Cada parametro nasce de uma decisao do gate F1 (G1-G5, ver PLAN.md) e pode ser
ajustado sem rebuild. Cada constante tem valor e FONTE.

=== MEMORIA DE CALCULO (para humanos) ===
O custo e' calculado POR AMOSTRA (nao por estrato) e soma duas parcelas:

1) ESCRITORIO (fixo, UMA vez por amostra): planejamento + relatorio + apresentacao,
   com horas que MUDAM COM O TIPO DE CONTRATO (HORAS_ESCRITORIO_POR_TIPO):
     LPT / Extensao de Redes      -> 8 + 24 + 4 = 36 h x R$360 = R$12.960
     MLA / Geracao Descentralizada -> 4 + 16 + 4 = 24 h x R$360 = R$ 8.640

2) CAMPO: N_EQUIPES x TAMANHO_EQUIPE x dias faturados x HORAS_DIA_CAMPO x tarifa de
   campo (R$600/h => R$4.800 por pessoa-dia). Os dias saem da geometria:
   - DIVISAO: as N equipes sao INDEPENDENTES. O itinerario e' cortado em N blocos
     geograficos contiguos e CADA equipe sai da capital, varre o seu bloco e volta.
     Por isso o km SOMADO cresce ao dividir (+18% a +37% com duas equipes, nos dados
     reais): a ida e a volta sao cobradas uma vez por equipe.
   - ROTEIRO (de cada equipe): sai da CAPITAL da UF do contrato, encadeia as paradas
     do seu bloco numa viagem so (vizinho mais proximo, municipio a municipio e obra
     a obra dentro do municipio) e volta a capital UMA vez no fim. Nao ha ida-e-volta
     por obra nem por municipio. Km em linha reta viram km de estrada pelo
     FATOR_RODOVIARIO; km viram horas pela VELOCIDADE_KMH.
   - INSPECAO: cada UC consome HORAS_DIA_CAMPO / UCS_POR_DIA[tipo] horas.
     LPT (rede/postes): 30 UCs/dia. MLA (fotovoltaico remoto): 3 UCs/dia.
   - DIAS: ditados pela equipe MAIS LENTA (o prazo tem de caber para todas):
     teto(maior horas de campo / (HORAS_DIA_CAMPO x TAMANHO_EQUIPE)) + DIAS_MOBILIZACAO.
     Arredondado PARA CIMA porque a equipe nao vende meio dia.

BENCHMARK (minhas_notas/Tabela_Resumo_Extratos_Amostra.xlsx, aba 'Resumo'): a
engenharia da PB 7a Tranche estimou 3 amostras e as tres obedecem, ao centavo, a
   custo = 12.960 + 9.600 x (dias + 1),  onde 9.600 = 2 pessoas x 8h x R$600.
Ou seja: mesma formula desta memoria com DUAS pessoas em campo. Ha duas maneiras de
chegar la, e elas NAO sao equivalentes:
   TAMANHO_EQUIPE = 2, N_EQUIPES = 1 -> uma dupla, UM roteiro. Reproduz o benchmark
                                        ao centavo (as duas viajam juntas).
   TAMANHO_EQUIPE = 1, N_EQUIPES = 2 -> duas equipes, DOIS roteiros. Mesmo custo de
                                        pessoal, mais km - e' o padrao daqui.
O padrao (N_EQUIPES_PADRAO = 2) custa MAIS que o benchmark de mesma mao de obra,
justamente porque cobra a ida e a volta de cada equipe.

Por que assim: mantem a camada de preco que o orgao ja usa e troca o julgamento
"condicoes logisticas" por geometria reprodutivel (coordenadas das UCs), sem
depender de malha rodoviaria externa. Detalhes e alternativas: planning/MODELO_CUSTO.md.
=== FIM DA MEMORIA DE CALCULO ===
"""
# --- Equipe (decisao G1 do gate) ---
# Perfil usado na estimativa. Tecnico raramente e' usado (nao sobe em poste quem estima).
PERFIL_EQUIPE = "ENGENHEIRO"
# Tarifas R$/hora por TIPO DE CONTRATO e perfil (Formulario de OS, aba 'Custos Inspecoes',
# celulas E3:F6). 'campo' = COM deslocamento; 'escritorio' = SEM deslocamento - e' a mesma
# distincao que o formulario faz na celula O48 ('Obra Com Deslocamento: SIM/NAO').
# O tipo entra porque o formulario tem DUAS tabelas de perfil:
#   LPT (Extensao de Redes)   -> Eng. Eletricista e ELETROTECNICO
#   MLA (Geracao Descentraliz.) -> Eng. Generalista e TECNICO
# O engenheiro custa igual nos dois (360/600); quem muda e' o tecnico. Como PERFIL_EQUIPE
# e' ENGENHEIRO (G1), hoje isso nao altera nenhum numero - fica correto para o dia em que
# alguem estimar com tecnico.
TARIFAS_HORA = {
    "LPT": {
        "ENGENHEIRO": {"campo": 600.0, "escritorio": 360.0},
        "TECNICO": {"campo": 593.0, "escritorio": 250.0},
    },
    "MLA": {
        "ENGENHEIRO": {"campo": 600.0, "escritorio": 360.0},
        "TECNICO": {"campo": 513.22, "escritorio": 273.22},
    },
}
# Diaria/pernoite em R$ por equipe-dia de campo (decisao G2: tarifa ja embute -> 0).
CUSTO_DIARIA = 0.0
# PESSOAS DENTRO DE UMA equipe. G1 fixou 1 (so o engenheiro estima).
# NAO confundir com N_EQUIPES_PADRAO abaixo: aqui e' o tamanho da equipe, la e' quantas
# equipes independentes vao a campo. Uma equipe de 2 pessoas faz UM roteiro (as duas
# viajam juntas); duas equipes de 1 fazem DOIS roteiros, cada um saindo da capital.
TAMANHO_EQUIPE = 1.0
# Quantas equipes INDEPENDENTES o calculo oficial (aba Resumo) assume. Cada uma tem o
# seu roteiro, sai da capital e volta - por isso o km SOMADO cresce ao dividir, e por
# isso este parametro muda a geometria, nao so a aritmetica. Decisao do humano em
# 2026-08-13: o padrao passou de 1 para 2 (era implicito antes de o parametro existir).
N_EQUIPES_PADRAO = 2
# Faixa de equipes que a aba 'Cenarios' varre, e o teto de dias que ela aceita por
# equipe. Combinacao que nao cabe no teto nao e' calculada nem exibida (decisao do
# humano: uma amostra que precise de mais de 20 dias por equipe nao e' cenario, e'
# inviabilidade - nao ha o que apresentar).
N_EQUIPES_MIN = 1
N_EQUIPES_MAX = 7
MAX_DIAS_POR_EQUIPE = 20

# --- Jornada e produtividade (decisao G5 do gate) ---
# Horas de um dia de campo (8h x 600 = 4.800/equipe-dia, formula decifrada do orgao).
HORAS_DIA_CAMPO = 8.0
# Horas de escritorio por OS (planejamento + relatorio + apresentacao), UMA vez por AMOSTRA
# e DIFERENTES POR TIPO DE CONTRATO. Fonte: Formulario de OS, aba 'Custos Inspecoes',
# celulas E26:E29 - tres formulas que leem o 'Tipo de obra' escolhido na celula E48 da aba
# 'Ordem de Servico Emissao'. E' um parametro binario que o modelo ignorava ate 2026-08-13:
#
#   etapa          Extensao de Redes (LPT)   Geracao Descentralizada (MLA)
#   planejamento              8 h                        4 h
#   relatorio                24 h                       16 h
#   apresentacao              4 h                        4 h
#   TOTAL                    36 h                       24 h
#
# Os 36 h que valiam para tudo eram os da EXTENSAO - logo, todo contrato MLA vinha com 12 h
# de escritorio a mais (R$ 4.320 por amostra). Mantido o desdobramento por etapa, e nao so
# o total, porque e' assim que a OS e' preenchida e conferida.
# A etapa 'Desenvolvimento' do formulario (112 h LPT / 56 h MLA) NAO entra aqui: e' o tempo
# de campo, que este projeto calcula da geometria em vez de assumir por tabela.
HORAS_ESCRITORIO_POR_TIPO = {
    "LPT": {"planejamento": 8.0, "relatorio": 24.0, "apresentacao": 4.0},
    "MLA": {"planejamento": 4.0, "relatorio": 16.0, "apresentacao": 4.0},
}
# Dias cobrados alem dos dias de trabalho, para a mobilizacao (sair da capital / voltar).
# CADA EQUIPE carrega o seu: o benchmark da engenharia cobra equipes x (dias + 1).
DIAS_MOBILIZACAO = 1.0
# Amostra usada quando o usuario nao escolhe (1 = principal; 2 e 3 sao as reservas).
AMOSTRA_PADRAO = 1
# UCs inspecionadas por equipe por dia, por tipo de contrato (decisao G5):
# LPT = obras com rede/postes/transformador; MLA = fotovoltaico em regioes remotas.
UCS_POR_DIA = {"LPT": 30.0, "MLA": 3.0}
# Tipo usado quando o contrato nao e' informado/encontrado.
TIPO_CONTRATO_PADRAO = "LPT"

# --- Chave de juncao entre o Lote e o Anexo V, por tipo de contrato ---
# GAP SEMANTICO DO SISTEMA LEGADO: a coluna do Lote se chama 'ODI' nos dois tipos de
# contrato, mas o que ela GUARDA muda:
#   LPT -> numero da ODI mesmo. Uma ODI agrupa varias UCs.
#   MLA -> numero da UNIDADE CONSUMIDORA. Cada obra e' um sistema individual, entao o
#          sistema legado que gera o Lote nunca criou um numero de ODI proprio e reaproveitou
#          a coluna. No Anexo V esse numero mora em 'Numero da Unidade Consumidora'.
# Sem esta tabela o programa juntaria pela coluna errada e acusaria "tranche errada" em
# dados perfeitamente validos (verificado na 3a Tranche RO, ECM 022/2025).
# Valores possiveis: "ODI" (casa com 'Numero ODI') e "UC" (casa com 'Numero da UC').
CHAVE_JUNCAO_POR_TIPO = {"LPT": "ODI", "MLA": "UC"}

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
# campos uf / tipo_contrato / vigente.
# Mora em dados/ e nao em minhas_notas/ porque e' INSUMO DE EXECUCAO, nao material de
# pesquisa: o programa nao roda sem ele e ele viaja no pacote enviado aos usuarios -
# uma pasta chamada "minhas_notas" nao faz sentido na maquina de quem recebe.
ARQUIVO_BASE_CONTRATOS = "dados/base_contratos.json"
