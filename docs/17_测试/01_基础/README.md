# 基础

> 软件测试基础 = **测试金字塔 + 四象限 + 单元/集成/E2E + TDD/BDD + xUnit(JUnit/pytest/Go test/Jest) + Mock/Stub/Fake + 覆盖率 + Test Doubles + 数据驱动(参数化) + 测试用例设计(等价类/边界/因果/正交) + Bug 生命周期 + Selenium WebDriver 入门**。本章面向初次接触自动化测试的开发/QA。

## 一、核心理念

### 1.1 测试金字塔（Mike Cohn）

```
       /\
      /E2E\          少 (10%)  慢 + 脆弱 + 真实
     /------\
    / 集成   \      中 (20-30%) 中速 + 中复杂
   /----------\
  / 单元       \    多 (60-70%) 快 + 稳定 + 便宜
 /--------------\
```

### 1.2 Google 测试三层

```
Small (单元):   单进程, < 100ms, 无网络/DB
Medium (集成):  单机, < 5s, 可用本地依赖
Large (E2E):    跨机, 分钟级, 真实环境
```

### 1.3 测试四象限（Brian Marick）

```
                自动化              手工
技术 ┌──────────────────┬──────────────────┐
面向 │ Q1 单元/组件/集成 │ Q4 性能/安全/兼容 │
     │ (自动 + 技术)     │ (工具支撑)         │
     ├──────────────────┼──────────────────┤
业务 │ Q2 故事/E2E       │ Q3 探索/演示/UAT │
面向 │ (业务自动)        │ (手工 + 业务)     │
     └──────────────────┴──────────────────┘
```

### 1.4 测试 vs 质量

```
测试 ≠ 质量保证 (QA)
测试 = 信息提供 + 风险揭示
QA = 全流程 (需求 + 设计 + 编码 + 测试 + 上线)

ISO/IEC 25010 质量模型 8 维:
  功能 + 性能 + 兼容 + 易用 + 可靠 + 安全 + 可维护 + 可移植
```

## 二、单元测试

### 2.1 xUnit 风格

```
原则:
  Fast    快 (< 100ms)
  Independent  独立 (无顺序)
  Repeatable   可重复
  Self-validating  自验证 (true/false)
  Timely  及时 (TDD)

AAA 模式:
  Arrange  准备 (输入 + Mock)
  Act      执行
  Assert   断言

模板:
  describe()/test()/expect()
  setUp / tearDown
  断言库 (assert / expect / should)
```

### 2.2 JUnit 5（Java）

```java
import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

class CalculatorTest {
    Calculator calc;
    
    @BeforeEach
    void setUp() { calc = new Calculator(); }
    
    @Test
    @DisplayName("加法正常")
    void testAdd() {
        assertEquals(5, calc.add(2, 3));
    }
    
    @ParameterizedTest
    @CsvSource({"1,2,3", "0,0,0", "-1,1,0"})
    void testAddParam(int a, int b, int expected) {
        assertEquals(expected, calc.add(a, b));
    }
    
    @Test
    void testDivByZero() {
        assertThrows(ArithmeticException.class, () -> calc.div(1, 0));
    }
}
```

```xml
<!-- Maven -->
<dependency>
  <groupId>org.junit.jupiter</groupId>
  <artifactId>junit-jupiter</artifactId>
  <version>5.10.0</version>
  <scope>test</scope>
</dependency>
```

### 2.3 pytest（Python）⭐

```python
# test_calc.py
import pytest

@pytest.fixture
def calc():
    return Calculator()

def test_add(calc):
    assert calc.add(2, 3) == 5

@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
])
def test_add_param(calc, a, b, expected):
    assert calc.add(a, b) == expected

def test_div_zero(calc):
    with pytest.raises(ZeroDivisionError):
        calc.div(1, 0)

# 跑测试
pytest -v
pytest --cov=src --cov-report=html  # 覆盖率
pytest -k "add"                       # 关键字过滤
pytest -m "smoke"                     # 标记过滤
pytest -n 4                           # 并行 (pytest-xdist)
```

