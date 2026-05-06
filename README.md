# SOLUCAO-1 - POSTEK OXScript

Repositorio de trabalho para criar solucoes OXScript com impressoras POSTEK.

## Objetivo

Organizar scripts, testes e documentacao das solucoes criadas para impressao de etiquetas, leitura de dados externos, RFID, scanner, TCP, Excel, Google Sheets, MySQL e outros fluxos que forem surgindo.

## Estrutura

```text
docs/       Documentacao curta e referencias
solucoes/   Scripts e projetos criados para casos reais
testes/     Arquivos auxiliares para validacao
```

## Referencias POSTEK

Os exemplos oficiais/localizados estao documentados em:

```text
docs/REFERENCIAS_POSTEK.md
```

## Solucoes em desenvolvimento

| Solucao | Descricao |
| --- | --- |
| `solucoes/calculo-parafusos` | Calcula quantidade de parafusos por peso, usando cadastro local e simulacao de balanca |
| `solucoes/saida-produtos-cache` | Bipa saidas de produtos, agrupa etiquetas em cache e envia impressao para POSTEK |

## Fluxo recomendado

1. Descrever a necessidade da etiqueta ou automacao.
2. Definir entrada de dados: manual, Excel, scanner, banco, API, RFID ou TCP.
3. Criar uma primeira versao simples.
4. Testar em ambiente controlado antes de usar em producao.
5. Registrar ajustes e versoes neste repositorio.
