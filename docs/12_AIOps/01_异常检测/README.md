# 异常检测

> AIOps 第一战场。**没有异常检测就没有 AIOps**——告警、定位、自愈、容量预测、SLO 守门全都建立在它之上。

## 一、异常检测的真实问题

```
监控数据的特点:
  - 高基数（百万级时间序列）
  - 多模态（指标 + 日志 + Trace + 事件）
  - 强周期（工作日/周末/节假日）
  - 弱标签（异常样本极少）
  - 概念漂移（业务和容量随时间变化）

传统阈值告警的痛点:
  ❌ 阈值难定（每个指标/服务/时段不同）
  ❌ 告警洪水（一个故障触发数百告警）
  ❌ 误报漏报（业务峰谷自然变化被误报）
  ❌ 维护爆炸（万级指标 × 多套环境）

→ 必须用算法：把"专家拍脑袋阈值"换成"数据驱动决策"
```

## 二、异常检测分层方法论（L1-L5）

```
L1  规则与统计     固定阈值 / 3σ / IQR / 同比环比
L2  时序分解       STL / Prophet / Holt-Winters
L3  机器学习       Isolation Forest / OneClassSVM / LOF / DBSCAN
L4  深度学习       AutoEncoder / VAE / LSTM-AE / Transformer
L5  专用框架/平台   ADTK / PyOD / Merlion / Kats / Skyline
```

**实战经验**：80% 场景 **L1 + L2** 已足够，**L3** 处理多维度，**L4** 处理复杂模式，**L5** 用框架封装提速。

---

## 三、L1：统计方法（最常用、最稳）

### 3.1 3σ / Z-Score 离群检测

```python
import numpy as np

def detect_3sigma(values, threshold=3.0):
    """适合：近似正态分布、稳定指标（CPU/内存）"""
    arr = np.asarray(values, dtype=float)
    mean, std = arr.mean(), arr.std()
    z = np.abs((arr - mean) / std)
    return z > threshold, z

# 改良版：滚动 3σ（适合非平稳序列）
def rolling_3sigma(values, window=60, threshold=3.0):
    s = pd.Series(values)
    mean = s.rolling(window).mean()
    std  = s.rolling(window).std()
    z    = (s - mean).abs() / std
    return z > threshold
```

**适用 / 不适用**：
- ✅ CPU、内存、磁盘使用率（近似正态）
- ❌ QPS、请求耗时（重尾分布，长尾会误报）

### 3.2 IQR（四分位距）—— 抗离群更强

```python
def detect_iqr(values, k=1.5):
    """适合：重尾分布、对极端值不敏感"""
    q1, q3 = np.percentile(values, [25, 75])
    iqr = q3 - q1
    lower, upper = q1 - k*iqr, q3 + k*iqr
    return [(v < lower) | (v > upper) for v in values]
```

### 3.3 MAD（中位绝对偏差）—— 比 3σ 更抗噪

```python
def detect_mad(values, threshold=3.5):
    """工业界：比 3σ 更稳健，推荐生产用"""
    arr = np.asarray(values)
    med = np.median(arr)
    mad = np.median(np.abs(arr - med))
    score = 0.6745 * (arr - med) / mad   # 修正系数
    return np.abs(score) > threshold
```

### 3.4 同比 / 环比

```python
def yoy_anomaly(today_value, history_same_time, ratio_threshold=0.3):
    """昨天/上周同时间点对比，业务指标必用"""
    baseline = np.median(history_same_time)
    deviation = (today_value - baseline) / baseline
    return abs(deviation) > ratio_threshold, deviation
```

**生产经验**：
```
监控告警里最有效的"算法"其实是:
  当前值 vs 上周同时段中位数 偏离 > 30%
  
简单暴力但精度高，万亿大厂都在用。
```

### 3.5 EWMA（指数加权移动平均）

```python
def ewma_anomaly(values, alpha=0.3, k=3):
    """对最近值更敏感，适合短期突变"""
    s = pd.Series(values)
    ewma = s.ewm(alpha=alpha).mean()
    std  = s.ewm(alpha=alpha).std()
    return (s - ewma).abs() > k * std
```

---

## 四、L2：时序分解与预测

### 4.1 STL 分解（Trend + Season + Residual）

