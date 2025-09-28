# TCPClient.py

import socket
import sys
import os
import time # Para medir o tempo
import csv  # Para salvar o log em formato de planilha

# --- Constantes ---
BUFFER_SIZE = 4096 # 4KB

def start_client(host, port):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        print(f"Conectado ao servidor em {host}:{port}")
    except ConnectionRefusedError:
        print(f"Erro: Conexão recusada. Verifique se o servidor está rodando em {host}:{port}.")
        return

    # Loop para a interface de comandos do usuário
    while True:
        command_input = input(">> Digite o comando (list, put <arquivo>, quit): ")
        parts = command_input.split()
        if not parts:
            continue
        
        command = parts[0].lower()

        # --- Lógica dos Comandos ---

        # Dentro do loop while True do cliente

        # No arquivo TCPClient.py, substitua este bloco inteiro:

        if command == "put":
            if len(parts) != 2:
                print("Uso: put <caminho_do_arquivo>")
                continue
            
            filepath = parts[1]
            if not os.path.exists(filepath):
                print(f"Erro: Arquivo '{filepath}' não encontrado.")
                continue

            filename = os.path.basename(filepath)
            filesize = os.path.getsize(filepath)

            # --- INÍCIO DA INSTRUMENTAÇÃO (preparação) ---
            log_file = 'client_log.csv'
            log_header = ['timestamp_inicio', 'timestamp_fim', 'arquivo', 'tamanho_bytes', 'duracao_s', 'taxa_Bps']
            
            if not os.path.exists(log_file):
                with open(log_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(log_header)
            # --- FIM DA INSTRUMENTAÇÃO (preparação) ---

            # 1. Envia o comando para o servidor
            client_socket.send(f"PUT {filename} {filesize}".encode('utf-8'))

            # 2. *** A LINHA QUE FALTAVA ***
            # Espera a resposta do servidor (OK ou ERROR) para criar a variável
            server_response = client_socket.recv(BUFFER_SIZE).decode('utf-8')

            # 3. Agora podemos checar a resposta e começar a medir o tempo
            if server_response == "OK":
                print(f"Servidor pronto. Enviando '{filename}' ({filesize} bytes)...")
                
                # Inicia a contagem do tempo ANTES de enviar o arquivo
                bytes_enviados = 0
                start_time = time.time()
                timestamp_inicio = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))
                
                try:
                    with open(filepath, 'rb') as f:
                        while True:
                            bytes_read = f.read(BUFFER_SIZE)
                            if not bytes_read:
                                break
                            client_socket.sendall(bytes_read)
                            bytes_enviados += len(bytes_read)
                    
                    final_response = client_socket.recv(BUFFER_SIZE).decode('utf-8')
                    print(f"[Servidor]: {final_response}")

                    # Finaliza a medição e grava o log APÓS o envio
                    end_time = time.time()
                    timestamp_fim = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))
                    duration = end_time - start_time
                    rate = bytes_enviados / duration if duration > 0 else 0

                    with open(log_file, 'a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([timestamp_inicio, timestamp_fim, filename, bytes_enviados, f"{duration:.4f}", f"{rate:.2f}"])
                    
                    print(f"Log da transferência salvo em '{log_file}'.")

                except Exception as e:
                    print(f"Erro durante o envio do arquivo: {e}")
            else:
                print(f"[Servidor]: {server_response}")

        elif command == "list":
            client_socket.send("LIST".encode('utf-8'))
            server_response = client_socket.recv(BUFFER_SIZE).decode('utf-8')
            print("\n--- Arquivos no Servidor ---\n" + server_response)
            print("---------------------------\n")

        elif command == "quit":
            client_socket.send("QUIT".encode('utf-8'))
            break # Sai do loop while

        else:
            print("Comando inválido. Comandos disponíveis: list, put <arquivo>, quit.")
            
    # Fecha a conexão após sair do loop
    print("Fechando conexão.")
    client_socket.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python TCPClient.py <host> <port>")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    start_client(host, port)