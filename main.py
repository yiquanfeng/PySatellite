import moderate_test, coding_test, ADtest, protocol
import numpy as np

if __name__ == "__main__":

    turbo = coding_test.TurboEncoderDecoder()
    _modulate = moderate_test.AmplitudeModem()
    _protocol = protocol.ProtocolHandler()

    # np.random.seed(42)
    # original_data = np.random.randint(0, 2, 1024)
    # frames = [original_data,original_data]
    frames = ADtest.get_frame()

    encode_bits = turbo.encode(frames)
    print(f"ecode_bits_len:{len(encode_bits[0])}")
    # print(encode_bits[0])

    send_p = _protocol.build_frames(encode_bits)
    print(f"send_p_len:{len(send_p[0])}")
    # print(send_p[0])

    _modulate_bits = _modulate.modulate(send_p)
    print(f"modulate_bits_len:{len(_modulate_bits[0])}")
    # print(_modulate_bits)

    demodulate_bits = _modulate.demodulate(_modulate_bits)
    print(f"demodulate_bits_len:{len(demodulate_bits[0])}")
    # print(demodulate_bits[0])


    recieve_p = _protocol.parse_frames(demodulate_bits)
    print(f"recieve_p_len:{len(recieve_p[0])}")
    # print(recieve_p[0])

#    # 误码率计算（关键修正部分）
#     # 确保输入格式统一（全部转为 numpy array）
#     tx_bits = np.array(send_p[0])  # 发送的比特流
#     rx_bits = np.array(demodulate_bits[0])  # 解调后的比特流

#     compared_bits = min(len(tx_bits), len(rx_bits))  # 确保比较长度一致
#     error_count = np.sum(tx_bits[:compared_bits] != rx_bits[:compared_bits])  # 统计错误比特数
#     ber = error_count / compared_bits  # 误码率 = 错误比特数 / 总比特数

#     print(f"误码率 (BER): {ber:.2%}")
#     print(f"误码数: {error_count}/{compared_bits}")

    decode_bits = turbo.decode(recieve_p)
    print(f"decode_bits_len:{len(decode_bits[0])}")

    #    # 误码率计算
    # # 确保输入格式统一（全部转为 numpy array）
    # tx_bits = np.array(encode_bits[0])  
    # rx_bits = np.array(decode_bits[0])  

    # compared_bits = min(len(tx_bits), len(rx_bits))  # 确保比较长度一致
    # error_count = np.sum(tx_bits[:compared_bits] != rx_bits[:compared_bits])  # 统计错误比特数
    # ber = error_count / compared_bits  # 误码率 = 错误比特数 / 总比特数

    # print(f"误码率 (BER): {ber:.2%}")
    # print(f"误码数: {error_count}/{compared_bits}")