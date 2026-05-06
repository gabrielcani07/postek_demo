import csv
import json
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PRODUTOS_PATH = BASE_DIR / "dados" / "produtos_parafusos.csv"
SAIDA_DIR = BASE_DIR / "saida"


def decimal_ptbr(valor: str) -> Decimal:
    texto = str(valor or "").strip().replace(",", ".")
    if not texto:
        return Decimal("0")
    return Decimal(texto)


def calcular_quantidade(peso_total_g: Decimal, peso_unitario_g: Decimal) -> tuple[int, Decimal]:
    if peso_unitario_g <= 0:
        return 0, peso_total_g
    quantidade = int((peso_total_g / peso_unitario_g).to_integral_value(rounding=ROUND_FLOOR))
    peso_calculado = Decimal(quantidade) * peso_unitario_g
    sobra = peso_total_g - peso_calculado
    return quantidade, sobra


def calcular_valor_total(quantidade: int, preco_unitario: Decimal) -> Decimal:
    return (Decimal(quantidade) * preco_unitario).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def carregar_produtos() -> list[dict[str, str | Decimal]]:
    produtos = []
    with PRODUTOS_PATH.open(encoding="utf-8-sig", newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            produtos.append(
                {
                    "sku": linha["sku"],
                    "tipo": linha["tipo"],
                    "codigo_barras": linha["codigo_barras"],
                    "descricao": linha["descricao"],
                    "medidas": linha["medidas"],
                    "peso_unitario_g": decimal_ptbr(linha["peso_unitario_g"]),
                    "preco_unitario": decimal_ptbr(linha["preco_unitario"]),
                }
            )
    return produtos


def gerar_etiqueta(produto: dict[str, str | Decimal], peso_total_g: Decimal) -> dict[str, str | int]:
    quantidade, sobra_g = calcular_quantidade(peso_total_g, produto["peso_unitario_g"])
    valor_total = calcular_valor_total(quantidade, produto["preco_unitario"])
    return {
        "sku": str(produto["sku"]),
        "tipo": str(produto["tipo"]),
        "codigo_barras": str(produto["codigo_barras"]),
        "descricao": str(produto["descricao"]),
        "medidas": str(produto["medidas"]),
        "peso_total_g": str(peso_total_g),
        "peso_unitario_g": str(produto["peso_unitario_g"]),
        "quantidade": quantidade,
        "sobra_g": str(sobra_g),
        "preco_unitario": str(produto["preco_unitario"]),
        "valor_total": str(valor_total),
    }


def salvar_etiqueta(etiqueta: dict[str, str | int]) -> Path:
    SAIDA_DIR.mkdir(parents=True, exist_ok=True)
    caminho = SAIDA_DIR / "ultima_etiqueta.json"
    caminho.write_text(json.dumps(etiqueta, ensure_ascii=False, indent=2), encoding="utf-8")
    return caminho


def main() -> None:
    produtos = carregar_produtos()
    for indice, produto in enumerate(produtos):
        print(f"{indice}: {produto['sku']} - {produto['medidas']}")

    indice = int(input("Produto: ").strip() or "0")
    peso_total_g = decimal_ptbr(input("Peso total em gramas: "))
    etiqueta = gerar_etiqueta(produtos[indice], peso_total_g)
    caminho = salvar_etiqueta(etiqueta)
    print(f"Quantidade: {etiqueta['quantidade']}")
    print(f"Valor total: R$ {str(etiqueta['valor_total']).replace('.', ',')}")
    print(f"Arquivo gerado: {caminho}")


if __name__ == "__main__":
    main()