```python
from statsmodels.tsa.seasonal import STL

# 把序列拆成 趋势 + 季节性 + 残差
res = STL(ts, period=24*60).fit()   # 周期 1 天（分钟粒度）
trend, season, resid = res.trend, res.seasonal, res.resid

# 在残差上跑 3σ
anomaly_mask = np.abs(resid) > 3 * resid.std()
```

**关键**：先去掉趋势和周期，在**残差**上检测异常——这是工业界最常用的"基线 + 偏离"模式。

### 4.2 Prophet（Facebook）

```python
from prophet import Prophet

df = pd.DataFrame({'ds': timestamps, 'y': values})

model = Prophet(
    yearly_seasonality=False,
    weekly_seasonality=True,
    daily_seasonality=True,
    interval_width=0.99,            # 99% 置信区间
    changepoint_prior_scale=0.05    # 趋势变化敏感度
)
model.add_country_holidays(country_name='CN')
model.fit(df)

future = model.make_future_dataframe(periods=24, freq='H')
forecast = model.predict(future)

# 真实值落在 [yhat_lower, yhat_upper] 外 = 异常
merged = df.merge(forecast[['ds','yhat','yhat_lower','yhat_upper']], on='ds')
merged['anomaly'] = (merged['y'] < merged['yhat_lower']) | \
                    (merged['y'] > merged['yhat_upper'])
```

**适用**：
- ✅ 有明确周期（每天/每周）
- ✅ 业务指标（订单/QPS/流量）
- ✅ 节假日影响明显

### 4.3 Holt-Winters（指数平滑）

```python
from statsmodels.tsa.holtwinters import ExponentialSmoothing

model = ExponentialSmoothing(
    ts,
    trend='add',
    seasonal='add',
    seasonal_periods=24
).fit()

pred = model.forecast(steps=12)
residuals = ts - model.fittedvalues
anomaly = np.abs(residuals) > 3 * residuals.std()
```

**特点**：比 Prophet 轻量，纯 statsmodels，无 C++ 依赖，适合大规模部署。

### 4.4 ARIMA / SARIMA

```python
from statsmodels.tsa.arima.model import ARIMA

model = ARIMA(ts, order=(1,1,1), seasonal_order=(1,1,1,24)).fit()
pred = model.get_forecast(steps=10)
mean, conf = pred.predicted_mean, pred.conf_int()

# 真实值在置信区间外 = 异常
```

**适用**：单序列、需要严谨统计检验的场景（金融、容量规划）。

### 4.5 何时选哪个

| 方法 | 训练速度 | 周期支持 | 节假日 | 鲁棒性 | 推荐度 |
|:---|:---:|:---:|:---:|:---:|:---:|
| STL + 3σ | ⭐⭐⭐⭐⭐ | 单周期 | ❌ | ⭐⭐⭐⭐ | **生产首选** |
| Prophet | ⭐⭐⭐ | 多周期 | ✅ | ⭐⭐⭐⭐ | 业务指标 |
| Holt-Winters | ⭐⭐⭐⭐ | 单周期 | ❌ | ⭐⭐⭐ | 轻量替代 |
| ARIMA | ⭐⭐ | 季节性 | ❌ | ⭐⭐⭐ | 学术 / 容量 |

---

## 五、L3：机器学习方法（sklearn 全家桶）

### 5.1 Isolation Forest（孤立森林）⭐⭐⭐⭐⭐

```python
from sklearn.ensemble import IsolationForest
import numpy as np

# 多维特征示例：[CPU, MEM, QPS, P99]
X = np.array([
    [60, 70, 1200, 180],
    [62, 71, 1180, 175],
    [58, 69, 1300, 190],
    [95, 90, 200,  3500],   # 异常：高 CPU + 高延迟 + 低 QPS
    ...
])

clf = IsolationForest(
    n_estimators=200,
    contamination=0.01,     # 假设异常占 1%
    max_samples='auto',
    random_state=42,
    n_jobs=-1
)
clf.fit(X)

pred = clf.predict(X)        # 1 正常，-1 异常
score = clf.decision_function(X)  # 分数越低越异常

# 增量预测
new_X = np.array([[70, 80, 1500, 220]])
print(clf.predict(new_X))
```

**核心思想**：随机切分数据，异常点更容易被快速隔离（树深度浅）。

**生产建议**：
- `contamination` 设小（0.001-0.01），避免误报
- 训练数据**必须用正常时段**
- 周期性重训（每周/每月，业务变化）

