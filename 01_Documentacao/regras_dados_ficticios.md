# Regras de geração dos dados fictícios

Este documento explica **como** os CSVs de `03_Dados/csv/` foram criados. Os parâmetros estão no início de [`gerar_dados.py`](../03_Dados/gerador/gerar_dados.py) e podem ser alterados para gerar uma nova versão.

Os padrões abaixo foram colocados de propósito para que as análises tenham o que explicar. Os números finais (desvios, margens, ranking de lojas) **não** estão calculados aqui: isso faz parte das etapas de SQL e Power BI.

## 1. Período e separação dos cenários

| Cenário | Arquivos | Meses |
|---|---|---|
| Realizado | `fato_vendas_AAAA`, `fato_devolucoes`, `fato_despesas` | jan/2024 a set/2026 |
| Orçamento aprovado | `fato_orcamento` | jan/2024 a dez/2026 |
| Forecast 9+3 | `fato_forecast` | out/2026 a dez/2026 |

- Data de corte do realizado: **30/09/2026** (último mês fechado; os dados foram gerados em 23/10/2026, com outubro ainda aberto).
- Nenhum fato de realizado tem data depois do corte. Devoluções que cairiam depois do corte não foram registradas.
- O forecast foi "feito" na data de corte: não usa nenhuma informação de out-dez/2026.

## 2. Lojas e unidade corporativa

- 24 lojas físicas (`L001`–`L024`) e a unidade `CORP`, sem vendas.
- Cada loja tem um fator de potencial de vendas (0,70 a 1,45) que define área, quadro de pessoal e volume.
- Lojas novas: **L023 Fortaleza** abre em 10/03/2025 e **L024 Campo Grande** em 18/08/2025. Começam com 55% do potencial e amadurecem linearmente. O orçamento previu maturação em 9 meses (L023) e 10 meses (L024); no realizado, L023 leva 16 meses e L024 só 8.
- Despesas de loja usam o departamento `OPERACOES_LOJA`. Despesas da `CORP` ficam nas áreas corporativas e **não são rateadas**.

## 3. Vendas (item de cupom)

1. Para cada loja, produto e dia, o volume esperado = giro do produto × potencial da loja × preferência regional (fixa, ±12%) × sazonalidade do mês e da categoria × índice de volume do ano × desempenho da loja × maturação.
2. O número de itens do dia segue uma distribuição de Poisson sobre esse volume, com choques aleatórios de mês (±3,5%) e de dia (±10%).
3. Os itens do dia são embaralhados e agrupados em cupons de 1 a 6 itens (média ~1,35). Se o mesmo produto cair duas vezes no cupom, as quantidades são somadas no mesmo item.
4. Quantidade por item: 1 a 3 para itens abaixo de R$ 20, normalmente 1 para eletro.
5. **Preço:** tabela anual com reajuste em janeiro (+4,5% em 2025, +5,0% em 2026), arredondada para final ,90.
6. **Desconto:** cada item tem uma chance de estar em promoção (25% em 2024, 26% em 2025, 32% em 2026, +17,5 p.p. em novembro pela Black Friday), com 10% a 30% de desconto.
7. **Custo:** custo médio mensal por produto, com reajuste anual (+4,5% em 2025; +5,2% em 2026, e +9,5% para eletro em 2026 pelo câmbio) e oscilação de até ±1,5% no mês.
8. **Dias especiais:** semana do Dia das Mães, Black Friday (sexta e fim de semana), semana do Natal; lojas fechadas em 01/01 e 25/12. Sábado é o dia mais forte da semana.
9. Produtos inativos: `PB-MAQ-0014` sai de linha em dez/2024 e `PB-CAB-0016` em jun/2025.

## 4. Devoluções

- 1,1% dos itens (2,5% em eletro beleza) são devolvidos de 1 a 30 dias depois da venda, sempre o item inteiro.
- O valor estornado é o valor líquido do item; o custo volta ao estoque e reduz o CMV no mês da devolução.

## 5. Despesas realizadas (competência mensal)

