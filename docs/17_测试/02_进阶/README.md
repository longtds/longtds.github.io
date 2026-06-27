# 进阶

> 测试进阶 = **API 测试(REST/GraphQL/gRPC) + Postman/Newman + 契约测试(Pact/Spring Cloud Contract) + UI 自动化进阶(Playwright/Cypress) + 移动测试(Appium/XCUITest/Espresso) + 性能测试(JMeter/k6/locust/wrk) + 数据库测试(Testcontainers) + 测试架构(POM/分层) + 测试数据管理 + CI/CD 集成 + 报告(Allure) + Flaky 治理 + 并行+分布式执行 + 国产化场景**。本章面向独立负责中型项目自动化测试的工程师。

## 一、API 测试

### 1.1 REST API

```bash
# curl 基础
curl -X POST https://api.example.com/users \
  -H "Authorization: Bearer xxx" \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice"}'

curl -w "@curl-format.txt" -o /dev/null -s ...
```

**Postman / Newman**:

```javascript
// Postman Pre-request
pm.environment.set("token", pm.collectionVariables.get("auth_token"));

// Postman Tests
pm.test("Status 200", () => pm.response.to.have.status(200));
pm.test("响应时间 < 500ms", () => pm.expect(pm.response.responseTime).to.be.below(500));
pm.test("body 包含 id", () => {
    const json = pm.response.json();
    pm.expect(json).to.have.property("id");
});
```

```bash
# Newman 命令行
newman run collection.json -e env.json -r htmlextra,allure
```

**Python + requests + pytest** ⭐:

```python
import pytest
import requests

BASE = "https://api.example.com"

@pytest.fixture
def auth_token():
    r = requests.post(f"{BASE}/login", json={"u":"x","p":"y"})
    return r.json()["token"]

def test_get_user(auth_token):
    r = requests.get(f"{BASE}/users/1", 
                      headers={"Authorization": f"Bearer {auth_token}"})
    assert r.status_code == 200
    assert r.json()["id"] == 1
    assert r.elapsed.total_seconds() < 1

@pytest.mark.parametrize("uid,expected", [(1,200),(99999,404)])
def test_user_status(auth_token, uid, expected):
    r = requests.get(f"{BASE}/users/{uid}",
                      headers={"Authorization": f"Bearer {auth_token}"})
    assert r.status_code == expected
```

**RestAssured（Java）**:

```java
given().header("Authorization","Bearer "+token)
       .when().get("/users/1")
       .then().statusCode(200)
              .body("id", equalTo(1))
              .time(lessThan(1000L));
```

**HTTP 客户端进阶**:

| 工具 | 语言 | 特点 |
|:---|:---|:---|
| **HTTPie** | CLI | 友好 |
| **Insomnia** | GUI | Postman 替代 |
| **Bruno** ⭐ | GUI | 文件版本化 (Git 友好) |
| **Hurl** | CLI | 文本驱动 + CI 友好 |
| **k6** | JS | 同时支持测 + 压 |

### 1.2 GraphQL

```python
import requests

query = """
query GetUser($id: ID!) {
  user(id: $id) { id name email }
}
"""

r = requests.post("https://api.example.com/graphql",
                  json={"query": query, "variables": {"id": "1"}})
assert r.json()["data"]["user"]["name"] == "Alice"
```

工具：**Insomnia / Postman / Altair / GraphQL Playground**

### 1.3 gRPC

```bash
# grpcurl
grpcurl -plaintext -d '{"id":1}' localhost:9090 pkg.Service/Get

# ghz 压测
ghz --insecure --proto api.proto --call pkg.Service/Get \
    -d '{"id":1}' -c 50 -n 10000 localhost:9090
```

```python
# pytest + grpc
import grpc
import user_pb2, user_pb2_grpc

def test_grpc():
    with grpc.insecure_channel("localhost:9090") as ch:
        stub = user_pb2_grpc.UserStub(ch)
        resp = stub.Get(user_pb2.UserRequest(id=1))
        assert resp.name == "Alice"
```

### 1.4 WebSocket / SSE

```python
# websocket-client
from websocket import create_connection
ws = create_connection("wss://example.com/ws")
ws.send('{"type":"ping"}')
msg = ws.recv()
assert "pong" in msg
ws.close()
```

## 二、契约测试（Contract Testing）

