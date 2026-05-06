from decimal import Decimal

from app_simulador import calcular_quantidade, calcular_valor_total


def test_calcular_quantidade_exata():
    quantidade, sobra = calcular_quantidade(Decimal("2500"), Decimal("1.25"))

    assert quantidade == 2000
    assert sobra == Decimal("0.00")


def test_calcular_quantidade_com_sobra():
    quantidade, sobra = calcular_quantidade(Decimal("10"), Decimal("3"))

    assert quantidade == 3
    assert sobra == Decimal("1")


def test_calcular_valor_total():
    valor = calcular_valor_total(2000, Decimal("0.08"))

    assert valor == Decimal("160.00")
