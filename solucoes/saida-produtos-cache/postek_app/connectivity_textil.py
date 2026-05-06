from ox_script import *

import json
import socket
import traceback


HOST = "0.0.0.0"
PORT = 12346
LAYOUT_PATH = "layout_textil.prn"
BUFFER_SIZE = 4096
servidor_ativo = False
status_controller = None


def valor_texto(payload, campo, padrao="-"):
    valor = payload.get(campo, padrao)
    if valor is None:
        return padrao
    texto = str(valor).strip()
    return texto if texto else padrao


def imprimir_etiqueta(payload):
    cmd = PTK_UpdateAllFormVariables(
        LAYOUT_PATH,
        Input1=valor_texto(payload, "Input1"),
        Input2=valor_texto(payload, "Input2"),
        Input3=valor_texto(payload, "Input3"),
        Input4=valor_texto(payload, "Input4"),
        Input5=valor_texto(payload, "Input5"),
        Input6=valor_texto(payload, "Input6"),
        Input7=valor_texto(payload, "Input7"),
        Input8=valor_texto(payload, "Input8"),
    )
    PTK_SendCmdToPrinter(cmd)


def atualizar_status(texto):
    print(texto)
    if status_controller is None:
        return
    try:
        status_controller.update(texto)
    except Exception:
        pass


def processar_linha(linha):
    texto = linha.strip()
    if not texto:
        return
    payload = json.loads(texto)
    imprimir_etiqueta(payload)
    atualizar_status("Etiqueta impressa: " + valor_texto(payload, "Input2"))


def processar_conexao(conexao):
    buffer = ""
    while True:
        dados = conexao.recv(BUFFER_SIZE)
        if not dados:
            break
        buffer += dados.decode("utf-8")
        while "\n" in buffer:
            linha, buffer = buffer.split("\n", 1)
            processar_linha(linha)
    processar_linha(buffer)


def iniciar_servidor():
    global servidor_ativo
    if servidor_ativo:
        atualizar_status("Servidor ja esta aguardando etiquetas.")
        return
    servidor_ativo = True

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORT))
    servidor.listen(5)
    atualizar_status("Aguardando etiquetas em " + HOST + ":" + str(PORT))

    while True:
        conexao, endereco = servidor.accept()
        atualizar_status("Conexao recebida de " + str(endereco))
        try:
            processar_conexao(conexao)
        except Exception:
            traceback.print_exc()
            atualizar_status("Erro ao processar etiqueta. Veja o log.")
        finally:
            conexao.close()


if __name__ == "__main__":
    controller = PTK_UIInit(
        PTK_UIPage(
            PTK_UIText(title="Saida de produtos"),
            status_controller := PTK_UITextBox(
                title="Status",
                value="Toque em Iniciar e mantenha esta tela aberta.",
            ),
            PTK_UIButton(title="Iniciar servidor", Onpressed=iniciar_servidor),
        ),
        require_execute_confirmation=False,
    )
