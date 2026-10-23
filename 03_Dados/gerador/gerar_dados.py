"""
People Beauty - FP&A Analytics
Gerador de dados fictícios (versão 1.0)

Gera os arquivos CSV de 03_Dados/csv/ a partir de premissas fixas e de uma
semente aleatória fixa. Executar de novo produz exatamente os mesmos arquivos.

Uso (Python 3.9+, somente biblioteca padrão):
    python 03_Dados/gerador/gerar_dados.py
    python 03_Dados/gerador/gerar_dados.py --saida C:\\temp\\csv --semente 2026

Formato dos arquivos: UTF-8 sem BOM, separador ';', decimal '.', datas
AAAA-MM-DD, cabeçalho na primeira linha. Valores monetários em BRL, sempre
positivos; o sinal na DRE vem de dim_plano_contas.SinalDRE.

Todos os dados são fictícios. Marcas de produtos são referências reais
permitidas pelo projeto; nomes de lojas, valores e volumes são inventados.
"""

import argparse
import calendar
import csv
import math
import os
import random
from collections import defaultdict
from datetime import date, timedelta

# =============================================================================
# 0. PARÂMETROS GERAIS
# =============================================================================
SEMENTE_PADRAO = 20261022
ANO_INICIO, ANO_FIM = 2024, 2026
DATA_CORTE_REALIZADO = date(2026, 9, 30)   # último dia com realizado
CENARIO_ORC = "ORCAMENTO_APROVADO"
CENARIO_FCT = "FORECAST_2026_9P3"

MESES_PT = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho",
            "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
MESES_ABREV = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set",
               "out", "nov", "dez"]
DIAS_PT = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira",
           "Sexta-feira", "Sábado", "Domingo"]

# =============================================================================
# 1. DIMENSÕES
# =============================================================================
# Código, nome, tipo, região, UF, cidade, abertura, formato, área m², fator de
# potencial de vendas (1,00 = loja média), aluguel R$/m² em 2024 (área e aluguel calibrados para o porte da loja).
LOJAS = [
    ("L001", "People Beauty Paulista",         "LOJA", "Sudeste",      "SP", "São Paulo",      "2016-03-15", "Rua",       95, 1.45, 130),
    ("L002", "People Beauty Moema",            "LOJA", "Sudeste",      "SP", "São Paulo",      "2017-05-10", "Shopping",  85, 1.20, 120),
    ("L003", "People Beauty Tatuapé",          "LOJA", "Sudeste",      "SP", "São Paulo",      "2018-08-20", "Shopping",  80, 1.10, 110),
    ("L004", "People Beauty Santo André",      "LOJA", "Sudeste",      "SP", "Santo André",    "2018-11-05", "Shopping",  75, 0.95, 100),
    ("L005", "People Beauty Campinas",         "LOJA", "Sudeste",      "SP", "Campinas",       "2019-02-12", "Shopping",  75, 1.05, 105),
    ("L006", "People Beauty Ribeirão Preto",   "LOJA", "Sudeste",      "SP", "Ribeirão Preto", "2019-06-03", "Shopping",  70, 0.90, 95),
    ("L007", "People Beauty Sorocaba",         "LOJA", "Sudeste",      "SP", "Sorocaba",       "2020-09-14", "Shopping",  65, 0.80, 90),
    ("L008", "People Beauty Copacabana",       "LOJA", "Sudeste",      "RJ", "Rio de Janeiro", "2017-10-02", "Rua",       80, 1.15, 115),
    ("L009", "People Beauty Tijuca",           "LOJA", "Sudeste",      "RJ", "Rio de Janeiro", "2019-04-22", "Shopping",  75, 0.95, 100),
    ("L010", "People Beauty Niterói",          "LOJA", "Sudeste",      "RJ", "Niterói",        "2020-03-02", "Shopping",  70, 0.90, 100),
    ("L011", "People Beauty Savassi",          "LOJA", "Sudeste",      "MG", "Belo Horizonte", "2018-07-09", "Rua",       75, 1.05, 90),
    ("L012", "People Beauty Uberlândia",       "LOJA", "Sudeste",      "MG", "Uberlândia",     "2021-05-17", "Shopping",  65, 0.72, 150),
    ("L013", "People Beauty Vitória",          "LOJA", "Sudeste",      "ES", "Vitória",        "2021-08-23", "Shopping",  70, 0.85, 95),
    ("L014", "People Beauty Batel",            "LOJA", "Sul",          "PR", "Curitiba",       "2018-04-16", "Shopping",  80, 1.10, 110),
    ("L015", "People Beauty Londrina",         "LOJA", "Sul",          "PR", "Londrina",       "2021-10-04", "Shopping",  65, 0.80, 85),
    ("L016", "People Beauty Moinhos de Vento", "LOJA", "Sul",          "RS", "Porto Alegre",   "2019-09-30", "Rua",       75, 1.00, 90),
    ("L017", "People Beauty Florianópolis",    "LOJA", "Sul",          "SC", "Florianópolis",  "2020-11-09", "Shopping",  75, 0.95, 100),
    ("L018", "People Beauty Joinville",        "LOJA", "Sul",          "SC", "Joinville",      "2022-03-21", "Shopping",  65, 0.75, 85),
    ("L019", "People Beauty Asa Sul",          "LOJA", "Centro-Oeste", "DF", "Brasília",       "2019-12-02", "Shopping",  75, 1.05, 105),
    ("L020", "People Beauty Goiânia",          "LOJA", "Centro-Oeste", "GO", "Goiânia",        "2022-06-13", "Shopping",  65, 0.70, 185),
    ("L021", "People Beauty Salvador",         "LOJA", "Nordeste",     "BA", "Salvador",       "2021-02-08", "Shopping",  75, 0.95, 100),
    ("L022", "People Beauty Recife",           "LOJA", "Nordeste",     "PE", "Recife",         "2022-09-05", "Shopping",  70, 0.90, 95),
    ("L023", "People Beauty Fortaleza",        "LOJA", "Nordeste",     "CE", "Fortaleza",      "2025-03-10", "Shopping",  75, 0.95, 100),
    ("L024", "People Beauty Campo Grande",     "LOJA", "Centro-Oeste", "MS", "Campo Grande",   "2025-08-18", "Shopping",  70, 0.85, 85),
    ("CORP", "People Beauty Corporativo", "CORPORATIVA", "Corporativo", "SP", "São Paulo",      "2016-01-04", "Escritório", 0, 0.0, 0),
]

DEPARTAMENTOS = [
    ("OPERACOES_LOJA", "Operações de Loja"),
    ("COMERCIAL",      "Comercial e Compras"),
    ("MARKETING",      "Marketing"),
    ("LOGISTICA",      "Logística e Distribuição"),
    ("FINANCEIRO",     "Financeiro e Controladoria"),
    ("GENTE_GESTAO",   "Gente e Gestão"),
    ("TECNOLOGIA",     "Tecnologia"),
    ("DIRETORIA",      "Diretoria e Administrativo"),
]

CENARIOS = [
    ("REALIZADO",          "Realizado",          "REALIZADO", "FECHADO",  "Realizado de jan/2024 a set/2026: fato_vendas_AAAA, fato_devolucoes e fato_despesas."),
    ("ORCAMENTO_APROVADO", "Orçamento Aprovado", "ORCAMENTO", "APROVADO", "Orçamento anual aprovado de 2024, 2025 e 2026: fato_orcamento."),
    ("FORECAST_2026_9P3",  "Forecast 9+3 2026",  "FORECAST",  "VIGENTE",  "Projeção de out-dez/2026 feita na data de corte (fato_forecast). Jan-set/2026 vem do realizado."),
]

