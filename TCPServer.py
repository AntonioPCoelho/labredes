# TCPServer.py

import socket
import threading
import os

# --- Constantes ---
HOST = '' # Escuta em todas as interfaces de rede
PORT = 13000
BUFFER_SIZE = 4096 # 4KB
SERVER_STORAGE = "server_files" # Diretório para salvar os arquivos

# --- Função para Lidar com Cada Cliente ---
def handle_client(conn, addr):
    """
    Esta função é executada em uma thread separada para cada cliente.
    """
    print(f"[NOVA CONEXÃO] {addr} conectado.")

    try:
        while True:
            # Recebe o comando do cliente
            client_command = conn.recv(BUFFER_SIZE).decode('utf-8')
            if not client_command:
                break # Se o cliente desconectar, encerra o loop

            parts = client_command.split()
            command = parts[0].upper()

            print(f"[{addr}] Comando recebido: {client_command}")

            # --- Lógica dos Comandos ---
            
            if command == "LIST":
                try:
                    file_list = os.listdir(SERVER_STORAGE)
                    if not file_list:
                        response = "Nenhum arquivo no servidor."
                    else:
                        response = "\n".join(file_list)
                    conn.sendall(response.encode('utf-8'))
                except Exception as e:
                    conn.sendall(f"ERRO ao listar arquivos: {e}".encode('utf-8'))

            elif command == "PUT":
                try:
                    filename = parts[1]
                    filesize = int(parts[2])
                    filepath = os.path.join(SERVER_STORAGE, filename)

                    # 1. Tratamento de Erro: Verifica se o arquivo já existe
                    if os.path.exists(filepath):
                        conn.sendall("ERROR: FILE_EXISTS".encode('utf-8'))
                        print(f"[{addr}] Envio de '{filename}' negado. Arquivo já existe.")
                        continue # Volta para o início do loop, esperando novo comando
                    else:
                        conn.sendall("OK".encode('utf-8')) # Sinal verde para o cliente enviar
                    
                    # 2. Lógica de Recebimento do Arquivo
                    bytes_recebidos = 0
                    with open(filepath, 'wb') as f:
                        while bytes_recebidos < filesize:
                            # Calcula quantos bytes ainda faltam para não exceder o buffer
                            bytes_a_ler = min(BUFFER_SIZE, filesize - bytes_recebidos)
                            data = conn.recv(bytes_a_ler)
                            if not data:
                                break # Conexão perdida no meio da transferência
                            f.write(data)
                            bytes_recebidos += len(data)
                    
                    # Verifica se o arquivo foi recebido por completo
                    if bytes_recebidos == filesize:
                        print(f"[{addr}] Arquivo '{filename}' recebido com sucesso.")
                        conn.sendall("SUCCESS: UPLOAD_COMPLETE".encode('utf-8'))
                    else:
                        print(f"[{addr}] Erro no upload de '{filename}'. Tamanho imcompatível.")
                        os.remove(filepath) # Remove o arquivo incompleto
                        
                except IndexError:
                    conn.sendall("ERROR: Formato do comando PUT inválido. Use: PUT <arquivo> <tamanho>".encode('utf-8'))
                except Exception as e:
                    print(f"[{addr}] Erro durante o PUT: {e}")
                    conn.sendall(f"ERROR: {e}".encode('utf-8'))

            elif command == "QUIT":
                print(f"[{addr}] Cliente solicitou desconexão.")
                break
            
            else:
                conn.sendall("ERROR: COMANDO_INVALIDO".encode('utf-8'))

    except ConnectionResetError:
        print(f"[{addr}] Conexão foi resetada pelo cliente.")
    except Exception as e:
        print(f"[ERRO] Erro na thread do cliente {addr}: {e}")
    finally:
        print(f"[CONEXÃO FECHADA] {addr}")
        conn.close()

# --- Função Principal do Servidor ---
def start_server():
    # Cria o diretório de armazenamento se ele não existir
    if not os.path.exists(SERVER_STORAGE):
        os.makedirs(SERVER_STORAGE)
        print(f"Diretório '{SERVER_STORAGE}' criado.")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5) # Aceita até 5 conexões na fila de espera
    print(f"[*] Servidor escutando em {HOST}:{PORT}")

    while True:
        conn, addr = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[CONEXÕES ATIVAS] {threading.active_count() - 1}")

if __name__ == "__main__":
    start_server()