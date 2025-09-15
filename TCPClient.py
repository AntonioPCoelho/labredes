from socket import *

# Defina o nome ou IP do servidor e a porta
serverName = '127.0.0.1' 
serverPort = 13000

# Cria o socket do cliente com os protocolos TCP/IP
clientSocket = socket(AF_INET, SOCK_STREAM)

# Conecta ao servidor
clientSocket.connect((serverName, serverPort))

# Pede ao usuário para digitar uma frase (usando input() para Python 3)
sentence = input('Input lowercase sentence: ')

# Envia a frase para o servidor (a string precisa ser codificada para bytes)
clientSocket.send(sentence.encode())

# Espera e recebe a resposta do servidor (até 1024 bytes)
modifiedSentence = clientSocket.recv(1024)

# Imprime a resposta decodificada (convertida de bytes para string)
print('From Server:', modifiedSentence.decode())

# Fecha a conexão
clientSocket.close()