# Código, nome, grupo DRE, natureza, sinal, alimentada por despesa, pai, nível,
# ordem, participa: receita líquida, CMV, resultado operacional, resultado líquido.
PLANO_CONTAS = [
    ("3.1",    "Receita bruta",                             "Receita bruta",         "RECEITA",  1, 0, "",    1, 100, 1, 0, 1, 1),
    ("3.1.01", "Venda de mercadorias",                      "Receita bruta",         "RECEITA",  1, 0, "3.1", 2, 110, 1, 0, 1, 1),
    ("3.2",    "Deduções da receita",                       "Deduções",              "DEDUCAO", -1, 0, "",    1, 200, 1, 0, 1, 1),
    ("3.2.01", "Impostos sobre vendas",                     "Deduções",              "DEDUCAO", -1, 1, "3.2", 2, 210, 1, 0, 1, 1),
    ("3.2.02", "Descontos concedidos",                      "Deduções",              "DEDUCAO", -1, 0, "3.2", 2, 220, 1, 0, 1, 1),
    ("3.2.03", "Devoluções de vendas",                      "Deduções",              "DEDUCAO", -1, 0, "3.2", 2, 230, 1, 0, 1, 1),
    ("4.1",    "Custo das mercadorias vendidas",            "CMV",                   "CUSTO",   -1, 0, "",    1, 300, 0, 1, 1, 1),
    ("4.1.01", "CMV - mercadorias",                         "CMV",                   "CUSTO",   -1, 0, "4.1", 2, 310, 0, 1, 1, 1),
    ("5",      "Despesas operacionais",                     "Despesas operacionais", "DESPESA", -1, 0, "",    1, 400, 0, 0, 1, 1),
    ("5.1",    "Despesas com pessoal",                      "Despesas operacionais", "DESPESA", -1, 0, "5",   2, 410, 0, 0, 1, 1),
    ("5.1.01", "Salários e encargos",                       "Despesas operacionais", "DESPESA", -1, 1, "5.1", 3, 411, 0, 0, 1, 1),
    ("5.1.02", "Benefícios",                                "Despesas operacionais", "DESPESA", -1, 1, "5.1", 3, 412, 0, 0, 1, 1),
    ("5.1.03", "Comissões de vendas",                       "Despesas operacionais", "DESPESA", -1, 1, "5.1", 3, 413, 0, 0, 1, 1),
    ("5.2",    "Despesas de ocupação",                      "Despesas operacionais", "DESPESA", -1, 0, "5",   2, 420, 0, 0, 1, 1),
    ("5.2.01", "Aluguel e condomínio",                      "Despesas operacionais", "DESPESA", -1, 1, "5.2", 3, 421, 0, 0, 1, 1),
    ("5.2.02", "Energia elétrica",                          "Despesas operacionais", "DESPESA", -1, 1, "5.2", 3, 422, 0, 0, 1, 1),
    ("5.2.03", "Água, gás e telefonia",                     "Despesas operacionais", "DESPESA", -1, 1, "5.2", 3, 423, 0, 0, 1, 1),
    ("5.2.04", "Manutenção e conservação",                  "Despesas operacionais", "DESPESA", -1, 1, "5.2", 3, 424, 0, 0, 1, 1),
    ("5.3",    "Despesas comerciais e de marketing",        "Despesas operacionais", "DESPESA", -1, 0, "5",   2, 430, 0, 0, 1, 1),
    ("5.3.01", "Marketing e mídia",                         "Despesas operacionais", "DESPESA", -1, 1, "5.3", 3, 431, 0, 0, 1, 1),
    ("5.3.02", "Taxas de cartão e meios de pagamento",      "Despesas operacionais", "DESPESA", -1, 1, "5.3", 3, 432, 0, 0, 1, 1),
    ("5.3.03", "Embalagens e materiais de loja",            "Despesas operacionais", "DESPESA", -1, 1, "5.3", 3, 433, 0, 0, 1, 1),
    ("5.4",    "Despesas administrativas",                  "Despesas operacionais", "DESPESA", -1, 0, "5",   2, 440, 0, 0, 1, 1),
    ("5.4.01", "Tecnologia e sistemas",                     "Despesas operacionais", "DESPESA", -1, 1, "5.4", 3, 441, 0, 0, 1, 1),
    ("5.4.02", "Serviços de terceiros",                     "Despesas operacionais", "DESPESA", -1, 1, "5.4", 3, 442, 0, 0, 1, 1),
    ("5.4.03", "Viagens e deslocamentos",                   "Despesas operacionais", "DESPESA", -1, 1, "5.4", 3, 443, 0, 0, 1, 1),
    ("5.4.04", "Despesas gerais",                           "Despesas operacionais", "DESPESA", -1, 1, "5.4", 3, 444, 0, 0, 1, 1),
    ("5.5",    "Despesas logísticas",                       "Despesas operacionais", "DESPESA", -1, 0, "5",   2, 450, 0, 0, 1, 1),
    ("5.5.01", "Fretes e distribuição",                     "Despesas operacionais", "DESPESA", -1, 1, "5.5", 3, 451, 0, 0, 1, 1),
    ("5.6",    "Depreciação e amortização",                 "Despesas operacionais", "DESPESA", -1, 0, "5",   2, 460, 0, 0, 1, 1),
    ("5.6.01", "Depreciação de instalações e equipamentos", "Despesas operacionais", "DESPESA", -1, 1, "5.6", 3, 461, 0, 0, 1, 1),
    ("6.1",    "Resultado financeiro",                      "Resultado financeiro",  "DESPESA", -1, 0, "",    1, 500, 0, 0, 0, 1),
    ("6.1.01", "Receitas financeiras",                      "Resultado financeiro",  "RECEITA",  1, 1, "6.1", 2, 510, 0, 0, 0, 1),
    ("6.1.02", "Despesas financeiras",                      "Resultado financeiro",  "DESPESA", -1, 1, "6.1", 2, 520, 0, 0, 0, 1),
    ("7.1",    "Impostos sobre o lucro",                    "Impostos sobre lucro",  "DESPESA", -1, 0, "",    1, 600, 0, 0, 0, 1),
    ("7.1.01", "IRPJ e CSLL",                               "Impostos sobre lucro",  "DESPESA", -1, 1, "7.1", 2, 610, 0, 0, 0, 1),
]

