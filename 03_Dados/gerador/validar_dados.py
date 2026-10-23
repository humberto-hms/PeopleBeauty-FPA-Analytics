"""
People Beauty - FP&A Analytics
Validação de integridade dos CSVs fictícios.

Uso:
    python 03_Dados/gerador/validar_dados.py [--pasta 03_Dados/csv]

Verifica chaves primárias, referências entre arquivos (chaves estrangeiras),
consistência dos cálculos e regras de negócio. Imprime a contagem de
registros de cada arquivo e termina com código 1 se alguma regra falhar.
"""

import argparse
import csv
import glob
import os
import sys
from collections import Counter, defaultdict
from datetime import date

TOL = 0.005   # tolerância de arredondamento (R$)


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


def main():
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--pasta", default=os.path.join(raiz, "csv"))
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
    prod_info = {r["CodigoProduto"]: r for r in prods}
    conta_info = {r["CodigoConta"]: r for r in contas}
    analiticas = {k for k, r in conta_info.items() if r["ContaAnalitica"] == "1"}

    # ------------------------------------------------------- formato geral
    print("\nFormato e codificação:")
    problemas = []
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
        cab = texto.split("\n", 1)[0]
        n_col = cab.count(";")
        if any(l.count(";") != n_col for l in texto.split("\n")[1:] if l):
            problemas.append(f"{a}: número de colunas variável")
    v.checar("UTF-8 sem BOM, separador ';' e mesmo nº de colunas em todas as linhas", problemas)
    v.checar("Datas em formato ISO AAAA-MM-DD (fatos)",
             [x for x in [r["DataVenda"] for r in vendas[:: 50]] + [r["DataDevolucao"] for r in devs]
              + [r["DataCompetencia"] for r in desp + orc + fct] if len(x) != 10 or x[4] != "-" or x[7] != "-"])

    # ------------------------------------------------------- dimensões
    print("\nDimensões (chaves primárias e hierarquias):")
    v.checar("dim_calendario: Data única", duplicados(cal, "Data"))
    v.checar("dim_calendario: 2024-01-01 a 2026-12-31 sem lacunas",
             [] if (len(cal) == 1096 and min(datas) == "2024-01-01" and max(datas) == "2026-12-31") else ["intervalo"])
    v.checar("dim_loja: CodigoLoja único", duplicados(lojas, "CodigoLoja"))
    v.checar("dim_loja: 24 lojas + 1 CORP",
             [] if len(lojas_fisicas) == 24 and loja_info.get("CORP", {}).get("TipoUnidade") == "CORPORATIVA"
             and len(lojas) == 25 else ["quantidade"])
    v.checar("dim_departamento: CodigoDepartamento único", duplicados(deps, "CodigoDepartamento"))
    v.checar("dim_cenario: CodigoCenario único", duplicados(cens, "CodigoCenario"))
    v.checar("dim_plano_contas: CodigoConta único", duplicados(contas, "CodigoConta"))
    v.checar("dim_plano_contas: conta pai existe", orfaos(contas, "CodigoContaPai", conta_info, True))
    v.checar("dim_categoria: CodigoCategoria único", duplicados(cats, "CodigoCategoria"))
    v.checar("dim_marca: CodigoMarca único", duplicados(marcas, "CodigoMarca"))
    v.checar("dim_produto: CodigoProduto único", duplicados(prods, "CodigoProduto"))
    v.checar("dim_produto -> dim_categoria", orfaos(prods, "CodigoCategoria", {r["CodigoCategoria"] for r in cats}))
    v.checar("dim_produto -> dim_marca", orfaos(prods, "CodigoMarca", {r["CodigoMarca"] for r in marcas}))
    v.checar("dim_produto: preço > custo > 0",
             [r["CodigoProduto"] for r in prods
              if not float(r["PrecoListaReferencia2024"]) > float(r["CustoReferencia2024"]) > 0])

    # ------------------------------------------------------------ vendas
    print("\nfato_vendas_AAAA (itens de cupom):")
    v.checar("PK (NumeroVenda, NumeroItem) única", duplicados(vendas, "NumeroVenda", "NumeroItem"))
    v.checar("Produto não se repete no mesmo cupom", duplicados(vendas, "NumeroVenda", "CodigoProduto"))
    v.checar("DataVenda existe em dim_calendario", orfaos(vendas, "DataVenda", datas))
    v.checar("CodigoLoja existe em dim_loja", orfaos(vendas, "CodigoLoja", loja_info))
    v.checar("CodigoProduto existe em dim_produto", orfaos(vendas, "CodigoProduto", prod_info))
    cupom = {}
    prob = []
    for r in vendas:
        k = r["NumeroVenda"]
        chave = (r["DataVenda"], r["CodigoLoja"])
        if cupom.setdefault(k, chave) != chave:
            prob.append(k)
    v.checar("Cada cupom tem uma única data e loja", prob)
    v.checar("Sem vendas na unidade CORP", [r["NumeroVenda"] for r in vendas if r["CodigoLoja"] not in lojas_fisicas])
    v.checar("Sem vendas antes da abertura da loja",
             [r["NumeroVenda"] for r in vendas if r["DataVenda"] < loja_info[r["CodigoLoja"]]["DataAbertura"]])
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

    # --------------------------------------------------------- devoluções
    print("\nfato_devolucoes:")
    itens = {(r["NumeroVenda"], r["NumeroItem"]): r for r in vendas}
    v.checar("PK IdDevolucao única", duplicados(devs, "IdDevolucao"))
    v.checar("Cada item devolvido no máximo uma vez", duplicados(devs, "NumeroVenda", "NumeroItem"))
    v.checar("(NumeroVenda, NumeroItem) existe em fato_vendas",
             [r["IdDevolucao"] for r in devs if (r["NumeroVenda"], r["NumeroItem"]) not in itens])
    prob = []
    for r in devs:
        it = itens.get((r["NumeroVenda"], r["NumeroItem"]))
        if not it:
            continue
        if (r["CodigoLoja"] != it["CodigoLoja"] or r["CodigoProduto"] != it["CodigoProduto"]
                or int(r["Quantidade"]) > int(it["Quantidade"]) or int(r["Quantidade"]) <= 0
                or not (it["DataVenda"] < r["DataDevolucao"] <= corte.isoformat())
                or abs(float(r["ValorDevolvido"]) - float(it["ValorLiquido"]) * int(r["Quantidade"]) / int(it["Quantidade"])) > TOL
                or abs(float(r["CustoDevolvido"]) - float(it["CustoTotal"]) * int(r["Quantidade"]) / int(it["Quantidade"])) > TOL):
            prob.append(r["IdDevolucao"])
    v.checar("Loja, produto, quantidade, valores e data coerentes com a venda (e até o corte)", prob)
    v.checar("DataDevolucao existe em dim_calendario", orfaos(devs, "DataDevolucao", datas))

    # -------------------------------------------- despesas / orçamento / forecast
    def checar_lancamentos(nome, linhas, chave):
        print(f"\n{nome}:")
        v.checar(f"Chave {chave} única", duplicados(linhas, *chave))
        v.checar("DataCompetencia = 1º dia do mês e existe em dim_calendario", orfaos(linhas, "DataCompetencia", meses_ini))
        v.checar("AnoMes coerente com DataCompetencia",
                 [r["AnoMes"] for r in linhas if r["AnoMes"] != r["DataCompetencia"][:4] + r["DataCompetencia"][5:7]])
        v.checar("CodigoLoja existe em dim_loja", orfaos(linhas, "CodigoLoja", loja_info))
        v.checar("CodigoDepartamento existe em dim_departamento",
                 orfaos(linhas, "CodigoDepartamento", {r["CodigoDepartamento"] for r in deps}))
        v.checar("CodigoConta existe e é analítica", orfaos(linhas, "CodigoConta", analiticas))
        v.checar("Lojas só usam OPERACOES_LOJA; CORP só usa áreas corporativas",
                 [(r["CodigoLoja"], r["CodigoDepartamento"]) for r in linhas
                  if (r["CodigoLoja"] == "CORP") == (r["CodigoDepartamento"] == "OPERACOES_LOJA")])
        v.checar("Valor positivo", [r["CodigoConta"] for r in linhas if float(r["Valor"]) <= 0])
        v.checar("Sem lançamento de loja antes do mês de abertura",
                 [(r["CodigoLoja"], r["AnoMes"]) for r in linhas
                  if r["CodigoLoja"] != "CORP" and r["DataCompetencia"][:7] < loja_info[r["CodigoLoja"]]["DataAbertura"][:7]])

    checar_lancamentos("fato_despesas (realizado)", desp, ("IdLancamento",))
    v.checar("Combinação competência + loja + departamento + conta única",
             duplicados(desp, "AnoMes", "CodigoLoja", "CodigoDepartamento", "CodigoConta"))
    v.checar("Somente contas alimentadas por despesa (IndicadorDespesa = 1)",
             sorted({r["CodigoConta"] for r in desp if conta_info[r["CodigoConta"]]["IndicadorDespesa"] != "1"}))
    v.checar("Somente meses até a data de corte", sorted({r["AnoMes"] for r in desp if int(r["AnoMes"]) > am_corte}))
    v.checar("Despesas financeiras e IR só na CORP",
             sorted({r["CodigoLoja"] for r in desp if r["CodigoConta"][0] in "67" and r["CodigoLoja"] != "CORP"}))

    chave_plan = ("CodigoCenario", "AnoMes", "CodigoLoja", "CodigoDepartamento", "CodigoConta")
    checar_lancamentos("fato_orcamento", orc, chave_plan)
    v.checar("Cenário = ORCAMENTO_APROVADO", sorted({r["CodigoCenario"] for r in orc} - {"ORCAMENTO_APROVADO"}))
    v.checar("36 meses (jan/2024 a dez/2026)", [] if len({r["AnoMes"] for r in orc}) == 36 else ["meses"])

    checar_lancamentos("fato_forecast", fct, chave_plan)
    v.checar("Cenário = FORECAST_2026_9P3", sorted({r["CodigoCenario"] for r in fct} - {"FORECAST_2026_9P3"}))
    v.checar("Somente meses posteriores ao corte (out-dez/2026)",
             sorted({r["AnoMes"] for r in fct if not (am_corte < int(r["AnoMes"]) <= 202612)}))
    v.checar("CodigoCenario existe em dim_cenario",
             orfaos(orc + fct, "CodigoCenario", {r["CodigoCenario"] for r in cens}))

    # ----------------------------------------------- resumo de conferência
    print("\nResumo de conferência (R$ mil, consolidado):")
    real = defaultdict(float)
    for r in vendas:
        a = r["DataVenda"][:4]
        real[(a, "3.1.01")] += float(r["ValorBruto"])
        real[(a, "3.2.02")] += float(r["ValorDesconto"])
        real[(a, "4.1.01")] += float(r["CustoTotal"])
    for r in devs:
        a = r["DataDevolucao"][:4]
        real[(a, "3.2.03")] += float(r["ValorDevolvido"])
        real[(a, "4.1.01")] -= float(r["CustoDevolvido"])
    for r in desp:
        real[(r["AnoMes"][:4], r["CodigoConta"])] += float(r["Valor"])
    plano = defaultdict(float)
    for r in orc:
        plano[("ORC", r["AnoMes"][:4], r["CodigoConta"])] += float(r["Valor"])
    for r in fct:
        plano[("FCT", r["AnoMes"][:4], r["CodigoConta"])] += float(r["Valor"])

    def dre(get):
        rb = get("3.1.01")
        rl = rb - get("3.2.01") - get("3.2.02") - get("3.2.03")
        lb = rl - get("4.1.01")
        opex = sum(get(c) for c in analiticas if c.startswith("5"))
        ro = lb - opex
        rliq = ro + get("6.1.01") - get("6.1.02") - get("7.1.01")
        return rb, rl, lb, opex, ro, rliq

    print(f"  {'Cenário':<26}{'Rec. bruta':>12}{'Rec. líq.':>12}{'Lucro bruto':>13}{'Desp. oper.':>13}{'Res. oper.':>12}{'Res. líq.':>12}")
    linhas_resumo = []
    for ano in ("2024", "2025", "2026"):
        linhas_resumo.append((f"Realizado {ano}" + (" (jan-set)" if ano == "2026" else ""), dre(lambda c: real[(ano, c)])))
        linhas_resumo.append((f"Orçamento {ano}", dre(lambda c: plano[("ORC", ano, c)])))
    linhas_resumo.append(("Forecast 2026 (out-dez)", dre(lambda c: plano[("FCT", "2026", c)])))
    for nome, vals in linhas_resumo:
        print(f"  {nome:<26}" + "".join(f"{x / 1000:>12,.0f} " for x in vals).replace(",", "."))

    print(f"\nResultado: {v.ok} verificações OK, {len(v.falhas)} com erro.")
    sys.exit(1 if v.falhas else 0)


if __name__ == "__main__":
    main()
