import RPi.GPIO as GPIO
import time
import math
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.ticker import MaxNLocator
import numpy as np

# 配置参数
C = 0.33e-6  # 电容值，单位为法拉(F)
R1 = 1000    # 固定电阻值，单位为欧姆(Ω)
V_THRESHOLD = 1.65  # GPIO阈值电压(V)
V_SUPPLY = 3.3      # 电源电压(V)
MAX_CHARGE_TIME = 0.1  # 最大充电时间(s)
MEASUREMENTS_PER_SAMPLE = 100  # 每次采样的测量次数
SAMPLE_INTERVAL = 0.5  # 采样间隔时间(s)
MAX_DATA_POINTS = 50  # 图表上显示的最大数据点数

# GPIO引脚配置
a_pin = 18
b_pin = 23

# 初始化中文字体支持
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
plt.rcParams["axes.unicode_minus"] = False  # 正确显示负号

# 初始化GPIO
def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(a_pin, GPIO.IN)
    GPIO.setup(b_pin, GPIO.IN)

# 电容放电
def discharge_capacitor():
    GPIO.setup(a_pin, GPIO.OUT)
    GPIO.output(a_pin, GPIO.LOW)
    GPIO.setup(b_pin, GPIO.OUT)
    GPIO.output(b_pin, GPIO.LOW)
    time.sleep(0.1)
    GPIO.setup(a_pin, GPIO.IN)
    GPIO.setup(b_pin, GPIO.IN)

# 测量充电时间
def measure_charge_time():
    discharge_capacitor()
    
    GPIO.setup(a_pin, GPIO.OUT)
    GPIO.output(a_pin, GPIO.HIGH)
    start_time = time.time()
    
    while GPIO.input(b_pin) == GPIO.LOW:
        if time.time() - start_time > MAX_CHARGE_TIME:
            raise TimeoutError("充电超时")
    
    charge_time = time.time() - start_time
    GPIO.setup(a_pin, GPIO.IN)
    
    return charge_time

# 计算电阻值
def calculate_resistance(charge_time):
    ln_term = math.log(V_SUPPLY / (V_SUPPLY - V_THRESHOLD))
    total_resistance = charge_time / (C * ln_term)
    return total_resistance - R1

# 读取平均电阻值
def read_average_resistance():
    measurements = []
    for _ in range(MEASUREMENTS_PER_SAMPLE):
        try:
            t = measure_charge_time()
            r = calculate_resistance(t)
            if 10 < r < 100000:  # 过滤异常值
                measurements.append(r)
        except Exception as e:
            print(f"测量错误: {e}")
        finally:
            discharge_capacitor()
    
    if not measurements:
        return None
    
    return sum(measurements) / len(measurements)

# 实时绘图初始化
def init_plot():
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title('实时电阻值监测')
    ax.set_xlabel('测量点')
    ax.set_ylabel('电阻值 (Ω)')
    ax.grid(True)
    
    # 设置x轴为整数
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    
    return fig, ax

# 主函数
def main():
    try:
        setup_gpio()
        print(f"开始电阻测量 (每 {SAMPLE_INTERVAL} 秒采样一次，每次采样 {MEASUREMENTS_PER_SAMPLE} 次)")
        print("按 Ctrl+C 停止")
        
        fig, ax = init_plot()
        line, = ax.plot([], [], 'b-', lw=2)
        x_data, y_data = [], []
        measurement_count = 0
        
        def update(frame):
            nonlocal measurement_count
            start_time = time.time()
            
            # 读取电阻值
            resistance = read_average_resistance()
            
            if resistance is not None:
                measurement_count += 1
                x_data.append(measurement_count)
                y_data.append(resistance)
                
                # 限制数据点数量
                if len(x_data) > MAX_DATA_POINTS:
                    x_data.pop(0)
                    y_data.pop(0)
                
                # 更新线条数据
                line.set_data(x_data, y_data)
                
                # 更新坐标轴范围
                ax.relim()
                ax.autoscale_view()
                
                # 更新标题显示当前值
                ax.set_title(f'实时电阻值监测 - 当前值: {resistance:.2f} Ω')
                
                # 控制台输出
                current_time = time.strftime("%H:%M:%S")
                print(f"时间: {current_time}, 测量点: {measurement_count}, 平均电阻值: {resistance:.2f} Ω")
            
            # 计算剩余时间以确保0.5秒的间隔
            elapsed = time.time() - start_time
            wait_time = max(0, SAMPLE_INTERVAL - elapsed)
            time.sleep(wait_time)
            
            return line,
        
        # 设置动画，使用blit=True以提高性能
        ani = animation.FuncAnimation(
            fig, update, interval=100, blit=True, cache_frame_data=False
        )
        
        plt.tight_layout()
        plt.show()
        
    except KeyboardInterrupt:
        print("\n程序已停止")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()