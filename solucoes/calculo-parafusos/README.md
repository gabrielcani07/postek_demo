# Calculo de parafusos por peso

MVP para calcular quantidade de parafusos usando peso total recebido de uma balanca.

## Problema

O operador precisa selecionar um tipo de parafuso, receber o peso total da balanca, ver a quantidade e o valor total calculados na tela e imprimir uma etiqueta com os dados do produto.

## Fluxo principal

1. Operador seleciona o produto.
2. Sistema carrega peso unitario, preco unitario, tipo, codigo de barras, descricao e medidas.
3. Balanca informa o peso total.
4. Sistema calcula:

```text
quantidade = peso_total_g / peso_unitario_g
valor_total = quantidade * preco_unitario
```

5. Operador confere a quantidade.
6. Operador imprime a etiqueta.

## MVP implementado agora

- Banco teste em CSV, abrivel pelo Excel.
- Simulador local em Python.
- Entrada manual no simulador local.
- Leitura direta da balanca Urano US POP-S no OX Script da POSTEK via USB-serial CH340.
- Calculo automatico da quantidade e do valor total.
- Geracao de arquivo `saida/ultima_etiqueta.json` com os dados calculados.

## Como testar no computador

Na pasta do projeto, rode:

```powershell
python .\solucoes\calculo-parafusos\app_simulador.py
```

Depois:

1. Selecione um produto.
2. Digite o peso total em gramas, por exemplo `2500`.
3. Clique em `Atualizar peso`.
4. Confira a quantidade calculada e o valor total.
5. Clique em `Gerar etiqueta`.

O arquivo de saida sera criado em:

```text
solucoes/calculo-parafusos/saida/ultima_etiqueta.json
```

## Campos do banco

Arquivo:

```text
dados/produtos_parafusos.csv
```

Campos:

| Campo | Descricao |
| --- | --- |
| `sku` | Codigo interno do produto |
| `tipo` | Tipo/familia do parafuso |
| `codigo_barras` | Codigo usado na etiqueta |
| `descricao` | Descricao generica |
| `medidas` | Medidas do parafuso |
| `peso_unitario_g` | Peso unitario em gramas |
| `preco_unitario` | Preco por unidade/peca |

## Riscos e pontos para confirmar

- A solucao usa acesso USB bruto ao conversor CH340 da balanca dentro do OX Script.
- Validado na POSTEK com a balanca Urano US POP-S enviando formatos como `PESO L: 0.634kg`, `T2BN0 0,110 kg` e `00326`.
- A impressora precisa permitir acesso a `/sys/bus/usb/devices` e `/dev/bus/usb` pelo OX Script.
- Como o layout do BarTender vai expor os campos variaveis.
- Tolerancia aceitavel: peso real pode variar por lote, sujeira, banho, rebarba ou calibracao da balanca.

## O que nao fazer agora

- Integrar com banco grande.
- Automatizar impressao real sem validar o layout.
- Tratar peso como 100% exato sem regra de tolerancia.
- Fechar comunicacao com balanca antes de saber o modelo/protocolo.
