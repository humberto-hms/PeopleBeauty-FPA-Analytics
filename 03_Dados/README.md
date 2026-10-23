# 03_Dados

Dados fictícios de origem da People Beauty, prontos para carga em um Data Warehouse em modelo estrela no SQL Server.

> Todos os dados são **fictícios**, criados apenas para estudo e demonstração.

## Conteúdo

| Caminho | O que é |
|---|---|
| `csv/` | Os 16 arquivos CSV (9 de referência + 7 de fatos) |
| `PeopleBeauty_Dados_Ficticios.zip` | Pacote para download: CSVs + dicionário + regras + resultado da validação |
| `gerador/gerar_dados.py` | Gerador reprodutível (semente fixa) |
| `gerador/validar_dados.py` | Validação de integridade e contagem de registros |
| `validacao_resultado.txt` | Saída da última validação |

Documentação:

- [Dicionário de dados](../01_Documentacao/dicionario_de_dados.md): colunas, tipos, granularidade, chaves e relacionamentos.
- [Regras de geração](../01_Documentacao/regras_dados_ficticios.md): premissas de vendas, despesas, orçamento e forecast.

## Arquivos e registros

| Arquivo | Grão | Registros |
|---|---|---:|
| dim_calendario.csv | dia (2024-01-01 a 2026-12-31) | 1.096 |
| dim_loja.csv | unidade (24 lojas + CORP) | 25 |
| dim_departamento.csv | departamento | 8 |
| dim_cenario.csv | cenário | 3 |
| dim_plano_contas.csv | conta gerencial | 36 |
| dim_categoria.csv | categoria | 5 |
| dim_marca.csv | marca | 21 |
| dim_produto.csv | produto | 66 |
| parametros.csv | parâmetro | 4 |
| fato_vendas_2024.csv | item de cupom | 492.307 |
| fato_vendas_2025.csv | item de cupom | 527.882 |
| fato_vendas_2026.csv | item de cupom (até 30/09) | 387.127 |
| fato_devolucoes.csv | item devolvido | 16.126 |
| fato_despesas.csv | competência × unidade × departamento × conta (realizado) | 12.432 |
| fato_orcamento.csv | cenário × competência × unidade × departamento × conta | 16.938 |
| fato_forecast.csv | idem, só out-dez/2026 | 1.464 |
| **Total** | | **1.455.540** |

## Formato

UTF-8 sem BOM · separador `;` · decimal `.` · datas `AAAA-MM-DD` · cabeçalho na primeira linha · fim de linha LF.

Dica para o SQL Server (Windows): no `BULK INSERT`, use `FIELDTERMINATOR = ';'`, `ROWTERMINATOR = '0x0a'`, `FIRSTROW = 2` e `CODEPAGE = '65001'`.

## Separação dos cenários

- **Realizado:** `fato_vendas_AAAA`, `fato_devolucoes`, `fato_despesas`, de jan/2024 até a data de corte **30/09/2026**.
- **Orçamento:** `fato_orcamento` (`ORCAMENTO_APROVADO`), jan/2024 a dez/2026.
- **Forecast:** `fato_forecast` (`FORECAST_2026_9P3`), out-dez/2026. O ano completo do forecast = realizado jan-set + forecast out-dez.

## Como gerar e validar de novo

```
python 03_Dados/gerador/gerar_dados.py
python 03_Dados/gerador/validar_dados.py
```

Python 3.9+ sem bibliotecas externas. A geração leva cerca de 1 minuto e produz arquivos idênticos aos publicados. A validação confere 72 regras (chaves primárias, referências entre arquivos, cálculos e regras de negócio) e termina com erro se alguma falhar.

Status: dados gerados e validados. Banco, carga e análises ainda não iniciados.
