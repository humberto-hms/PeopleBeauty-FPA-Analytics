# Regras de geração dos dados fictícios (versão 2.0, omnichannel)

Este documento explica **como** os CSVs de `03_Dados/csv/` foram criados. Os parâmetros estão no início de [`gerar_dados.py`](../03_Dados/gerador/gerar_dados.py) e podem ser alterados para gerar uma nova versão.

A versão 2.0 simula uma operação omnichannel com três canais comerciais: **lojas físicas** (`LOJA_FISICA`), **site próprio** (`SITE_PROPRIO`) e **Mercado Livre** (`MERCADO_LIVRE`). Os valores são fictícios e **não** representam estatísticas reais da People Beauty nem tarifas, volumes ou condições reais do Mercado Livre.

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

## 2. Canais, lojas e unidade corporativa

| Canal | Tipo | Início | Onde aparece |
|---|---|---|---|
| `LOJA_FISICA` | FISICO | antes de 2024 | 24 lojas de `dim_loja` |
| `SITE_PROPRIO` | DIGITAL_PROPRIO | antes de 2024 (04/11/2019) | sem loja; expedido pelo centro de distribuição |
| `MERCADO_LIVRE` | MARKETPLACE | **01/04/2025** (lançamento) | sem loja; expedido pelo centro de distribuição |


- 24 lojas físicas (`L001`–`L024`) e a unidade `CORP`, sem vendas.
- Cada loja tem um fator de potencial de vendas (0,70 a 1,45) que define área, quadro de pessoal e volume.
- Lojas novas: **L023 Fortaleza** abre em 10/03/2025 e **L024 Campo Grande** em 18/08/2025. Começam com 55% do potencial e amadurecem linearmente. O orçamento previu maturação em 9 meses (L023) e 10 meses (L024); no realizado, L023 leva 16 meses e L024 só 8.
- Despesas de loja usam o departamento `OPERACOES_LOJA`. Custos diretamente atribuíveis aos canais digitais usam o departamento `CANAIS_DIGITAIS`, sem loja e com o canal preenchido.
- Despesas da `CORP` ficam nas áreas corporativas, sem canal, e **não são rateadas**. O centro de distribuição que expede os pedidos digitais é um custo da CORP (departamento `LOGISTICA`) e continua sem rateio; isso deve ser considerado ao comparar a rentabilidade dos canais.
- **Lojas físicas e CORP foram geradas exatamente como na versão 1.0** (mesma semente e mesma sequência aleatória). Os canais digitais usam uma sequência aleatória própria. A única mudança nas linhas físicas e da CORP é a conta 7.1.01 (IRPJ/CSLL), que agora inclui o lucro dos canais digitais.

## 3. Vendas das lojas físicas (item de cupom)

1. Para cada loja, produto e dia, o volume esperado = giro do produto × potencial da loja × preferência regional (fixa, ±12%) × sazonalidade do mês e da categoria × índice de volume do ano × desempenho da loja × maturação.
2. O número de itens do dia segue uma distribuição de Poisson sobre esse volume, com choques aleatórios de mês (±3,5%) e de dia (±10%).
3. Os itens do dia são embaralhados e agrupados em cupons de 1 a 6 itens (média ~1,35). Se o mesmo produto cair duas vezes no cupom, as quantidades são somadas no mesmo item.
4. Quantidade por item: 1 a 3 para itens abaixo de R$ 20, normalmente 1 para eletro.
5. **Preço:** tabela anual com reajuste em janeiro (+4,5% em 2025, +5,0% em 2026), arredondada para final ,90.
6. **Desconto:** cada item tem uma chance de estar em promoção (25% em 2024, 26% em 2025, 32% em 2026, +17,5 p.p. em novembro pela Black Friday), com 10% a 30% de desconto.
7. **Custo:** custo médio mensal por produto, com reajuste anual (+4,5% em 2025; +5,2% em 2026, e +9,5% para eletro em 2026 pelo câmbio) e oscilação de até ±1,5% no mês.
8. **Dias especiais:** semana do Dia das Mães, Black Friday (sexta e fim de semana), semana do Natal; lojas fechadas em 01/01 e 25/12. Sábado é o dia mais forte da semana.
9. Produtos inativos: `PB-MAQ-0014` sai de linha em dez/2024 e `PB-CAB-0016` em jun/2025.

## 4. Vendas do site próprio e do Mercado Livre (item de pedido)

