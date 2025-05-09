import struct
import crcmod
from typing import Union, List, Dict, Tuple

class ProtocolHandler:
    """
    增强版协议处理器（支持多组比特流输入和多帧处理）
    帧格式：[帧头(2B) | 长度(2B) | 数据(NB) | CRC16(2B)]
    """
    def __init__(self):
        self.header = b'\xAA\x55'
        self.crc16 = crcmod.predefined.mkCrcFun('crc-16')
        self.header_bits = self._bytes_to_bits(self.header)

    def build_frames(self, payloads: List[List[int]]) -> List[List[int]]:
        """
        组帧方法（支持多组比特流输入）
        :param payloads: 包含多个比特流数组的列表，每个数组元素为0或1
        :return: 包含多个完整帧比特流数组的列表
        """
        output = []
        for payload in payloads:
            if not all(bit in (0, 1) for bit in payload):
                raise ValueError("输入列表必须只包含0或1")
            payload_bytes = self._bits_to_bytes(payload)
            length = len(payload_bytes)
            payload_bytes = self.header + struct.pack('>H', length) + payload_bytes
            crc = self.crc16(payload_bytes)
            payload_bytes += struct.pack('>H', crc)
            payload_bits = self._bytes_to_bits(payload_bytes)
            output.append(payload_bits)

        # exp = [0,1,1,0,0,1,1,0,1,1,1,1,1,0,1,0]
        # exp_byte = self._bits_to_bytes(exp)
        # print(exp_byte)
        # length_e = len(exp_byte)
        # exp_pack = self.header + struct.pack('>H', length_e) + exp_byte
        # print(exp_pack)
        # crc = self.crc16(exp_pack)
        # exp_pack += struct.pack('>H', crc)
        # print(exp_pack)
        # exp_bit = self._bytes_to_bits(exp_pack)
        # print(exp_bit)
        # expt_byte_back = self._parse_single_frame(exp_bit,True)
        # print(expt_byte_back)

        return output

    def parse_frames(self, raw_data: List[List[int]], return_bits: bool = True) -> List[Dict]:
        results = []
        remaining_data = [arr.copy() for arr in raw_data]  # 复制原始数据避免修改
        # print(remaining_data)
        # 跟踪当前处理位置
        current_array = 0
        raw_data_len = len(raw_data)
        while current_array < raw_data_len:
            # 尝试解析当前帧
            frame_result = self._parse_single_frame(remaining_data[current_array],True)
            # print(frame_result)
            if frame_result['valid']:  
                results.append(frame_result['payload_bits'])
                current_array = current_array + 1
            else:
                current_array = current_array + 1
        return results

    def _parse_single_frame(self, frame_bits: List[int], return_bits: bool) -> Dict:
        """
        解析单个帧的内部方法
        """
        result = {
            'valid': False,
            'payload': None,
            'payload_bits': None,
            'error': None,
            'length': 0
        }

        try:
            # 将比特流转换为字节流
            frame_bytes = self._bits_to_bytes(frame_bits)
            # print(frame_bytes)

            # 基础长度检查（帧头2B + 长度2B + CRC2B = 最小6B）
            if len(frame_bytes) < 6:
                result['error'] = "数据长度不足"
                return result

            # 检查帧头
            if frame_bytes[:2] != self.header:
                result['error'] = "帧头不匹配"
                return result

            # 提取长度字段
            length = struct.unpack('>H', frame_bytes[2:4])[0]

            # 检查是否有足够的数据
            if len(frame_bytes) < 6 + length:
                result['error'] = f"数据不完整（需要:{6+length} 实际:{len(frame_bytes)})"
                return result

            # 只处理完整帧
            frame_bytes = frame_bytes[:6+length]

            # CRC校验
            received_crc = struct.unpack('>H', frame_bytes[-2:])[0]
            calculated_crc = self.crc16(frame_bytes[:-2])
            if received_crc != calculated_crc:
                result['error'] = f"CRC校验失败（接收:{hex(received_crc)} 计算:{hex(calculated_crc)})"
                return result

            # 提取有效载荷
            payload_bytes = frame_bytes[4:-2]
            payload_bits = self._bytes_to_bits(payload_bytes)

            result.update({
                'valid': True,
                'payload': payload_bytes,
                'payload_bits': payload_bits,
                'length': length
            })

        except Exception as e:
            result['error'] = f"解析异常: {str(e)}"

        return result

    def _find_header(self, bits: List[List[int]]) -> Union[int, None]:
        """
        在比特流中查找帧头位置（支持二维数组输入）
        
        :param bits: 由多个01数组组成的二维数组，例如 [[0,1,0], [1,0,1], ...]
        :return: 帧头起始位置（数组索引），找不到返回None
        """
        # 确保header_bits是普通列表而不是numpy数组
        header_bits = list(self.header_bits)
        # print(header_bits)
        
        # 将二维数组展平为一维列表以便比较
        flattened_bits = [bit for sublist in bits for bit in sublist]
        # print(bits)
        # print(flattened_bits)
        
        for i in range(len(flattened_bits) - len(header_bits) + 1):
            # 获取当前窗口的比特片段
            window = flattened_bits[i:i+len(header_bits)]
            # 逐个比较比特位
            if all(w == h for w, h in zip(window, header_bits)):
                # 返回原始二维数组中的索引位置
                # 计算对应的二维数组索引
                array_index = 0
                bit_count = 0
                for arr in bits:
                    if i < bit_count + len(arr):
                        return array_index
                    bit_count += len(arr)
                    array_index += 1
        return None


    @staticmethod
    def _bits_to_bytes(bits: List[int]) -> bytes:
        if not all(bit in (0, 1) for bit in bits):
            raise ValueError("输入列表必须只包含0或1")
        
        if len(bits) % 8 != 0:
            raise ValueError("输入比特长度必须是8的倍数")
        
        return bytes(
            sum(bit << (7 - i) for i, bit in enumerate(bits[j:j+8]))
            for j in range(0, len(bits), 8)
        )


    @staticmethod
    def _bytes_to_bits(data: bytes) -> List[int]:
        """将bytes转换为0/1列表（MSB优先）"""
        bits = []
        for byte in data:
            bits.extend([(byte >> (7-i)) & 1 for i in range(8)])
        return bits


