import RPi.GPIO as GPIO
import time, math

C = 0.33 # 电容值，单位为微法拉uF
R1 = 1000 # 电阻值，单位为欧姆Ω

GPIO.setmode(GPIO.BCM) # 使用BCM引脚编号方式

# 引脚a通过固定的1k电阻器和热敏电阻串联为电容器充电
# 针脚b通过固定的1k电阻使电容器放电
a_pin = 18 # BCM引脚18
b_pin = 23 # BCM引脚23

GPIO.setup(a_pin, GPIO.OUT) # 设置a引脚为输出
GPIO.setup(b_pin, GPIO.IN) # 设置b引脚为输入

# 清空电容器以为其充电做准备
def discharge():
    GPIO.setup(a_pin, GPIO.OUT) # 设置a引脚为输出
    GPIO.output(a_pin, GPIO.LOW) # 将a引脚拉低
    time.sleep(0.1) # 等待100毫秒
    GPIO.setup(a_pin, GPIO.IN) # 设置a引脚为输入
    GPIO.setup(b_pin, GPIO.IN) # 设置b引脚为输入
    GPIO.output(b_pin, GPIO.LOW) # 将b引脚拉低，确保b引脚状态清晰

# 返回电容上的电压升压到1.65V所花费的时间（uS）
def charge_time():
    discharge() # 确保电容器已放电
    GPIO.setup(a_pin, GPIO.OUT) # 设置a引脚为输出
    GPIO.output(a_pin, GPIO.HIGH) # 将a引脚拉高开始充电
    start_time = time.time() # 记录开始时间
    while GPIO.input(b_pin) == GPIO.LOW: # 等待b引脚变为高电平
        pass
    end_time = time.time() # 记录结束时间
    GPIO.setup(a_pin, GPIO.IN) # 设置a引脚为输入
    return (end_time - start_time) * 1e6 # 返回充电时间，单位为微秒uS

# 以模拟读数作为首次对电容器放电后充电所需的时间
def analog_read():
    discharge() # 确保电容器已放电
    time.sleep(0.01) # 等待10毫秒
    return charge_time() # 返回充电时间

# 将电容器充电所需的时间转换为电阻值
# 为减小误差，执行100次测量并取平均值
def read_resistance():
    total_time = 0
    for _ in range(100):
        total_time += charge_time() # 累加充电时间
    average_time = total_time / 100 # 计算平均充电时间
    resistance = (average_time * 1e-6) / (C * math.log(2)) # 使用公式计算电阻值
    return resistance


try:
    while True:
        print(read_resistance()) # 打印电阻值
        time.sleep(0.5) # 每0.5秒测量一次
finally:
    GPIO.cleanup()# 清理GPIO释放资源






