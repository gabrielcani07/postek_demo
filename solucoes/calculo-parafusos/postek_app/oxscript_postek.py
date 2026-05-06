from ox_script import *
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP


EXCEL_PATH = "produtos_parafusos.xlsx"
LAYOUT_PATH = "layout_parafusos.prn"

produtos = []
produto_atual = None
peso_total_g = Decimal("0")
quantidade = 0
sobra_g = Decimal("0")
valor_total = Decimal("0")


def decimal_ptbr(valor):
    texto = str(valor).strip().replace(",", ".")
    if texto == "":
        return Decimal("0")
    return Decimal(texto)


def moeda_ptbr(valor):
    return ("R$ " + format(valor, ".2f")).replace(".", ",")


def quantidade_formatada(valor):
    return str(valor) + " uni"


def peso_formatado(valor_g):
    if valor_g < Decimal("1000"):
        valor = valor_g.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
        texto = format(valor, "f").rstrip("0").rstrip(".")
        return texto.replace(".", ",") + " g"

    valor_kg = (valor_g / Decimal("1000")).quantize(
        Decimal("0.001"), rounding=ROUND_HALF_UP
    )
    return format(valor_kg, ".3f").replace(".", ",") + " kg"


def carregar_produtos():
    from openpyxl import load_workbook

    workbook = load_workbook(EXCEL_PATH, data_only=True)
    sheet = workbook.active
    cabecalho = [str(celula.value).strip() for celula in sheet[1]]

    lista = []
    for linha in sheet.iter_rows(min_row=2, values_only=True):
        if not linha or linha[0] is None:
            continue
        item = dict(zip(cabecalho, linha))
        lista.append(
            {
                "sku": str(item["sku"]),
                "tipo": str(item["tipo"]),
                "codigo_barras": str(item["codigo_barras"]),
                "descricao": str(item["descricao"]),
                "medidas": str(item["medidas"]),
                "peso_unitario_g": decimal_ptbr(item["peso_unitario_g"]),
                "preco_unitario": decimal_ptbr(item["preco_unitario"]),
            }
        )
    return lista


def nome_produto(produto):
    return produto["sku"] + " - " + produto["medidas"]


def selecionar_produto(value):
    global produto_atual
    if len(produtos) == 0:
        produto_atual = None
        return
    produto_atual = produtos[int(value)]
    atualizar_resumo()


def atualizar_peso(value):
    global peso_total_g
    global quantidade
    global sobra_g
    global valor_total

    if produto_atual is None:
        return

    peso_total_g = decimal_ptbr(peso_controller.value)
    if peso_total_g <= 0:
        quantidade = 0
        sobra_g = Decimal("0")
        valor_total = Decimal("0")
        atualizar_resumo()
        return

    quantidade_decimal = peso_total_g / produto_atual["peso_unitario_g"]
    quantidade = int(quantidade_decimal.to_integral_value(rounding=ROUND_FLOOR))
    peso_calculado = Decimal(quantidade) * produto_atual["peso_unitario_g"]
    sobra_g = peso_total_g - peso_calculado
    valor_total = (Decimal(quantidade) * produto_atual["preco_unitario"]).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    atualizar_resumo()


def atualizar_resumo():
    if produto_atual is None:
        resumo_controller.update("Nenhum produto carregado")
        return

    texto = (
        "SKU: " + produto_atual["sku"] + "\n"
        "Produto: " + produto_atual["descricao"] + "\n"
        "Medidas: " + produto_atual["medidas"] + "\n"
        "Peso unit.: " + str(produto_atual["peso_unitario_g"]) + " g\n"
        "Peso total: " + peso_formatado(peso_total_g) + "\n"
        "Quantidade: " + quantidade_formatada(quantidade) + "\n"
        "Valor total: " + moeda_ptbr(valor_total)
    )
    resumo_controller.update(texto)


def imprimir_etiqueta():
    if produto_atual is None:
        return

    atualizar_peso(peso_controller.value)
    cmd = PTK_UpdateAllFormVariables(
        LAYOUT_PATH,
        Input1=produto_atual["sku"],
        Input2=produto_atual["codigo_barras"],
        Input3=produto_atual["descricao"],
        Input4=produto_atual["medidas"],
        Input5=quantidade_formatada(quantidade),
        Input6=peso_formatado(peso_total_g),
        Input7=moeda_ptbr(produto_atual["preco_unitario"]),
        Input8=moeda_ptbr(valor_total),
    )
    PTK_SendCmdToPrinter(cmd)


if __name__ == "__main__":
    produtos = carregar_produtos()
    nomes_produtos = [nome_produto(produto) for produto in produtos]
    if len(produtos) > 0:
        produto_atual = produtos[0]

    controller = PTK_UIInit(
        PTK_UIPage(
            produto_controller := PTK_UIList(
                title="Produto",
                items=nomes_produtos,
                valueType="int",
                value=0,
                Onpressed=selecionar_produto,
            ),
            peso_controller := PTK_UIInput(
                title="Peso total em gramas",
                value="2500",
                Onsubmit=atualizar_peso,
            ),
            resumo_controller := PTK_UITextBox(title="Resumo", value="Carregando..."),
            PTK_UIButton(title="Imprimir", Onpressed=imprimir_etiqueta),
        ),
        require_execute_confirmation=False,
    )
    atualizar_peso(peso_controller.value)