### 2.4 Go testing

```go
// calc_test.go
package calc

import "testing"

func TestAdd(t *testing.T) {
    got := Add(2, 3)
    if got != 5 {
        t.Errorf("Add(2,3) = %d; want 5", got)
    }
}

func TestAddTable(t *testing.T) {
    tests := []struct {
        name    string
        a, b    int
        want    int
    }{
        {"正常", 1, 2, 3},
        {"零", 0, 0, 0},
        {"负", -1, 1, 0},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            if got := Add(tt.a, tt.b); got != tt.want {
                t.Errorf("got %d, want %d", got, tt.want)
            }
        })
    }
}

// Benchmark
func BenchmarkAdd(b *testing.B) {
    for i := 0; i < b.N; i++ {
        Add(2, 3)
    }
}
```

```bash
go test ./...
go test -v -cover
go test -race          # 数据竞争
go test -bench=.        # benchmark
go test -coverprofile=cover.out && go tool cover -html=cover.out
```

### 2.5 Jest（JavaScript/TypeScript）⭐

```javascript
// calc.test.js
import { add, div } from './calc';

describe('Calculator', () => {
    beforeEach(() => { /* setup */ });
    
    test('加法', () => {
        expect(add(2, 3)).toBe(5);
    });
    
    test.each([
        [1, 2, 3],
        [0, 0, 0],
    ])('add(%i, %i) = %i', (a, b, expected) => {
        expect(add(a, b)).toBe(expected);
    });
    
    test('除零抛错', () => {
        expect(() => div(1, 0)).toThrow();
    });
    
    test('异步', async () => {
        const data = await fetchUser(1);
        expect(data.name).toBe('Alice');
    });
});
```

```bash
npm test
jest --coverage
jest --watch
```

### 2.6 其他主流

| 语言 | 框架 | 特点 |
|:---|:---|:---|
| Java | **JUnit 5** ⭐ / TestNG | 注解 + 参数化 |
| Python | **pytest** ⭐ / unittest | 灵活 + 插件丰富 |
| Go | testing (内置) ⭐ + testify | 简洁 + 内置 cover/race |
| JS/TS | **Jest** ⭐ / Vitest / Mocha | 快 + 快照 |
| C# | xUnit / NUnit / MSTest | .NET 全家桶 |
| Ruby | RSpec ⭐ / Minitest | BDD 风格 |
| Rust | 内置 + cargo test | 文档测试 + 集成 |
| C/C++ | GoogleTest ⭐ / Catch2 | 强大 + 工业级 |
| PHP | PHPUnit | 经典 |
| Kotlin | KotlinTest / JUnit 5 | DSL |

## 三、Test Doubles（测试替身）

```
Dummy:  占位, 不用
Fake:   简化实现 (内存 DB / SQLite)
Stub:   预设返回值
Spy:    Stub + 记录调用
Mock:   预期 + 验证调用 ⭐
```

### 3.1 Mock 框架

**Python (unittest.mock / pytest-mock)**:

```python
from unittest.mock import Mock, patch, MagicMock

def test_user_service():
    mock_db = Mock()
    mock_db.get_user.return_value = {"id": 1, "name": "Alice"}
    
    service = UserService(mock_db)
    user = service.get(1)
    
    assert user["name"] == "Alice"
    mock_db.get_user.assert_called_once_with(1)

@patch('mymodule.requests.get')
def test_api(mock_get):
    mock_get.return_value.json.return_value = {"ok": True}
    result = fetch_data()
    assert result["ok"]
```

**Java (Mockito)** ⭐:

```java
@Test
void testGetUser() {
    UserRepo repo = mock(UserRepo.class);
    when(repo.findById(1L)).thenReturn(new User(1L, "Alice"));
    
    UserService svc = new UserService(repo);
    User user = svc.get(1L);
    
    assertEquals("Alice", user.getName());
    verify(repo, times(1)).findById(1L);
}
```

