from ox_script import *

# Rascunho para execucao futura na POSTEK.
# Ainda depende de confirmar como a balanca envia dados para a impressora.

excel_path = "produtos_parafusos.xlsx"
produto_atual = None
peso_total_g = 0
quantidade = 0
valor_total = 0


def selecionar_produto(value):
    global produto_atual
    produto_atual = value


def calcular_quantidade_por_peso(peso_total, peso_unitario):
    return int(float(peso_total) / float(peso_unitario))


def calcular_valor_total(quantidade_total, preco_unitario):
    return round(float(quantidade_total) * float(preco_unitario), 2)


def imprimir_etiqueta():
    # Depois que o layout do BarTender estiver pronto, vamos substituir
    # "layout_parafusos.txt" pelo arquivo exportado da etiqueta.
    cmd = PTK_UpdateAllFormVariables(
        "layout_parafusos.txt",
        Input1=str(produto_atual["sku"]),
        Input2=str(produto_atual["codigo_barras"]),
        Input3=str(produto_atual["descricao"]),
        Input4=str(produto_atual["medidas"]),
        Input5=str(quantidade),
        Input6=str(peso_total_g),
        Input7=str(produto_atual["preco_unitario"]),
        Input8=str(valor_total),
    )
    PTK_SendCmdToPrinter(cmd)


controller = PTK_UIInit(
    PTK_UIPage(
        PTK_UIText(title="Calculo de parafusos"),
        PTK_UIText(title="Aguardando definicao da balanca"),
        PTK_UIButton(title="Imprimir", Onpressed=imprimir_etiqueta),
    ),
    require_execute_confirmation=False,
)