### 5.2 One-Class SVM

```python
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

clf = OneClassSVM(
    kernel='rbf',
    gamma='auto',
    nu=0.01                  # 异常比例上限
)
clf.fit(X_scaled)

pred = clf.predict(X_scaled)         # 1 / -1
score = clf.score_samples(X_scaled)  # 越大越正常
```

**适用**：小数据集（< 10k）、高维特征。
**不适用**：大规模数据（O(n²) 训练慢）、强周期序列。

### 5.3 LOF（Local Outlier Factor）

```python
from sklearn.neighbors import LocalOutlierFactor

# 离线检测
clf = LocalOutlierFactor(n_neighbors=20, contamination=0.01)
pred = clf.fit_predict(X)              # 直接 fit + predict

# 在线检测（novelty mode）
clf2 = LocalOutlierFactor(n_neighbors=20, novelty=True)
clf2.fit(X_train)
pred = clf2.predict(X_new)
```

**适合**：局部密度变化场景（同样的值在 A 区域正常，在 B 区域异常）。

### 5.4 DBSCAN（密度聚类做异常）

```python
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

X_scaled = StandardScaler().fit_transform(X)
clf = DBSCAN(eps=0.5, min_samples=10)
labels = clf.fit_predict(X_scaled)
# label = -1 即为噪声点 / 异常
anomalies = X[labels == -1]
```

**适合**：任意形状簇、稀疏点天然识别为异常。
**不适合**：维度 > 20（要先降维）。

### 5.5 Elliptic Envelope（椭圆包络）

```python
from sklearn.covariance import EllipticEnvelope

clf = EllipticEnvelope(contamination=0.01, support_fraction=0.9)
clf.fit(X)
pred = clf.predict(X)
```

**适合**：高斯分布的多维数据。

### 5.6 KNN 距离法

```python
from sklearn.neighbors import NearestNeighbors

nn = NearestNeighbors(n_neighbors=20)
nn.fit(X_train)
distances, _ = nn.kneighbors(X_test)
score = distances.mean(axis=1)    # 平均距离越大越异常
threshold = np.percentile(score, 99)
anomaly = score > threshold
```

**优点**：直观、好解释，给 SRE 看的报告里"距离 N 个最相似时段的平均偏离"很有说服力。

### 5.7 五种 sklearn 方法对比

| 方法 | 时间复杂度 | 维度 | 训练量 | 适合场景 |
|:---|:---:|:---:|:---:|:---|
| **Isolation Forest** | O(n log n) | 中-高 | 大 | **通用首选** |
| One-Class SVM | O(n²) | 高 | 小 | 小数据高维 |
| LOF | O(n²) | 中 | 中 | 局部密度变化 |
| DBSCAN | O(n²) | 低-中 | 中 | 聚类 + 异常 |
| Elliptic Envelope | O(n × d²) | 低 | 中 | 高斯分布 |

### 5.8 PyOD（统一 ML 异常检测库）⭐⭐⭐⭐⭐

```python
# PyOD 封装 40+ 算法，API 统一，sklearn 风格
# pip install pyod

from pyod.models.iforest import IForest
from pyod.models.lof import LOF
from pyod.models.knn import KNN
from pyod.models.copod import COPOD      # 概率方法，无需调参
from pyod.models.ecod import ECOD         # 2022 新算法，零调参
from pyod.models.combination import aom, moa, average, maximization

# 多模型集成
models = [IForest(), LOF(), KNN(), COPOD(), ECOD()]
scores = np.zeros([X.shape[0], len(models)])
for i, m in enumerate(models):
    m.fit(X)
    scores[:, i] = m.decision_function(X)

# 集成分数（平均）
final_score = average(scores)

# 自动阈值
from pyod.utils.utility import standardizer
threshold = np.percentile(final_score, 99)
```

**强烈推荐**：PyOD 已成 Python 异常检测**事实标准库**，比手工调 sklearn 快得多。

---

## 六、L4：深度学习方法

### 6.1 AutoEncoder（自编码器）