**JS (Jest)**:

```javascript
const fetchData = jest.fn();
fetchData.mockResolvedValue({ data: 42 });

const spy = jest.spyOn(api, 'get');
expect(spy).toHaveBeenCalledWith('/users');
```

**Go (gomock / testify/mock)**:

```go
// gomock 生成
//go:generate mockgen -source=user.go -destination=mock_user.go
mockRepo := NewMockUserRepo(ctrl)
mockRepo.EXPECT().FindById(1).Return(&User{Name: "Alice"}, nil)
```

## 四、覆盖率

```
类型:
  Line       行覆盖
  Branch     分支 (if/else)
  Function   函数
  Statement  语句
  Path       路径 (难达 100%)
  Condition  条件 (a && b 中每个值)
  MC/DC      改进条件 (航空 DO-178)

工具:
  Java:    JaCoCo ⭐
  Python:  coverage.py + pytest-cov ⭐
  Go:      内置 go test -cover ⭐
  JS:      Istanbul (Jest 内置) / nyc
  C/C++:   gcov / lcov / kcov
  .NET:    coverlet
  Ruby:    SimpleCov

阈值:
  核心库: > 80% 行 + > 70% 分支
  业务:   > 60% 行
  基础设施: > 50%
  
警示:
  ☐ 高覆盖率 ≠ 高质量
  ☐ 关注未覆盖代码 (新增 + 关键路径)
  ☐ Mutation Testing 才看出真假
```

## 五、TDD / BDD

### 5.1 TDD（Kent Beck）

```
Red → Green → Refactor

1. Red: 写失败测试 (一次一个)
2. Green: 写最简代码让测试过
3. Refactor: 重构 (保持绿)

变体:
  ATDD (Acceptance) → Cucumber/Gherkin
  Outside-In TDD (从 E2E 到单元)
  Inside-Out TDD (从单元到集成)

收益:
  - 设计驱动 (先想 API)
  - 文档 (测试即文档)
  - 回归保障
  - 重构信心
```

### 5.2 BDD（行为驱动）

```
Given (前置) → When (动作) → Then (结果)

Cucumber / SpecFlow / behave (Python):

Feature: 用户登录
  Scenario: 正确密码
    Given 用户 "alice" 存在
    When 输入密码 "secret123"
    Then 登录成功
    And 跳转到首页
```

```python
# behave (Python)
from behave import given, when, then

@given('用户 "{name}" 存在')
def step_user_exists(context, name):
    context.user = create_user(name)

@when('输入密码 "{pwd}"')
def step_enter_pwd(context, pwd):
    context.result = login(context.user, pwd)

@then('登录成功')
def step_success(context):
    assert context.result.ok
```

## 六、测试用例设计

```
等价类划分 (Equivalence Partitioning):
  有效 + 无效, 选代表
  例: 1-100 整数 → {50} (有效) + {0, 101} (无效)

边界值分析 (BVA) ⭐:
  Min, Min-1, Max, Max+1
  例: [1, 100] → 0, 1, 100, 101

判定表 (Decision Table):
  条件组合 → 动作

因果图 (Cause-Effect):
  画图 + 推规则

正交实验 (Orthogonal):
  L4/L8/L16 表, 减少组合
  工具: PICT (Microsoft)

状态迁移:
  状态机图 + 覆盖状态/迁移

错误推测:
  经验找易错点
  (空 / null / 边界 / 并发 / 顺序)
```

## 七、Selenium 入门（Web UI）

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()
driver.get("https://example.com/login")

# 定位
driver.find_element(By.ID, "username").send_keys("alice")
driver.find_element(By.NAME, "password").send_keys("secret")
driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()

# 显式等待
WebDriverWait(driver, 10).until(
    EC.url_contains("/home")
)

