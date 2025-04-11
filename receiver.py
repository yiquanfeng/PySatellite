import socket

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
            RawData = conn.recv(1024)
            if not RawData:
                break
            
            # 简单解调（这里只是示例，实际需要复杂的解调算法）
            demodulated_message = RawData.decode()
            print(f"Received: {demodulated_message}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # 关闭连接
        conn.close()
    