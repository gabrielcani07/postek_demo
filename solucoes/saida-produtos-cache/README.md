# Saida de produtos texteis com cache de bipagens

MVP para o operador bipar produtos no coletor/celular, agrupar por codigo e imprimir as etiquetas somente ao finalizar.

## Regra implementada

```text
Bipou:
789001
789002
789001
789003

Resultado:
789001 - 2 etiquetas
789002 - 1 etiqueta
789003 - 1 etiqueta
```

## Como funciona

```text
Coletor/celular/PC
  -> tela web local
  -> cache temporario da sessao
  -> inventario vindo do Google Sheets ou CSV
  -> impressao em lote simulada ou TCP para POSTEK
```

## Colunas esperadas na planilha

Para reaproveitar o layout de parafusos, o exemplo textil usa a mesma quantidade de variaveis.

| Campo | Nomes aceitos |
| --- | --- |
| Codigo | `codigo_barras`, `codigo`, `code`, `barcode`, `ean`, `gtin`, `sku` |
| Referencia | `sku`, `codigo_interno`, `id` |
| Categoria | `tipo`, `categoria`, `category`, `linha` |
| Descricao | `descricao`, `description`, `produto`, `nome` |
| Tamanho/Cor | `medidas`, `tamanho_cor`, `tamanho`, `grade`, `size`, `cor` |
| Peso/Gramatura | `peso_unitario_g`, `gramatura`, `peso`, `weight` |
| Preco | `preco_unitario`, `preco`, `price`, `valor` |
| Composicao | `composicao`, `composition`, `tecido` |

Modelo recomendado para sua planilha:

```text
sku,tipo,codigo_barras,descricao,medidas,peso_unitario_g,preco_unitario,composicao
TXT-CAM-BAS-M-AZ,Camiseta,7891000000011,Camiseta basica algodao,Tam M / Azul,180,39.90,100% algodao
```

## Como testar no computador

Na pasta do projeto:

```powershell
python .\solucoes\saida-produtos-cache\app.py
```

Ou, dentro da pasta `saida-produtos-cache`, execute:

```text
iniciar_servico_web.bat
```

Abra no navegador:

```text
http://localhost:8080
```

Para testar no celular/coletor na mesma rede:

```text
http://192.168.1.7:8080
```

## Google Sheets

Por padrao, o sistema tenta carregar esta planilha:

```text
https://docs.google.com/spreadsheets/d/1zzlB_CjRyYvdNfOdZjh_5ifHF_bLw6QVgHRYK4Ro2iY/edit?usp=sharing
```

O sistema aceita o link normal de compartilhamento e converte automaticamente para CSV.
Para funcionar sem login, a planilha precisa estar publicada/compartilhada de forma que o CSV seja acessivel.

Se a planilha nao abrir, o sistema usa o arquivo local:

```text
dados/produtos_exemplo.csv
```

## Impressao

O modo padrao e simulacao. Ao finalizar, o sistema registra o historico incremental em:

```text
logs/historico-impressoes.txt
logs/historico-impressoes.jsonl
```

Para debug de impressao, tambem e possivel salvar os arquivos por lote ativando:

```powershell
$env:SAVE_PRINT_BATCH_FILES="1"
```

Arquivos que vao para a impressora:

```text
postek_app/connectivity_textil.py
postek_app/layout_textil.prn
```

Na POSTEK/OXScript, execute o `connectivity_textil.py` e deixe ele aberto. Ele fica aguardando as etiquetas na porta `12346`.

Como a porta RAW `9100` da POSTEK fica aberta para impressao direta, o caminho recomendado e enviar direto para ela:

```powershell
$env:PRINT_MODE="raw9100"
$env:POSTEK_PRINTER_HOST="192.168.1.21"
$env:POSTEK_PRINTER_PORT="9100"
$env:POSTEK_LABEL_HEIGHT_DOTS="320"
$env:POSTEK_LABEL_GAP_DOTS="25"
python .\solucoes\saida-produtos-cache\app.py
```

Se a impressora imprimir uma etiqueta e pular outra, reduza `POSTEK_LABEL_HEIGHT_DOTS`.
Em impressoras 203 dpi, a conta aproximada e:

```text
altura em mm x 8 = altura em dots
```

Exemplos:

```text
50 mm -> 400 dots
40 mm -> 320 dots
35 mm -> 280 dots
30 mm -> 240 dots
```

Importante: o IP `192.168.1.7` e o IP do computador/servidor para o celular acessar o sistema. O IP `192.168.1.21` e o IP da impressora POSTEK.

Atencao: a porta `9100` normalmente e a porta RAW de impressao da propria impressora. O `connectivity_textil.py` usa a porta `12346`, mas algumas configuracoes de OXScript nao deixam essa porta acessivel pela rede.

## Riscos antes de usar em producao

- Confirmar o IP e a porta reais da impressora POSTEK.
- Confirmar que a impressora consegue rodar `connectivity_textil.py`.
- Confirmar se o layout `layout_textil.prn` esta alinhado fisicamente na etiqueta real.
- Evitar deixar a impressora aberta na rede sem controle.
- Adicionar usuario/senha se o sistema for usado por mais pessoas ou em rede exposta.
- Se isso movimentar estoque real, precisa gravar historico em banco e impedir dupla finalizacao.