```python
import torch, torch.nn as nn

class AE(nn.Module):
    def __init__(self, dim_in, dim_z=8):
        super().__init__()
        self.enc = nn.Sequential(
            nn.Linear(dim_in, 32), nn.ReLU(),
            nn.Linear(32, 16), nn.ReLU(),
            nn.Linear(16, dim_z)
        )
        self.dec = nn.Sequential(
            nn.Linear(dim_z, 16), nn.ReLU(),
            nn.Linear(16, 32), nn.ReLU(),
            nn.Linear(32, dim_in)
        )
    def forward(self, x):
        return self.dec(self.enc(x))

# 训练只用正常数据
model = AE(dim_in=10).cuda()
opt   = torch.optim.Adam(model.parameters(), lr=1e-3)
for ep in range(100):
    for batch in normal_loader:
        x = batch.cuda()
        y = model(x)
        loss = nn.functional.mse_loss(y, x)
        opt.zero_grad(); loss.backward(); opt.step()

# 推理：重构误差大 = 异常
def detect(x):
    with torch.no_grad():
        err = ((model(x) - x) ** 2).mean(dim=1)
    return err > threshold
```

**核心思想**：模型只见过正常数据，重构异常数据会出错。

### 6.2 VAE（变分自编码器）

```python
# 比 AE 多一个概率重构损失项 + KL 散度
# 可输出"异常概率"，更可解释
# 多维指标异常检测主流选择
```

### 6.3 LSTM-AE（时序 AE）

```python
class LSTMAE(nn.Module):
    def __init__(self, n_features, hidden=64):
        super().__init__()
        self.enc = nn.LSTM(n_features, hidden, batch_first=True)
        self.dec = nn.LSTM(hidden, n_features, batch_first=True)
    def forward(self, x):
        h, _ = self.enc(x)
        out, _ = self.dec(h)
        return out
# 训练同 AE，输入窗口序列
```

**适合**：多变量时序，捕捉时间依赖。

### 6.4 Transformer-based（2024+ 新势力）

| 模型 | 用途 |
|:---|:---|
| **Anomaly Transformer** | 单序列异常检测 SOTA |
| **TranAD** | 多变量异常检测 |
| **TimesNet** | 通用时序基础模型 |
| **Chronos / Lag-Llama / TimeGPT** | 时序大模型，零样本 |

```python
# Chronos: Amazon 开源时序大模型
from chronos import ChronosPipeline

pipe = ChronosPipeline.from_pretrained("amazon/chronos-t5-small")
forecast = pipe.predict(context=ts[-512:], prediction_length=24, num_samples=20)
# 真实值在预测分布外 = 异常
```

### 6.5 推荐技术选型（DL 部分）

| 数据特点 | 推荐 |
|:---|:---|
| 单序列 + 周期 | Prophet / Anomaly Transformer |
| 多变量时序 | LSTM-AE / TranAD |
| 高维多模态 | VAE / Deep SVDD |
| 大量未标注 | AutoEncoder / IForest |
| 极少标注但要高精度 | 半监督 DeepSAD |
| 想零样本 | Chronos / Lag-Llama |

---

## 七、L5：开源框架与平台

### 7.1 ADTK（轻量级 sklearn 风格）

```python
# pip install adtk
from adtk.data import validate_series
from adtk.detector import (
    ThresholdAD, QuantileAD, InterQuartileRangeAD,
    SeasonalAD, AutoregressionAD, PersistAD
)
from adtk.aggregator import OrAggregator
from adtk.visualization import plot

s = validate_series(ts)

# 季节性检测
detector1 = SeasonalAD(c=3.0, side='both')
ad1 = detector1.fit_detect(s)

# 自回归检测
detector2 = AutoregressionAD(n_steps=7*24)
ad2 = detector2.fit_detect(s)

# 多检测器投票
agg = OrAggregator()
combined = agg.aggregate([ad1, ad2])

plot(s, anomaly=combined, anomaly_color='red')
```

### 7.2 Merlion（Salesforce）

```python
# pip install salesforce-merlion
from merlion.utils import TimeSeries
from merlion.models.defaults import DefaultDetectorConfig, DefaultDetector

ts = TimeSeries.from_pd(df)
model = DefaultDetector(DefaultDetectorConfig())
model.train(ts)
labels = model.get_anomaly_label(ts)
scores = model.get_anomaly_score(ts)
```

**优势**：自动选模型 + 集成 + 评估指标完整。

### 7.3 Kats（Meta）