# Código, nome, categoria, subcategoria, marca, status, preço de lista 2024
# (R$), peso de giro (unidades relativas por mês). Itens INATIVO saem de linha
# na data indicada em DESCONTINUADOS.
PRODUTOS = [
    ("PB-CAB-0001", "Elseve Shampoo Reparação Total 400 ml",            "Cabelos", "Shampoo",         "Elseve",              "ATIVO",   24.90, 22),
    ("PB-CAB-0002", "Elseve Condicionador Reparação Total 400 ml",      "Cabelos", "Condicionador",   "Elseve",              "ATIVO",   26.90, 18),
    ("PB-CAB-0003", "Elseve Máscara Hidratação Intensa 300 g",          "Cabelos", "Máscara capilar", "Elseve",              "ATIVO",   32.90, 12),
    ("PB-CAB-0004", "Elseve Óleo Capilar Nutrição 100 ml",              "Cabelos", "Finalizador",     "Elseve",              "ATIVO",   36.90, 8),
    ("PB-CAB-0005", "Pantene Shampoo Liso Extremo 400 ml",              "Cabelos", "Shampoo",         "Pantene",             "ATIVO",   23.90, 20),
    ("PB-CAB-0006", "Pantene Condicionador Liso Extremo 400 ml",        "Cabelos", "Condicionador",   "Pantene",             "ATIVO",   25.90, 16),
    ("PB-CAB-0007", "Pantene Ampola de Tratamento 15 ml",               "Cabelos", "Tratamento",      "Pantene",             "ATIVO",    9.90, 14),
    ("PB-CAB-0008", "Salon Line Creme para Pentear Cachos 300 ml",      "Cabelos", "Finalizador",     "Salon Line",          "ATIVO",   19.90, 20),
    ("PB-CAB-0009", "Salon Line Gelatina Modeladora 550 g",             "Cabelos", "Finalizador",     "Salon Line",          "ATIVO",   21.90, 14),
    ("PB-CAB-0010", "Salon Line Shampoo Low Poo 300 ml",                "Cabelos", "Shampoo",         "Salon Line",          "ATIVO",   18.90, 14),
    ("PB-CAB-0011", "Wella Professionals Shampoo Profissional 250 ml",  "Cabelos", "Shampoo",         "Wella Professionals", "ATIVO",   89.90, 5),
    ("PB-CAB-0012", "Wella Professionals Máscara Reconstrução 150 ml",  "Cabelos", "Máscara capilar", "Wella Professionals", "ATIVO",  119.90, 4),
    ("PB-CAB-0013", "Wella Professionals Óleo Reflexo 100 ml",          "Cabelos", "Finalizador",     "Wella Professionals", "ATIVO",  139.90, 3),
    ("PB-CAB-0014", "L'Oréal Paris Coloração Permanente Castanho",      "Cabelos", "Coloração",       "L'Oréal Paris",       "ATIVO",   34.90, 10),
    ("PB-CAB-0015", "L'Oréal Paris Coloração Permanente Louro Claro",   "Cabelos", "Coloração",       "L'Oréal Paris",       "ATIVO",   34.90, 8),
    ("PB-CAB-0016", "Pantene Shampoo Cachos 175 ml",                    "Cabelos", "Shampoo",         "Pantene",             "INATIVO", 14.90, 10),
    ("PB-SKN-0001", "CeraVe Loção Hidratante Facial 52 ml",             "Skincare", "Hidratante facial",   "CeraVe",         "ATIVO",   79.90, 8),
    ("PB-SKN-0002", "CeraVe Gel de Limpeza Facial 236 ml",              "Skincare", "Limpeza facial",      "CeraVe",         "ATIVO",   84.90, 8),
    ("PB-SKN-0003", "CeraVe Creme Hidratante Corporal 454 g",           "Skincare", "Hidratante corporal", "CeraVe",         "ATIVO",  119.90, 5),
    ("PB-SKN-0004", "La Roche-Posay Protetor Solar Facial FPS 60 40 g", "Skincare", "Protetor solar",      "La Roche-Posay", "ATIVO",   89.90, 10),
    ("PB-SKN-0005", "La Roche-Posay Gel de Limpeza Pele Oleosa 150 g",  "Skincare", "Limpeza facial",      "La Roche-Posay", "ATIVO",   94.90, 5),
    ("PB-SKN-0006", "La Roche-Posay Água Termal 150 ml",                "Skincare", "Tratamento facial",   "La Roche-Posay", "ATIVO",   69.90, 5),
    ("PB-SKN-0007", "Principia Sérum Niacinamida 30 ml",                "Skincare", "Sérum",               "Principia",      "ATIVO",   49.90, 10),
    ("PB-SKN-0008", "Principia Sérum Vitamina C 30 ml",                 "Skincare", "Sérum",               "Principia",      "ATIVO",   59.90, 8),
    ("PB-SKN-0009", "Principia Gel de Limpeza Facial 150 ml",           "Skincare", "Limpeza facial",      "Principia",      "ATIVO",   39.90, 7),
    ("PB-SKN-0010", "Neutrogena Protetor Solar Corporal FPS 50 200 ml", "Skincare", "Protetor solar",      "Neutrogena",     "ATIVO",   64.90, 8),
    ("PB-SKN-0011", "Neutrogena Hidratante Facial em Gel 50 g",         "Skincare", "Hidratante facial",   "Neutrogena",     "ATIVO",   54.90, 6),
    ("PB-SKN-0012", "Neutrogena Lenço Demaquilante 25 unidades",        "Skincare", "Limpeza facial",      "Neutrogena",     "ATIVO",   24.90, 12),
    ("PB-SKN-0013", "NIVEA Creme Hidratante Facial 100 g",              "Skincare", "Hidratante facial",   "NIVEA",          "ATIVO",   29.90, 12),
    ("PB-SKN-0014", "NIVEA Protetor Solar FPS 50 200 ml",               "Skincare", "Protetor solar",      "NIVEA",          "ATIVO",   49.90, 10),
    ("PB-SKN-0015", "L'Oréal Paris Sérum Facial Anti-idade 30 ml",      "Skincare", "Sérum",               "L'Oréal Paris",  "ATIVO",   74.90, 6),
    ("PB-MAQ-0001", "Maybelline Máscara de Cílios à Prova d'Água",      "Maquiagem", "Olhos",      "Maybelline", "ATIVO",   54.90, 12),
    ("PB-MAQ-0002", "Maybelline Base Líquida Matte 30 ml",              "Maquiagem", "Rosto",      "Maybelline", "ATIVO",   59.90, 10),
    ("PB-MAQ-0003", "Maybelline Corretivo Líquido 6 ml",                "Maquiagem", "Rosto",      "Maybelline", "ATIVO",   44.90, 10),
    ("PB-MAQ-0004", "Vult Batom Cremoso",                               "Maquiagem", "Lábios",     "Vult",       "ATIVO",   19.90, 16),
    ("PB-MAQ-0005", "Vult Pó Compacto Translúcido",                     "Maquiagem", "Rosto",      "Vult",       "ATIVO",   29.90, 10),
    ("PB-MAQ-0006", "Vult Lápis de Olho Preto",                         "Maquiagem", "Olhos",      "Vult",       "ATIVO",   14.90, 16),
    ("PB-MAQ-0007", "Ruby Rose Paleta de Sombras 12 cores",             "Maquiagem", "Olhos",      "Ruby Rose",  "ATIVO",   39.90, 8),
    ("PB-MAQ-0008", "Ruby Rose Batom Líquido Matte",                    "Maquiagem", "Lábios",     "Ruby Rose",  "ATIVO",   16.90, 16),
    ("PB-MAQ-0009", "Ruby Rose Kit de Pincéis 5 peças",                 "Maquiagem", "Acessórios", "Ruby Rose",  "ATIVO",   34.90, 6),
    ("PB-MAQ-0010", "Boca Rosa Base Líquida 30 ml",                     "Maquiagem", "Rosto",      "Boca Rosa",  "ATIVO",   69.90, 9),
    ("PB-MAQ-0011", "Boca Rosa Blush Cremoso",                          "Maquiagem", "Rosto",      "Boca Rosa",  "ATIVO",   49.90, 8),
    ("PB-MAQ-0012", "Boca Rosa Gloss Labial",                           "Maquiagem", "Lábios",     "Boca Rosa",  "ATIVO",   39.90, 10),
    ("PB-MAQ-0013", "L'Oréal Paris Máscara de Cílios Volume",           "Maquiagem", "Olhos",      "L'Oréal Paris", "ATIVO", 59.90, 9),
    ("PB-MAQ-0014", "Vult Sombra Individual",                           "Maquiagem", "Olhos",      "Vult",       "INATIVO", 12.90, 10),
    ("PB-HIG-0001", "Dove Sabonete em Barra 90 g",                      "Higiene pessoal", "Sabonete",            "Dove",       "ATIVO",  4.49, 24),
    ("PB-HIG-0002", "Dove Sabonete Líquido 250 ml",                     "Higiene pessoal", "Sabonete",            "Dove",       "ATIVO", 19.90, 18),
    ("PB-HIG-0003", "Dove Desodorante Aerosol 150 ml",                  "Higiene pessoal", "Desodorante",         "Dove",       "ATIVO", 17.90, 16),
    ("PB-HIG-0004", "Rexona Desodorante Aerosol Masculino 150 ml",      "Higiene pessoal", "Desodorante",         "Rexona",     "ATIVO", 15.90, 15),
    ("PB-HIG-0005", "Rexona Desodorante Roll-on 50 ml",                 "Higiene pessoal", "Desodorante",         "Rexona",     "ATIVO", 11.90, 12),
    ("PB-HIG-0006", "NIVEA Desodorante Aerosol 150 ml",                 "Higiene pessoal", "Desodorante",         "NIVEA",      "ATIVO", 16.90, 13),
    ("PB-HIG-0007", "NIVEA Loção Hidratante Corporal 400 ml",           "Higiene pessoal", "Hidratante corporal", "NIVEA",      "ATIVO", 29.90, 14),
    ("PB-HIG-0008", "Granado Sabonete Glicerina 90 g",                  "Higiene pessoal", "Sabonete",            "Granado",    "ATIVO",  7.90, 16),
    ("PB-HIG-0009", "Granado Talco Antisséptico 100 g",                 "Higiene pessoal", "Cuidados com os pés", "Granado",    "ATIVO", 14.90, 10),
    ("PB-HIG-0010", "Granado Água de Colônia 230 ml",                   "Higiene pessoal", "Perfumaria",          "Granado",    "ATIVO", 49.90, 6),
    ("PB-HIG-0011", "Johnson's Shampoo Infantil 200 ml",                "Higiene pessoal", "Infantil",            "Johnson's",  "ATIVO", 16.90, 12),
    ("PB-HIG-0012", "Johnson's Óleo Corporal Infantil 200 ml",          "Higiene pessoal", "Infantil",            "Johnson's",  "ATIVO", 24.90, 8),
    ("PB-HIG-0013", "Johnson's Sabonete Líquido Infantil 200 ml",       "Higiene pessoal", "Infantil",            "Johnson's",  "ATIVO", 18.90, 10),
    ("PB-ELE-0001", "Taiff Secador de Cabelo 2000 W",                   "Eletro beleza", "Secador",         "Taiff",    "ATIVO", 299.90, 2.2),
    ("PB-ELE-0002", "Taiff Prancha Alisadora Cerâmica",                 "Eletro beleza", "Prancha",         "Taiff",    "ATIVO", 249.90, 2.0),
    ("PB-ELE-0003", "Taiff Modelador de Cachos",                        "Eletro beleza", "Modelador",       "Taiff",    "ATIVO", 219.90, 1.2),
    ("PB-ELE-0004", "Philips Secador de Cabelo Compacto 1600 W",        "Eletro beleza", "Secador",         "Philips",  "ATIVO", 169.90, 2.4),
    ("PB-ELE-0005", "Philips Prancha Alisadora Íons",                   "Eletro beleza", "Prancha",         "Philips",  "ATIVO", 199.90, 2.0),
    ("PB-ELE-0006", "Philips Aparador de Pelos Multifuncional",         "Eletro beleza", "Aparador",        "Philips",  "ATIVO", 229.90, 1.6),
    ("PB-ELE-0007", "Britânia Secador de Cabelo 1900 W",                "Eletro beleza", "Secador",         "Britânia", "ATIVO", 139.90, 2.4),
    ("PB-ELE-0008", "Britânia Escova Secadora Rotativa",                "Eletro beleza", "Escova secadora", "Britânia", "ATIVO", 189.90, 2.0),
]
# Itens inativos: último mês com venda.
DESCONTINUADOS = {"PB-CAB-0016": 202506, "PB-MAQ-0014": 202412}

