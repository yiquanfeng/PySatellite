import socket
import data_proccess

# 接收端地址
RECEIVER_HOST = '127.0.0.1'
RECEIVER_PORT = 8889

# 创建 TCP 套接字
receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
receiver_socket.bind((RECEIVER_HOST, RECEIVER_PORT))
receiver_socket.listen(1)

print(f"Receiver is listening on {RECEIVER_HOST}:{RECEIVER_PORT}")

while True:
    # 接受中继节点连接
    conn, addr = receiver_socket.accept()
    print(f"Connected by {addr}")

    try:
        while True:
            # 接收数据
            tmpData = conn.recv(1024)
            RawData = tmpData.decode()
            recieve = data_proccess.recieve_data_proccess(RawData)
            if not RawData:
                break

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # 关闭连接
        conn.close()
    