```python
# pip install kats
from kats.consts import TimeSeriesData
from kats.detectors.outlier import OutlierDetector
from kats.detectors.cusum_detection import CUSUMDetector

ts_data = TimeSeriesData(df)

# 综合异常检测
od = OutlierDetector(ts_data, decomp='additive', iqr_mult=3.0)
od.detector()
outliers = od.outliers

# 突变点检测（业务转折）
cusum = CUSUMDetector(ts_data)
changes = cusum.detector()
```

### 7.4 Skyline / Anomalia / Suod

| 框架 | 用途 |
|:---|:---|
| **Etsy Skyline** | 老牌指标异常检测 |
| **Linkedin ThirdEye** | 平台级（带 UI） |
| **NetData ML** | 嵌入式 ML |
| **Anomalia** | 多算法集成 |
| **SUOD** | PyOD 子集，大规模加速 |

### 7.5 商业 / 闭源

| 产品 | 特点 |
|:---|:---|
| Datadog Watchdog | 自动基线 |
| Dynatrace Davis | AI 因果 |
| New Relic Lookout | 自动异常 |
| 阿里云 ARMS Insights | 国内主流 |
| 腾讯云 Anomaly | 国内 |

---

## 八、多指标 / 多维度异常检测

### 8.1 KPI 关联挖掘

```python
# 多 KPI 一起检测，避免单指标误报
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

X = df[['cpu','mem','qps','p99','err_rate']].values
Xn = StandardScaler().fit_transform(X)

# PCA 降维 + 重构误差
pca = PCA(n_components=3).fit(Xn)
recon = pca.inverse_transform(pca.transform(Xn))
err = ((Xn - recon)**2).sum(axis=1)
anomaly = err > np.percentile(err, 99)
```

### 8.2 多维 IForest

```python
# 直接把所有指标喂给 IForest，让模型自己学相关性
clf = IsolationForest(contamination=0.005, n_estimators=300)
clf.fit(df[features])
df['anomaly'] = clf.predict(df[features]) == -1
df['score']   = -clf.score_samples(df[features])

# 异常 case 输出解释
import shap
explainer = shap.TreeExplainer(clf)
shap_values = explainer.shap_values(df[features].iloc[anomaly_idx])
shap.force_plot(...)
```

### 8.3 微服务调用链异常

```
方法:
  - 每个 service-endpoint 单独建模
  - Trace 上做图异常检测（GraphSAGE / GNN）
  - p99 + error_rate + qps 联合检测
  
工具:
  - OpenTelemetry → Tempo / Jaeger → 分析层
  - Pinpoint / SkyWalking AI 插件
```

---

## 九、推理 / GPU / LLM 场景的异常检测

### 9.1 推理服务关键指标

| 指标 | 异常含义 |
|:---|:---|
| **TPOT**（每 token 时延） | 模型变慢 / KV Cache 满 |
| **TTFT**（首 token 时延） | Prefill 拥堵 |
| **GPU SM 利用率** | 调度不均 / 显存碎片 |
| **GPU 显存使用** | 模型膨胀 / 泄漏 |
| **ECC 错误率** | GPU 即将故障 |
| **NCCL 重传率** | 网络抖动 |
| **batch size** | 调度策略问题 |

### 9.2 GPU 异常检测示例

```python
# DCGM Exporter 暴露指标 → Prometheus → 检测
features = ['gpu_util', 'mem_used', 'temp', 'ecc_errors', 'power']

# 单卡建模 + 跨卡协同
clf = IsolationForest(contamination=0.001)
clf.fit(historical_normal_data)

# 故障预测：ECC 错误数 7 日累计 > 阈值 OR 温度持续 > 85
def gpu_health_score(df):
    ecc_trend = df['ecc_errors'].diff().rolling(168).sum()  # 7d 累计
    temp_high = (df['temp'] > 85).rolling(60).sum()
    return ecc_trend + temp_high * 10
```

### 9.3 LLM 输出漂移

```python
# 输出 token 长度分布异常 = 模型出问题
# perplexity 突增 = 输入分布变了
# 拒答率突增 = 模型/policy 异常

from scipy.stats import wasserstein_distance

def drift_detect(today_outputs, baseline_outputs):
    """Earth Mover Distance 检测分布漂移"""
    return wasserstein_distance(today_outputs, baseline_outputs)
```

### 9.4 推理 SLO 守门

