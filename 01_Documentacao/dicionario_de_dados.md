# Dicionário de dados — CSVs fictícios

Arquivos em [`03_Dados/csv/`](../03_Dados/csv/). Todos os dados são **fictícios**.

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
| Campos vazios | string vazia (ex.: `CodigoContaPai` de contas de nível 1) |

Prefixo `dim_` = arquivo de referência (dimensão); `fato_` = arquivo de fatos.

## Mapa de relacionamentos

```
dim_categoria ─┐
dim_marca ─────┼── dim_produto ──┐
               │                 ├── fato_vendas_AAAA ── fato_devolucoes
dim_calendario ┼─────────────────┤   (NumeroVenda, NumeroItem)
               │                 │
dim_loja ──────┼─────────────────┤
dim_departamento ────────────────┼── fato_despesas
dim_plano_contas ────────────────┼── fato_orcamento
dim_cenario ─────────────────────┴── fato_forecast
```

| Fato.coluna | Referência |
|---|---|
| `fato_vendas_AAAA.DataVenda` | `dim_calendario.Data` |
| `fato_vendas_AAAA.CodigoLoja` | `dim_loja.CodigoLoja` |
| `fato_vendas_AAAA.CodigoProduto` | `dim_produto.CodigoProduto` |
| `fato_devolucoes.(NumeroVenda, NumeroItem)` | `fato_vendas_AAAA.(NumeroVenda, NumeroItem)` |
| `fato_devolucoes.DataDevolucao` | `dim_calendario.Data` |
| `fato_devolucoes.CodigoLoja` / `CodigoProduto` | `dim_loja` / `dim_produto` |
| `fato_despesas`, `fato_orcamento`, `fato_forecast` `.DataCompetencia` | `dim_calendario.Data` |
| idem `.CodigoLoja` | `dim_loja.CodigoLoja` |
| idem `.CodigoDepartamento` | `dim_departamento.CodigoDepartamento` |
| idem `.CodigoConta` | `dim_plano_contas.CodigoConta` (somente contas com `ContaAnalitica = 1`) |
| `fato_orcamento`, `fato_forecast` `.CodigoCenario` | `dim_cenario.CodigoCenario` |
| `dim_produto.CodigoCategoria` | `dim_categoria.CodigoCategoria` |
| `dim_produto.CodigoMarca` | `dim_marca.CodigoMarca` |
| `dim_plano_contas.CodigoContaPai` | `dim_plano_contas.CodigoConta` |

Os três arquivos `fato_vendas_2024.csv`, `fato_vendas_2025.csv` e `fato_vendas_2026.csv` formam **uma única tabela lógica**; foram separados por ano apenas para manter cada arquivo abaixo de 50 MB. `NumeroVenda` é sequencial e único entre os três.

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

### dim_loja.csv
Grão: **uma unidade** (24 lojas + CORP). PK: `CodigoLoja`.

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
| CodigoDepartamento | texto | `OPERACOES_LOJA` (lojas) ou área corporativa |
| NomeDepartamento | texto | Nome |
| TipoUnidade | texto | `LOJA` ou `CORPORATIVA`: tipo de unidade que pode usar o departamento |

### dim_cenario.csv
PK: `CodigoCenario`.

| CodigoCenario | Uso |
|---|---|
| REALIZADO | Rótulo para os fatos de realizado (vendas, devoluções, despesas). Os fatos de realizado **não** têm coluna de cenário |
| ORCAMENTO_APROVADO | `fato_orcamento`, jan/2024 a dez/2026 |
| FORECAST_2026_9P3 | `fato_forecast`, somente out-dez/2026 |

Colunas: `CodigoCenario`, `NomeCenario`, `TipoCenario`, `StatusCenario`, `Descricao`.

### dim_plano_contas.csv
Grão: **uma conta gerencial** (36). PK: `CodigoConta`. Hierarquia em até 3 níveis.

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

Subtotais da DRE (receita líquida, lucro bruto, resultado operacional, resultado líquido) **não são contas**: saem das colunas `Participa*`.

### dim_categoria.csv
PK: `CodigoCategoria` (`CAB`, `SKN`, `MAQ`, `HIG`, `ELE`). Colunas: `CodigoCategoria`, `NomeCategoria`, `Descricao`.

### dim_marca.csv
PK: `CodigoMarca` (21 marcas). Colunas: `CodigoMarca`, `NomeMarca`.

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
| PrecoListaReferencia2024 | decimal | Preço de venda de 2024 |
| CustoReferencia2024 | decimal | Custo de aquisição médio de 2024 (informativo) |

O preço e o custo efetivamente praticados estão em cada linha de venda.

