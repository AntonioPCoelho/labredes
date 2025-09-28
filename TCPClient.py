# TCPClient.py

import socket
import sys
import os
import time  # Usado para medir o tempo de transferência
import csv   # Para salvar o log em um formato de planilha (CSV)
import json  # Para salvar as métricas detalhadas do TCP

# --- Constantes ---
# Define o tamanho do buffer para 4KB. É um bom valor padrão.
BUFFER_SIZE = 4096

def start_client(host, port):
    """
    Função principal que inicia o cliente e se conecta ao servidor.
    """
    try:
        # Cria o socket do cliente (TCP/IP)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Tenta se conectar ao host e porta fornecidos
        client_socket.connect((host, port))
        print(f"Conectado ao servidor em {host}:{port}")
    except ConnectionRefusedError:
        # Se a conexão for recusada, provavelmente o servidor não está no ar.
        print(f"Erro: Conexão recusada. Verifique se o servidor está rodando em {host}:{port}.")
        return
    except socket.gaierror:
        # Se o host não for encontrado (ex: erro de digitação no IP ou nome)
        print(f"Erro: Host '{host}' não encontrado. Verifique o endereço do servidor.")
        return

    # Loop principal para a interface de comandos do usuário
    while True:
        command_input = input(">> Digite o comando (list, put <arquivo>, quit): ")
        parts = command_input.split()
        if not parts:
            # Se o usuário só apertar Enter, continua para a próxima iteração
            continue
        
        command = parts[0].lower()

        # --- Lógica dos Comandos ---

        if command == "put":
            # Verifica se o usuário passou o nome do arquivo junto com o comando
            if len(parts) != 2:
                print("Uso: put <caminho_do_arquivo>")
                continue
            
            filepath = parts[1]
            # Checa se o arquivo que o usuário quer enviar realmente existe
            if not os.path.exists(filepath):
                print(f"Erro: Arquivo '{filepath}' não encontrado.")
                continue

            # Pega só o nome do arquivo (sem o caminho) e o seu tamanho
            filename = os.path.basename(filepath)
            filesize = os.path.getsize(filepath)

            # --- Preparação dos Arquivos de Log ---
            log_file_csv = 'client_log.csv'
            # Cria um arquivo JSON separado para as métricas TCP de cada transferência
            log_file_tcp_info = f'tcp_info_log_{filename}.json'
            log_header = ['timestamp_inicio', 'timestamp_fim', 'arquivo', 'tamanho_bytes', 'duracao_s', 'taxa_Bps']
            
            # Se o arquivo de log principal (CSV) não existir, cria ele e escreve o cabeçalho
            if not os.path.exists(log_file_csv):
                with open(log_file_csv, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(log_header)
            
            # 1. Avisa o servidor que queremos enviar um arquivo (comando PUT)
            client_socket.send(f"PUT {filename} {filesize}".encode('utf-8'))

            # 2. Espera o "joinha" (OK) do servidor para começar o envio
            server_response = client_socket.recv(BUFFER_SIZE).decode('utf-8')

            # 3. Se o servidor respondeu "OK", a gente começa a festa
            if server_response == "OK":
                print(f"Servidor pronto. Enviando '{filename}' ({filesize} bytes)...")
                
                # Prepara as variáveis para medir o tempo e a performance
                bytes_enviados = 0
                tcp_info_history = [] # Lista para guardar as métricas TCP
                start_time = time.time() # Marca o tempo de início
                timestamp_inicio = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))
                
                try:
                    # Abre o arquivo em modo de leitura binária ('rb')
                    with open(filepath, 'rb') as f:
                        while True:
                            # Tenta coletar as métricas TCP a cada iteração do loop.
                            # Isso nos dá uma "foto" do estado da conexão ao longo do tempo.
                            try:
                                # A mágica acontece aqui! Pedimos ao sistema operacional infos da conexão.
                                # O '11' é o código para TCP_INFO no Linux.
                                # O '104' é o tamanho esperado da estrutura de dados.
                                tcp_info_raw = client_socket.getsockopt(socket.IPPROTO_TCP, 11, 104)
                                
                                # Guardamos o timestamp e a lista de informações
                                tcp_info_history.append({
                                    'timestamp': time.time(),
                                    'tcp_info': list(tcp_info_raw) # Convertemos para lista pra salvar em JSON
                                })
                            except (socket.error, AttributeError, ImportError):
                                # Se der erro (ex: rodando no Windows), não faz nada e segue a vida.
                                pass

                            # Lê um pedaço do arquivo (do tamanho do nosso buffer)
                            bytes_read = f.read(BUFFER_SIZE)
                            if not bytes_read:
                                # Se não há mais nada para ler, saímos do loop
                                break
                            # Envia o pedaço lido para o servidor
                            client_socket.sendall(bytes_read)
                            bytes_enviados += len(bytes_read)
                    
                    # Depois que o loop acaba, espera a confirmação final do servidor
                    final_response = client_socket.recv(BUFFER_SIZE).decode('utf-8')
                    print(f"[Servidor]: {final_response}")

                    # Agora que acabou, vamos calcular os resultados e salvar nos logs
                    end_time = time.time() # Marca o tempo final
                    timestamp_fim = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))
                    duration = end_time - start_time
                    # Calcula a taxa de transferência (bytes por segundo)
                    rate = bytes_enviados / duration if duration > 0 else 0

                    # Salva os dados gerais da transferência no arquivo CSV
                    with open(log_file_csv, 'a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([timestamp_inicio, timestamp_fim, filename, bytes_enviados, f"{duration:.4f}", f"{rate:.2f}"])
                    print(f"Log da transferência salvo em '{log_file_csv}'.")

                    # Se conseguimos coletar as métricas TCP, salva elas no arquivo JSON
                    if tcp_info_history:
                        with open(log_file_tcp_info, 'w') as f:
                            json.dump(tcp_info_history, f, indent=4)
                        print(f"Log de métricas TCP salvo em '{log_file_tcp_info}'.")

                except Exception as e:
                    print(f"Ocorreu um erro durante o envio do arquivo: {e}")
            else:
                # Se o servidor não mandou "OK" (ex: arquivo já existe), mostra a resposta dele
                print(f"[Servidor]: {server_response}")

        elif command == "list":
            # Envia o comando LIST para o servidor
            client_socket.send("LIST".encode('utf-8'))
            # Recebe e imprime a lista de arquivos
            server_response = client_socket.recv(BUFFER_SIZE).decode('utf-8')
            print("\n--- Arquivos no Servidor ---\n" + server_response)
            print("---------------------------\n")

        elif command == "quit":
            # Avisa o servidor que estamos saindo
            client_socket.send("QUIT".encode('utf-8'))
            break # Sai do loop while e encerra o cliente

        else:
            print("Comando inválido. Tente: list, put <arquivo> ou quit.")
            
    # Fecha a conexão de forma limpa
    print("Fechando conexão.")
    client_socket.close()

# --- Ponto de Entrada do Script ---
if __name__ == "__main__":
    # Verifica se o usuário passou o host e a porta ao executar o script
    if len(sys.argv) != 3:
        print("Uso: python TCPClient.py <host> <port>")
        sys.exit(1) # Encerra o programa se os argumentos estiverem errados
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    start_client(host, port)
