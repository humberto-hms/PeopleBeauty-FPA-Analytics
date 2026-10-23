# Auditoria da versão 1.0 e mudanças da versão 2.0 (omnichannel)

Data: 23/10/2026. Objetivo: incluir os canais **site próprio** e **Mercado Livre** sem perder a versão anterior dos dados.

## 1. Situação encontrada (versão 1.0, commit `638d299`)

| Item auditado | Resultado |
|---|---|
| Dimensão ou coluna de canal | **Não existia** em nenhum CSV, no gerador, no dicionário, nas regras, no README nem no `projeto_config.json` |
| Menção a e-commerce ou marketplace | Nenhuma em todo o repositório |
| ZIP de dados | Idêntico aos CSVs do repositório (16 CSVs + documentação) |
| Vendas | 1.407.316 itens de cupom, só em 24 lojas físicas, 2024-01-02 a 2026-09-30, PK `NumeroVenda` + `NumeroItem` (máximo `NumeroVenda` = 1.049.657) |
| Devoluções | 16.126 itens, ligados à venda por `NumeroVenda` + `NumeroItem` |
| Despesas | 12.432 lançamentos por competência × loja × departamento × conta; CORP separada, sem rateio |
| Orçamento | 16.938 linhas por cenário × mês × loja × departamento × conta, jan/2024 a dez/2026 |
| Forecast | 1.464 linhas, só out-dez/2026 |

### Distribuição dos valores na versão 1.0

- Receita bruta realizada: R$ 79,8 milhões (2024: 26,6; 2025: 30,2; jan-set/2026: 23,0).
- Por loja: maior L001 (6,9% da receita), menores L024 (1,5%), L023 (2,1%, lojas novas) e L020 (2,9%).
- Por categoria: Skincare 33,2%, Cabelos 23,3%, Maquiagem 21,1%, Eletro beleza 14,3%, Higiene pessoal 8,2%.
- Por mês: menor fev/2024 (R$ 1,79 milhão), maior dez/2025 (R$ 3,90 milhões).
- Por grupo de contas (realizado): lojas concentram impostos sobre vendas, pessoal e ocupação; a CORP concentra folha administrativa, marketing de marca, tecnologia, resultado financeiro e IRPJ/CSLL.

## 2. Impacto em chaves e relacionamentos

| Arquivo | Mudança | Motivo |
|---|---|---|
| `dim_canal.csv` | **novo** | Identificador, nome, tipo e início de cada canal |
| `dim_loja.csv` | sem mudança | Site e Mercado Livre não são lojas |
| `dim_departamento.csv` | + `CANAIS_DIGITAIS`; `TipoUnidade` aceita `DIGITAL` | Custos diretos dos canais digitais, separados das lojas e da CORP |
| `dim_plano_contas.csv` | + 5.3.04, 5.3.05, 5.5.02, 5.5.03; 5.3.03 renomeada | Custos de marketplace e e-commerce |
| `dim_cenario.csv` | só descrições | Cenários continuam os mesmos |
| `fato_vendas_AAAA.csv` | + `CodigoCanal`, + `NumeroPedidoExterno`; `CodigoLoja` vazio no digital | O canal está no grão do item vendido |
| `fato_devolucoes.csv` | + `CodigoCanal` | Canal da venda original |
| `fato_despesas.csv` | + `CodigoCanal`; `CodigoLoja` vazio no digital; `IdLancamento` renumerado | Custos por canal; CORP sem canal |
| `fato_orcamento.csv` | + `CodigoCanal` | Orçamento por canal |
| `fato_forecast.csv` | + `CodigoCanal` | Forecast por canal |
| `dim_calendario`, `dim_produto`, `dim_categoria`, `dim_marca`, `parametros` | sem mudança | — |

`CodigoLoja` e `CodigoCanal` passam a ser chaves estrangeiras **opcionais**. Nenhuma chave primária mudou de formato: a PK das vendas continua `NumeroVenda` + `NumeroItem`, com faixas numéricas separadas por canal.

## 3. O que foi preservado

- Versão 1.0 completa em `03_Dados/versoes/PeopleBeauty_Dados_Ficticios_v1.0.zip` e no histórico do Git (`git checkout 638d299 -- 03_Dados`).
- Itens de venda, devoluções, despesas, orçamento e forecast das lojas físicas e da CORP são **idênticos** aos da 1.0 (conferido automaticamente pelo `validar_dados.py --versao-anterior`), exceto:
  - as colunas novas (`CodigoCanal`, `NumeroPedidoExterno`);
  - a conta 7.1.01 IRPJ/CSLL, recalculada com o lucro do digital;
  - a renumeração de `IdLancamento` em `fato_despesas`.

## 4. Riscos tratados

| Risco | Tratamento |
|---|---|
| Venda digital confundida com loja | `CodigoLoja` vazio + validação |
| Conflito de identificadores | Faixas de `NumeroVenda` por canal; pedido externo único por canal |
| Comissão tratada como CMV | Comissão em 5.3.04 (`fato_despesas`); CMV só de `CustoTotal` |
| Custo contado duas vezes | `fato_despesas` não aceita contas de vendas/CMV; taxa de cartão não é lançada no marketplace |
| Orçamento duplicado | Chave única com canal; soma por canal = consolidado |
| Rateio implícito da CORP | CORP sem canal; nenhuma despesa corporativa atribuída a canal |
| Realizado após o corte | Nenhum fato realizado depois de 30/09/2026; forecast só out-dez/2026 |

## 5. Limitação conhecida

O custo do centro de distribuição (CORP/`LOGISTICA`) atende lojas e digital, mas não é rateado. A margem de contribuição dos canais digitais, portanto, não inclui armazenagem nem a equipe do CD. Isso é intencional e está documentado; um rateio, se desejado, deve ser feito na camada analítica com regra explícita.