1. Mesma lógica de volume das lojas (Poisson diário sobre o volume esperado), com potencial próprio por canal: R$ 205 mil/mês de receita bruta no site e R$ 140 mil/mês no Mercado Livre maduro, em preços de 2024.
2. **Crescimento (realizado):** site +17% em 2025 e +13,7% em 2026 sobre o ano anterior; Mercado Livre começa em abril/2025 com 25% do potencial e amadurece em 10 meses, +10% em 2026.
3. **Mix:** o digital vende mais skincare e eletro e menos higiene pessoal; itens abaixo de R$ 20 vendem pouco no marketplace.
4. **Pedidos:** site com 1 a 7 itens (média ~1,6); Mercado Livre quase sempre 1 item (12% com 2).
5. **Dias:** dias úteis mais fortes que o fim de semana; Black Friday 4,5× um dia normal, com fim de semana e Cyber Monday fortes; pedidos de Natal concentrados entre 8 e 18/12; o digital não fecha em 01/01 e 25/12.
6. **Preço:** site = tabela das lojas. Mercado Livre = tabela + 8%, final ,90 (repasse parcial da comissão).
7. **Desconto:** site com cupons (28% dos itens em 2024–2025, 33% em 2026, +25 p.p. em novembro, 10% a 30%); Mercado Livre com campanhas (12%–14% dos itens, +10 p.p. em novembro, 5% a 15%).
8. **Custo:** o mesmo custo médio mensal do produto em todos os canais. O CMV não inclui comissão, frete nem tarifa.
9. **Identificadores:** `NumeroVenda` interno em faixas separadas (lojas < 50 milhões; site a partir de 50.000.001; Mercado Livre a partir de 80.000.001). `NumeroPedidoExterno`: `SITE-AAAA-NNNNNNN` no site e um número fictício de 16 dígitos no Mercado Livre.

## 5. Devoluções

- Lojas: 1,1% dos itens (2,5% em eletro beleza) são devolvidos de 1 a 30 dias depois da venda, sempre o item inteiro.
- Site: 3,5% (5,0% em eletro); Mercado Livre: 4,5% (6,0% em eletro), de 3 a 30 dias depois da venda.
- Toda devolução guarda o canal, a loja (se houver) e a referência `NumeroVenda` + `NumeroItem` da venda original.
- O valor estornado é o valor líquido do item; o custo volta ao estoque e reduz o CMV no mês da devolução.

## 6. Despesas realizadas (competência mensal)

### 6.1 Lojas físicas e CORP

| Conta | Lojas | CORP |
|---|---|---|
| 3.2.01 Impostos sobre vendas | 17% de (bruto − descontos − devoluções) | — |
| 5.1.01 Salários e encargos | quadro por porte; dissídio em maio; +15% em nov/dez (temporários) | folha por área |
| 5.1.02 Benefícios | por pessoa | 20% da folha |
| 5.1.03 Comissões | 1,5% da receita líquida | — |
| 5.2.01 Aluguel e condomínio | maior entre valor fixo por m² e 6,5% da receita (reajuste em janeiro) | escritório e CD |
| 5.2.02 Energia | por m², mais alta no verão | escritório |
| 5.2.03 / 5.2.04 | valor fixo / manutenção por m² com eventos corretivos pontuais | escritório |
| 5.3.01 Marketing | 0,8% da receita (local) | 1,5% da receita das lojas físicas (marketing de marca), reforço em mai/nov/dez |
| 5.3.02 Taxas de cartão | 2,3% da venda líquida | — |
| 5.3.03 Embalagens e preparação | 0,6% da receita | — |
| 5.4.01 Tecnologia | — | licenças + projeto de ERP em 2026 |
| 5.4.02 / 5.4.03 / 5.4.04 | serviços (limpeza, segurança), despesas gerais | auditoria, jurídico, recrutamento, viagens |
| 5.5.01 Fretes | 1,2% da receita (CD → loja) | 0,8% da receita das lojas (CD) |
| 5.6.01 Depreciação | por m² | TI e CD |
| 6.1.01 / 6.1.02 | — | receitas de aplicações / antecipação de recebíveis, sobre a receita das lojas |
| 7.1.01 IRPJ e CSLL | — | 34% do lucro consolidado do mês (lojas + digital + CORP), quando positivo, sem compensação de prejuízo |

Receita líquida (para os percentuais) = (bruto − descontos − devoluções) × (1 − 17%). As despesas da CORP continuam calculadas sobre a receita das lojas, como na versão 1.0.

### 6.2 Custos diretos dos canais digitais (departamento `CANAIS_DIGITAIS`)

Venda líquida = bruto − descontos − devoluções.