### parametros.csv
| CodigoParametro | Valor |
|---|---|
| DATA_CORTE_REALIZADO | 2026-09-30 |
| SEMENTE_GERADOR | Semente usada pelo gerador |
| ALIQUOTA_IMPOSTO_VENDA | 0.17 |
| ALIQUOTA_IRPJ_CSLL | 0.34 |

---

## Arquivos de fatos

### fato_vendas_2024.csv, fato_vendas_2025.csv, fato_vendas_2026.csv
Grão: **um item de cupom** (um produto dentro de uma venda). PK composta: `NumeroVenda` + `NumeroItem`. Um mesmo produto aparece no máximo uma vez por cupom. Período: 2024-01-02 a 2026-09-30.

| Coluna | Tipo | Descrição |
|---|---|---|
| NumeroVenda | inteiro | Número do cupom, único na rede |
| NumeroItem | inteiro | Sequência do item no cupom (1, 2, …) |
| DataVenda | data | FK `dim_calendario` |
| CodigoLoja | texto | FK `dim_loja` (nunca `CORP`) |
| CodigoProduto | texto | FK `dim_produto` |
| Quantidade | inteiro | Unidades vendidas (> 0) |
| PrecoUnitario | decimal | Preço de tabela do ano |
| ValorBruto | decimal | `Quantidade x PrecoUnitario` |
| ValorDesconto | decimal | Desconto promocional do item (0 a 30% do bruto) |
| ValorLiquido | decimal | `ValorBruto - ValorDesconto` |
| CustoUnitario | decimal | Custo médio do produto no mês |
| CustoTotal | decimal | `Quantidade x CustoUnitario` |

Contas: `ValorBruto` → 3.1.01; `ValorDesconto` → 3.2.02; `CustoTotal` → 4.1.01.

### fato_devolucoes.csv
Grão: **um item de cupom devolvido**. PK: `IdDevolucao`. Chave única: `NumeroVenda` + `NumeroItem` (FK para a venda).

| Coluna | Tipo | Descrição |
|---|---|---|
| IdDevolucao | inteiro | Identificador |
| DataDevolucao | data | Entre 1 e 30 dias depois da venda e até 2026-09-30 |
| NumeroVenda, NumeroItem | inteiro | Item devolvido |
| CodigoLoja, CodigoProduto | texto | Iguais aos da venda (facilitam o relacionamento direto) |
| Quantidade | inteiro | Quantidade devolvida (igual à vendida) |
| ValorDevolvido | decimal | Valor líquido estornado → conta 3.2.03 |
| CustoDevolvido | decimal | Custo que volta ao estoque → reduz o CMV 4.1.01 |

A devolução entra na competência do mês da `DataDevolucao`.

### fato_despesas.csv (realizado)
Grão: **um lançamento por competência, unidade, departamento e conta**. PK: `IdLancamento`. Chave única de negócio: `AnoMes` + `CodigoLoja` + `CodigoDepartamento` + `CodigoConta`. Período: jan/2024 a set/2026.

| Coluna | Tipo | Descrição |
|---|---|---|
| IdLancamento | inteiro | Identificador |
| DataCompetencia | data | 1º dia do mês de competência |
| AnoMes | inteiro | `AAAAMM` |
| CodigoLoja | texto | Loja ou `CORP` |
| CodigoDepartamento | texto | `OPERACOES_LOJA` para lojas; área corporativa para `CORP` |
| CodigoConta | texto | Conta com `IndicadorDespesa = 1` |
| Valor | decimal | Valor positivo |

Contém impostos sobre vendas (3.2.01), despesas operacionais (5.x), resultado financeiro (6.1.01 receita e 6.1.02 despesa) e IRPJ/CSLL (7.1.01). **Despesas corporativas ficam somente em `CORP`, sem rateio para as lojas.** Resultado financeiro e IR existem só na `CORP`.

### fato_orcamento.csv
Grão: **cenário + mês + unidade + departamento + conta**. Chave única: `CodigoCenario` + `AnoMes` + `CodigoLoja` + `CodigoDepartamento` + `CodigoConta`. Cenário `ORCAMENTO_APROVADO`, jan/2024 a dez/2026.

Colunas: `CodigoCenario`, `DataCompetencia`, `AnoMes`, `CodigoLoja`, `CodigoDepartamento`, `CodigoConta`, `Valor`.

Diferente do realizado, o orçamento traz **todas** as contas analíticas no mesmo arquivo, inclusive as de vendas (3.1.01, 3.2.02, 3.2.03, 4.1.01).

### fato_forecast.csv
Mesmo layout e grão de `fato_orcamento`. Cenário `FORECAST_2026_9P3`, **somente out/2026 a dez/2026**. O forecast do ano 2026 completo = realizado de jan-set/2026 + este arquivo.

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
