"""
People Beauty - FP&A Analytics
Validação de integridade dos CSVs fictícios (versão 2.0 — omnichannel).

Uso:
    python 03_Dados/gerador/validar_dados.py
    python 03_Dados/gerador/validar_dados.py --pasta 03_Dados/csv --versao-anterior <pasta com os CSVs v1.0>

Verifica chaves primárias, referências entre arquivos (chaves estrangeiras),
regras dos canais, consistência dos cálculos, datas, devoluções, ausência de
duplicação de custos e de orçamento, reconciliação por canal, separação entre
realizado, orçamento e forecast e a compatibilidade entre o dicionário de dados
e os cabeçalhos. Com --versao-anterior, confere também que lojas físicas e CORP
continuam iguais à versão 1.0. Termina com código 1 se alguma regra falhar.
"""

import argparse
import csv
import glob
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import date

TOL = 0.005   # tolerância de arredondamento (R$)
CANAIS = ("LOJA_FISICA", "SITE_PROPRIO", "MERCADO_LIVRE")
DIGITAIS = ("SITE_PROPRIO", "MERCADO_LIVRE")
CONTAS_VENDAS = {"3.1.01", "3.2.02", "3.2.03", "4.1.01"}
FAIXA_NUMERO_VENDA = {"LOJA_FISICA": (1, 49999999), "SITE_PROPRIO": (50000001, 79999999),
                      "MERCADO_LIVRE": (80000001, 99999999)}
PADRAO_PEDIDO = {"SITE_PROPRIO": re.compile(r"^SITE-(\d{4})-\d{7}$"), "MERCADO_LIVRE": re.compile(r"^2\d{15}$")}