```
关键 SLO:
  - TTFT P99 < 500ms
  - TPOT P99 < 50ms
  - 错误率 < 0.1%
  - GPU 故障率 < 1/月

检测策略:
  - 实时滑窗 + EWMA
  - 多维度联合（不要只看 P99）
  - 告警分级 (warn/critical)
```

---

## 十、实战架构

### 10.1 完整数据管道

```
数据源:
  Prometheus / VictoriaMetrics / InfluxDB
   ↓
预处理:
  - 缺失值填充（前向填充/插值）
  - 去抖动（EWMA 平滑）
  - 重采样（统一粒度）
  - 归一化（StandardScaler / MinMax）
   ↓
特征工程:
  - 时间特征（hour, dow, holiday）
  - 滚动统计（mean/std/p95）
  - 差分 / 同比 / 环比
  - 多指标组合
   ↓
检测引擎:
  L1 规则（实时）  ────→ 告警
  L2 STL/Prophet（小时级） ────→ 告警
  L3 IForest/PyOD（小时-天） ────→ 告警
  L4 AE/LSTM-AE（天级）  ────→ 告警
   ↓
后处理:
  - 抑制（同故障合并）
  - 投票（多算法集成）
  - 业务过滤（变更窗口屏蔽）
   ↓
告警分发:
  Prometheus Alertmanager / 自研网关
   ↓
LLM 加工:
  原始告警 → LLM 摘要 + 根因建议
   ↓
通知:
  企业微信 / 钉钉 / 飞书 / 短信
```

### 10.2 工业部署样板

```python
# 周期性训练 + 在线推理
import joblib, schedule

# 训练任务（每天凌晨）
def train_daily():
    df = load_recent_30days()
    df = preprocess(df)
    clf = IsolationForest(contamination=0.005, n_estimators=200)
    clf.fit(df[features])
    joblib.dump(clf, f'/models/iforest-{date.today()}.pkl')

# 推理任务（每分钟）
def detect_realtime():
    clf = joblib.load('/models/iforest-latest.pkl')
    df_now = load_last_5min()
    df_now = preprocess(df_now)
    score = -clf.score_samples(df_now[features])
    anomalies = df_now[score > threshold]
    if not anomalies.empty:
        send_alert(anomalies)

schedule.every().day.at("03:00").do(train_daily)
schedule.every(1).minutes.do(detect_realtime)
```

### 10.3 部署形态

| 形态 | 适合 |
|:---|:---|
| **Sidecar 检测**（每节点本地） | 边缘 / 嵌入式 |
| **集中检测服务**（一个 Flask/FastAPI） | 中小规模 |
| **Spark / Flink 流式** | 大规模 |
| **Ray Serve** | 多模型并发 |
| **Prom 内置 + Cortex/Mimir** | 云原生 |

---

## 十一、评估指标（你的算法到底准不准）

```
基础指标:
  Precision  = TP / (TP + FP)  误报敏感
  Recall     = TP / (TP + FN)  漏报敏感
  F1         = 2PR / (P+R)
  AUC-PR     = 异常稀有场景比 ROC 更准

时序专用:
  Point-Adjust F1（事件级而非点级）
  Affiliation Metrics
  VUS-ROC / VUS-PR（连续异常段）

业务指标:
  MTTD (Mean Time to Detect) 越短越好
  MTTR (Mean Time to Recover)
  Alert Volume / day（噪声多少）
  False Alarm Rate
```

```python
from sklearn.metrics import precision_score, recall_score, f1_score, average_precision_score
from sklearn.metrics import classification_report, confusion_matrix

print(classification_report(y_true, y_pred))
print(confusion_matrix(y_true, y_pred))
print('AUC-PR:', average_precision_score(y_true, y_score))
```

---

## 十二、常见坑（生产血泪）

| 坑 | 建议 |
|:---|:---|
| **用全量数据训** | 必须用正常时段（人工筛 or 规则过滤） |
| **没做归一化** | 不同量纲指标会被 IForest 偏置 |
| **contamination 设大** | 默认 0.01 起，太大全是误报 |
| **模型不重训** | 业务在变，模型每周重训一次 |
| **没有同比** | 工作日 vs 周末 vs 节假日完全不同 |
| **告警洪水** | 加抑制 + 时间窗合并 |
| **多算法不投票** | 单算法误报高，集成投票必装 |
| **没有变更窗口屏蔽** | 发布期/演练期数据不应进入训练 |
| **季节性没去掉** | 必先 STL 拆出残差再检测 |
| **数据缺失没处理** | 缺失被当成 0 触发误报 |
| **特征工程偷懒** | 衍生特征比原始更有信号 |
| **没有可解释性** | SHAP / 重要特征排序必加 |
| **训练数据只一个服务** | 集群级模型 + 服务级微调 |
| **DL 用错场景** | 数据 < 万条不要上 DL |
| **算法集成无去重** | 各算法分数标准化后再聚合 |

