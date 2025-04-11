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
            tmpData = conn.recv(1024)
            RawData = tmpData.decode()
            if not RawData:
                break
            ## 二进制解码
            chunk_size = 8
            chunks = [RawData[i:i + chunk_size] for i in range(0, len(RawData), chunk_size)]
            decoded_data = []
            for chunk in chunks:
            # 将 8 位二进制数转换为整数
                dec_num = int(chunk, 2)
            # 将整数转换为字符
                char = chr(dec_num)
                decoded_data.append(char)
            
            print(f"Received: {RawData}")
            print(f"Received: {decoded_data}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # 关闭连接
        conn.close()
    