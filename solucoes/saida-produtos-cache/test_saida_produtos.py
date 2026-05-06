import json

from app import Inventory, ScanSession, build_print_lines, normalize_inventory_source, parse_products


def test_agrupa_bipagens_por_codigo():
    inventory = Inventory()
    inventory.products = parse_products(
        [
            {"codigo_barras": "789001", "produto": "Produto A"},
            {"codigo_barras": "789002", "produto": "Produto B"},
            {"codigo_barras": "789003", "produto": "Produto C"},
        ]
    )
    session = ScanSession()

    session.add("789001")
    session.add("789002")
    session.add("789001")
    session.add("789003")

    items = session.summary(inventory)

    assert [(item["code"], item["quantity"]) for item in items] == [
        ("789001", 2),
        ("789002", 1),
        ("789003", 1),
    ]


def test_gera_uma_linha_por_etiqueta():
    products = parse_products(
        [
            {
                "codigo_barras": "789001",
                "sku": "TXT-001",
                "tipo": "Camiseta",
                "descricao": "Camiseta basica",
                "medidas": "Tam M / Azul",
                "preco_unitario": "39.90",
                "composicao": "100% algodao",
            }
        ]
    )
    inventory = Inventory()
    inventory.products = products
    session = ScanSession()
    session.add("789001")
    session.add("789001")

    lines = build_print_lines(session.summary(inventory))

    assert len(lines) == 2
    first_label = json.loads(lines[0])
    assert first_label == {
        "Input1": "TXT-001",
        "Input2": "789001",
        "Input3": "Camiseta basica",
        "Input4": "Tam M / Azul",
        "Input5": "1 un",
        "Input6": "Camiseta",
        "Input7": "R$ 39,90",
        "Input8": "100% algodao",
    }


def test_converte_link_google_sheets_para_csv():
    source = "https://docs.google.com/spreadsheets/d/1zzlB_CjRyYvdNfOdZjh_5ifHF_bLw6QVgHRYK4Ro2iY/edit?usp=sharing"

    csv_source = normalize_inventory_source(source)

    assert csv_source == (
        "https://docs.google.com/spreadsheets/d/"
        "1zzlB_CjRyYvdNfOdZjh_5ifHF_bLw6QVgHRYK4Ro2iY/gviz/tq?tqx=out:csv&gid=0"
    )
