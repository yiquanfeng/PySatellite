import moderate_test, coding_test, protocol, ADtest
import numpy as np

def send_data_proccess():
    turbo = coding_test.TurboEncoderDecoder()
    _modulate = moderate_test.AmplitudeModem()
    _protocol = protocol.ProtocolHandler()

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

    return _modulate_bits

def recieve_data_proccess(modulate_bits):
    turbo = coding_test.TurboEncoderDecoder()
    _modulate = moderate_test.AmplitudeModem()
    _protocol = protocol.ProtocolHandler()

    demodulate_bits = _modulate.demodulate(modulate_bits)
    print(f"demodulate_bits_len:{len(demodulate_bits[0])}")
    # print(demodulate_bits[0])

    recieve_p = _protocol.parse_frames(demodulate_bits)
    print(f"recieve_p_len:{len(recieve_p[0])}")

    decode_bits = turbo.decode(recieve_p)
    print(f"decode_bits_len:{len(decode_bits[0])}")

    return decode_bits

