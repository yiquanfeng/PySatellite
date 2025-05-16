import socket
import random

# 中继节点地址
relay_host = '127.0.0.1'
relay_port = 8888

# 创建 TCP 套接字
relay_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
relay_socket.bind((relay_host, relay_port))
relay_socket.listen(1)

print(f"Relay node is listening on {relay_host}:{relay_port}")


while True:
    conn, addr = relay_socket.accept()
    print(f"Connected by {addr}")

    try:
        while True:
            # 接收数据

            data = conn.recv(1024)
            decoded_data = data.decode()
            if not decoded_data:
                break
            
            ## 根据发来的地址连接receiver
            info = {}
            pairs = decoded_data.split(',')
            for pair in pairs:
                key, value = pair.split(':')
                info[key] = value
            
            receiver_host = info.get('receiver_host')
            receiver_port = int(info.get('receiver_port'))
            receive_data = info.get('data')

            receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            receiver_socket.connect((receiver_host, receiver_port))


            # 模拟信号传输损耗（丢包）
            if random.random() < 0.001:  # 0.1% 的丢包率
                print("Packet lost.")
            else:
                # 转发数据
                receiver_socket.sendall(receive_data.encode())
                print(f"Relayed: {receive_data}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # 关闭连接
        conn.close()
    