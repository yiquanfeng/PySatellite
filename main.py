import moderate_test, coding_test, ADtest
import numpy as np

if __name__ == "__main__":

    turbo = coding_test.TurboEncoderDecoder()
    _modulate = moderate_test.QPSKModem()
    # _protocol = protocol.ProtocolHandler()


    # np.random.seed(42)
    # original_data = np.random.randint(0, 2, 1024)
    # frames = [original_data,original_data]
    frames = ADtest.get_frame()

    encode_bits = turbo.encode(frames)
    print(len(encode_bits[0]))

    # send_p = _protocol.build_frame(encode_bits)

    _modulate_bits = _modulate.modulate(encode_bits)
    print(len(_modulate_bits[0]))

    de_modulate_bits = _modulate.demodulate(_modulate_bits)
    print(len(de_modulate_bits[0]))

    # recieve_p = _protocol.parse_frame(de_modulate_bits)

    decode_bits = turbo.decode(de_modulate_bits)
    print(len(decode_bits[1]))



    
    # print("frame_bit :" + len(frames[0]))
    # print(len(frames))