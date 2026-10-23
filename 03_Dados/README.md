# 03_Dados

Dados fictícios de origem da People Beauty (versão 2.0, omnichannel), prontos para carga em um Data Warehouse em modelo estrela no SQL Server.

> Todos os dados são **fictícios**, criados apenas para estudo e demonstração. Não representam estatísticas reais da People Beauty nem do Mercado Livre.

## Conteúdo

| Caminho | O que é |
|---|---|
| `csv/` | Os 17 arquivos CSV (10 de referência + 7 de fatos) |
| `PeopleBeauty_Dados_Ficticios.zip` | Pacote v2.0 para download: CSVs + dicionário + regras + auditoria + validação |
| `versoes/PeopleBeauty_Dados_Ficticios_v1.0.zip` | Versão 1.0 preservada (somente lojas físicas) |
| `gerador/gerar_dados.py` | Gerador reprodutível (semente fixa) |
| `gerador/validar_dados.py` | Validação de integridade e contagem de registros |
| `validacao_resultado.txt` | Saída da última validação |

Documentação:

- [Dicionário de dados](../01_Documentacao/dicionario_de_dados.md): colunas, tipos, granularidade, chaves, relacionamentos e versões.
- [Regras de geração](../01_Documentacao/regras_dados_ficticios.md): premissas de vendas, canais, custos de marketplace, orçamento e forecast.
- [Auditoria omnichannel](../01_Documentacao/auditoria_omnichannel.md): situação da v1.0, impacto em chaves e o que foi preservado.

## Canais

| CodigoCanal | Canal | Onde está a venda |
|---|---|---|
| `LOJA_FISICA` | 24 lojas | `CodigoLoja` = `L001` … `L024` |
| `SITE_PROPRIO` | e-commerce próprio | sem loja, `NumeroPedidoExterno` = `SITE-AAAA-NNNNNNN` |
| `MERCADO_LIVRE` | marketplace (desde 01/04/2025) | sem loja, `NumeroPedidoExterno` de 16 dígitos |

A unidade `CORP` não é canal: tem só despesas corporativas, sem canal e sem rateio.

## Arquivos e registros

| Arquivo | Grão | Registros |
|---|---|---:|
| dim_calendario.csv | dia (2024-01-01 a 2026-12-31) | 1.096 |
| dim_canal.csv | canal comercial | 3 |
| dim_loja.csv | unidade (24 lojas + CORP) | 25 |
| dim_departamento.csv | departamento | 9 |
| dim_cenario.csv | cenário | 3 |
| dim_plano_contas.csv | conta gerencial | 40 |
| dim_categoria.csv | categoria | 5 |
| dim_marca.csv | marca | 21 |
| dim_produto.csv | produto | 66 |
| parametros.csv | parâmetro | 4 |
| fato_vendas_2024.csv | item vendido | 533.541 |
| fato_vendas_2025.csv | item vendido | 589.870 |
| fato_vendas_2026.csv | item vendido (até 30/09) | 447.237 |
| fato_devolucoes.csv | item devolvido | 22.316 |
| fato_despesas.csv | competência × canal/unidade × departamento × conta (realizado) | 12.895 |
| fato_orcamento.csv | cenário × competência × canal/unidade × departamento × conta | 17.681 |
| fato_forecast.csv | idem, só out-dez/2026 | 1.542 |
| **Total** | | **1.626.354** |

Itens de venda por canal: lojas físicas 1.407.316 (iguais à v1.0), site próprio 130.827, Mercado Livre 32.505.

## Formato

UTF-8 sem BOM · separador `;` · decimal `.` · datas `AAAA-MM-DD` · cabeçalho na primeira linha · fim de linha LF.

Dica para o SQL Server (Windows): no `BULK INSERT`, use `FIELDTERMINATOR = ';'`, `ROWTERMINATOR = '0x0a'`, `FIRSTROW = 2` e `CODEPAGE = '65001'`. As colunas `CodigoLoja` e `CodigoCanal` podem vir vazias; trate vazio como `NULL` antes de criar as chaves estrangeiras.

`fato_vendas_2025.csv` tem cerca de 52 MB. O GitHub mostra um aviso acima de 50 MB, mas aceita arquivos de até 100 MB.

## Separação dos cenários

- **Realizado:** `fato_vendas_AAAA`, `fato_devolucoes`, `fato_despesas`, de jan/2024 até a data de corte **30/09/2026**.
- **Orçamento:** `fato_orcamento` (`ORCAMENTO_APROVADO`), jan/2024 a dez/2026, por canal.
- **Forecast:** `fato_forecast` (`FORECAST_2026_9P3`), out-dez/2026, por canal. O ano completo do forecast = realizado jan-set + forecast out-dez.

## Como gerar e validar de novo

```
python 03_Dados/gerador/gerar_dados.py
python 03_Dados/gerador/validar_dados.py
```

Python 3.9+ sem bibliotecas externas. A geração produz arquivos idênticos aos publicados. A validação confere 118 regras (chaves primárias, referências entre arquivos, regras dos canais, cálculos, datas, devoluções, duplicidade de custos e orçamento, reconciliação por canal, separação dos cenários e dicionário x cabeçalhos) e termina com erro se alguma falhar.

Para conferir também que lojas físicas e CORP não mudaram em relação à v1.0 (5 regras a mais, 123 no total), descompacte o ZIP da v1.0 e rode:

```
python 03_Dados/gerador/validar_dados.py --versao-anterior <pasta>/PeopleBeauty_Dados_Ficticios/csv
```

Status: dados v2.0 gerados e validados. Banco, carga e análises ainda não iniciados.
