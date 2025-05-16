import time
import data_proccess

class GroundStation:
    def __init__(self, name, satellite):
        self.name = name
        self.satellite = satellite  # 连接的卫星
    
    def send_data(self, target_name, message):
        """向目标地面站发送数据"""
        print(f"\n[{self.name}] 发起通信请求 → 目标: {target_name}")
        # print(f"    ↳ 信息: '{message}'")
        
        # 第一跳：地面站 → 卫星
        transmission_time = self.satellite.receive_from_ground(self.name, target_name, message)
        
        # 记录总传输时间
        print(f"\n★ 通信完成！总传输时间: {transmission_time:.2f} ms")

    def receive_data(self, sender, message):
        """接收来自卫星的数据"""
        recieve_data1 = data_proccess.recieve_data_proccess(message)
        print(f"[{self.name}] 收到来自 {sender} 的信息: '{recieve_data1}'")


class Satellite:
    def __init__(self, orbit_height_km=35786):  # 默认地球静止轨道高度
        self.orbit_height = orbit_height_km
        self.ground_stations = {}  # 注册的地面站字典 {name: object}
        self.processing_delay = 5  # ms 星上处理时延
    
    def register_station(self, ground_station):
        """注册地面站"""
        self.ground_stations[ground_station.name] = ground_station
    
    def calculate_propagation_delay(self, station1, station2):
        """计算传播时延（简化版）"""
        # 假设卫星位于两站中间位置
        distance = 2 * self.orbit_height  # 近似往返距离（km）
        light_speed = 299792  # km/s
        return (distance / light_speed) * 1000  # 转换为毫秒
    
    def receive_from_ground(self, sender_name, target_name, message):
        """接收地面站数据并转发"""
        start_time = time.time()
        
        # 验证目标是否存在
        if target_name not in self.ground_stations:
            raise ValueError(f"目标地面站 {target_name} 未注册！")
        
        print(f"\n[卫星] 收到来自 {sender_name} 的上行数据")
        print("    ↳ 开始星上处理...")
        
        # 处理时延
        time.sleep(self.processing_delay / 1000)
        
        # 计算传播时延
        propagation_delay = self.calculate_propagation_delay(sender_name, target_name)
        
        # 第二跳：卫星 → 目标地面站
        self.ground_stations[target_name].receive_data(sender_name, message)
        
        # 计算总传输时间
        total_time = (time.time() - start_time) * 1000  # 转换为毫秒
        return total_time


# 模拟演示
if __name__ == "__main__":
    # 创建卫星（地球静止轨道）
    sat = Satellite()
    
    # 创建两个地面站并注册
    gs_beijing = GroundStation("北京地面站", sat)
    gs_newyork = GroundStation("酒泉地面站", sat)
    sat.register_station(gs_beijing)
    sat.register_station(gs_newyork)
    
    data = data_proccess.send_data_proccess()

    # # 北京站发送测试消息
    gs_beijing.send_data("酒泉地面站", data)