```
背景:
  微服务多 → E2E 太慢/脆
  契约 = Consumer 和 Provider 之间的约定
  
工具:
  Pact ⭐ (跨语言, 最流行)
  Spring Cloud Contract (Java)
  PactFlow (商业 Broker)

流程:
  1. Consumer 写测试 → 生成 Pact 文件
  2. 推到 Pact Broker
  3. Provider 拉 Pact → 验证
  4. CI 集成: Consumer/Provider 改动 → 触发验证
```

**Pact 示例（JS Consumer + Java Provider）**:

```javascript
// Consumer (JS)
const { Pact, Matchers } = require('@pact-foundation/pact');

provider.addInteraction({
    state: 'user 1 exists',
    uponReceiving: 'get user 1',
    withRequest: { method: 'GET', path: '/users/1' },
    willRespondWith: {
        status: 200,
        body: { id: Matchers.integer(1), name: Matchers.string('Alice') }
    }
});
```

```java
// Provider (Java)
@Provider("user-service")
@PactBroker(host = "broker.example.com")
class UserProviderTest {
    @TestTemplate
    @ExtendWith(PactVerificationInvocationContextProvider.class)
    void pactVerification(PactVerificationContext ctx) { ctx.verifyInteraction(); }
}
```

## 三、UI 自动化进阶

### 3.1 Playwright ⭐ (最热)

```python
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    ctx = browser.new_context()
    page = ctx.new_page()
    
    page.goto("https://example.com/login")
    page.get_by_label("用户名").fill("alice")
    page.get_by_label("密码").fill("secret")
    page.get_by_role("button", name="登录").click()
    
    expect(page).to_have_url(re.compile(r"/home"))
    expect(page.get_by_text("欢迎")).to_be_visible()
    
    page.screenshot(path="home.png")
    ctx.tracing.start(screenshots=True, snapshots=True)
    # ... 操作
    ctx.tracing.stop(path="trace.zip")
```

**Playwright 优势**：
- 跨浏览器 (Chromium/Firefox/WebKit)
- 自动等待
- 网络拦截 (route)
- 录制 (`codegen`)
- Trace Viewer (调试神器)
- 移动模拟 + 多 Context (多用户并发)
- Python / JS / Java / .NET 多语言

### 3.2 Cypress（前端首选）

```javascript
describe('Login', () => {
    it('登录成功跳转首页', () => {
        cy.visit('/login');
        cy.get('[data-cy=username]').type('alice');
        cy.get('[data-cy=password]').type('secret');
        cy.get('[data-cy=submit]').click();
        cy.url().should('include', '/home');
        cy.contains('欢迎').should('be.visible');
    });
    
    it('网络拦截 + 桩', () => {
        cy.intercept('GET', '/api/users', { fixture: 'users.json' }).as('users');
        cy.visit('/users');
        cy.wait('@users');
    });
});
```

特点：前端开发友好、内置时间旅行调试，**不支持多 tab/iframe 跨域**（Playwright 解决）。

### 3.3 Selenium 4（老牌）

```python
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Selenium Grid 分布式
driver = webdriver.Remote(
    command_executor='http://grid:4444',
    options=webdriver.ChromeOptions()
)
```

### 3.4 Page Object Model (POM)

```python
# pages/login_page.py
class LoginPage:
    URL = "/login"
    
    def __init__(self, page):
        self.page = page
        self.username = page.get_by_label("用户名")
        self.password = page.get_by_label("密码")
        self.submit = page.get_by_role("button", name="登录")
    
    def login(self, u, p):
        self.username.fill(u)
        self.password.fill(p)
        self.submit.click()
        return HomePage(self.page)

# tests/test_login.py
def test_login(page):
    login = LoginPage(page)
    page.goto(login.URL)
    home = login.login("alice", "secret")
    expect(home.welcome).to_be_visible()
```

POM 进阶：**Screenplay Pattern**（Serenity BDD）。

### 3.5 视觉回归测试

```
Percy / Applitools / BackstopJS / Playwright snapshots
对比像素 + 自动忽略动态区
适合: 前端 UI 改动验证, 设计走查
```

## 四、移动测试

### 4.1 Appium（跨平台）

```python
from appium import webdriver

caps = {
    "platformName": "Android",
    "deviceName": "emulator-5554",
    "app": "/path/app.apk",
    "automationName": "UiAutomator2"
}
driver = webdriver.Remote("http://localhost:4723", caps)
driver.find_element("id", "username").send_keys("alice")
```

### 4.2 原生