---

## 十三、推荐技术栈（2025）

### 13.1 中小团队（百-千指标）

```
存储:     Prometheus + Thanos / VictoriaMetrics
检测:     PyOD + Prophet + sklearn
框架:     ADTK / Merlion
集成:     Python FastAPI 微服务
告警:     Alertmanager → LLM 加工 → 企业微信
可视化:   Grafana
```

### 13.2 大型团队（万-百万指标）

```
存储:     VictoriaMetrics Cluster / TDengine
计算:     Flink / Spark Streaming
检测:     PyOD + Merlion + 自研 DL（VAE/LSTM-AE）
模型存储: MLflow / Weights & Biases
特征:     Feast / 自研 FS
平台:     Kubeflow / Ray Serve
告警:     自研网关 + 抑制 + 分级 + LLM 加工
可视化:   Grafana + 自研根因 UI
```

### 13.3 国产可替代清单

| 国外 | 国产 |
|:---|:---|
| Prometheus | VictoriaMetrics（更轻）/ Nightingale |
| InfluxDB | TDengine（国产时序冠军） |
| Grafana | Grafana 直接用 / 自研 |
| Watchdog/Davis | 阿里 ARMS / 腾讯云 / 华为云 |

---

## 十四、学习路径

```
入门（1 周）:
  1. Pandas + NumPy 时序基础
  2. 3σ / IQR / MAD 三大统计法实现
  3. Prophet 跑通业务指标

中级（1 个月）:
  4. sklearn 五大异常检测算法
  5. PyOD 全家桶上手
  6. Isolation Forest 调参实战
  7. STL 分解 + 残差检测

进阶（3 个月）:
  8. AutoEncoder / VAE 多维异常
  9. LSTM-AE 时序深度检测
  10. ADTK / Merlion / Kats 框架
  11. 多算法集成 + SHAP 可解释

专家（半年+）:
  12. Anomaly Transformer / TranAD 复现
  13. 推理服务 / GPU 健康度建模
  14. 因果分析 + 根因定位
  15. 时序大模型（Chronos/TimesFM）落地
  16. 自研 AIOps 平台
```

---

## 十五、参考资料

```
论文:
  - "Isolation Forest" (Liu et al., 2008)
  - "Outlier Detection: A Survey" (Aggarwal)
  - "Anomaly Transformer" (Xu et al., 2022)
  - "TimesNet" (Wu et al., 2023)
  - "Chronos: Learning the Language of Time Series" (Amazon, 2024)

书:
  - 《Outlier Analysis》(Aggarwal)
  - 《Practical Time Series Analysis》(O'Reilly)
  - 《AIOps 实战》(电子工业出版社)

开源:
  - PyOD: https://github.com/yzhao062/pyod
  - ADTK: https://github.com/arundo/adtk
  - Merlion: https://github.com/salesforce/Merlion
  - Kats: https://github.com/facebookresearch/Kats
  - TODS: https://github.com/datamllab/tods
  - Awesome AD: https://github.com/yzhao062/anomaly-detection-resources

数据集:
  - NAB (Numenta Anomaly Benchmark)
  - Yahoo S5 Webscope
  - SMD (Server Machine Dataset)
  - MSL / SMAP (NASA)
  - KPI Anomaly Detection Dataset (清华)
```

---

> 📖 **核心判断**：异常检测不是"上算法"那么简单。**生产里 80% 价值来自 L1+L2（统计 + 时序分解）**，sklearn ML 方法（**Isolation Forest 是事实标准**）覆盖多维场景，深度学习只在数据量大且复杂模式下才划算。**PyOD + Prophet + ADTK** 是 2025 中小团队最性价比的三件套。最容易翻车的不是算法选错，而是：训练数据没清洗、没做季节性分解、没有多算法投票、没有业务变更窗口屏蔽——记住这四条比记 100 个算法更有用。