| Conta | Lojas | CORP |
|---|---|---|
| 3.2.01 Impostos sobre vendas | 17% de (bruto − descontos − devoluções) | — |
| 5.1.01 Salários e encargos | quadro por porte; dissídio em maio; +15% em nov/dez (temporários) | folha por área |
| 5.1.02 Benefícios | por pessoa | 20% da folha |
| 5.1.03 Comissões | 1,5% da receita líquida | — |
| 5.2.01 Aluguel e condomínio | maior entre valor fixo por m² e 6,5% da receita (reajuste em janeiro) | escritório e CD |
| 5.2.02 Energia | por m², mais alta no verão | escritório |
| 5.2.03 / 5.2.04 | valor fixo / manutenção por m² com eventos corretivos pontuais | escritório |
| 5.3.01 Marketing | 0,8% da receita (local) | 1,5% da receita da rede (nacional), reforço em mai/nov/dez |
| 5.3.02 Taxas de cartão | 2,3% da venda líquida | — |
| 5.3.03 Embalagens | 0,6% da receita | — |
| 5.4.01 Tecnologia | — | licenças + projeto de ERP em 2026 |
| 5.4.02 / 5.4.03 / 5.4.04 | serviços (limpeza, segurança), despesas gerais | auditoria, jurídico, recrutamento, viagens |
| 5.5.01 Fretes | 1,2% da receita | 0,8% da receita da rede (CD) |
| 5.6.01 Depreciação | por m² | TI e CD |
| 6.1.01 / 6.1.02 | — | receitas de aplicações / antecipação de recebíveis |
| 7.1.01 IRPJ e CSLL | — | 34% do lucro do mês, quando positivo (sem compensação de prejuízo) |

Receita líquida (para os percentuais) = (bruto − descontos − devoluções) × (1 − 17%).

## 6. Orçamento

- Feito com as mesmas fórmulas do realizado, **sem ruído aleatório** e com as premissas que a empresa tinha antes de cada ano.
- Valores mensais por unidade, departamento e conta (inclusive receita, descontos, devoluções e CMV).
- Premissas de 2026 mais otimistas que o realizado:
  - volume +7,5% a +9% em cabelos, maquiagem e eletro (realizado bem menor; maquiagem e eletro caem);
  - reajuste de preço de 6,0% (realizado 5,0%);
  - desconto médio de 5% (realizado sobe com as promoções);
  - custo +5,0% para todas as categorias (eletro sobe 9,5%);
  - dissídio de 5,0% (realizado 6,8%);
  - energia sem bandeira tarifária (realizado com bandeira vermelha de jun a set/2026);
  - projeto de ERP e marketing nacional abaixo do realizado; despesa financeira de 1,20% da receita (realizado 1,45%).
- Lojas com desempenho diferente do orçado: **L012 Uberlândia** e **L020 Goiânia** (queda de fluxo, aluguel caro), **L007 Sorocaba** (2026), e lojas acima do orçado: **L001**, **L014**, **L019** (2026).

## 7. Forecast 9+3 (out-dez/2026)

- **Receita bruta:** orçamento do mês × (realizado ÷ orçado de jan-set/2026), por loja.
- **Descontos, devoluções e CMV:** taxa realizada de jan-set/2026 sobre a receita do forecast, mantendo o efeito sazonal de novembro previsto no orçamento.
- **Impostos sobre vendas:** 17% da venda líquida do forecast.
- **Despesas variáveis** (comissões, cartão, embalagens, marketing local, fretes, resultado financeiro): % realizado de jul-set/2026 × receita do forecast.
- **Despesas fixas** (pessoal, ocupação, tecnologia, marketing nacional, depreciação etc.): média realizada de jul-set/2026 × sazonalidade do orçamento.
- **IRPJ/CSLL:** recalculado sobre o lucro do forecast.

## 8. Reprodutibilidade

- Semente fixa (`SEMENTE_GERADOR` em `parametros.csv`). Executar o gerador de novo produz arquivos idênticos byte a byte.
- Python 3.9+ e apenas a biblioteca padrão.
