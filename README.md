# People Beauty — FP&A Analytics

Projeto de portfólio de **FP&A (Financial Planning & Analysis)** e **Business Intelligence** aplicado a uma rede fictícia de varejo de beleza e cuidados pessoais.

> **Status atual:** estrutura inicial do repositório. O banco de dados, as análises SQL, o modelo Power BI e os resultados **ainda não foram desenvolvidos**. Tudo o que aparece abaixo como indicador, pergunta ou etapa é **planejamento**, não resultado.

> **Aviso:** a People Beauty é uma empresa fictícia. Todos os dados financeiros e operacionais utilizados neste projeto serão fictícios, criados exclusivamente para fins de estudo e demonstração. Qualquer semelhança com empresas reais é coincidência.

---

## 1. Apresentação

A **People Beauty** é uma rede de varejo de beleza e cuidados pessoais com **24 lojas** e **1 unidade corporativa** (CORP), responsável pelas despesas administrativas centrais.

Este projeto simula o trabalho de uma área de FP&A: consolidar orçamento e realizado, explicar desvios, medir a rentabilidade das lojas, projetar o fechamento do ano e transformar números em recomendações para a diretoria.

## 2. Problema de negócio

A diretoria precisa responder, com uma única fonte confiável de dados:

- O resultado do ano está dentro do orçamento? Onde estão os maiores desvios?
- Os desvios vêm de volume de vendas, de preço/mix, de custo da mercadoria ou de despesas?
- Quais lojas geram valor e quais consomem resultado?
- Qual é a expectativa de fechamento do ano, considerando o realizado até a data de corte?
- Que ações devem ser priorizadas para proteger a margem e o resultado operacional?

## 3. Objetivos e perguntas financeiras

**Objetivos**

1. Estruturar uma base financeira em SQL Server com orçamento, realizado e forecast.
2. Construir uma DRE gerencial por loja, região e consolidado.
3. Analisar orçamento versus realizado com abertura dos desvios.
4. Avaliar rentabilidade por loja e eficiência das despesas operacionais.
5. Elaborar um forecast financeiro para o fechamento do exercício.
6. Comunicar conclusões em um dashboard Power BI e em recomendações executivas.

**Perguntas a responder**

| Tema | Pergunta |
|---|---|
| Receita | Como a receita líquida evolui por mês, loja e categoria? Onde o realizado fica acima ou abaixo do orçamento? |
| CMV e margem | A margem bruta está sendo preservada? Quais lojas ou categorias pressionam o CMV? |
| Despesas | Quais grupos de despesa operacional estão acima do orçado? O peso da unidade corporativa é adequado? |
| Rentabilidade | Quais lojas têm melhor e pior margem de contribuição e resultado operacional? |
| Forecast | Qual é o resultado esperado para o ano e qual o gap em relação ao orçamento? |
| Decisão | Quais ações concretas devem ser recomendadas à diretoria? |

## 4. Indicadores planejados

- Receita bruta, deduções e receita líquida
- CMV e margem bruta (R$ e %)
- Despesas operacionais por grupo e % da receita líquida
- Margem de contribuição por loja
- EBITDA gerencial e resultado operacional
- Desvio orçado x realizado (R$ e %)
- Forecast x orçamento (gap de fechamento)
- Crescimento mês contra mês e ano contra ano
- Ranking de rentabilidade por loja

As definições e fórmulas serão documentadas em `01_Documentacao/` à medida que forem construídas.

## 5. Tecnologias previstas

| Ferramenta | Uso previsto |
|---|---|
| SQL Server | Banco de dados, tabelas, chaves, carga e consultas |
| T-SQL | Consultas analíticas e views |
| Power BI | Modelo de dados, medidas DAX e dashboard |
| Excel | Apoio a conferências e premissas, se necessário |
| Git e GitHub | Versionamento e publicação do portfólio |
| Windows CMD | Organização inicial do ambiente (`iniciar_projeto.cmd`) |

## 6. Etapas do desenvolvimento

| # | Etapa | Entregável | Status |
|---|---|---|---|
| 0 | Estrutura do repositório | Pastas, README, configuração e CMD | Concluída |
| 1 | Documentação e premissas | Escopo, dicionário de dados, plano de contas gerencial | Planejada |
| 2 | Modelagem no SQL Server | Banco, tabelas, chaves e relacionamentos | Planejada |
| 3 | Dados fictícios e carga | Base fictícia e rotina de carga | Planejada |
| 4 | Análises SQL | Consultas e views de orçamento x realizado, DRE e rentabilidade | Planejada |
| 5 | Power BI | Modelo, medidas DAX e dashboard | Planejada |
| 6 | Resultados e recomendações | Conclusões, forecast e recomendações executivas | Planejada |

O status desta tabela será atualizado somente quando cada etapa estiver efetivamente concluída.

## 7. Estrutura de pastas

```
PeopleBeauty_FPA_Analytics_BI/
├── README.md               Visão geral do projeto (este arquivo)
├── projeto_config.json     Parâmetros e escopo do projeto
├── .gitignore              Arquivos que não devem ser versionados
├── iniciar_projeto.cmd     Organiza as pastas do ambiente no Windows
├── 01_Documentacao/        Escopo, premissas, dicionário de dados e decisões
├── 02_SQL_Server/          Scripts de criação do banco, tabelas e carga
├── 03_Dados/               Dados fictícios de origem (orientações)
├── 04_Analises_SQL/        Consultas analíticas e views
├── 05_Power_BI/            Modelo, medidas DAX e dashboard
└── 06_Resultados/          Conclusões, prints e recomendações executivas
```

## 8. Como começar

1. Clone o repositório.
2. No Windows, dê um duplo clique em `iniciar_projeto.cmd` ou execute-o pelo Prompt de Comando a partir da pasta do projeto.
3. O script apenas confere e cria as pastas que estiverem faltando. Ele não executa SQL, não gera dados e não instala ferramentas.

## 9. Planejamento x resultados

Para manter a transparência do portfólio:

- **Planejamento:** tudo o que está descrito nas seções 3, 4 e 6 deste README.
- **Resultados efetivos:** somente o que estiver publicado em `06_Resultados/`, com data e etapa correspondente.

No momento, **não há resultados publicados**.

## 10. Autoria

Projeto desenvolvido por **Humberto** ([@humberto-hms](https://github.com/humberto-hms)). O banco de dados, as consultas, as views, as medidas DAX e o dashboard serão construídos manualmente pelo autor.
