import requests
import time

# 新应用配置
api_key = "app-eAalqcHLyQrAs45tXXxq0lGG"
url = "http://localhost/v1/workflows/run"

# 测试摘要
abstract = """本发明涉及心脏血液泵技术领域，具体涉及被动式心室辅助循环装置。包括：电机体外壳，电机体外壳内配置有定子、转子，定子、转子中的一个包括线圈；套装的轴流通道壳；轴流通道壳的上端被配置主动脉瓣面向至心室的下面，电源，被配置操作耦接到所述线圈；控制器，被配置操作耦接到所述电源以人工选定模式选择控制所述电源改变所述转子为某一转速后，转子以某一转速模式保持工作，不同某一转速被配置有对应的流体出口界面输出的辅助压力。该装置控制在一个转速状态，待心衰患者的心脏搏动提供比正常心脏收缩压力小的收缩压时，当收缩压与辅助压力共同叠加提供正常心脏收缩压力，使得心衰患者维持一个正常心脏收缩压力。"""

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "inputs": {
        "abstract": abstract
    },
    "response_mode": "blocking",
    "user": "pq"
}

print("开始测试响应时间...")
print("=" * 50)

# 测试3次取平均值
times = []
for i in range(3):
    start_time = time.time()
    try:
        response = requests.post(url, headers=headers, json=data, timeout=120)
        end_time = time.time()
        elapsed = end_time - start_time
        times.append(elapsed)

        if response.status_code == 200:
            result = response.json()
            print(f"测试 {i+1}: {elapsed:.2f}s")
            print(f"完整响应: {result}")
            outputs = result.get('data', {}).get('outputs', {})
            print(f"outputs: {outputs}")
        else:
            print(f"测试 {i+1}: {elapsed:.2f}s, 错误: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"测试 {i+1}: 失败, 错误: {e}")

print("=" * 50)
if times:
    avg_time = sum(times) / len(times)
    print(f"平均响应时间: {avg_time:.2f}s")
    print(f"建议并发间隔: {avg_time * 2:.2f}s (响应时间 * 2)")