# 使用示例
if __name__ == "__main__":
    proto = ProtocolHandler()

    # 测试数据 - 创建多组比特流载荷
    payloads = [
        [0,1,0,0,1,0,0,0, 0,1,1,0,0,1,0,1],  # "He" (8 bits per char)
        [0,1,1,0,1,0,0,0, 0,1,1,0,1,1,0,0],  # "hl"
        [0,1,1,0,1,1,0,0, 0,1,1,0,1,1,0,0],  # "ll"
        [0,1,1,0,1,1,0,0, 0,1,1,0,1,1,0,0, 0,1,1,0,1,1,0,1]  # "llm"
    ]

    # 为每组比特流生成帧
    frames = proto.build_frames(payloads)
    print(f"共生成 {len(frames)} 个帧")
    print(frames)

    # 将所有帧合并为一个比特流（模拟传输）
    combined_bits = []
    for frame in frames:
        combined_bits.extend(frame)
    print(combined_bits)

    # 解析多帧
    parsed_frames = proto.parse_frames(combined_bits)
    print(f"\n共解析到 {len(parsed_frames)} 个有效帧:")

    for i, frame in enumerate(parsed_frames, 1):
        print(f"\n帧 {i}:")
        print(f"有效: {frame['valid']}")
        if frame['valid']:
            print(f"载荷(bytes): {frame['payload']}")
            print(f"载荷(bits): {frame['payload_bits']}")
            print(f"恢复的字符串: {frame['payload'].decode('ascii')}")
        else:
            print(f"错误: {frame['error']}")
