import socket
import random

relay_host = '127.0.0.1'
relay_port = 8888

receiver_host = '127.0.0.1'
receiver_port = 8889

sender_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sender_socket.connect((relay_host, relay_port))

data = 'hello world'
# 八位二进制编码
encoded_data = ''.join((format(ord(char), '08b')) for char in data)

message = f"receiver_host:{receiver_host},receiver_port:{receiver_port},data:{encoded_data}"

try:
    modulated_message = message.encode()

    sender_socket.sendall(modulated_message)
    print(f"Sent: {message}")

except Exception as e:
    print(f"Error: {e}")
finally:
    sender_socket.close()
    