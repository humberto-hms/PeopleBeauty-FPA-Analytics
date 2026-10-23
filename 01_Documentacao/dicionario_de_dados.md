# Dicionário de dados — CSVs fictícios (versão 2.0, omnichannel)

Arquivos em [`03_Dados/csv/`](../03_Dados/csv/). Todos os dados são **fictícios**: nenhum valor representa estatística real da People Beauty, do Mercado Livre ou de qualquer empresa.

A versão 2.0 acrescenta os canais **site próprio** e **Mercado Livre** à rede de 24 lojas físicas. A versão 1.0 (somente lojas físicas) está preservada; veja a seção [Versões](#versões).

## Convenções

| Item | Regra |
|---|---|
| Codificação | UTF-8 **sem BOM** |
| Separador | ponto e vírgula `;` |
| Decimal | ponto `.` (ex.: `1234.56`), sem separador de milhar |
| Datas | ISO `AAAA-MM-DD` |
| Período de competência | `AnoMes` inteiro `AAAAMM` e `DataCompetencia` = 1º dia do mês |
| Cabeçalho | primeira linha, nomes em PascalCase sem acento |
| Fim de linha | LF (`\n`) |
| Valores monetários | BRL, 2 casas, **sempre positivos**. O sinal na DRE vem de `dim_plano_contas.SinalDRE` |
| Campos vazios | string vazia = "não se aplica" (ex.: `CodigoLoja` de uma venda do site; `CodigoCanal` de uma despesa da CORP) |

Prefixo `dim_` = arquivo de referência (dimensão); `fato_` = arquivo de fatos.

## Canais, lojas e CORP

| Origem do registro | CodigoCanal | CodigoLoja | CodigoDepartamento |
|---|---|---|---|
| Loja física | `LOJA_FISICA` | `L001` … `L024` | `OPERACOES_LOJA` |
| Site próprio | `SITE_PROPRIO` | vazio | `CANAIS_DIGITAIS` (só nos lançamentos) |
| Mercado Livre | `MERCADO_LIVRE` | vazio | `CANAIS_DIGITAIS` (só nos lançamentos) |
| Unidade corporativa | vazio | `CORP` | área corporativa (`DIRETORIA`, `FINANCEIRO` …) |

- Site e Mercado Livre **não** estão em `dim_loja`; são expedidos pelo centro de distribuição, cujos custos já ficam na `CORP` (departamento `LOGISTICA`).
- A `CORP` não é canal de vendas: não tem vendas, devoluções, receita nem CMV, e suas despesas **não são rateadas** entre canais.
- Assim, `CodigoLoja` e `CodigoCanal` são chaves estrangeiras **opcionais** (aceitam vazio/NULL). Cada lançamento pertence a exatamente um canal ou à CORP.

## Mapa de relacionamentos

```
dim_categoria ─┐
dim_marca ─────┼── dim_produto ──┐
               │                 ├── fato_vendas_AAAA ── fato_devolucoes
dim_calendario ┼─────────────────┤   (NumeroVenda, NumeroItem)
dim_canal ─────┼─────────────────┤
dim_loja ──────┼─────────────────┤
dim_departamento ────────────────┼── fato_despesas
dim_plano_contas ────────────────┼── fato_orcamento
dim_cenario ─────────────────────┴── fato_forecast
```

| Fato.coluna | Referência | Obrigatória |
|---|---|---|
| `fato_vendas_AAAA.DataVenda` | `dim_calendario.Data` | sim |
| `fato_vendas_AAAA.CodigoCanal` | `dim_canal.CodigoCanal` | sim |
| `fato_vendas_AAAA.CodigoLoja` | `dim_loja.CodigoLoja` | só em `LOJA_FISICA` |
| `fato_vendas_AAAA.CodigoProduto` | `dim_produto.CodigoProduto` | sim |
| `fato_devolucoes.(NumeroVenda, NumeroItem)` | `fato_vendas_AAAA.(NumeroVenda, NumeroItem)` | sim |
| `fato_devolucoes.DataDevolucao` | `dim_calendario.Data` | sim |
| `fato_devolucoes.CodigoCanal` / `CodigoLoja` / `CodigoProduto` | `dim_canal` / `dim_loja` / `dim_produto` | como na venda |
| `fato_despesas`, `fato_orcamento`, `fato_forecast` `.DataCompetencia` | `dim_calendario.Data` | sim |
| idem `.CodigoCanal` | `dim_canal.CodigoCanal` | vazio só na CORP |
| idem `.CodigoLoja` | `dim_loja.CodigoLoja` | vazio só no digital |
| idem `.CodigoDepartamento` | `dim_departamento.CodigoDepartamento` | sim |
| idem `.CodigoConta` | `dim_plano_contas.CodigoConta` (só `ContaAnalitica = 1`) | sim |
| `fato_orcamento`, `fato_forecast` `.CodigoCenario` | `dim_cenario.CodigoCenario` | sim |
| `dim_produto.CodigoCategoria` | `dim_categoria.CodigoCategoria` | sim |
| `dim_produto.CodigoMarca` | `dim_marca.CodigoMarca` | sim |
| `dim_plano_contas.CodigoContaPai` | `dim_plano_contas.CodigoConta` | vazio no nível 1 |

Os três arquivos `fato_vendas_2024.csv`, `fato_vendas_2025.csv` e `fato_vendas_2026.csv` formam **uma única tabela lógica**, separada por ano apenas para reduzir o tamanho de cada arquivo.

---

## Arquivos de referência

### dim_calendario.csv
Grão: **um dia**, de 2024-01-01 a 2026-12-31 (1.096 linhas). PK: `Data`.

| Coluna | Tipo | Descrição |
|---|---|---|
| Data | data | Dia (PK) |
| DataKey | inteiro | `AAAAMMDD`, alternativa inteira à PK |
| Ano | inteiro | Ano |
| MesNumero | inteiro | 1 a 12 |
| MesNome | texto | Janeiro … Dezembro |
| MesAnoAbrev | texto | `jan/24` |
| AnoMes | inteiro | `AAAAMM` |
| Trimestre | inteiro | 1 a 4 |
| TrimestreAno | texto | `T1/2024` |
| Dia | inteiro | Dia do mês |
| DiaSemanaNumero | inteiro | 1 = segunda … 7 = domingo (ISO) |
| DiaSemanaNome | texto | Segunda-feira … Domingo |
| FimDeSemana | 0/1 | 1 para sábado e domingo |
| InicioMes | data | 1º dia do mês (liga com `DataCompetencia`) |
| FimMes | data | Último dia do mês |
| PeriodoRealizado | 0/1 | 1 até a data de corte do realizado (2026-09-30) |

### dim_canal.csv
Grão: **um canal comercial** (3). PK: `CodigoCanal`. Novo na versão 2.0.

| Coluna | Tipo | Descrição |
|---|---|---|
| CodigoCanal | texto | `LOJA_FISICA`, `SITE_PROPRIO`, `MERCADO_LIVRE` (códigos estáveis) |
| NomeCanal | texto | Lojas físicas, Site próprio, Mercado Livre |
| TipoCanal | texto | `FISICO`, `DIGITAL_PROPRIO` ou `MARKETPLACE` |
| DataInicioOperacao | data | Início fictício da operação. Mercado Livre: 2025-04-01 |
| Descricao | texto | Descrição do canal |

### dim_loja.csv
Grão: **uma unidade** (24 lojas + CORP). PK: `CodigoLoja`. Não contém canais digitais.

| Coluna | Tipo | Descrição |
|---|---|---|
| CodigoLoja | texto(4) | `L001` … `L024` e `CORP` |
| NomeLoja | texto | Nome fantasia fictício |
| TipoUnidade | texto | `LOJA` ou `CORPORATIVA` |
| Regiao | texto | Sudeste, Sul, Centro-Oeste, Nordeste ou Corporativo |
| UF | texto(2) | Estado |
| Cidade | texto | Cidade |
| DataAbertura | data | Inauguração. L023 = 2025-03-10 e L024 = 2025-08-18 |
| Formato | texto | Rua, Shopping ou Escritório |
| AreaVendaM2 | inteiro | Área de vendas (vazio para CORP) |

### dim_departamento.csv
PK: `CodigoDepartamento`.

| Coluna | Tipo | Descrição |
|---|---|---|
| CodigoDepartamento | texto | `OPERACOES_LOJA`, `CANAIS_DIGITAIS` ou área corporativa |
| NomeDepartamento | texto | Nome |
| TipoUnidade | texto | `LOJA`, `DIGITAL` ou `CORPORATIVA`: onde o departamento pode ser usado |

### dim_cenario.csv
PK: `CodigoCenario`.

| Coluna | Tipo | Descrição |
|---|---|---|
| CodigoCenario | texto | `REALIZADO`, `ORCAMENTO_APROVADO`, `FORECAST_2026_9P3` |
| NomeCenario | texto | Nome do cenário |
| TipoCenario | texto | REALIZADO, ORCAMENTO ou FORECAST |
| StatusCenario | texto | FECHADO, APROVADO ou VIGENTE |
| Descricao | texto | Período e arquivos do cenário |

`REALIZADO` é um rótulo para os fatos de realizado (vendas, devoluções, despesas), que **não** têm coluna de cenário. `ORCAMENTO_APROVADO` está em `fato_orcamento` (jan/2024 a dez/2026) e `FORECAST_2026_9P3` em `fato_forecast` (só out-dez/2026).

### dim_plano_contas.csv
Grão: **uma conta gerencial** (40). PK: `CodigoConta`. Hierarquia em até 3 níveis.

| Coluna | Tipo | Descrição |
|---|---|---|
| CodigoConta | texto | Ex.: `5.1.01` |
| NomeConta | texto | Nome da conta |
| GrupoDRE | texto | Receita bruta, Deduções, CMV, Despesas operacionais, Resultado financeiro, Impostos sobre lucro |
| NaturezaConta | texto | RECEITA, DEDUCAO, CUSTO, DESPESA |
| SinalDRE | +1/-1 | Multiplicador do valor (sempre positivo) na DRE |
| IndicadorDespesa | 0/1 | 1 = realizado vem de `fato_despesas` |
| CodigoContaPai | texto | Conta sintética superior (vazio no nível 1) |
| NivelHierarquia | inteiro | 1 a 3 |
| OrdemExibicao | inteiro | Ordem de exibição na DRE |
| ParticipaReceitaLiquida | 0/1 | Entra no subtotal Receita líquida |
| ParticipaCMV | 0/1 | Entra no CMV |
| ParticipaResultadoOperacional | 0/1 | Entra no Resultado operacional |
| ParticipaResultadoLiquido | 0/1 | Entra no Resultado líquido |
| ContaAnalitica | 0/1 | 1 = recebe lançamentos; 0 = conta sintética (só agrupa) |
| OrigemRealizado | texto | Arquivo de onde sai o realizado: `fato_vendas`, `fato_devolucoes` ou `fato_despesas` |

Contas novas na versão 2.0 (premissa gerencial do projeto, não uma classificação contábil definitiva): **5.3.04** Comissões e tarifas de marketplace, **5.3.05** Mídia de performance e anúncios patrocinados, **5.5.02** Frete de entrega ao cliente, **5.5.03** Logística reversa de devoluções. A conta **5.3.03** passou a se chamar "Embalagens e preparação de pedidos" (mesmo código, cobre lojas e digital). Subtotais da DRE não são contas: saem das colunas `Participa*`.

### dim_categoria.csv
PK: `CodigoCategoria`.

| Coluna | Tipo | Descrição |
|---|---|---|
| CodigoCategoria | texto | `CAB`, `SKN`, `MAQ`, `HIG`, `ELE` |
| NomeCategoria | texto | Nome da categoria |
| Descricao | texto | O que a categoria inclui |

### dim_marca.csv
PK: `CodigoMarca` (21 marcas).

| Coluna | Tipo | Descrição |
|---|---|---|
| CodigoMarca | texto | Nome da marca em maiúsculas, sem acento |
| NomeMarca | texto | Nome da marca |

### dim_produto.csv
Grão: **um produto** (66, sendo 2 inativos). PK: `CodigoProduto`.

| Coluna | Tipo | Descrição |
|---|---|---|
| CodigoProduto | texto | `PB-CAT-NNNN` |
| NomeProduto | texto | Descrição genérica do item |
| CodigoCategoria | texto | FK para `dim_categoria` |
| Subcategoria | texto | Ex.: Shampoo, Sérum, Secador |
| CodigoMarca | texto | FK para `dim_marca` |
| StatusProduto | texto | ATIVO ou INATIVO |
| DataDescontinuacao | data | Último dia com venda (somente INATIVO) |
| PrecoListaReferencia2024 | decimal | Preço de venda de 2024 nas lojas e no site |
| CustoReferencia2024 | decimal | Custo de aquisição médio de 2024 (informativo) |

O preço e o custo efetivamente praticados estão em cada linha de venda.

### parametros.csv

| Coluna | Tipo | Descrição |
|---|---|---|
| CodigoParametro | texto | `DATA_CORTE_REALIZADO`, `SEMENTE_GERADOR`, `ALIQUOTA_IMPOSTO_VENDA`, `ALIQUOTA_IRPJ_CSLL` |
| Valor | texto | 2026-09-30, semente, 0.17 e 0.34 |
| Descricao | texto | Significado do parâmetro |

---

## Arquivos de fatos

### fato_vendas_2024.csv, fato_vendas_2025.csv, fato_vendas_2026.csv
Grão: **um item vendido** (um produto dentro de uma venda ou pedido). PK composta: `NumeroVenda` + `NumeroItem`. Um mesmo produto aparece no máximo uma vez por venda. Período: 2024-01-01 a 2026-09-30.

| Coluna | Tipo | Descrição |
|---|---|---|
| NumeroVenda | inteiro | Identificador interno único da venda. Faixas sem conflito: lojas 1 a 49.999.999; site a partir de 50.000.001; Mercado Livre a partir de 80.000.001 |
| NumeroItem | inteiro | Sequência do item na venda (1, 2, …) |
| DataVenda | data | FK `dim_calendario` |
| CodigoCanal | texto | FK `dim_canal` |
| CodigoLoja | texto | FK `dim_loja`; preenchido só em `LOJA_FISICA` (nunca `CORP`) |
| NumeroPedidoExterno | texto | Vazio nas lojas. Site: `SITE-AAAA-NNNNNNN` (ano da venda + sequência contínua). Mercado Livre: número fictício de 16 dígitos iniciado em 2, único por pedido |
| CodigoProduto | texto | FK `dim_produto` |
| Quantidade | inteiro | Unidades vendidas (> 0) |
| PrecoUnitario | decimal | Preço praticado no canal (Mercado Livre = tabela + 8%) |
| ValorBruto | decimal | `Quantidade x PrecoUnitario` |
| ValorDesconto | decimal | Desconto do item (0 a 30% do bruto) |
| ValorLiquido | decimal | `ValorBruto - ValorDesconto` (receita do item) |
| CustoUnitario | decimal | Custo médio do produto no mês, igual em todos os canais |
| CustoTotal | decimal | `Quantidade x CustoUnitario` (CMV do item) |

Contas: `ValorBruto` → 3.1.01; `ValorDesconto` → 3.2.02; `CustoTotal` → 4.1.01. Comissões, frete e tarifas do marketplace **não** estão aqui: ficam em `fato_despesas`.

### fato_devolucoes.csv
Grão: **um item devolvido**. PK: `IdDevolucao`. Chave única: `NumeroVenda` + `NumeroItem` (FK para a venda).

| Coluna | Tipo | Descrição |
|---|---|---|
| IdDevolucao | inteiro | Identificador |
| DataDevolucao | data | Separada da data da venda: 1 a 30 dias depois (3 a 30 no digital) e até 2026-09-30 |
| NumeroVenda | inteiro | Venda original |
| NumeroItem | inteiro | Item devolvido |
| CodigoCanal | texto | Canal da venda original |
| CodigoLoja | texto | Loja da venda original (vazio no digital) |
| CodigoProduto | texto | Igual ao da venda |
| Quantidade | inteiro | Quantidade devolvida (igual à vendida) |
| ValorDevolvido | decimal | Valor líquido estornado → conta 3.2.03 |
| CustoDevolvido | decimal | Custo que volta ao estoque → reduz o CMV 4.1.01 |

A devolução entra na competência do mês da `DataDevolucao`. A venda original continua em `fato_vendas` (a receita não é apagada); o estorno aparece uma única vez aqui.

### fato_despesas.csv
Realizado. Grão: **um lançamento por competência, canal/unidade, departamento e conta**. PK: `IdLancamento`. Chave única de negócio: `AnoMes` + `CodigoCanal` + `CodigoLoja` + `CodigoDepartamento` + `CodigoConta`. Período: jan/2024 a set/2026.

| Coluna | Tipo | Descrição |
|---|---|---|
| IdLancamento | inteiro | Identificador |
| DataCompetencia | data | 1º dia do mês de competência |
| AnoMes | inteiro | `AAAAMM` |
| CodigoCanal | texto | Canal do custo; vazio nas despesas da CORP |
| CodigoLoja | texto | Loja física ou `CORP`; vazio nos custos dos canais digitais |
| CodigoDepartamento | texto | Veja a tabela [Canais, lojas e CORP](#canais-lojas-e-corp) |
| CodigoConta | texto | Conta com `IndicadorDespesa = 1` |
| Valor | decimal | Valor positivo |

Contém impostos sobre vendas (3.2.01), despesas operacionais (5.x), resultado financeiro (6.1.01 e 6.1.02) e IRPJ/CSLL (7.1.01). Resultado financeiro e IR existem só na `CORP`. Não contém receita, descontos, devoluções nem CMV, que vêm de vendas e devoluções.

### fato_orcamento.csv
Grão: **cenário + mês + canal/unidade + departamento + conta**. Chave única: `CodigoCenario` + `AnoMes` + `CodigoCanal` + `CodigoLoja` + `CodigoDepartamento` + `CodigoConta`. Cenário `ORCAMENTO_APROVADO`, jan/2024 a dez/2026.

| Coluna | Tipo | Descrição |
|---|---|---|
| CodigoCenario | texto | `ORCAMENTO_APROVADO` |
| DataCompetencia | data | 1º dia do mês |
| AnoMes | inteiro | `AAAAMM` |
| CodigoCanal | texto | Canal; vazio na CORP |
| CodigoLoja | texto | Loja física ou `CORP`; vazio no digital |
| CodigoDepartamento | texto | Mesma regra de `fato_despesas` |
| CodigoConta | texto | Qualquer conta analítica, inclusive vendas (3.1.01, 3.2.02, 3.2.03, 4.1.01) |
| Valor | decimal | Valor positivo |

Cada linha pertence a um único canal ou à CORP, então a soma por canal (+ CORP) é o consolidado, sem duplicação.

### fato_forecast.csv
Mesmo grão e regras de `fato_orcamento`. Cenário `FORECAST_2026_9P3`, **somente out/2026 a dez/2026**. O forecast do ano 2026 completo = realizado de jan-set/2026 + este arquivo.

| Coluna | Tipo | Descrição |
|---|---|---|
| CodigoCenario | texto | `FORECAST_2026_9P3` |
| DataCompetencia | data | 1º dia do mês (out, nov ou dez/2026) |
| AnoMes | inteiro | 202610, 202611 ou 202612 |
| CodigoCanal | texto | Canal; vazio na CORP |
| CodigoLoja | texto | Loja física ou `CORP`; vazio no digital |
| CodigoDepartamento | texto | Mesma regra de `fato_despesas` |
| CodigoConta | texto | Conta analítica |
| Valor | decimal | Valor positivo |

---

## Como montar cada linha da DRE (referência)

| Linha | Realizado | Orçamento / Forecast |
|---|---|---|
| 3.1.01 Receita bruta | Σ `fato_vendas.ValorBruto` | conta 3.1.01 |
| 3.2.01 Impostos sobre vendas | `fato_despesas` conta 3.2.01 | conta 3.2.01 |
| 3.2.02 Descontos | Σ `fato_vendas.ValorDesconto` | conta 3.2.02 |
| 3.2.03 Devoluções | Σ `fato_devolucoes.ValorDevolvido` | conta 3.2.03 |
| 4.1.01 CMV | Σ `fato_vendas.CustoTotal` − Σ `fato_devolucoes.CustoDevolvido` | conta 4.1.01 |
| 5.x, 6.x, 7.x | `fato_despesas` | contas 5.x, 6.x, 7.x |

Todas as linhas podem ser abertas por `CodigoCanal`. A CORP aparece como "sem canal" (corporativo, não alocado).

## Versões

| Versão | Conteúdo | Como recuperar |
|---|---|---|
| 1.0 | 24 lojas físicas + CORP, sem canal | `03_Dados/versoes/PeopleBeauty_Dados_Ficticios_v1.0.zip`, ou `git checkout 638d299 -- 03_Dados` |
| 2.0 | Três canais (lojas, site próprio, Mercado Livre) + CORP | `03_Dados/csv/` e `03_Dados/PeopleBeauty_Dados_Ficticios.zip` |

Na versão 2.0, os registros das lojas físicas e da CORP são idênticos aos da 1.0, exceto pelas colunas novas e pela conta 7.1.01 (IRPJ/CSLL), recalculada com o lucro dos canais digitais. Os `IdLancamento` foram renumerados.
