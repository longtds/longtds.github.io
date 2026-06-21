# 异常检测

## 统计方法（L1）

```python
# 3σ 离群检测
import numpy as np

def detect_anomaly_3sigma(values, threshold=3):
    mean = np.mean(values)
    std = np.std(values)
    return [abs(v - mean) > threshold * std for v in values]

# 移动平均漂移
def detect_trend(values, window=5):
    ma = np.convolve(values, np.ones(window)/window, mode='valid')
    return ma
```

## 时序预测（L2）

Prophet 是 Facebook 开源的时序预测工具，适合有周期性的指标。

```python
from prophet import Prophet

model = Prophet(yearly_seasonality=False, weekly_seasonality=True)
model.fit(df)
future = model.make_future_dataframe(periods=24, freq='H')
forecast = model.predict(future)
```

## ML 方法（L3）

| 方法 | 场景 | 优点 | 缺点 |
|:---|:---|:---|:---|
| Isolation Forest | 通用异常检测 | 无需标注 | 不适用时序 |
| VAE (变分自编码器) | 多维指标 | 可解释性 | 训练复杂 |
| LSTM | 时序异常 | 捕捉长期依赖 | 资源消耗高 |

## 推理场景检测指标

- TPOT 突增检测（模型变慢）
- GPU 故障预测（ECC 错误率趋势）
- 显存碎片化检测（batch size 下降）
- 模型行为漂移（输出分布变化）