| Conta | Site próprio | Mercado Livre |
|---|---|---|
| 3.2.01 Impostos sobre vendas | 17% da venda líquida | 17% da venda líquida |
| 5.1.01 / 5.1.02 Equipe | R$ 9.500/mês + 20% de benefícios, com dissídio | R$ 4.200/mês + 20%, a partir do lançamento |
| 5.3.02 Taxas de pagamento | 3,2% da venda líquida (gateway) | — (incluída na comissão) |
| 5.3.03 Embalagens e preparação de pedidos | R$ 3,40 por pedido | R$ 2,90 por pedido |
| **5.3.04 Comissões e tarifas de marketplace** | — | 13% da venda líquida (14% em 2026) + R$ 6,00 por pedido abaixo de R$ 79 |
| **5.3.05 Mídia de performance e anúncios patrocinados** | 5% da venda líquida (6% em 2026) | 3% (3,5% em 2026), anúncios patrocinados |
| 5.4.01 Tecnologia | plataforma: R$ 3.800/mês + 1,2% da venda líquida | integrador: R$ 850/mês |
| **5.5.02 Frete de entrega ao cliente** | R$ 17,90 por pedido a partir de R$ 99 (frete grátis); R$ 3,00 abaixo disso | R$ 15,90 por pedido a partir de R$ 79; zero abaixo disso |
| **5.5.03 Logística reversa de devoluções** | R$ 18,00 por devolução | R$ 21,00 por devolução |

Valores por pedido são corrigidos pela inflação do ano.

**Custos deixados de fora (decisão do projeto):** armazenagem e fulfillment do marketplace (o CD é próprio e fica na CORP), antecipação de recebíveis do marketplace, chargebacks e fraudes, multas por atraso, frete cobrado do cliente como receita e rateio de despesas corporativas. Nenhum desses itens muda a comparação básica de margem entre canais e todos aumentariam a complexidade sem ganho analítico.

**Sem duplicidade:** comissão, frete, mídia, embalagem e logística reversa existem só em `fato_despesas`; o CMV existe só em `fato_vendas`/`fato_devolucoes`. A taxa de pagamento não é lançada no Mercado Livre porque já faz parte da comissão.

## 7. Orçamento

- Feito com as mesmas fórmulas do realizado, **sem ruído aleatório** e com as premissas que a empresa tinha antes de cada ano.
- Valores mensais por canal/unidade, departamento e conta (inclusive receita, descontos, devoluções e CMV).
- **Distribuição entre canais:** o orçamento não é rateado de um total. Cada canal tem o próprio orçamento, construído com as próprias premissas; o consolidado é a soma de lojas físicas + site + Mercado Livre + CORP. Cada linha pertence a um único canal (ou à CORP), então não há duplicação.
- O orçamento das lojas físicas e da CORP é o mesmo da versão 1.0 (exceto IRPJ/CSLL).
- Premissas dos canais digitais no orçamento: site +3% de volume em 2024, +20% em 2025 e +45% em 2026 sobre a base; Mercado Livre com lançamento em abril/2025 amadurecendo em 6 meses (realizado: 10) e +25% em 2026 (realizado: +10%); comissão do marketplace mantida em 13% (realizado: 14% em 2026); frete médio de R$ 8,00 por pedido no site e R$ 11,00 no Mercado Livre; 45% dos pedidos do marketplace abaixo do mínimo para frete grátis.
- Premissas de 2026 mais otimistas que o realizado:
  - volume +7,5% a +9% em cabelos, maquiagem e eletro (realizado bem menor; maquiagem e eletro caem);
  - reajuste de preço de 6,0% (realizado 5,0%);
  - desconto médio de 5% (realizado sobe com as promoções);
  - custo +5,0% para todas as categorias (eletro sobe 9,5%);
  - dissídio de 5,0% (realizado 6,8%);
  - energia sem bandeira tarifária (realizado com bandeira vermelha de jun a set/2026);
  - projeto de ERP e marketing nacional abaixo do realizado; despesa financeira de 1,20% da receita (realizado 1,45%).
- Lojas com desempenho diferente do orçado: **L012 Uberlândia** e **L020 Goiânia** (queda de fluxo, aluguel caro), **L007 Sorocaba** (2026), e lojas acima do orçado: **L001**, **L014**, **L019** (2026).

## 8. Forecast 9+3 (out-dez/2026)

- Feito separadamente para cada loja física, para cada canal digital e para a CORP, com as mesmas regras.
- **Receita bruta:** orçamento do mês × (realizado ÷ orçado de jan-set/2026), por loja e por canal digital.
- **Descontos, devoluções e CMV:** taxa realizada de jan-set/2026 sobre a receita do forecast, mantendo o efeito sazonal de novembro previsto no orçamento.
- **Impostos sobre vendas:** 17% da venda líquida do forecast.
- **Despesas variáveis** (comissões de vendedores e de marketplace, cartão, embalagens, marketing local, mídia de performance, fretes, logística reversa, resultado financeiro): % realizado de jul-set/2026 × receita do forecast.
- **Despesas fixas** (pessoal, ocupação, tecnologia, marketing nacional, depreciação etc.): média realizada de jul-set/2026 × sazonalidade do orçamento.
- **IRPJ/CSLL:** recalculado sobre o lucro consolidado do forecast (lojas + digital + CORP).

## 9. Reprodutibilidade

- Semente fixa (`SEMENTE_GERADOR` em `parametros.csv`). Executar o gerador de novo produz arquivos idênticos byte a byte.
- Python 3.9+ e apenas a biblioteca padrão.