assert "欢迎" in driver.page_source
driver.quit()
```

定位优先级：`ID > Name > CSS > XPath > Link Text > Tag Name`

## 八、Bug 生命周期

```
New → Assigned → In Progress → Resolved → Verified → Closed
                              ↓
                          Rejected / Duplicate
                              ↓
                          Reopened (验证失败)

严重度 (Severity):
  Blocker  阻塞 (无法继续)
  Critical 严重 (核心功能)
  Major    一般 (重要功能)
  Minor    次要
  Trivial  细节

优先级 (Priority):
  P0/P1/P2/P3

模板:
  - 标题 (现象 + 模块)
  - 环境 (OS + 版本 + 配置)
  - 步骤 (1, 2, 3 重现)
  - 预期 vs 实际
  - 截图 / 日志 / 视频
  - 附件 (HAR / 网络包)
```

## 九、Checklist（基础）

```
理念:
☐ 金字塔 + 四象限
☐ Small/Medium/Large 分层

单元:
☐ xUnit (JUnit/pytest/Go test/Jest)
☐ AAA 模式
☐ 参数化 / 数据驱动
☐ Fixture / setUp / tearDown
☐ 异常断言

Mock:
☐ Mockito (Java) / mock (Python) / Jest / gomock
☐ Stub vs Mock vs Spy

覆盖率:
☐ Line / Branch / Function
☐ JaCoCo / coverage.py / go cover / Istanbul
☐ 阈值 (核心 80%, 业务 60%)

TDD/BDD:
☐ Red-Green-Refactor
☐ Cucumber / behave Given-When-Then

用例设计:
☐ 等价类 + 边界值
☐ 判定表 + 因果图
☐ 正交 (PICT)

UI 入门:
☐ Selenium WebDriver
☐ ID > CSS > XPath
☐ 显式等待

Bug:
☐ 生命周期
☐ Severity vs Priority
☐ 标准模板
```

## 十、入门 20 题

```
1.  测试金字塔三层
2.  TDD 三步
3.  AAA 模式
4.  Mock vs Stub
5.  覆盖率 Line vs Branch
6.  Fixture 作用
7.  参数化测试好处
8.  pytest -m / -k 区别
9.  JUnit @BeforeEach vs @BeforeAll
10. Jest expect 常用 matcher
11. Go testing.T vs B
12. 等价类 + 边界值
13. BDD Given-When-Then
14. Test Doubles 5 种
15. Mockito verify vs when
16. coverage.py 用法
17. Selenium 等待策略 (隐/显)
18. Bug Severity vs Priority
19. Flaky test 含义
20. 异常断言写法 (4 种语言)
```

## 十一、推荐栈（基础）

```
Java:        JUnit 5 ⭐ + Mockito + AssertJ + JaCoCo
Python:      pytest ⭐ + pytest-mock + pytest-cov + pytest-xdist
Go:          testing + testify + gomock + go cover
JS/TS:       Jest ⭐ / Vitest + ts-jest + @testing-library
C#:         xUnit + Moq + coverlet
Ruby:       RSpec + WebMock + SimpleCov
Rust:       cargo test + mockall + cargo-tarpaulin
C/C++:      GoogleTest + GMock + gcov/lcov
BDD:        Cucumber (Java/JS) + behave (Python) + SpecFlow (.NET)
UI:         Selenium WebDriver (入门)
管理:        Notion / TestRail / Zephyr
CI:         GitHub Actions / GitLab CI / Jenkins
报告:        Allure ⭐ + HTML 报告
```

> 📖 **核心判断**：测试基础 = **金字塔(单元 70% + 集成 20% + E2E 10%) + xUnit(JUnit/pytest/Go test/Jest) + Mock(Mockito/mock) + 覆盖率(JaCoCo/coverage/Istanbul) + TDD/BDD + 用例设计(等价类/边界值) + Selenium 入门 + Bug 生命周期**。能给项目搭"单元 + 集成 + 覆盖率 + CI"基本盘, 就具备初级测试/质量工程师能力。**测试是设计活动, 不是事后检查。**