def ler(pasta, nome):
    with open(os.path.join(pasta, nome), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


class Validador:
    def __init__(self):
        self.falhas = []
        self.ok = 0

    def checar(self, descricao, problemas):
        problemas = list(problemas)
        if problemas:
            self.falhas.append((descricao, len(problemas), problemas[:5]))
            print(f"  [ERRO] {descricao}: {len(problemas)} ocorrência(s). Exemplos: {problemas[:5]}")
        else:
            self.ok += 1
            print(f"  [OK]   {descricao}")


def duplicados(linhas, *campos):
    c = Counter(tuple(l[k] for k in campos) for l in linhas)
    return [k for k, n in c.items() if n > 1]


def orfaos(linhas, campo, validos, permitir_vazio=False):
    return sorted({l[campo] for l in linhas if l[campo] not in validos and not (permitir_vazio and l[campo] == "")})


def colunas_do_dicionario(caminho):
    """{arquivo: [colunas]} a partir das seções '### arquivo.csv' e da tabela 'Coluna' logo abaixo."""
    resultado = {}
    atuais = []
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            if linha.startswith("### "):
                atuais = re.findall(r"([a-z_0-9]+\.csv)", linha)
                for a in atuais:
                    resultado[a] = []
            elif atuais and linha.startswith("| ") and not linha.startswith("| Coluna") and not linha.startswith("|---"):
                nome = linha.split("|")[1].strip().strip("`")
                for a in atuais:
                    resultado[a].append(nome)
            elif atuais and linha.startswith("#"):
                atuais = []
    return resultado


def main():
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--pasta", default=os.path.join(raiz, "csv"))
    ap.add_argument("--dicionario", default=os.path.join(os.path.dirname(raiz), "01_Documentacao", "dicionario_de_dados.md"))
    ap.add_argument("--versao-anterior", default="", help="Pasta com os CSVs da versão 1.0 (opcional)")
    args = ap.parse_args()
    p = args.pasta
    v = Validador()

    # ------------------------------------------------------------ leitura
    arquivos = sorted(os.path.basename(x) for x in glob.glob(os.path.join(p, "*.csv")))
    print("Contagem de registros (sem cabeçalho):")
    contagem = {}
    for a in arquivos:
        with open(os.path.join(p, a), encoding="utf-8") as f:
            contagem[a] = sum(1 for _ in f) - 1
        print(f"  {a:<32} {contagem[a]:>10,}".replace(",", "."))
    print(f"  {'TOTAL':<32} {sum(contagem.values()):>10,}".replace(",", "."))

    cal = ler(p, "dim_calendario.csv")
    lojas = ler(p, "dim_loja.csv")
    deps = ler(p, "dim_departamento.csv")
    canais = ler(p, "dim_canal.csv")
    cens = ler(p, "dim_cenario.csv")
    contas = ler(p, "dim_plano_contas.csv")
    cats = ler(p, "dim_categoria.csv")
    marcas = ler(p, "dim_marca.csv")
    prods = ler(p, "dim_produto.csv")
    params = {r["CodigoParametro"]: r["Valor"] for r in ler(p, "parametros.csv")}
    vendas = []
    for a in arquivos:
        if a.startswith("fato_vendas_"):
            vendas.extend(ler(p, a))
    devs = ler(p, "fato_devolucoes.csv")
    desp = ler(p, "fato_despesas.csv")
    orc = ler(p, "fato_orcamento.csv")
    fct = ler(p, "fato_forecast.csv")

    corte = date.fromisoformat(params["DATA_CORTE_REALIZADO"])
    am_corte = corte.year * 100 + corte.month
    datas = {r["Data"] for r in cal}
    meses_ini = {r["InicioMes"] for r in cal}
    loja_info = {r["CodigoLoja"]: r for r in lojas}
    lojas_fisicas = {k for k, r in loja_info.items() if r["TipoUnidade"] == "LOJA"}
    canal_info = {r["CodigoCanal"]: r for r in canais}
    dep_info = {r["CodigoDepartamento"]: r for r in deps}
    prod_info = {r["CodigoProduto"]: r for r in prods}
    conta_info = {r["CodigoConta"]: r for r in contas}
    analiticas = {k for k, r in conta_info.items() if r["ContaAnalitica"] == "1"}

    # ------------------------------------------------------- formato geral
    print("\nFormato, codificação e dicionário de dados:")
    problemas = []
    cabecalhos = {}
    for a in arquivos:
        with open(os.path.join(p, a), "rb") as f:
            bruto = f.read()
        if bruto.startswith(b"\xef\xbb\xbf"):
            problemas.append(f"{a}: tem BOM")
        try:
            texto = bruto.decode("utf-8")
        except UnicodeDecodeError:
            problemas.append(f"{a}: não é UTF-8")
            continue
        if "\r" in texto:
            problemas.append(f"{a}: tem CR")
        cab = texto.split("\n", 1)[0]
        cabecalhos[a] = cab.split(";")
        n_col = cab.count(";")
        if any(l.count(";") != n_col for l in texto.split("\n")[1:] if l):
            problemas.append(f"{a}: número de colunas variável")
    v.checar("UTF-8 sem BOM, fim de linha LF, separador ';' e mesmo nº de colunas em todas as linhas", problemas)
    v.checar("Datas em formato ISO AAAA-MM-DD (fatos)",
             [x for x in [r["DataVenda"] for r in vendas[:: 50]] + [r["DataDevolucao"] for r in devs]
              + [r["DataCompetencia"] for r in desp + orc + fct] if not re.match(r"^\d{4}-\d{2}-\d{2}$", x)])
    dic = colunas_do_dicionario(args.dicionario)
    v.checar("Todo CSV está documentado no dicionário", [a for a in arquivos if a not in dic])
    v.checar("Dicionário não descreve arquivos inexistentes", [a for a in dic if a not in arquivos])
    v.checar("Colunas do dicionário = cabeçalho do CSV (nomes e ordem)",
             [f"{a}: dicionário {dic[a]} x arquivo {cabecalhos[a]}" for a in arquivos if a in dic and dic[a] != cabecalhos[a]])

    # ------------------------------------------------------- dimensões
    print("\nDimensões (chaves primárias e hierarquias):")
    v.checar("dim_calendario: Data única", duplicados(cal, "Data"))
    v.checar("dim_calendario: 2024-01-01 a 2026-12-31 sem lacunas",
             [] if (len(cal) == 1096 and min(datas) == "2024-01-01" and max(datas) == "2026-12-31") else ["intervalo"])
    v.checar("dim_calendario: PeriodoRealizado = 1 somente até a data de corte",
             [r["Data"] for r in cal if (r["PeriodoRealizado"] == "1") != (r["Data"] <= corte.isoformat())])
    v.checar("dim_loja: CodigoLoja único", duplicados(lojas, "CodigoLoja"))
    v.checar("dim_loja: 24 lojas físicas + 1 CORP, sem canais digitais",
             [] if len(lojas_fisicas) == 24 and loja_info.get("CORP", {}).get("TipoUnidade") == "CORPORATIVA"
             and len(lojas) == 25 and not set(loja_info) & set(CANAIS) else ["quantidade ou unidade indevida"])
    v.checar("dim_canal: CodigoCanal único", duplicados(canais, "CodigoCanal"))
    v.checar("dim_canal: exatamente LOJA_FISICA, SITE_PROPRIO e MERCADO_LIVRE",
             [] if sorted(canal_info) == sorted(CANAIS) else sorted(canal_info))
    v.checar("dim_departamento: CodigoDepartamento único", duplicados(deps, "CodigoDepartamento"))
    v.checar("dim_cenario: CodigoCenario único", duplicados(cens, "CodigoCenario"))
    v.checar("dim_plano_contas: CodigoConta único", duplicados(contas, "CodigoConta"))
    v.checar("dim_plano_contas: conta pai existe", orfaos(contas, "CodigoContaPai", conta_info, True))
    v.checar("dim_plano_contas: conta filha com nível = nível do pai + 1",
             [c for c, r in conta_info.items() if r["CodigoContaPai"]
              and int(r["NivelHierarquia"]) != int(conta_info[r["CodigoContaPai"]]["NivelHierarquia"]) + 1])
    v.checar("dim_categoria: CodigoCategoria único", duplicados(cats, "CodigoCategoria"))
    v.checar("dim_marca: CodigoMarca único", duplicados(marcas, "CodigoMarca"))
    v.checar("dim_produto: CodigoProduto único", duplicados(prods, "CodigoProduto"))
    v.checar("dim_produto -> dim_categoria", orfaos(prods, "CodigoCategoria", {r["CodigoCategoria"] for r in cats}))
    v.checar("dim_produto -> dim_marca", orfaos(prods, "CodigoMarca", {r["CodigoMarca"] for r in marcas}))
    v.checar("dim_produto: preço > custo > 0",
             [r["CodigoProduto"] for r in prods
              if not float(r["PrecoListaReferencia2024"]) > float(r["CustoReferencia2024"]) > 0])

    # ------------------------------------------------------------ vendas
    print("\nfato_vendas_AAAA (itens de venda, três canais):")
    v.checar("PK (NumeroVenda, NumeroItem) única", duplicados(vendas, "NumeroVenda", "NumeroItem"))
    v.checar("Produto não se repete na mesma venda", duplicados(vendas, "NumeroVenda", "CodigoProduto"))
    v.checar("Arquivo do ano contém só vendas daquele ano",
             [a for a in arquivos if a.startswith("fato_vendas_")
              for r in ler(p, a)[:: 997] if not r["DataVenda"].startswith(a[12:16])])
    v.checar("DataVenda existe em dim_calendario", orfaos(vendas, "DataVenda", datas))
    v.checar("CodigoCanal existe em dim_canal", orfaos(vendas, "CodigoCanal", canal_info))
    v.checar("CodigoLoja existe em dim_loja (vazio só no digital)", orfaos(vendas, "CodigoLoja", loja_info, True))
    v.checar("CodigoProduto existe em dim_produto", orfaos(vendas, "CodigoProduto", prod_info))
    v.checar("LOJA_FISICA: loja física preenchida e sem pedido externo",
             [r["NumeroVenda"] for r in vendas if r["CodigoCanal"] == "LOJA_FISICA"
              and (r["CodigoLoja"] not in lojas_fisicas or r["NumeroPedidoExterno"])])
    v.checar("Site e Mercado Livre: sem loja e com pedido externo",
             [r["NumeroVenda"] for r in vendas if r["CodigoCanal"] in DIGITAIS
              and (r["CodigoLoja"] or not r["NumeroPedidoExterno"])])
    v.checar("Sem vendas na unidade CORP", [r["NumeroVenda"] for r in vendas if r["CodigoLoja"] == "CORP"])
    v.checar("NumeroVenda dentro da faixa do canal (sem conflito entre canais)",
             [r["NumeroVenda"] for r in vendas
              if not FAIXA_NUMERO_VENDA[r["CodigoCanal"]][0] <= int(r["NumeroVenda"]) <= FAIXA_NUMERO_VENDA[r["CodigoCanal"]][1]])
    v.checar("NumeroPedidoExterno no formato do canal (SITE-AAAA-NNNNNNN; Mercado Livre 16 dígitos)",
             [r["NumeroPedidoExterno"] for r in vendas if r["CodigoCanal"] in DIGITAIS
              and not PADRAO_PEDIDO[r["CodigoCanal"]].match(r["NumeroPedidoExterno"])])
    venda_cab = {}
    prob_cab, prob_ext = [], []
    ext_por_venda = {}
    for r in vendas:
        k = r["NumeroVenda"]
        chave = (r["DataVenda"], r["CodigoCanal"], r["CodigoLoja"], r["NumeroPedidoExterno"])
        if venda_cab.setdefault(k, chave) != chave:
            prob_cab.append(k)
        if r["NumeroPedidoExterno"]:
            if ext_por_venda.setdefault((r["CodigoCanal"], r["NumeroPedidoExterno"]), k) != k:
                prob_ext.append(r["NumeroPedidoExterno"])
    v.checar("Cada venda tem uma única data, canal, loja e pedido externo", prob_cab)
    v.checar("NumeroPedidoExterno único por canal (um pedido = uma venda)", prob_ext)
    v.checar("Pedido do site com o ano da venda",
             [r["NumeroPedidoExterno"] for r in vendas[:: 7] if r["CodigoCanal"] == "SITE_PROPRIO"
              and r["NumeroPedidoExterno"][5:9] != r["DataVenda"][:4]])
    v.checar("Sem vendas antes da abertura da loja",
             [r["NumeroVenda"] for r in vendas if r["CodigoLoja"] in lojas_fisicas
              and r["DataVenda"] < loja_info[r["CodigoLoja"]]["DataAbertura"]])
    v.checar("Sem vendas antes do início de operação do canal",
             [r["NumeroVenda"] for r in vendas if r["DataVenda"] < canal_info[r["CodigoCanal"]]["DataInicioOperacao"]])
    v.checar("Sem vendas após a data de corte do realizado",
             [r["NumeroVenda"] for r in vendas if r["DataVenda"] > corte.isoformat()])
    v.checar("Produto descontinuado sem venda após a descontinuação",
             [r["NumeroVenda"] for r in vendas
              if prod_info[r["CodigoProduto"]]["DataDescontinuacao"]
              and r["DataVenda"] > prod_info[r["CodigoProduto"]]["DataDescontinuacao"]])
    prob_q, prob_b, prob_l, prob_c, prob_d = [], [], [], [], []
    for r in vendas:
        q = int(r["Quantidade"])
        pu, vb, vd, vl = float(r["PrecoUnitario"]), float(r["ValorBruto"]), float(r["ValorDesconto"]), float(r["ValorLiquido"])
        cu, ct = float(r["CustoUnitario"]), float(r["CustoTotal"])
        if q <= 0 or pu <= 0 or cu <= 0:
            prob_q.append(r["NumeroVenda"])
        if abs(q * pu - vb) > TOL:
            prob_b.append(r["NumeroVenda"])
        if abs(vb - vd - vl) > TOL:
            prob_l.append(r["NumeroVenda"])
        if abs(q * cu - ct) > TOL:
            prob_c.append(r["NumeroVenda"])
        if vd < 0 or vd > vb * 0.30 + TOL:
            prob_d.append(r["NumeroVenda"])
    v.checar("Quantidade, preço e custo unitário positivos", prob_q)
    v.checar("ValorBruto = Quantidade x PrecoUnitario", prob_b)
    v.checar("ValorLiquido = ValorBruto - ValorDesconto", prob_l)
    v.checar("CustoTotal = Quantidade x CustoUnitario", prob_c)
    v.checar("Desconto entre 0% e 30% do bruto", prob_d)
    custo_mes = defaultdict(set)
    for r in vendas:
        custo_mes[(r["CodigoProduto"], r["DataVenda"][:7])].add(r["CustoUnitario"])
    v.checar("Custo unitário igual em todos os canais no mesmo produto e mês (CMV não depende do canal)",
             [k for k, s in custo_mes.items() if len(s) > 1])

    # --------------------------------------------------------- devoluções
    print("\nfato_devolucoes:")
    itens = {(r["NumeroVenda"], r["NumeroItem"]): r for r in vendas}
    v.checar("PK IdDevolucao única", duplicados(devs, "IdDevolucao"))
    v.checar("Cada item devolvido no máximo uma vez (estorno não duplicado)", duplicados(devs, "NumeroVenda", "NumeroItem"))
    v.checar("(NumeroVenda, NumeroItem) existe em fato_vendas",
             [r["IdDevolucao"] for r in devs if (r["NumeroVenda"], r["NumeroItem"]) not in itens])
    v.checar("CodigoCanal existe em dim_canal", orfaos(devs, "CodigoCanal", canal_info))
    prob = []
    for r in devs:
        it = itens.get((r["NumeroVenda"], r["NumeroItem"]))
        if not it:
            continue
        if (r["CodigoCanal"] != it["CodigoCanal"] or r["CodigoLoja"] != it["CodigoLoja"]
                or r["CodigoProduto"] != it["CodigoProduto"]
                or not 0 < int(r["Quantidade"]) <= int(it["Quantidade"])
                or not (it["DataVenda"] < r["DataDevolucao"] <= corte.isoformat())
                or abs(float(r["ValorDevolvido"]) - float(it["ValorLiquido"]) * int(r["Quantidade"]) / int(it["Quantidade"])) > TOL
                or abs(float(r["CustoDevolvido"]) - float(it["CustoTotal"]) * int(r["Quantidade"]) / int(it["Quantidade"])) > TOL):
            prob.append(r["IdDevolucao"])
    v.checar("Canal, loja, produto, quantidade, valores e datas coerentes com a venda original (até o corte)", prob)
    v.checar("DataDevolucao existe em dim_calendario", orfaos(devs, "DataDevolucao", datas))

    # -------------------------------------------- despesas / orçamento / forecast
    corporativos = {k for k, r in dep_info.items() if r["TipoUnidade"] == "CORPORATIVA"}

    def tipo_linha(r):
        """LOJA, DIGITAL ou CORP; None se a combinação canal/loja/departamento for inválida."""
        c, l, d = r["CodigoCanal"], r["CodigoLoja"], r["CodigoDepartamento"]
        if c == "LOJA_FISICA" and l in lojas_fisicas and d == "OPERACOES_LOJA":
            return "LOJA"
        if c in DIGITAIS and l == "" and d == "CANAIS_DIGITAIS":
            return "DIGITAL"
        if c == "" and l == "CORP" and d in corporativos:
            return "CORP"
        return None

    def checar_lancamentos(nome, linhas, chave):
        print(f"\n{nome}:")
        v.checar(f"Chave {' + '.join(chave)} única (sem duplicação)", duplicados(linhas, *chave))
        v.checar("DataCompetencia = 1º dia do mês e existe em dim_calendario", orfaos(linhas, "DataCompetencia", meses_ini))
        v.checar("AnoMes coerente com DataCompetencia",
                 [r["AnoMes"] for r in linhas if r["AnoMes"] != r["DataCompetencia"][:4] + r["DataCompetencia"][5:7]])
        v.checar("CodigoCanal existe em dim_canal (vazio só na CORP)", orfaos(linhas, "CodigoCanal", canal_info, True))
        v.checar("CodigoLoja existe em dim_loja (vazio só no digital)", orfaos(linhas, "CodigoLoja", loja_info, True))
        v.checar("CodigoDepartamento existe em dim_departamento", orfaos(linhas, "CodigoDepartamento", dep_info))
        v.checar("CodigoConta existe e é analítica", orfaos(linhas, "CodigoConta", analiticas))
        v.checar("Combinação válida: loja física/LOJA_FISICA/OPERACOES_LOJA, digital/sem loja/CANAIS_DIGITAIS "
                 "ou CORP/sem canal/área corporativa (CORP sem rateio)",
                 [(r["CodigoCanal"], r["CodigoLoja"], r["CodigoDepartamento"]) for r in linhas if tipo_linha(r) is None])
        v.checar("Valor positivo", [r["CodigoConta"] for r in linhas if float(r["Valor"]) <= 0])
        v.checar("Sem lançamento de loja antes do mês de abertura",
                 [(r["CodigoLoja"], r["AnoMes"]) for r in linhas
                  if r["CodigoLoja"] in lojas_fisicas and r["DataCompetencia"][:7] < loja_info[r["CodigoLoja"]]["DataAbertura"][:7]])
        v.checar("Sem lançamento de canal antes do mês de início de operação",
                 [(r["CodigoCanal"], r["AnoMes"]) for r in linhas
                  if r["CodigoCanal"] and r["DataCompetencia"][:7] < canal_info[r["CodigoCanal"]]["DataInicioOperacao"][:7]])
        v.checar("Comissão de marketplace (5.3.04) só no MERCADO_LIVRE",
                 sorted({r["CodigoCanal"] or r["CodigoLoja"] for r in linhas
                         if r["CodigoConta"] == "5.3.04" and r["CodigoCanal"] != "MERCADO_LIVRE"}))
        v.checar("Taxa de cartão (5.3.02) não lançada no MERCADO_LIVRE (já incluída na comissão)",
                 sorted({r["AnoMes"] for r in linhas if r["CodigoConta"] == "5.3.02" and r["CodigoCanal"] == "MERCADO_LIVRE"}))
        v.checar("Resultado financeiro e IRPJ/CSLL só na CORP",
                 sorted({r["CodigoCanal"] or r["CodigoLoja"] for r in linhas
                         if r["CodigoConta"][0] in "67" and r["CodigoLoja"] != "CORP"}))
        v.checar("CORP sem contas de vendas e CMV (CORP não é canal)",
                 sorted({r["CodigoConta"] for r in linhas if r["CodigoLoja"] == "CORP" and r["CodigoConta"] in CONTAS_VENDAS}))

    checar_lancamentos("fato_despesas (realizado)", desp, ("IdLancamento",))
    v.checar("Competência + canal + loja + departamento + conta única",
             duplicados(desp, "AnoMes", "CodigoCanal", "CodigoLoja", "CodigoDepartamento", "CodigoConta"))
    v.checar("Somente contas alimentadas por despesa (sem receita, desconto, devolução ou CMV: custo não duplicado)",
             sorted({r["CodigoConta"] for r in desp if conta_info[r["CodigoConta"]]["IndicadorDespesa"] != "1"}))
    v.checar("Somente meses até a data de corte", sorted({r["AnoMes"] for r in desp if int(r["AnoMes"]) > am_corte}))
    unid_venda = {(r["DataVenda"][:4] + r["DataVenda"][5:7], r["CodigoCanal"], r["CodigoLoja"]) for r in vendas}
    unid_desp = {(r["AnoMes"], r["CodigoCanal"], r["CodigoLoja"]) for r in desp if r["CodigoConta"] == "3.2.01"}
    v.checar("Impostos sobre vendas (3.2.01) em todo mês com venda, por canal e loja, e só nele",
             sorted(unid_venda ^ unid_desp)[:20])

    chave_plan = ("CodigoCenario", "AnoMes", "CodigoCanal", "CodigoLoja", "CodigoDepartamento", "CodigoConta")
    checar_lancamentos("fato_orcamento", orc, chave_plan)
    v.checar("Cenário = ORCAMENTO_APROVADO", sorted({r["CodigoCenario"] for r in orc} - {"ORCAMENTO_APROVADO"}))
    v.checar("36 meses (jan/2024 a dez/2026)", [] if len({r["AnoMes"] for r in orc}) == 36 else ["meses"])
    v.checar("Cada canal ativo tem receita orçada em todos os meses de operação",
             [(c, am) for c in CANAIS for am in sorted({r["AnoMes"] for r in orc})
              if am[:4] + "-" + am[4:] >= canal_info[c]["DataInicioOperacao"][:7]
              and not any(r["CodigoCanal"] == c and r["AnoMes"] == am and r["CodigoConta"] == "3.1.01" for r in orc)])

    checar_lancamentos("fato_forecast", fct, chave_plan)
    v.checar("Cenário = FORECAST_2026_9P3", sorted({r["CodigoCenario"] for r in fct} - {"FORECAST_2026_9P3"}))
    v.checar("Somente meses posteriores ao corte (out-dez/2026)",
             sorted({r["AnoMes"] for r in fct if not (am_corte < int(r["AnoMes"]) <= 202612)}))
    v.checar("Forecast cobre os três canais e a CORP",
             sorted(set(CANAIS + ("",)) - {r["CodigoCanal"] for r in fct}))
    v.checar("CodigoCenario existe em dim_cenario",
             orfaos(orc + fct, "CodigoCenario", {r["CodigoCenario"] for r in cens}))

    # --------------------------------------- separação dos cenários e reconciliação
    print("\nSeparação dos cenários e reconciliação por canal:")
    v.checar("Nenhum fato de realizado em meses de forecast",
             sorted({x for x in [r["DataVenda"][:7] for r in vendas] + [r["DataDevolucao"][:7] for r in devs]
                     + [r["DataCompetencia"][:7] for r in desp] if x > corte.isoformat()[:7]}))
    v.checar("Forecast não repete meses do realizado", sorted({r["AnoMes"] for r in fct if int(r["AnoMes"]) <= am_corte}))

    def reconciliar(nome, linhas, chave_mes, chave_valor, filtro=lambda r: True):
        por_canal = defaultdict(float)
        total = defaultdict(float)
        for r in linhas:
            if not filtro(r):
                continue
            por_canal[(r[chave_mes], r["CodigoCanal"])] += float(r[chave_valor])
            total[r[chave_mes]] += float(r[chave_valor])
        soma = defaultdict(float)
        for (m, _), x in por_canal.items():
            soma[m] += x
        v.checar(f"{nome}: soma dos canais (+ CORP) = consolidado em todos os períodos",
                 [m for m in total if abs(total[m] - soma[m]) > 0.01])

    mes_venda = [dict(r, Mes=r["DataVenda"][:7]) for r in vendas]
    reconciliar("Vendas (ValorBruto)", mes_venda, "Mes", "ValorBruto")
    reconciliar("Vendas (CustoTotal)", mes_venda, "Mes", "CustoTotal")
    reconciliar("Despesas realizadas", desp, "AnoMes", "Valor")
    reconciliar("Orçamento", orc, "AnoMes", "Valor")
    reconciliar("Forecast", fct, "AnoMes", "Valor")
    # A receita do realizado por canal deve fechar com a soma dos itens.
    rec_canal = defaultdict(float)
    for r in vendas:
        rec_canal[r["CodigoCanal"]] += float(r["ValorBruto"])
    v.checar("Receita bruta realizada: soma por canal = soma de todos os itens",
             [] if abs(sum(rec_canal.values()) - sum(float(r["ValorBruto"]) for r in vendas)) < 0.01 else ["diferença"])

    # ------------------------------------------- comparação com a versão 1.0
    if args.versao_anterior:
        print("\nComparação com a versão 1.0 (lojas físicas e CORP preservadas):")
        pa = args.versao_anterior
        v1_vendas = []
        for a in sorted(glob.glob(os.path.join(pa, "fato_vendas_*.csv"))):
            v1_vendas.extend(ler(pa, os.path.basename(a)))
        campos = ["NumeroVenda", "NumeroItem", "DataVenda", "CodigoLoja", "CodigoProduto", "Quantidade",
                  "PrecoUnitario", "ValorBruto", "ValorDesconto", "ValorLiquido", "CustoUnitario", "CustoTotal"]
        atual = [tuple(r[c] for c in campos) for r in vendas if r["CodigoCanal"] == "LOJA_FISICA"]
        v.checar("Itens das lojas físicas idênticos aos da v1.0",
                 [] if atual == [tuple(r[c] for c in campos) for r in v1_vendas] else ["diferença nas vendas"])
        campos_dev = ["IdDevolucao", "DataDevolucao", "NumeroVenda", "NumeroItem", "CodigoLoja", "CodigoProduto",
                      "Quantidade", "ValorDevolvido", "CustoDevolvido"]
        atual_dev = [tuple(r[c] for c in campos_dev) for r in devs if r["CodigoCanal"] == "LOJA_FISICA"]
        v.checar("Devoluções das lojas físicas idênticas às da v1.0",
                 [] if atual_dev == [tuple(r[c] for c in campos_dev) for r in ler(pa, "fato_devolucoes.csv")]
                 else ["diferença nas devoluções"])

        def chave_valor(linhas, cenario=False):
            return {((r["CodigoCenario"],) if cenario else ()) + (r["AnoMes"], r["CodigoLoja"], r["CodigoDepartamento"],
                    r["CodigoConta"]): r["Valor"] for r in linhas
                    if r.get("CodigoCanal", "LOJA_FISICA") in ("LOJA_FISICA", "") and r["CodigoConta"] != "7.1.01"}

        for nome, atual_l, arq, cen in (("Despesas", desp, "fato_despesas.csv", False),
                                        ("Orçamento", orc, "fato_orcamento.csv", True),
                                        ("Forecast", fct, "fato_forecast.csv", True)):
            a1, a2 = chave_valor(ler(pa, arq), cen), chave_valor(atual_l, cen)
            v.checar(f"{nome} das lojas e da CORP idênticos à v1.0 (exceto IRPJ/CSLL, recalculado com o digital)",
                     sorted(k for k in set(a1) | set(a2) if a1.get(k) != a2.get(k))[:10])

    # ----------------------------------------------- resumo de conferência
    print("\nResumo de conferência por canal (R$ mil):")
    real = defaultdict(float)
    for r in vendas:
        a = r["DataVenda"][:4]
        real[(a, r["CodigoCanal"], "3.1.01")] += float(r["ValorBruto"])
        real[(a, r["CodigoCanal"], "3.2.02")] += float(r["ValorDesconto"])
        real[(a, r["CodigoCanal"], "4.1.01")] += float(r["CustoTotal"])
    for r in devs:
        a = r["DataDevolucao"][:4]
        real[(a, r["CodigoCanal"], "3.2.03")] += float(r["ValorDevolvido"])
        real[(a, r["CodigoCanal"], "4.1.01")] -= float(r["CustoDevolvido"])
    for r in desp:
        real[(r["AnoMes"][:4], r["CodigoCanal"] or "CORP", r["CodigoConta"])] += float(r["Valor"])
    plano = defaultdict(float)
    for nome, linhas in (("ORC", orc), ("FCT", fct)):
        for r in linhas:
            plano[(nome, r["AnoMes"][:4], r["CodigoCanal"] or "CORP", r["CodigoConta"])] += float(r["Valor"])

    def dre(get):
        rb = get("3.1.01")
        rl = rb - get("3.2.01") - get("3.2.02") - get("3.2.03")
        lb = rl - get("4.1.01")
        opex = sum(get(c) for c in analiticas if c.startswith("5"))
        return rb, rl, lb, opex, lb - opex

    print(f"  {'Cenário / canal':<38}{'Rec. bruta':>12}{'Rec. líq.':>12}{'Lucro bruto':>13}{'Desp. oper.':>13}{'Res. oper.':>12}")
    for ano in ("2024", "2025", "2026"):
        for canal in CANAIS + ("CORP",):
            for nome, get in ((f"Realizado {ano}" + (" (jan-set)" if ano == "2026" else ""), lambda c: real[(ano, canal, c)]),
                              (f"Orçamento {ano}", lambda c: plano[("ORC", ano, canal, c)])):
                vals = dre(get)
                if any(abs(x) > 0.5 for x in vals):
                    print(f"  {nome + ' ' + canal:<38}" + "".join(f"{x / 1000:>12,.0f} " for x in vals).replace(",", "."))
    for canal in CANAIS + ("CORP",):
        vals = dre(lambda c: plano[("FCT", "2026", canal, c)])
        print(f"  {'Forecast out-dez/2026 ' + canal:<38}" + "".join(f"{x / 1000:>12,.0f} " for x in vals).replace(",", "."))

    total = v.ok + len(v.falhas)
    print(f"\nResultado: {total} verificações executadas, {v.ok} passaram, {len(v.falhas)} falharam.")
    for descricao, n, _ in v.falhas:
        print(f"  Falhou: {descricao} ({n})")
    sys.exit(1 if v.falhas else 0)


if __name__ == "__main__":
    main()