CATEGORIAS = ["Cabelos", "Skincare", "Maquiagem", "Higiene pessoal", "Eletro beleza"]

CODIGO_CATEGORIA = {"Cabelos": "CAB", "Skincare": "SKN", "Maquiagem": "MAQ",
                    "Higiene pessoal": "HIG", "Eletro beleza": "ELE"}
DESCRICAO_CATEGORIA = {
    "Cabelos": "Shampoos, condicionadores, tratamentos, finalizadores e coloração",
    "Skincare": "Dermocosméticos: limpeza, hidratação, sérum e proteção solar",
    "Maquiagem": "Rosto, olhos, lábios e acessórios",
    "Higiene pessoal": "Sabonetes, desodorantes, hidratantes corporais, infantil e colônias",
    "Eletro beleza": "Secadores, pranchas, modeladores e aparadores",
}
# Custo de aquisição / preço de lista (2024), por categoria.
RAZAO_CUSTO = {"Cabelos": 0.33, "Skincare": 0.36, "Maquiagem": 0.29,
               "Higiene pessoal": 0.40, "Eletro beleza": 0.47}

# =============================================================================
# 2. PREMISSAS DE NEGÓCIO (realizado x orçamento)
# =============================================================================
# Receita bruta média de uma loja de fator 1,00 num mês médio de 2024 (R$).
RECEITA_BRUTA_BASE = 100000.0

# Sazonalidade do varejo de beleza: Dia das Mães (mai), Namorados (jun),
# Pais (ago), Black Friday (nov) e Natal (dez).
SAZONALIDADE = [0.86, 0.83, 0.95, 0.96, 1.17, 1.02, 0.96, 1.00, 0.95, 1.00, 1.16, 1.44]
SAZ_CATEGORIA = {
    "Skincare":      [1.12, 1.08, 1.00, 0.95, 0.95, 0.92, 0.92, 0.95, 1.00, 1.02, 1.03, 1.06],  # protetor solar no verão
    "Eletro beleza": [0.85, 0.85, 0.95, 0.95, 1.20, 1.00, 0.90, 1.05, 0.90, 0.95, 1.30, 1.35],  # presentes
}
# Peso relativo de cada dia da semana (seg..dom).
PESO_DIA_SEMANA = [0.80, 0.88, 0.90, 0.95, 1.12, 1.40, 0.75]

# Índice de volume por categoria em relação a 2024 (mesmas lojas).
VOLUME_REAL = {
    2024: {c: 1.00 for c in CATEGORIAS},
    2025: {"Cabelos": 1.035, "Skincare": 1.075, "Maquiagem": 1.040, "Higiene pessoal": 1.020, "Eletro beleza": 1.030},
    2026: {"Cabelos": 1.045, "Skincare": 1.150, "Maquiagem": 0.985, "Higiene pessoal": 1.030, "Eletro beleza": 0.960},
}
# O que cada orçamento anual assumiu para o mesmo índice.
VOLUME_ORC = {
    2024: {"Cabelos": 1.020, "Skincare": 1.030, "Maquiagem": 1.025, "Higiene pessoal": 1.015, "Eletro beleza": 1.040},
    2025: {"Cabelos": 1.030, "Skincare": 1.070, "Maquiagem": 1.050, "Higiene pessoal": 1.020, "Eletro beleza": 1.040},
    2026: {"Cabelos": 1.075, "Skincare": 1.140, "Maquiagem": 1.090, "Higiene pessoal": 1.050, "Eletro beleza": 1.080},
}
# Reajuste acumulado da tabela de preços de venda, aplicado em janeiro (base 2024 = 1).
PRECO_REAL = {2024: 1.000, 2025: 1.045, 2026: 1.045 * 1.050}
PRECO_ORC = {2024: 1.000, 2025: 1.045, 2026: 1.045 * 1.060}
# Reajuste acumulado do custo de aquisição. Eletro sofre com o câmbio em 2026.
CUSTO_REAL = {2024: {c: 1.0 for c in CATEGORIAS},
              2025: {c: 1.045 for c in CATEGORIAS},
              2026: {c: 1.045 * (1.095 if c == "Eletro beleza" else 1.052) for c in CATEGORIAS}}
CUSTO_ORC = {2024: {c: 1.0 for c in CATEGORIAS},
             2025: {c: 1.045 for c in CATEGORIAS},
             2026: {c: 1.045 * 1.050 for c in CATEGORIAS}}

# Descontos promocionais por item: probabilidade de o item ter desconto e
# percentuais possíveis. Desconto médio esperado = prob x 0,20.
PERCENTUAIS_DESCONTO = [0.10, 0.15, 0.20, 0.25, 0.30]
PROB_DESCONTO_REAL = {2024: 0.250, 2025: 0.260, 2026: 0.320}  # 2026: campanhas para sustentar volume
PROB_EXTRA_NOV = 0.175                                          # Black Friday
DESCONTO_ORC = {2024: 0.050, 2025: 0.050, 2026: 0.050}          # % da receita bruta
DESCONTO_EXTRA_NOV_ORC = 0.030
# Devoluções: probabilidade de um item vendido ser devolvido (até 30 dias).
DEVOLUCAO_REAL = {"Eletro beleza": 0.025, "_": 0.011}
DEVOLUCAO_ORC = {"Eletro beleza": 0.020, "_": 0.010}
# Alíquota efetiva de ICMS + PIS/COFINS sobre a venda líquida de descontos e devoluções.
ALIQ_IMPOSTO_VENDA = 0.17
ALIQ_IR_CSLL = 0.34

# Fator de desempenho por loja e ano (realizado). O orçamento assume 1,00.
DESEMPENHO_LOJA = {
    "L001": {2025: 1.02, 2026: 1.03},
    "L012": {2024: 0.97, 2025: 0.93, 2026: 0.86},   # concorrência nova no shopping
    "L020": {2024: 0.96, 2025: 0.92, 2026: 0.88},   # baixo fluxo, aluguel caro
    "L014": {2026: 1.04},
    "L019": {2026: 1.03},
    "L007": {2026: 0.95},
}
# Rampa de maturação de lojas novas (meses até 100% do potencial).
RAMPA_REAL = {"L023": 16, "L024": 8}
RAMPA_ORC = {"L023": 9, "L024": 10}
RAMPA_INICIAL = 0.55

# Dissídio (reajuste salarial aplicado em maio).
DISSIDIO_REAL = {2024: 0.050, 2025: 0.055, 2026: 0.068}
DISSIDIO_ORC = {2024: 0.050, 2025: 0.050, 2026: 0.050}
# Energia: bandeira tarifária vermelha a partir de jun/2026.
ENERGIA_EXTRA_REAL = {202606: 1.14, 202607: 1.16, 202608: 1.18, 202609: 1.15}
# Reajuste anual de aluguel (IGP-M / IPCA) aplicado em janeiro.
ALUGUEL_REAJ = {2024: 1.000, 2025: 1.045, 2026: 1.045 * 1.050}
INFLACAO = PRECO_REAL   # reajuste genérico de despesas gerais

# Contas cujo valor acompanha a receita (usado no forecast).
CONTAS_VARIAVEIS = {"3.2.01", "5.1.03", "5.3.01", "5.3.02", "5.3.03", "5.5.01", "6.1.01", "6.1.02"}


def arred(v):
    return round(v + 1e-9, 2)