```
iOS:        XCUITest (Apple 官方) + WebDriverAgent
Android:    Espresso (Google 官方, 单元 + UI) + UiAutomator
```

### 4.3 国产 + 云测

```
WeTest (腾讯)
TestBird (云测)
讯飞云测试
华为云 DevTesting
阿里 MQC
```

工具：**Maestro** ⭐ (YAML 驱动, 新势力) / **Detox** (RN 专用)

## 五、性能测试

### 5.1 JMeter（经典）

```
GUI 设计 → 命令行执行
线程组 + 取样器 + 监听器
分布式压测 (master + slave)
插件 (Plugins Manager)
```

```bash
jmeter -n -t test.jmx -l result.jtl -e -o report/
```

### 5.2 k6（现代）⭐

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    stages: [
        { duration: '2m', target: 100 },   // 上升
        { duration: '5m', target: 100 },   // 稳态
        { duration: '2m', target: 200 },
        { duration: '5m', target: 200 },
        { duration: '2m', target: 0 },     // 下降
    ],
    thresholds: {
        http_req_duration: ['p(95)<500'],
        http_req_failed: ['rate<0.01'],
    },
};

export default function() {
    const r = http.get('https://api.example.com/users/1');
    check(r, {
        'status 200': (r) => r.status === 200,
        'duration < 500ms': (r) => r.timings.duration < 500,
    });
    sleep(1);
}
```

```bash
k6 run -u 100 -d 5m script.js
k6 run --out influxdb=http://localhost:8086/k6 script.js
# Grafana k6 dashboard
```

### 5.3 locust（Python）

```python
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        self.client.post("/login", json={"u":"x","p":"y"})
    
    @task(3)
    def view_users(self):
        self.client.get("/users")
    
    @task(1)
    def create_user(self):
        self.client.post("/users", json={"name": "test"})
```

```bash
locust -f locustfile.py --host=https://example.com
locust --headless -u 100 -r 10 -t 5m
```

### 5.4 wrk / wrk2（HTTP 极简）

```bash
wrk -t12 -c400 -d30s --latency https://example.com
wrk2 -t4 -c100 -d60s -R 1000 https://example.com  # 固定 RPS
```

### 5.5 ghz（gRPC）

```bash
ghz --insecure --proto api.proto --call S/Get \
    -d '{"id":1}' -c 50 -n 100000 localhost:9090
```

### 5.6 Gatling（Scala / 高性能）

```scala
class BasicSim extends Simulation {
    val httpProtocol = http.baseUrl("https://example.com")
    val scn = scenario("基础")
        .exec(http("get_user").get("/users/1").check(status.is(200)))
    setUp(scn.inject(rampUsers(1000) during (30 seconds)))
        .protocols(httpProtocol)
}
```

### 5.7 性能测试类型

```
基线 (Baseline):     单用户
负载 (Load):         预期峰值
压力 (Stress):       超过峰值 → 找极限
浸泡 (Soak / 长稳):  长时间 (24h+) → 内存泄漏
峰值 (Spike):        瞬时极高 → 弹性
容量 (Capacity):     找 SLA 边界
混沌 (Chaos load):   + 故障注入
```

工具栈推荐：
- **接口/微服务**: k6 ⭐ + Grafana
- **复杂场景**: JMeter (兼容多协议)
- **Python 团队**: locust
- **极速 HTTP**: wrk
- **gRPC**: ghz
- **金融/银行**: Gatling

## 六、数据库测试

### 6.1 Testcontainers ⭐

```python
# pytest + testcontainers
from testcontainers.postgres import PostgresContainer

def test_db():
    with PostgresContainer("postgres:16") as pg:
        url = pg.get_connection_url()
        # 跑 migration + 测试
        ...
```

```java
// Java
@Container
static PostgreSQLContainer<?> pg = new PostgreSQLContainer<>("postgres:16");

@DynamicPropertySource
static void props(DynamicPropertyRegistry r) {
    r.add("spring.datasource.url", pg::getJdbcUrl);
    r.add("spring.datasource.username", pg::getUsername);
    r.add("spring.datasource.password", pg::getPassword);
}
```

```javascript
// JS
const { GenericContainer } = require('testcontainers');
const pg = await new GenericContainer('postgres:16')
    .withExposedPorts(5432).start();
