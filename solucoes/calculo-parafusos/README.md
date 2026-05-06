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
- Entrada manual simulando a balanca.
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

- Protocolo real da balanca: serial, USB, TCP, Bluetooth ou outro.
- Formato do dado enviado pela balanca: exemplo `ST,GS,+002.500kg` ou apenas `2500`.
- Se a POSTEK consegue ler diretamente a balanca pela porta disponivel.
- Como o layout do BarTender vai expor os campos variaveis.
- Tolerancia aceitavel: peso real pode variar por lote, sujeira, banho, rebarba ou calibracao da balanca.

## O que nao fazer agora

- Integrar com banco grande.
- Automatizar impressao real sem validar o layout.
- Tratar peso como 100% exato sem regra de tolerancia.
- Fechar comunicacao com balanca antes de saber o modelo/protocolo.
