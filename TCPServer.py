from socket import *

serverPort = 13000

# Cria o socket do servidor com os protocolos TCP/IP
serverSocket = socket(AF_INET, SOCK_STREAM)

# Associa o socket a um endereço IP vazio (aceita conexões de qualquer interface) e à porta 12000
serverSocket.bind(('', serverPort))

# Coloca o socket em modo de escuta, aguardando por uma conexão
serverSocket.listen(1)

# Usa a função print() do Python 3
print('The server is ready to receive')

# Loop infinito para aceitar conexões continuamente
while True:
    # --- Início do Bloco Indentado ---
    # Aceita uma nova conexão de um cliente
    connectionSocket, addr = serverSocket.accept()
    
    # Recebe os dados (até 1024 bytes) e decodifica para string
    sentence = connectionSocket.recv(1024).decode()
    
    # Converte a string para maiúsculas
    capitalizedSentence = sentence.upper()
    
    # Envia a string em maiúsculas de volta para o cliente, codificando para bytes
    connectionSocket.send(capitalizedSentence.encode())
    
    # Fecha a conexão com este cliente específico
    connectionSocket.close()
    # --- Fim do Bloco Indentado ---