def primeiro_dia(am):
    return date(am // 100, am % 100, 1).isoformat()


def meses_periodo():
    for ano in range(ANO_INICIO, ANO_FIM + 1):
        for mes in range(1, 13):
            yield ano, mes


def realizado(ano, mes):
    return date(ano, mes, calendar.monthrange(ano, mes)[1]) <= DATA_CORTE_REALIZADO


def slug(txt):
    trad = str.maketrans("áàâãéêíóôõúçÁÀÂÃÉÊÍÓÔÕÚÇ'", "aaaaeeiooouc" + "AAAAEEIOOOUC" + " ")
    return "_".join(txt.translate(trad).upper().replace("-", " ").split())


def preco_tabela(preco_2024, ano):
    """Preço de venda do ano: reajuste de janeiro arredondado para o final ,90
    mais próximo (,49 ou ,99 abaixo de R$ 10). Em 2024 vale o preço de lista."""
    if ano == ANO_INICIO:
        return preco_2024
    p = preco_2024 * PRECO_REAL[ano]
    if p < 10:
        return round(round((p - 0.49) * 2) / 2 + 0.49, 2)
    return round(round(p - 0.90) + 0.90, 2)


def fator_salarial(dissidio, ano, mes):
    """Índice salarial acumulado desde jan/2024 (dissídio em maio)."""
    f = 1.0
    for a in range(ANO_INICIO, ano + 1):
        if a < ano or mes >= 5:
            f *= 1 + dissidio[a]
    return f


class Gerador:
    def __init__(self, semente):
        self.rnd = random.Random(semente)
        self.lojas = [l for l in LOJAS if l[2] == "LOJA"]
        self.info_loja = {l[0]: l for l in LOJAS}
        self.cat = {p[0]: p[2] for p in PRODUTOS}
        # Preferência regional fixa por loja x produto.
        self.pref = {(l[0], p[0]): math.exp(self.rnd.gauss(0, 0.12)) for l in self.lojas for p in PRODUTOS}
        # Custo unitário de referência 2024.
        self.custo_base = {p[0]: p[6] * RAZAO_CUSTO[p[2]] * (1 + self.rnd.uniform(-0.04, 0.04)) for p in PRODUTOS}
        # Giro relativo: itens abaixo de R$ 20 pesam metade (cupom médio mais alto).
        self.giro = {p[0]: p[7] * (0.5 if p[6] < 20 else 1.0) for p in PRODUTOS}
        # Quantidade média por item de cupom, conforme faixa de preço.
        self.dist_qtd = {}
        for p in PRODUTOS:
            if p[6] < 20:
                self.dist_qtd[p[0]] = ([1, 2, 3], [0.60, 0.30, 0.10])
            elif p[6] < 100:
                self.dist_qtd[p[0]] = ([1, 2, 3], [0.85, 0.13, 0.02])
            else:
                self.dist_qtd[p[0]] = ([1, 2], [0.97, 0.03])
        self.qtd_media = {k: sum(q * w for q, w in zip(*v)) for k, v in self.dist_qtd.items()}
        # Calibra unidades por "peso de giro" para a receita bruta base.
        receita_peso = sum(self.giro[p[0]] * p[6] for p in PRODUTOS if p[0] not in DESCONTINUADOS)
        self.unid_por_peso = RECEITA_BRUTA_BASE / receita_peso
        # Custo médio mensal por produto (realizado): oscila ±1,5% em torno do índice.
        self.custo_mes = {}
        for p in PRODUTOS:
            desvio = 0.0
            for ano, mes in meses_periodo():
                desvio = 0.6 * desvio + self.rnd.gauss(0, 0.006)
                self.custo_mes[(p[0], ano * 100 + mes)] = round(
                    self.custo_base[p[0]] * CUSTO_REAL[ano][p[2]] * (1 + max(-0.015, min(0.015, desvio))), 2)
        self.vendas = []        # itens de cupom
        self.devolucoes = []
        self.despesas = []
        self.orcamento = []
        self.forecast = []
        # Agregados mensais por loja (realizado e orçamento) para despesas e forecast.
        self.agg_real = defaultdict(lambda: defaultdict(float))
        self.agg_orc = defaultdict(lambda: defaultdict(float))

    # ------------------------------------------------------------------ util
    def ruido(self, sigma):
        return math.exp(self.rnd.gauss(0, sigma))

    def poisson(self, lam):
        if lam <= 0:
            return 0
        if lam > 30:
            return max(0, int(round(self.rnd.gauss(lam, math.sqrt(lam)))))
        limite, k, p = math.exp(-lam), 0, 1.0
        while True:
            p *= self.rnd.random()
            if p <= limite:
                return k
            k += 1

    def fracao_dia(self, loja, d, rampa):
        """Fração do potencial de vendas da loja no dia (0 antes da abertura)."""
        abertura = date.fromisoformat(self.info_loja[loja][6])
        if d < abertura:
            return 0.0
        n = rampa.get(loja)
        if not n:
            return 1.0
        meses = (d.year - abertura.year) * 12 + (d.month - abertura.month)
        return min(1.0, RAMPA_INICIAL + (1 - RAMPA_INICIAL) * meses / n)

    def fracao_mes(self, loja, ano, mes, rampa):
        dias = calendar.monthrange(ano, mes)[1]
        return sum(self.fracao_dia(loja, date(ano, mes, d), rampa) for d in range(1, dias + 1)) / dias

    @staticmethod
    def sazonal(cat, mes):
        return SAZONALIDADE[mes - 1] * SAZ_CATEGORIA.get(cat, [1.0] * 12)[mes - 1]

    @staticmethod
    def pesos_dias(ano, mes):
        """Peso de cada dia no mês (soma = nº de dias), com datas comerciais."""
        dias = calendar.monthrange(ano, mes)[1]
        pesos = []
        for dia in range(1, dias + 1):
            d = date(ano, mes, dia)
            w = PESO_DIA_SEMANA[d.weekday()]
            # Dia das Mães: segundo domingo de maio e a semana anterior.
            if mes == 5:
                dom2 = [x for x in range(1, 15) if date(ano, 5, x).weekday() == 6][1]
                if dom2 - 6 <= dia <= dom2:
                    w *= 1.9
            # Black Friday: última sexta de novembro e o fim de semana seguinte.
            if mes == 11:
                bf = max(x for x in range(22, 31) if date(ano, 11, x).weekday() == 4)
                if dia == bf:
                    w *= 3.2
                elif bf < dia <= bf + 2:
                    w *= 1.6
            if mes == 12:
                if 18 <= dia <= 24:
                    w *= 2.0
                elif dia == 25:
                    w = 0.0                       # Natal: lojas fechadas
                elif dia == 31:
                    w *= 0.5
            if mes == 1 and dia == 1:
                w = 0.0                           # Confraternização: lojas fechadas
            pesos.append(w)
        s = sum(pesos)
        return [w * dias / s for w in pesos]

    # ------------------------------------------------------------- vendas
    def gerar_vendas(self):
        num_venda = 0
        id_dev = 0
        for ano, mes in meses_periodo():
            if not realizado(ano, mes):
                continue
            am = ano * 100 + mes
            dias = calendar.monthrange(ano, mes)[1]
            pesos = self.pesos_dias(ano, mes)
            prob_desc = PROB_DESCONTO_REAL[ano] + (PROB_EXTRA_NOV if mes == 11 else 0)
            for loja in self.lojas:
                cod = loja[0]
                desemp = DESEMPENHO_LOJA.get(cod, {}).get(ano, 1.0)
                choque_mes = self.ruido(0.035)
                # Linhas esperadas por produto no mês (antes do peso do dia).
                base = []
                for p in PRODUTOS:
                    if p[0] in DESCONTINUADOS and am > DESCONTINUADOS[p[0]]:
                        continue
                    unid = (self.giro[p[0]] * self.unid_por_peso * loja[9] * self.pref[(cod, p[0])]
                            * self.sazonal(p[2], mes) * VOLUME_REAL[ano][p[2]] * desemp * choque_mes)
                    base.append((p, unid / self.qtd_media[p[0]] / dias))
                for dia in range(1, dias + 1):
                    d = date(ano, mes, dia)
                    frac = self.fracao_dia(cod, d, RAMPA_REAL)
                    if frac == 0 or pesos[dia - 1] == 0:
                        continue
                    choque_dia = self.ruido(0.10)
                    linhas = []
                    for p, lam in base:
                        n = self.poisson(lam * pesos[dia - 1] * frac * choque_dia)
                        linhas.extend([p] * n)
                    self.rnd.shuffle(linhas)
                    i = 0
                    while i < len(linhas):
                        # Itens por cupom: 1 a 6, média ~1,7.
                        tam = min(len(linhas) - i, 1 + min(5, int(self.rnd.expovariate(1 / 0.75))))
                        num_venda += 1
                        vistos = {}
                        n_item = 0
                        for p in linhas[i:i + tam]:
                            qtd = self.rnd.choices(*self.dist_qtd[p[0]])[0]
                            if p[0] in vistos:                 # mesmo produto no cupom: soma no item
                                vistos[p[0]][5] += qtd
                                continue
                            n_item += 1
                            item = [num_venda, n_item, d, cod, p[0], qtd]
                            vistos[p[0]] = item
                        for item in vistos.values():
                            pcod, qtd = item[4], item[5]
                            p_unit = preco_tabela(PRODUTOS_IDX[pcod][6], ano)
                            bruto = round(qtd * p_unit, 2)
                            pct = self.rnd.choice(PERCENTUAIS_DESCONTO) if self.rnd.random() < prob_desc else 0.0
                            desc = round(bruto * pct, 2)
                            c_unit = self.custo_mes[(pcod, am)]
                            custo = round(qtd * c_unit, 2)
                            linha = [item[0], item[1], d.isoformat(), cod, pcod, qtd, p_unit, bruto, desc,
                                     round(bruto - desc, 2), c_unit, custo]
                            self.vendas.append(linha)
                            agg = self.agg_real[(am, cod)]
                            agg["bruta"] += bruto
                            agg["desc"] += desc
                            agg["cmv"] += custo
                            agg["qtd"] += qtd
                            # Devolução do item inteiro em até 30 dias.
                            if self.rnd.random() < DEVOLUCAO_REAL.get(self.cat[pcod], DEVOLUCAO_REAL["_"]):
                                d_dev = d + timedelta(days=self.rnd.randint(1, 30))
                                if d_dev <= DATA_CORTE_REALIZADO:
                                    id_dev += 1
                                    self.devolucoes.append([id_dev, d_dev.isoformat(), item[0], item[1], cod, pcod,
                                                            qtd, round(bruto - desc, 2), custo])
                                    am_dev = d_dev.year * 100 + d_dev.month
                                    self.agg_real[(am_dev, cod)]["dev"] += round(bruto - desc, 2)
                                    self.agg_real[(am_dev, cod)]["cmv_dev"] += custo
                        i += tam

    # --------------------------------------------------------- orçamento
    def orcamento_vendas(self):
        """Valores esperados (sem ruído) por loja, mês e conta de vendas."""
        for ano, mes in meses_periodo():
            am = ano * 100 + mes
            for loja in self.lojas:
                cod = loja[0]
                frac = self.fracao_mes(cod, ano, mes, RAMPA_ORC)
                if frac == 0:
                    continue
                bruta = desc = dev = cmv = 0.0
                for p in PRODUTOS:
                    if p[0] in DESCONTINUADOS and am > DESCONTINUADOS[p[0]]:
                        continue
                    cat = p[2]
                    unid = (self.giro[p[0]] * self.unid_por_peso * loja[9] * self.pref[(cod, p[0])]
                            * self.sazonal(cat, mes) * VOLUME_ORC[ano][cat] * frac)
                    b = unid * p[6] * PRECO_ORC[ano]
                    tx_desc = DESCONTO_ORC[ano] + (DESCONTO_EXTRA_NOV_ORC if mes == 11 else 0)
                    tx_dev = DEVOLUCAO_ORC.get(cat, DEVOLUCAO_ORC["_"])
                    bruta += b
                    desc += b * tx_desc
                    dev += b * (1 - tx_desc) * tx_dev
                    cmv += unid * self.custo_base[p[0]] * CUSTO_ORC[ano][cat] * (1 - tx_dev)
                agg = self.agg_orc[(am, cod)]
                agg.update(bruta=bruta, desc=desc, dev=dev, cmv=cmv)

    # ----------------------------------------------------------- despesas
    def despesas_loja(self, loja, ano, mes, agg, real):
        """{conta: valor} de uma loja num mês, a partir das vendas do mês."""
        am = ano * 100 + mes
        cod, area, aluguel_m2, fator = loja[0], loja[8], loja[10], loja[9]
        r = self.ruido if real else (lambda s: 1.0)
        venda_liq = agg["bruta"] - agg["desc"] - agg["dev"]
        rl = venda_liq * (1 - ALIQ_IMPOSTO_VENDA)
        frac = self.fracao_mes(cod, ano, mes, RAMPA_REAL if real else RAMPA_ORC)
        aberto = 1.0 if frac > 0 else 0.0
        abertura = date.fromisoformat(loja[6])
        if (abertura.year, abertura.month) == (ano, mes):
            aberto = (calendar.monthrange(ano, mes)[1] - abertura.day + 1) / calendar.monthrange(ano, mes)[1]
            aberto = max(aberto, 0.5)            # equipe contratada antes da inauguração
        quadro = round(1 + 2 * fator)
        f_sal = fator_salarial(DISSIDIO_REAL if real else DISSIDIO_ORC, ano, mes)
        temporarios = 1.15 if mes in (11, 12) else 1.0
        manut = area * 4.5 * INFLACAO[ano] * r(0.20)
        if real and self.rnd.random() < 0.06:
            manut *= 3.0                          # manutenção corretiva pontual
        d = {
            "3.2.01": venda_liq * ALIQ_IMPOSTO_VENDA,
            "5.1.01": quadro * 3150 * f_sal * temporarios * aberto * r(0.02),
            "5.1.02": quadro * 720 * f_sal * aberto * r(0.02),
            "5.1.03": rl * 0.015 * r(0.03),
            "5.2.01": max(area * aluguel_m2 * ALUGUEL_REAJ[ano] * aberto, rl * 0.065) * r(0.01),
            "5.2.02": area * 17 * (1.10 if mes in (1, 2, 3, 12) else 1.0) * aberto
                      * (ENERGIA_EXTRA_REAL.get(am, 1.0) if real else 1.0) * INFLACAO[ano] * r(0.06),
            "5.2.03": 600 * INFLACAO[ano] * aberto * r(0.05),
            "5.2.04": manut * aberto,
            "5.3.01": rl * 0.008 * r(0.15),
            "5.3.02": venda_liq * 0.023 * r(0.02),
            "5.3.03": rl * 0.006 * r(0.08),
            "5.4.02": area * 11 * INFLACAO[ano] * aberto * r(0.04),
            "5.4.04": 450 * INFLACAO[ano] * aberto * r(0.12),
            "5.5.01": rl * 0.012 * r(0.06),
            "5.6.01": area * 32 * aberto,
        }
        return {k: arred(v) for k, v in d.items() if v > 0}

    def despesas_corp(self, ano, mes, rl_total, real):
        """{(departamento, conta): valor} da CORP num mês."""
        r = self.ruido if real else (lambda s: 1.0)
        f_sal = fator_salarial(DISSIDIO_REAL if real else DISSIDIO_ORC, ano, mes)
        fi = INFLACAO[ano]
        folha = {"DIRETORIA": 17000, "FINANCEIRO": 8500, "GENTE_GESTAO": 4700, "TECNOLOGIA": 7200,
                 "MARKETING": 6000, "COMERCIAL": 8500, "LOGISTICA": 11000}
        d = {}
        for dep, v in folha.items():
            d[(dep, "5.1.01")] = v * f_sal * r(0.015)
            d[(dep, "5.1.02")] = v * 0.20 * f_sal * r(0.02)
        reforco = {5: 1.35, 11: 1.45, 12: 1.30}.get(mes, 1.0)
        mkt = 0.015 if not real or ano < 2026 else 0.018           # 2026: mais mídia para sustentar volume
        d[("MARKETING", "5.3.01")] = rl_total * mkt * reforco * r(0.08)
        tec = 12000 * fi
        if ano == 2026:                                           # projeto de novo ERP
            tec += 8000 if not real else (8000 * (1.45 if mes >= 3 else 1.0))
        d[("TECNOLOGIA", "5.4.01")] = tec * r(0.05)
        d[("TECNOLOGIA", "5.6.01")] = 4500 + (1800 if ano == 2026 and mes >= 7 else 0)
        d[("LOGISTICA", "5.5.01")] = rl_total * 0.008 * r(0.05)
        d[("LOGISTICA", "5.2.01")] = 10000 * ALUGUEL_REAJ[ano] * r(0.01)
        d[("LOGISTICA", "5.6.01")] = 3200
        d[("DIRETORIA", "5.2.01")] = 7000 * ALUGUEL_REAJ[ano] * r(0.01)
        d[("DIRETORIA", "5.2.02")] = 1000 * fi * r(0.06)
        d[("DIRETORIA", "5.2.03")] = 650 * fi * r(0.05)
        d[("DIRETORIA", "5.4.02")] = 6000 * fi * r(0.12)           # auditoria, jurídico, consultorias
        d[("DIRETORIA", "5.4.03")] = 1600 * fi * r(0.20)
        d[("DIRETORIA", "5.4.04")] = 1300 * fi * r(0.10)
        d[("COMERCIAL", "5.4.03")] = 2000 * fi * r(0.18)
        d[("GENTE_GESTAO", "5.4.02")] = 2300 * fi * r(0.15)         # recrutamento e treinamento
        d[("FINANCEIRO", "5.4.02")] = 2100 * fi * r(0.08)
        d[("FINANCEIRO", "6.1.01")] = rl_total * 0.0035 * r(0.10)   # aplicações financeiras
        d[("FINANCEIRO", "6.1.02")] = rl_total * (0.0120 if not real or ano < 2026 else 0.0145) * r(0.06)  # antecipação de recebíveis
        return {k: arred(v) for k, v in d.items()}

    def gerar_despesas_e_orcamento(self):
        id_lanc = 0
        for ano, mes in meses_periodo():
            am = ano * 100 + mes
            for cenario in (["REAL"] if realizado(ano, mes) else []) + ["ORC"]:
                real = cenario == "REAL"
                aggs = self.agg_real if real else self.agg_orc
                linhas = []   # (loja, dep, conta, valor)
                rl_total = lucro = 0.0
                for loja in self.lojas:
                    agg = aggs.get((am, loja[0]))
                    if not agg or agg["bruta"] == 0:
                        continue
                    venda_liq = agg["bruta"] - agg["desc"] - agg["dev"]
                    cmv = agg["cmv"] - agg.get("cmv_dev", 0.0)
                    rl = venda_liq * (1 - ALIQ_IMPOSTO_VENDA)
                    rl_total += rl
                    lucro += rl - cmv
                    if not real:
                        linhas += [(loja[0], "OPERACOES_LOJA", "3.1.01", arred(agg["bruta"])),
                                   (loja[0], "OPERACOES_LOJA", "3.2.02", arred(agg["desc"])),
                                   (loja[0], "OPERACOES_LOJA", "3.2.03", arred(agg["dev"])),
                                   (loja[0], "OPERACOES_LOJA", "4.1.01", arred(cmv))]
                    for conta, v in self.despesas_loja(loja, ano, mes, agg, real).items():
                        linhas.append((loja[0], "OPERACOES_LOJA", conta, v))
                        if conta != "3.2.01":
                            lucro -= v
                for (dep, conta), v in self.despesas_corp(ano, mes, rl_total, real).items():
                    linhas.append(("CORP", dep, conta, v))
                    lucro += v if conta == "6.1.01" else -v
                if lucro > 0:   # IRPJ/CSLL do mês sobre o lucro antes do IR (sem compensação de prejuízo)
                    linhas.append(("CORP", "FINANCEIRO", "7.1.01", arred(lucro * ALIQ_IR_CSLL)))
                for loja, dep, conta, v in linhas:
                    if real:
                        id_lanc += 1
                        self.despesas.append([id_lanc, primeiro_dia(am), am, loja, dep, conta, v])
                    else:
                        self.orcamento.append([CENARIO_ORC, primeiro_dia(am), am, loja, dep, conta, v])

    # ----------------------------------------------------------- forecast
    def gerar_forecast(self):
        """Forecast 9+3 feito na data de corte para out-dez/2026.

        Vendas: orçamento x (realizado / orçado de jan-set/2026) por loja e conta.
        Despesas fixas: média realizada de jul-set ajustada pela sazonalidade do
        orçamento. Despesas variáveis: % realizado de jul-set x receita do forecast.
        Marketing nacional segue a regra das fixas para manter as campanhas de nov/dez.
        """
        orc = defaultdict(float)
        for c, _, am, loja, dep, conta, v in self.orcamento:
            orc[(am, loja, dep, conta)] += v
        # Realizado de 2026 no mesmo formato de contas.
        real = defaultdict(float)
        for am_l, agg in self.agg_real.items():
            am, loja = am_l
            if am // 100 == 2026:
                real[(am, loja, "OPERACOES_LOJA", "3.1.01")] += agg["bruta"]
                real[(am, loja, "OPERACOES_LOJA", "3.2.02")] += agg["desc"]
                real[(am, loja, "OPERACOES_LOJA", "3.2.03")] += agg["dev"]
                real[(am, loja, "OPERACOES_LOJA", "4.1.01")] += agg["cmv"] - agg.get("cmv_dev", 0.0)
        for _, _, am, loja, dep, conta, v in self.despesas:
            if am // 100 == 2026:
                real[(am, loja, dep, conta)] += v

        def soma(base, loja, dep, conta, meses):
            return sum(base.get((am, loja, dep, conta), 0.0) for am in meses)

        ytd = [202600 + m for m in range(1, 10)]
        q3 = [202607, 202608, 202609]
        chaves = sorted({k[1:] for k in orc if k[0] >= 202610})
        fct = {}
        # 1) Vendas por loja.
        rl_loja = defaultdict(float)
        for loja, dep, conta in chaves:
            if conta not in ("3.1.01", "3.2.02", "3.2.03", "4.1.01"):
                continue
            b_real = soma(real, loja, dep, "3.1.01", ytd)
            b_orc = soma(orc, loja, dep, "3.1.01", ytd)
            for am in (202610, 202611, 202612):
                bruta_orc = orc[(am, loja, dep, "3.1.01")]
                bruta = bruta_orc * (b_real / b_orc if b_orc else 1.0)
                if conta == "3.1.01":
                    v = bruta
                else:
                    taxa_real = soma(real, loja, dep, conta, ytd) / b_real if b_real else 0.0
                    taxa_orc_mes = orc[(am, loja, dep, conta)] / bruta_orc if bruta_orc else 0.0
                    taxa_orc_ytd = soma(orc, loja, dep, conta, ytd) / b_orc if b_orc else 0.0
                    v = bruta * (taxa_real + (taxa_orc_mes - taxa_orc_ytd))   # mantém o efeito Black Friday
                fct[(am, loja, dep, conta)] = v
        for am in (202610, 202611, 202612):
            for loja in {k[1] for k in fct}:
                vl = sum(fct.get((am, loja, "OPERACOES_LOJA", c), 0.0) * s
                         for c, s in (("3.1.01", 1), ("3.2.02", -1), ("3.2.03", -1)))
                rl_loja[(am, loja)] = vl * (1 - ALIQ_IMPOSTO_VENDA)
        rl_total = defaultdict(float)
        for (am, loja), v in rl_loja.items():
            rl_total[am] += v
        rl_real_q3 = defaultdict(float)
        for am in q3:
            for loja in [l[0] for l in self.lojas]:
                agg = self.agg_real.get((am, loja))
                if agg:
                    v = (agg["bruta"] - agg["desc"] - agg["dev"]) * (1 - ALIQ_IMPOSTO_VENDA)
                    rl_real_q3[loja] += v
                    rl_real_q3["CORP"] += v
        # 2) Despesas.
        for loja, dep, conta in chaves:
            if conta in ("3.1.01", "3.2.02", "3.2.03", "4.1.01", "7.1.01"):
                continue
            for am in (202610, 202611, 202612):
                if conta == "3.2.01":
                    vl = rl_loja[(am, loja)] / (1 - ALIQ_IMPOSTO_VENDA)
                    v = vl * ALIQ_IMPOSTO_VENDA
                elif conta in CONTAS_VARIAVEIS and not (loja == "CORP" and conta == "5.3.01"):
                    rl = rl_total[am] if loja == "CORP" else rl_loja[(am, loja)]
                    pct_real = soma(real, loja, dep, conta, q3) / rl_real_q3[loja] if rl_real_q3[loja] else 0.0
                    v = rl * pct_real
                else:
                    media_q3 = soma(real, loja, dep, conta, q3) / 3
                    o_q3 = soma(orc, loja, dep, conta, q3) / 3
                    v = media_q3 * (orc[(am, loja, dep, conta)] / o_q3) if o_q3 else orc[(am, loja, dep, conta)]
                fct[(am, loja, dep, conta)] = v
        # 3) IRPJ/CSLL.
        for am in (202610, 202611, 202612):
            lucro = 0.0
            for (m, loja, dep, conta), v in fct.items():
                if m != am:
                    continue
                if conta == "3.1.01":
                    lucro += v * (1 - ALIQ_IMPOSTO_VENDA)
                elif conta in ("3.2.02", "3.2.03"):
                    lucro -= v * (1 - ALIQ_IMPOSTO_VENDA)
                elif conta == "6.1.01":
                    lucro += v
                elif conta != "3.2.01":
                    lucro -= v
            if lucro > 0:
                fct[(am, "CORP", "FINANCEIRO", "7.1.01")] = lucro * ALIQ_IR_CSLL
        for (am, loja, dep, conta), v in fct.items():
            if v > 0:
                self.forecast.append([CENARIO_FCT, primeiro_dia(am), am, loja, dep, conta, arred(v)])


PRODUTOS_IDX = {p[0]: p for p in PRODUTOS}


# =============================================================================
# 3. SAÍDA
# =============================================================================
def escrever(pasta, nome, cabecalho, linhas):
    caminho = os.path.join(pasta, nome)
    n = 0
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(cabecalho)
        for l in linhas:
            w.writerow(["{:.2f}".format(x) if isinstance(x, float) else x for x in l])
            n += 1
    print(f"  {nome:<32} {n:>10,} registros".replace(",", "."))
    return n


def calendario():
    d = date(ANO_INICIO, 1, 1)
    while d <= date(ANO_FIM, 12, 31):
        tri = (d.month - 1) // 3 + 1
        yield [d.isoformat(), d.year * 10000 + d.month * 100 + d.day, d.year, d.month, MESES_PT[d.month - 1],
               f"{MESES_ABREV[d.month - 1]}/{str(d.year)[2:]}", d.year * 100 + d.month, tri, f"T{tri}/{d.year}",
               d.day, d.isoweekday(), DIAS_PT[d.weekday()], 1 if d.weekday() >= 5 else 0,
               date(d.year, d.month, 1).isoformat(),
               date(d.year, d.month, calendar.monthrange(d.year, d.month)[1]).isoformat(),
               1 if d <= DATA_CORTE_REALIZADO else 0]
        d += timedelta(days=1)


def main():
    ap = argparse.ArgumentParser(description="Gera os CSVs fictícios da People Beauty.")
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--saida", default=os.path.join(raiz, "csv"))
    ap.add_argument("--semente", type=int, default=SEMENTE_PADRAO)
    args = ap.parse_args()
    os.makedirs(args.saida, exist_ok=True)

    print("Gerando vendas...")
    g = Gerador(args.semente)
    g.gerar_vendas()
    print("Gerando orçamento, despesas e forecast...")
    g.orcamento_vendas()
    g.gerar_despesas_e_orcamento()
    g.gerar_forecast()

    print(f"Gravando em {args.saida}")
    marcas = sorted({p[4] for p in PRODUTOS})
    escrever(args.saida, "dim_calendario.csv",
             ["Data", "DataKey", "Ano", "MesNumero", "MesNome", "MesAnoAbrev", "AnoMes", "Trimestre",
              "TrimestreAno", "Dia", "DiaSemanaNumero", "DiaSemanaNome", "FimDeSemana", "InicioMes", "FimMes",
              "PeriodoRealizado"], calendario())
    escrever(args.saida, "dim_loja.csv",
             ["CodigoLoja", "NomeLoja", "TipoUnidade", "Regiao", "UF", "Cidade", "DataAbertura", "Formato",
              "AreaVendaM2"],
             [list(l[:8]) + [l[8] if l[2] == "LOJA" else ""] for l in LOJAS])
    escrever(args.saida, "dim_departamento.csv", ["CodigoDepartamento", "NomeDepartamento", "TipoUnidade"],
             [[c, n, "LOJA" if c == "OPERACOES_LOJA" else "CORPORATIVA"] for c, n in DEPARTAMENTOS])
    escrever(args.saida, "dim_cenario.csv",
             ["CodigoCenario", "NomeCenario", "TipoCenario", "StatusCenario", "Descricao"], CENARIOS)
    escrever(args.saida, "dim_plano_contas.csv",
             ["CodigoConta", "NomeConta", "GrupoDRE", "NaturezaConta", "SinalDRE", "IndicadorDespesa",
              "CodigoContaPai", "NivelHierarquia", "OrdemExibicao", "ParticipaReceitaLiquida", "ParticipaCMV",
              "ParticipaResultadoOperacional", "ParticipaResultadoLiquido", "ContaAnalitica", "OrigemRealizado"],
             [list(c) + [0 if any(o[6] == c[0] for o in PLANO_CONTAS) else 1,
                         "" if any(o[6] == c[0] for o in PLANO_CONTAS) else
                         ("fato_despesas" if c[5] else ("fato_devolucoes" if c[0] == "3.2.03" else "fato_vendas"))]
              for c in PLANO_CONTAS])
    escrever(args.saida, "dim_categoria.csv", ["CodigoCategoria", "NomeCategoria", "Descricao"],
             [[CODIGO_CATEGORIA[c], c, DESCRICAO_CATEGORIA[c]] for c in CATEGORIAS])
    escrever(args.saida, "dim_marca.csv", ["CodigoMarca", "NomeMarca"], [[slug(m), m] for m in marcas])
    escrever(args.saida, "dim_produto.csv",
             ["CodigoProduto", "NomeProduto", "CodigoCategoria", "Subcategoria", "CodigoMarca", "StatusProduto",
              "DataDescontinuacao", "PrecoListaReferencia2024", "CustoReferencia2024"],
             [[p[0], p[1], CODIGO_CATEGORIA[p[2]], p[3], slug(p[4]), p[5],
               date(DESCONTINUADOS[p[0]] // 100, DESCONTINUADOS[p[0]] % 100,
                    calendar.monthrange(DESCONTINUADOS[p[0]] // 100, DESCONTINUADOS[p[0]] % 100)[1]).isoformat()
               if p[0] in DESCONTINUADOS else "", p[6], arred(g.custo_base[p[0]])] for p in PRODUTOS])
    escrever(args.saida, "parametros.csv", ["CodigoParametro", "Valor", "Descricao"],
             [["DATA_CORTE_REALIZADO", DATA_CORTE_REALIZADO.isoformat(),
               "Último dia com realizado. Out-dez/2026: somente orçamento e forecast 9+3."],
              ["SEMENTE_GERADOR", str(args.semente), "Semente aleatória usada na geração dos dados."],
              ["ALIQUOTA_IMPOSTO_VENDA", str(ALIQ_IMPOSTO_VENDA),
               "Alíquota efetiva sobre (receita bruta - descontos - devoluções), conta 3.2.01."],
              ["ALIQUOTA_IRPJ_CSLL", str(ALIQ_IR_CSLL), "Alíquota de IRPJ + CSLL sobre o lucro mensal positivo, conta 7.1.01."]])
    cab_vendas = ["NumeroVenda", "NumeroItem", "DataVenda", "CodigoLoja", "CodigoProduto", "Quantidade",
                  "PrecoUnitario", "ValorBruto", "ValorDesconto", "ValorLiquido", "CustoUnitario", "CustoTotal"]
    for ano in range(ANO_INICIO, ANO_FIM + 1):
        linhas = [v for v in g.vendas if v[2].startswith(str(ano))]
        if linhas:
            escrever(args.saida, f"fato_vendas_{ano}.csv", cab_vendas, linhas)
    escrever(args.saida, "fato_devolucoes.csv",
             ["IdDevolucao", "DataDevolucao", "NumeroVenda", "NumeroItem", "CodigoLoja", "CodigoProduto",
              "Quantidade", "ValorDevolvido", "CustoDevolvido"], g.devolucoes)
    cab_plan = ["CodigoCenario", "DataCompetencia", "AnoMes", "CodigoLoja", "CodigoDepartamento", "CodigoConta", "Valor"]
    escrever(args.saida, "fato_despesas.csv",
             ["IdLancamento", "DataCompetencia", "AnoMes", "CodigoLoja", "CodigoDepartamento", "CodigoConta", "Valor"],
             g.despesas)
    escrever(args.saida, "fato_orcamento.csv", cab_plan, sorted(g.orcamento, key=lambda r: (r[2], r[3], r[4], r[5])))
    escrever(args.saida, "fato_forecast.csv", cab_plan, sorted(g.forecast, key=lambda r: (r[2], r[3], r[4], r[5])))


if __name__ == "__main__":
    main()