```

支持：PG / MySQL / Redis / Kafka / Elasticsearch / MongoDB / RabbitMQ / Selenium Grid / LocalStack(AWS) ...

### 6.2 Schema + 数据

```
工具:
  Liquibase / Flyway (DB 迁移)
  Bytebase (现代)
  
Fixture:
  factory_boy (Python)
  Factory Bot (Ruby)
  fishery (TS)
  Faker (假数据, 多语言)

种子:
  SQL 脚本
  JSON/YAML fixture
  Snapshot 还原
```

### 6.3 数据隔离

```
方法:
  - Transaction Rollback (每用例)
  - DB per worker (并行)
  - Container per test (Testcontainers)
  - Snapshot + Restore
  - Anonymization (生产数据脱敏)
```

## 七、测试架构（分层）

```
项目结构 (Python 示例):
  tests/
    unit/                    单元 (mock 外部)
    integration/             集成 (本地 DB / Redis)
    e2e/                     端到端 (真实)
    contract/                契约 (Pact)
    perf/                    性能 (k6 / locust)
    fixtures/                数据
    conftest.py              全局 fixture
  pytest.ini / pyproject.toml
  
分层 (UI):
  Tests → Page Objects → Components → Driver

设计模式:
  POM (Page Object) ⭐
  Screenplay
  Builder (数据)
  Factory (对象)
  Singleton (Driver)

风格:
  AAA + Given-When-Then
  独立 + 顺序无关
  Hermetic (无外部依赖) ⭐ Google
```

## 八、测试数据管理

```
策略:
  - 静态 fixture (JSON/YAML/SQL)
  - 工厂模式 (factory_boy)
  - 生成 (Faker / mimesis)
  - 录制 + 回放 (VCR / nock)
  - 数据脱敏 (生产 → 测试)

工具:
  Faker ⭐ (多语言)
  factory_boy (Python)
  Hypothesis (属性测试)
  Snowfakery (Salesforce)
  Tonic.ai (商业脱敏)
  ARX (匿名化)
  
原则:
  - 测试数据 与 测试用例 配对
  - 不依赖共享数据库
  - 每测试可重新生成
  - 敏感数据脱敏入测试
```

## 九、CI/CD 集成

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]

jobs:
  unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r requirements.txt pytest pytest-cov pytest-xdist
      - run: pytest -n 4 --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v4

  e2e:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env: { POSTGRES_PASSWORD: x }
        ports: ['5432:5432']
    steps:
      - uses: actions/checkout@v4
      - run: npx playwright install --with-deps
      - run: npx playwright test
      - uses: actions/upload-artifact@v4
        if: failure()
        with: { name: trace, path: test-results/ }

  pact:
    runs-on: ubuntu-latest
    steps:
      - uses: pactflow/actions/can-i-deploy@v1
```

**门禁策略**:
- PR: 单元 + 集成 + 覆盖率 ≥ 阈值
- Merge: 契约验证
- Dev/Staging: E2E
- Pre-prod: 性能基线

## 十、Allure 报告 ⭐

```python
import allure

@allure.epic("用户管理")
@allure.feature("登录")
@allure.story("正常登录")
@allure.severity(allure.severity_level.CRITICAL)
def test_login():
    with allure.step("打开登录页"):
        ...
    with allure.step("输入凭证"):
        ...
    allure.attach.file("screenshot.png", attachment_type=allure.attachment_type.PNG)
```

```bash
pytest --alluredir=allure-results
allure serve allure-results   # 本地 GUI
allure generate -o allure-report
```

支持：pytest / JUnit / TestNG / Mocha / Cypress / Playwright / Cucumber

## 十一、Flaky 测试治理

```
Flaky = 间歇性失败 (无代码改动也可能失败)

原因:
  - 时序 (race / async)
  - 共享状态
  - 网络抖动
  - 时间依赖 (today / now)
  - 顺序依赖
  - 资源竞争 (端口 / 文件)
  - 真实第三方 API
  - 等待不当 (sleep 替代显式)

治理:
  ☐ 检测 (CI 重跑统计 / Devloop 工具)
  ☐ Quarantine (隔离 + Tag)
  ☐ 根因 (一次一变量)
  ☐ 修复策略:
    - 显式等待 (替代 sleep)
    - Mock 外部
    - Hermetic 数据
    - Idempotent fixture
    - 并发安全 (端口随机)
  ☐ KPI: Flaky 率 < 1%

工具:
  pytest-rerunfailures (重试, 慎用)
  flaky (Python)
  Trunk Flaky Tests (商业)
  Datadog CI Visibility
```

## 十二、并行 + 分布式执行

```
策略:
  - 单机多进程 (pytest-xdist / Maven surefire fork)
  - 容器并行 (CI matrix)
  - Selenium Grid / Playwright shard
  - K8s 分布式 (kuberntes-test-controller / Argo Workflows)

工具:
  pytest-xdist        Python (-n auto)
  Maven Surefire     Java (forkCount)
  Jest --maxWorkers
  Cypress Parallel
  Playwright --shard=1/4

挑战:
  - 数据隔离 (DB per worker)
  - 端口冲突
  - 共享外部资源 (Redis / 第三方)
  - 报告聚合 (Allure merge)
```

## 十三、国产化场景

```
浏览器:
  浏览器内核 (360 / QQ / UC / Edge for China)
  WebView (国产手机)
  
移动:
  小米 / 华为 / OPPO / vivo 真机云 (WeTest / TestBird)
  鸿蒙 HarmonyOS (DevEco Testing)
  小程序 (微信 / 支付宝 / 抖音 / 百度) → mini-program-automator + Playwright + 小程序云测

国产化:
  麒麟 + UOS + openEuler 上测试
  TiDB / OceanBase / GaussDB 兼容
  达梦 / 人大金仓 / 神舟通用 DB
  WPS / OnlyOffice 兼容

监管:
  等保 2/3 测试场景
  关基测试报告
```

## 十四、Checklist（进阶）

```
API:
☐ REST + GraphQL + gRPC + WS
☐ Postman/Newman + requests/RestAssured + Bruno

契约:
☐ Pact + Pact Broker
☐ CI 双侧验证

UI:
☐ Playwright ⭐ + POM
☐ Cypress (前端)
☐ Selenium Grid 分布式
☐ 视觉回归

移动:
☐ Appium + XCUITest + Espresso
☐ 云测 (WeTest / TestBird)
☐ Maestro / Detox

性能:
☐ k6 ⭐ + JMeter + locust + wrk
☐ ghz (gRPC) + Gatling
☐ 7 种性能测试类型

DB:
☐ Testcontainers ⭐
☐ Liquibase/Flyway
☐ factory_boy / Faker

架构:
☐ 分层 (unit/integration/e2e/contract/perf)
☐ POM + Screenplay
☐ Hermetic 测试

CI:
☐ PR/Merge/E2E 三级门禁
☐ 并行 (xdist / shard)
☐ Allure 报告

Flaky:
☐ Quarantine + 根因
☐ Flaky 率 < 1%
☐ 显式等待

国产化:
☐ 麒麟/UOS/openEuler
☐ TiDB/OceanBase 兼容
☐ 鸿蒙 + 小程序云测
```

## 十五、推荐栈（进阶）

```
API:        Postman/Newman + Bruno ⭐ + requests + RestAssured
GraphQL:    Insomnia + Altair
gRPC:       grpcurl + ghz
契约:        Pact ⭐ + Pact Broker (Pactflow)
UI:         Playwright ⭐ + Cypress + Selenium 4
视觉:        Percy / Applitools / Playwright snapshots
移动:        Appium + XCUITest + Espresso + Maestro
云测:        WeTest / TestBird / 华为 DevTesting / Sauce Labs
性能:        k6 ⭐ + JMeter + locust + wrk + ghz + Gatling
DB:         Testcontainers ⭐ + Liquibase/Flyway + Bytebase
数据:        Faker + factory_boy + Hypothesis
CI:         GitHub Actions / GitLab CI / Jenkins + Allure
并行:        pytest-xdist + Playwright shard + Cypress parallel
管理:        TestRail / Zephyr / Notion + Jira
监控测试:    Datadog Synthetics / Grafana k6 / Prometheus
报告:        Allure ⭐ + HTML + Slack/钉钉通知
```

> 📖 **核心判断**：测试进阶 = **API(REST/GraphQL/gRPC + Bruno/Pact 契约) + UI(Playwright ⭐ + POM + Cypress) + 移动(Appium + Maestro + 云测) + 性能(k6 ⭐ + JMeter + locust + ghz) + DB(Testcontainers ⭐) + 测试架构分层 + CI 多级门禁 + Allure 报告 + Flaky < 1% 治理 + 并行/分布式 + 国产化场景**。能独立给中型项目搭"API + UI + 性能 + DB + 契约 + CI"全栈自动化, 就具备资深测试工程师能力。
