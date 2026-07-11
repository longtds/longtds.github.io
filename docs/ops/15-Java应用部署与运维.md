# Java 应用部署与运维

> 从单体到微服务，Java 应用的技术架构、运行模式、JVM 调优、容器化部署、故障排查全流程实战。

---

## 一、Java 应用架构演进

### 1.1 架构演进路线

```
架构演进:

  单体应用          垂直拆分          SOA              微服务            云原生
  (Monolith)       (Vertical)       (Service)        (Microservice)   (Cloud Native)

  ┌─────────┐     ┌─────────┐     ┌──────────┐     ┌───────────────┐     ┌───────────────┐
  │  Web UI  │     │  Web UI  │     │  Web UI   │     │  Gateway      │     │  Gateway      │
  │  业务逻辑 │     │  应用 A  │     │           │     │  ↓↓↓↓↓        │     │  ↓↓↓↓↓        │
  │  数据访问 │     │  应用 B  │     │ ESB 总线  │     │ Svc1 Svc2 Svc3│     │ Svc1 Svc2 Svc3│
  │          │     │          │     │  ↕↕↕↕↕   │     │  ↕   ↕   ↕   │     │  ↕   ↕   ↕   │
  │  全在一个 │     │  各自独立 │     │ Service A │     │ DB1  DB2  MQ │     │ K8s + Istio   │
  │  进程里   │     │  数据库   │     │ Service B │     │              │     │ Serverless    │
  └─────────┘     └─────────┘     └──────────┘     └───────────────┘     └───────────────┘

  2000s           2010s           2013             2015                 2020+

  特点:
  单体:   简单, 部署方便, 难扩展
  垂直:   按业务拆分, 数据库独立
  SOA:    ESB 总线, 服务间通过总线通信
  微服务: 服务自治, 独立部署, API 通信
  云原生: 容器+K8s+Service Mesh, 弹性伸缩
```

### 1.2 单体 vs 微服务

| 维度 | 单体应用 | 微服务 |
|:---|:---|:---|
| 代码结构 | 单一 WAR/JAR | 多个独立服务 |
| 数据库 | 共享数据库 | 每服务独立数据库 |
| 通信方式 | 方法调用 (进程内) | HTTP/RPC/gRPC (跨进程) |
| 部署方式 | 单个包部署 | 独立部署 |
| 扩展性 | 整体扩展 | 按需独立扩展 |
| 技术栈 | 统一技术栈 | 可异构 (Java/Go/Python) |
| 团队协作 | 全在一个代码库 | 服务自治, 团队独立 |
| 故障影响 | 一挂全挂 | 局部故障 (可降级) |
| 复杂度 | ⭐ 低 | ⭐ 高 (分布式问题) |
| 运维难度 | ⭐ 低 | ⭐ 高 (服务多) |
| 适用场景 | 中小项目, 团队小 | 大型项目, 多团队 |
| CI/CD | 简单 | 复杂 (多服务流水线) |
| 数据一致性 | 本地事务 | 分布式事务 (Saga/TCC) |

### 1.3 选型建议

```
什么时候用单体:
  - 团队 < 10 人
  - 业务领域单一
  - 快速验证 MVP
  - 内部管理系统

什么时候用微服务:
  - 团队 > 20 人, 多团队并行开发
  - 业务领域复杂, 多模块
  - 需要独立扩展 (如秒杀模块单独扩容)
  - 需要技术栈异构

  谨记: 不要为了微服务而微服务!
  先单体 → 业务清晰后 → 按领域拆分微服务
```

---

## 二、单体应用架构

### 2.1 典型技术栈

```
单体应用技术栈 (2026 主流):

  ┌─────────────────────────────────────────────┐
  │                  前端                        │
  │  Vue3 + ElementPlus / React + Ant Design    │
  │  (打包到 static/ 目录, 由后端提供静态资源)    │
  ├─────────────────────────────────────────────┤
  │                Web 层                        │
  │  Spring MVC (REST API)                      │
  │  Spring Security (认证授权)                  │
  │  Spring Validation (参数校验)                │
  ├─────────────────────────────────────────────┤
  │               业务层                         │
  │  Spring Boot 3.x                            │
  │  Spring Context (IoC/DI)                    │
  │  Spring AOP (切面: 日志/权限/事务)            │
  ├─────────────────────────────────────────────┤
  │               数据层                         │
  │  MyBatis-Plus (ORM, 国内主流)                │
  │  Spring Data JPA (备选)                     │
  │  Druid (连接池 + SQL 监控)                   │
  │  Flyway / Liquibase (数据库版本管理)         │
  ├─────────────────────────────────────────────┤
  │               中间件                        │
  │  Spring Data Redis (缓存)                   │
  │  Spring Kafka (消息队列)                    │
  │  Caffeine (本地缓存)                        │
  │  EasyExcel (Excel 导入导出)                  │
  ├─────────────────────────────────────────────┤
  │               运行时                         │
  │  JDK 21 (LTS) + Spring Boot 3.x            │
  │  内嵌 Tomcat / Undertow                     │
  │  打包: Fat JAR (可执行 JAR)                 │
  └─────────────────────────────────────────────┘
```

### 2.2 项目结构

```
my-app/
├── pom.xml                              # Maven 配置
├── src/
│   ├── main/
│   │   ├── java/com/example/app/
│   │   │   ├── MyAppApplication.java    # 启动类
│   │   │   ├── config/                  # 配置类
│   │   │   │   ├── WebMvcConfig.java
│   │   │   │   ├── SecurityConfig.java
│   │   │   │   ├── DruidConfig.java
│   │   │   │   └── RedisConfig.java
│   │   │   ├── controller/              # Controller 层
│   │   │   │   └── UserController.java
│   │   │   ├── service/                 # Service 层
│   │   │   │   ├── UserService.java     # 接口
│   │   │   │   └── impl/
│   │   │   │       └── UserServiceImpl.java  # 实现
│   │   │   ├── mapper/                  # Mapper 层 (MyBatis)
│   │   │   │   └── UserMapper.java
│   │   │   ├── entity/                  # 实体类
│   │   │   │   └── User.java
│   │   │   ├── dto/                     # 数据传输对象
│   │   │   │   ├── UserDTO.java
│   │   │   │   └── UserVO.java
│   │   │   ├── common/                  # 公共组件
│   │   │   │   ├── Result.java          # 统一返回
│   │   │   │   ├── ResultCode.java
│   │   │   │   └── PageResult.java
│   │   │   ├── exception/               # 异常处理
│   │   │   │   ├── BizException.java
│   │   │   │   └── GlobalExceptionHandler.java
│   │   │   ├── aop/                     # 切面
│   │   │   │   ├── LogAspect.java       # 操作日志
│   │   │   │   └── RateLimitAspect.java # 限流
│   │   │   └── utils/                   # 工具类
│   │   │       └── JwtUtil.java
│   │   ├── resources/
│   │   │   ├── application.yml          # 主配置
│   │   │   ├── application-prod.yml     # 生产配置
│   │   │   ├── mapper/                  # MyBatis XML
│   │   │   │   └── UserMapper.xml
│   │   │   ├── static/                  # 静态资源
│   │   │   └── db/migration/            # Flyway 脚本
│   │   │       └── V1__init.sql
│   │   └── docker/
│   │       └── Dockerfile
│   └── test/                            # 测试
└── Jenkinsfile                          # CI/CD
```

### 2.3 Maven 配置

```xml
<!-- pom.xml -->
<project>
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.3.0</version>
    </parent>

    <groupId>com.example</groupId>
    <artifactId>my-app</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <properties>
        <java.version>21</java.version>
        <mybatis-plus.version>3.5.7</mybatis-plus.version>
        <druid.version>1.2.23</druid.version>
    </properties>

    <dependencies>
        <!-- Web -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>

        <!-- 嵌入式容器: 默认 Tomcat, 换 Undertow 更高性能 -->
        <!--
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
            <exclusions>
                <exclusion>
                    <groupId>org.springframework.boot</groupId>
                    <artifactId>spring-boot-starter-tomcat</artifactId>
                </exclusion>
            </exclusions>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-undertow</artifactId>
        </dependency>
        -->

        <!-- 数据库 -->
        <dependency>
            <groupId>com.baomidou</groupId>
            <artifactId>mybatis-plus-spring-boot3-starter</artifactId>
            <version>${mybatis-plus.version}</version>
        </dependency>
        <dependency>
            <groupId>com.alibaba</groupId>
            <artifactId>druid-spring-boot-3-starter</artifactId>
            <version>${druid.version}</version>
        </dependency>
        <dependency>
            <groupId>com.mysql</groupId>
            <artifactId>mysql-connector-j</artifactId>
        </dependency>

        <!-- Redis -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-redis</artifactId>
        </dependency>
        <dependency>
            <groupId>org.apache.commons</groupId>
            <artifactId>commons-pool2</artifactId>
        </dependency>

        <!-- 安全 -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-security</artifactId>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-api</artifactId>
            <version>0.12.6</version>
        </dependency>

        <!-- 消息队列 -->
        <dependency>
            <groupId>org.springframework.kafka</groupId>
            <artifactId>spring-kafka</artifactId>
        </dependency>

        <!-- 监控 -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-actuator</artifactId>
        </dependency>
        <dependency>
            <groupId>io.micrometer</groupId>
            <artifactId>micrometer-registry-prometheus</artifactId>
        </dependency>

        <!-- 工具 -->
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <optional>true</optional>
        </dependency>
        <dependency>
            <groupId>cn.hutool</groupId>
            <artifactId>hutool-all</artifactId>
            <version>5.8.27</version>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
                <configuration>
                    <excludes>
                        <exclude>
                            <groupId>org.projectlombok</groupId>
                            <artifactId>lombok</artifactId>
                        </exclude>
                    </excludes>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
```

### 2.4 应用配置

```yaml
# application.yml
spring:
  application:
    name: my-app

  # === Profile ===
  profiles:
    active: ${PROFILE:prod}

  # === 数据源 ===
  datasource:
    type: com.alibaba.druid.pool.DruidDataSource
    driver-class-name: com.mysql.cj.jdbc.Driver
    url: jdbc:mysql://${MYSQL_HOST:localhost}:${MYSQL_PORT:3306}/${MYSQL_DB:mydb}?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai&useSSL=false&allowPublicKeyRetrieval=true
    username: ${MYSQL_USER:root}
    password: ${MYSQL_PASS:password}
    druid:
      initial-size: 5
      min-idle: 5
      max-active: 20
      max-wait: 60000
      time-between-eviction-runs-millis: 60000
      min-evictable-idle-time-millis: 300000
      validation-query: SELECT 1
      test-while-idle: true
      test-on-borrow: false
      test-on-return: false
      # 监控
      stat-view-servlet:
        enabled: true
        url-pattern: /druid/*
        # 生产环境配置 IP 白名单
        allow: 192.168.1.0/24
        login-username: druid
        login-password: DruidPass2026!
      filter:
        stat:
          enabled: true
          slow-sql-millis: 1000      # 慢 SQL 阈值
        wall:
          enabled: true

  # === Redis ===
  data:
    redis:
      host: ${REDIS_HOST:localhost}
      port: ${REDIS_PORT:6379}
      password: ${REDIS_PASS:}
      database: 0
      lettuce:
        pool:
          max-active: 16
          max-idle: 8
          min-idle: 2
        shutdown-timeout: 200ms

  # === Kafka ===
  kafka:
    bootstrap-servers: ${KAFKA_SERVERS:localhost:9092}
    producer:
      retries: 3
      batch-size: 16384
      buffer-memory: 33554432
      acks: all
    consumer:
      group-id: my-app
      auto-offset-reset: earliest
      enable-auto-commit: false
      max-poll-records: 500
    listener:
      ack-mode: manual_immediate

  # === 线程池 ===
  threads:
    virtual:
      enabled: true                  # JDK 21 虚拟线程

  # === Jackson ===
  jackson:
    date-format: yyyy-MM-dd HH:mm:ss
    time-zone: Asia/Shanghai
    default-property-inclusion: non_null

# === MyBatis-Plus ===
mybatis-plus:
  mapper-locations: classpath*:mapper/**/*.xml
  type-aliases-package: com.example.app.entity
  configuration:
    map-underscore-to-camel-case: true
    cache-enabled: true
    log-impl: org.apache.ibatis.logging.slf4j.Slf4jImpl
  global-config:
    db-config:
      id-type: assign_id
      logic-delete-field: deleted
      logic-delete-value: 1
      logic-not-delete-value: 0

# === 日志 ===
logging:
  level:
    root: INFO
    com.example.app: DEBUG
    com.example.app.mapper: DEBUG
  file:
    name: /opt/app/logs/my-app.log
  logback:
    rollingpolicy:
      max-file-size: 100MB
      max-history: 30
      total-size-cap: 10GB

# === Actuator 监控 ===
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus,env,loggers,threaddump,heapdump
  endpoint:
    health:
      show-details: when-authorized
  metrics:
    tags:
      application: ${spring.application.name}
```

### 2.5 启动类与核心代码

```java
// 启动类
@SpringBootApplication
@MapperScan("com.example.app.mapper")
public class MyAppApplication {
    public static void main(String[] args) {
        SpringApplication.run(MyAppApplication.class, args);
    }
}

// 统一返回
@Data
@Builder
public class Result<T> {
    private int code;
    private String message;
    private T data;
    private long timestamp;

    public static <T> Result<T> success(T data) {
        return Result.<T>builder()
            .code(200).message("success").data(data)
            .timestamp(System.currentTimeMillis()).build();
    }

    public static <T> Result<T> error(int code, String message) {
        return Result.<T>builder()
            .code(code).message(message).data(null)
            .timestamp(System.currentTimeMillis()).build();
    }
}

// 全局异常处理
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(BizException.class)
    public Result<Void> handleBiz(BizException e) {
        return Result.error(e.getCode(), e.getMessage());
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public Result<Void> handleValidation(MethodArgumentNotValidException e) {
        String msg = e.getBindingResult().getFieldErrors().stream()
            .map(f -> f.getField() + ": " + f.getDefaultMessage())
            .collect(Collectors.joining("; "));
        return Result.error(400, msg);
    }

    @ExceptionHandler(Exception.class)
    public Result<Void> handleException(Exception e) {
        log.error("系统异常", e);
        return Result.error(500, "系统内部错误");
    }
}

// Controller
@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    @GetMapping("/{id}")
    public Result<UserVO> getById(@PathVariable Long id) {
        return Result.success(userService.getById(id));
    }

    @PostMapping
    public Result<UserVO> create(@Valid @RequestBody UserDTO dto) {
        return Result.success(userService.create(dto));
    }

    @GetMapping
    public Result<PageResult<UserVO>> page(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String keyword) {
        return Result.success(userService.page(page, size, keyword));
    }
}

// Service
public interface UserService {
    UserVO getById(Long id);
    UserVO create(UserDTO dto);
    PageResult<UserVO> page(int page, int size, String keyword);
}

@Service
@RequiredArgsConstructor
@Slf4j
public class UserServiceImpl implements UserService {

    private final UserMapper userMapper;
    private final RedisTemplate<String, Object> redisTemplate;

    @Override
    public UserVO getById(Long id) {
        // 缓存
        String key = "user:" + id;
        UserVO cached = (UserVO) redisTemplate.opsForValue().get(key);
        if (cached != null) {
            return cached;
        }
        User user = userMapper.selectById(id);
        if (user == null) {
            throw new BizException(404, "用户不存在");
        }
        UserVO vo = UserVO.from(user);
        redisTemplate.opsForValue().set(key, vo, 30, TimeUnit.MINUTES);
        return vo;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public UserVO create(UserDTO dto) {
        User user = new User();
        BeanUtils.copyProperties(dto, user);
        userMapper.insert(user);
        return UserVO.from(user);
    }

    @Override
    public PageResult<UserVO> page(int page, int size, String keyword) {
        Page<User> p = new Page<>(page, size);
        LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
        if (StrUtil.isNotBlank(keyword)) {
            wrapper.like(User::getUsername, keyword)
                   .or().like(User::getEmail, keyword);
        }
        wrapper.orderByDesc(User::getCreateTime);
        Page<User> result = userMapper.selectPage(p, wrapper);
        List<UserVO> list = result.getRecords().stream()
            .map(UserVO::from).collect(Collectors.toList());
        return PageResult.of(list, result.getTotal(), page, size);
    }
}
```

---

## 三、微服务架构

### 3.1 Spring Cloud 技术栈

```
Spring Cloud 微服务技术栈 (2026 主流):

  ┌─────────────────────────────────────────────────────────────┐
  │                     前端 / 移动端                            │
  ├─────────────────────────────────────────────────────────────┤
  │                    API Gateway (Spring Cloud Gateway)       │
  │            路由 / 鉴权 / 限流 / 熔断 / 日志                   │
  ├──────────┬──────────┬──────────┬──────────┬───────────────┤
  │ 用户服务  │ 订单服务  │ 商品服务  │ 支付服务  │  ...         │
  │ user-svc │ order-svc│ product  │ pay-svc  │              │
  │          │          │  -svc    │          │              │
  │ Spring   │ Spring   │ Spring   │ Spring   │              │
  │ Boot     │ Boot     │ Boot     │ Boot     │              │
  ├──────────┴──────────┴──────────┴──────────┴───────────────┤
  │  注册中心/配置中心: Nacos                                    │
  │  服务调用: OpenFeign / Dubbo                                │
  │  负载均衡: Spring Cloud LoadBalancer                        │
  │  熔断限流: Sentinel                                         │
  │  链路追踪: Micrometer Tracing + Zipkin/SkyWalking           │
  │  消息驱动: Spring Cloud Stream (Kafka/RocketMQ)             │
  │  分布式事务: Seata (Saga/TCC)                               │
  ├─────────────────────────────────────────────────────────────┤
  │  MySQL   Redis   Kafka   MinIO   ES   ClickHouse          │
  └─────────────────────────────────────────────────────────────┘

  核心组件:
  Nacos      注册中心 + 配置中心 (替代 Eureka + Config)
  Gateway    API 网关 (路由/鉴权/限流)
  OpenFeign  声明式 HTTP 调用 (替代 RestTemplate)
  Sentinel   熔断/限流/降级 (替代 Hystrix)
  Seata      分布式事务 (AT/TCC/Saga)
  SkyWalking 链路追踪 (APM)
```

### 3.2 Nacos 注册中心与配置中心

```bash
# === Nacos 部署 ===
# 单机模式 (开发)
docker run -d --name nacos \
    -p 8848:8848 -p 9848:9848 \
    -e MODE=standalone \
    -e JVM_XMS=512m -e JVM_XMX=512m \
    nacos/nacos-server:v2.4.0

# 集群模式 (生产)
# 3 节点 + MySQL
# nacos-cluster.yaml
cat > /opt/nacos/conf/cluster.conf << 'EOF'
192.168.1.10:8848
192.168.1.11:8848
192.168.1.12:8848
EOF

# application.properties (MySQL)
cat > /opt/nacos/conf/application.properties << 'EOF'
spring.datasource.platform=mysql
db.num=1
db.url.0=jdbc:mysql://192.168.1.10:3306/nacos?characterEncoding=utf8&connectTimeout=1000&socketTimeout=3000&autoReconnect=true
db.user.0=nacos
db.password.0=NacosPass2026!

nacos.naming.empty-service.auto-clean=true
nacos.naming.empty-service.clean.initial-delay-ms=50000
nacos.naming.empty-service.clean.period-ms=30000
nacos.core.auth.enabled=true
nacos.core.auth.server.identity.key=nacos
nacos.core.auth.server.identity.value=NacosIdentity2026
EOF

# 访问: http://<ip>:8848/nacos
# 默认: nacos / nacos
```

```xml
<!-- 微服务引入 Nacos -->
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-nacos-discovery</artifactId>
</dependency>
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-nacos-config</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-bootstrap</artifactId>
</dependency>
```

```yaml
# bootstrap.yml (Nacos 配置, 必须在 bootstrap 阶段加载)
spring:
  application:
    name: user-service
  cloud:
    nacos:
      # 注册中心
      discovery:
        server-addr: 192.168.1.10:8848,192.168.1.11:8848,192.168.1.12:8848
        namespace: production              # 命名空间隔离
        group: DEFAULT_GROUP
        cluster-name: BJ                   # 集群名 (同机房优先)
      # 配置中心
      config:
        server-addr: ${spring.cloud.nacos.discovery.server-addr}
        namespace: ${spring.cloud.nacos.discovery.namespace}
        group: DEFAULT_GROUP
        file-extension: yaml               # 配置文件扩展名
        # 共享配置 (所有服务共用)
        shared-configs:
          - data-id: common.yaml
            group: SHARED_GROUP
            refresh: true                  # 动态刷新
        # 扩展配置
        extension-configs:
          - data-id: redis.yaml
            group: SHARED_GROUP
            refresh: true
```

### 3.3 API Gateway

```xml
<!-- gateway/pom.xml -->
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-gateway</artifactId>
</dependency>
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-nacos-discovery</artifactId>
</dependency>
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-sentinel</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis-reactive</artifactId>
</dependency>
```

```yaml
# gateway/application.yml
server:
  port: 8080

spring:
  application:
    name: gateway
  cloud:
    nacos:
      discovery:
        server-addr: 192.168.1.10:8848
    gateway:
      # === 路由配置 ===
      routes:
        # 用户服务
        - id: user-service
          uri: lb://user-service           # 负载均衡
          predicates:
            - Path=/api/users/**
          filters:
            - StripPrefix=0                # 不截断前缀
            - name: RequestRateLimiter     # 限流
              args:
                redis-rate-limiter.replenishRate: 100    # 令牌填充速率
                redis-rate-limiter.burstCapacity: 200    # 令牌桶容量
                key-resolver: "#{@ipKeyResolver}"       # 限流 key (IP)

        # 订单服务
        - id: order-service
          uri: lb://order-service
          predicates:
            - Path=/api/orders/**
          filters:
            - StripPrefix=0

        # 支付服务
        - id: pay-service
          uri: lb://pay-service
          predicates:
            - Path=/api/pay/**
          filters:
            - StripPrefix=0

      # === 跨域 ===
      globalcors:
        cors-configurations:
          '[/**]':
            allowed-origins: "https://app.example.com"
            allowed-methods: "*"
            allowed-headers: "*"
            allow-credentials: true
            max-age: 3600

      # === 服务发现配置 ===
      discovery:
        locator:
          enabled: false                    # 关闭自动路由 (手动配置更安全)

    sentinel:
      transport:
        dashboard: 192.168.1.10:8858
      filter:
        enabled: true
      scg:
        fallback:
          mode: response
          response-status: 429
          response-body: '{"code":429,"message":"请求过于频繁,请稍后重试"}'
```

```java
// Gateway 鉴权过滤器
@Component
public class AuthFilter implements GlobalFilter, Ordered {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    // 白名单路径
    private static final Set<String> WHITELIST = Set.of(
        "/api/users/login",
        "/api/users/register",
        "/actuator"
    );

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String path = request.getURI().getPath();

        // 白名单放行
        if (WHITELIST.stream().anyMatch(path::startsWith)) {
            return chain.filter(exchange);
        }

        // 获取 Token
        String token = request.getHeaders().getFirst("Authorization");
        if (StrUtil.isBlank(token) || !token.startsWith("Bearer ")) {
            return unauthorized(exchange, "缺少认证信息");
        }
        token = token.substring(7);

        // 验证 Token
        try {
            Claims claims = JwtUtil.parse(token);
            String userId = claims.getSubject();

            // 检查 Redis 中 Token 是否有效
            String cached = redisTemplate.opsForValue().get("token:" + userId);
            if (!token.equals(cached)) {
                return unauthorized(exchange, "Token 已失效");
            }

            // 传递用户信息到下游服务
            ServerHttpRequest mutated = request.mutate()
                .header("X-User-Id", userId)
                .header("X-User-Name", claims.get("name", String.class))
                .build();
            return chain.filter(exchange.mutate().request(mutated).build());

        } catch (Exception e) {
            return unauthorized(exchange, "Token 无效");
        }
    }

    private Mono<Void> unauthorized(ServerWebExchange exchange, String message) {
        ServerHttpResponse response = exchange.getResponse();
        response.setStatusCode(HttpStatus.UNAUTHORIZED);
        response.getHeaders().setContentType(MediaType.APPLICATION_JSON);
        String body = "{\"code\":401,\"message\":\"" + message + "\"}";
        DataBuffer buffer = response.bufferFactory().wrap(body.getBytes());
        return response.writeWith(Mono.just(buffer));
    }

    @Override
    public int getOrder() {
        return -100;                       // 最高优先级
    }
}

// IP 限流 Key
@Configuration
public class RateLimiterConfig {
    @Bean
    public KeyResolver ipKeyResolver() {
        return exchange -> Mono.just(
            exchange.getRequest().getRemoteAddress().getAddress().getHostAddress()
        );
    }
}
```

### 3.4 OpenFeign 服务间调用

```java
// Feign 客户端 (订单服务调用用户服务)
@FeignClient(name = "user-service", path = "/api/users", configuration = FeignConfig.class)
public interface UserFeignClient {

    @GetMapping("/{id}")
    Result<UserVO> getById(@PathVariable Long id);

    @PostMapping
    Result<UserVO> create(@RequestBody UserDTO dto);
}

// Feign 配置
@Configuration
public class FeignConfig {
    @Bean
    public RequestInterceptor requestInterceptor() {
        return template -> {
            // 传递认证信息
            RequestAttributes attrs = RequestContextHolder.getRequestAttributes();
            if (attrs instanceof ServletRequestAttributes) {
                HttpServletRequest request = ((ServletRequestAttributes) attrs).getRequest();
                String token = request.getHeader("Authorization");
                if (token != null) {
                    template.header("Authorization", token);
                }
                // 传递链路追踪 ID
                String traceId = request.getHeader("X-Trace-Id");
                if (traceId != null) {
                    template.header("X-Trace-Id", traceId);
                }
            }
        };
    }

    @Bean
    public feign.Logger.Level loggerLevel() {
        return feign.Logger.Level.BASIC;   // 生产环境用 BASIC
    }

    @Bean
    public feign.Retryer retryer() {
        return new feign.Retryer.Default(100, 1000, 3);  // 重试 3 次
    }
}

// Service 调用
@Service
@RequiredArgsConstructor
public class OrderService {

    private final UserFeignClient userFeignClient;

    public OrderVO createOrder(OrderDTO dto) {
        // 通过 Feign 调用用户服务
        Result<UserVO> result = userFeignClient.getById(dto.getUserId());
        if (result.getCode() != 200) {
            throw new BizException("用户不存在");
        }
        UserVO user = result.getData();

        Order order = new Order();
        order.setUserId(user.getId());
        order.setUserName(user.getUsername());
        // ... 业务逻辑
        return OrderVO.from(order);
    }
}
```

### 3.5 Sentinel 熔断限流

```xml
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-sentinel</artifactId>
</dependency>
```

```yaml
# application.yml
spring:
  cloud:
    sentinel:
      transport:
        dashboard: 192.168.1.10:8858
        port: 8719
      eager: true                        # 立即连接 Dashboard
      datasource:
        # 从 Nacos 拉取规则 (持久化)
        ds1:
          nacos:
            server-addr: 192.168.1.10:8848
            data-id: ${spring.application.name}-flow-rules
            group-id: SENTINEL_GROUP
            data-type: json
            rule-type: flow
```

```java
// Sentinel 注解
@RestController
@RequiredArgsConstructor
public class OrderController {

    // 限流: 100 QPS, 超出返回降级
    @GetMapping("/{id}")
    @SentinelResource(value = "getOrder",
        blockHandler = "getOrderBlockHandler",
        fallback = "getOrderFallback")
    public Result<OrderVO> getById(@PathVariable Long id) {
        return Result.success(orderService.getById(id));
    }

    // 限流降级
    public Result<OrderVO> getOrderBlockHandler(Long id, BlockException e) {
        return Result.error(429, "请求过于频繁,请稍后重试");
    }

    // 熔断降级
    public Result<OrderVO> getOrderFallback(Long id, Throwable e) {
        log.error("获取订单失败, 降级处理", e);
        return Result.error(503, "服务暂时不可用,请稍后重试");
    }
}

// 全局降级配置
@Configuration
public class SentinelConfig {
    @PostConstruct
    public void init() {
        // 异常比例熔断: 5 秒内异常比例 > 50%, 熔断 10 秒
        DegradeRule rule = new DegradeRule();
        rule.setResource("getOrder");
        rule.setGrade(CircuitBreakerStrategy.ERROR_RATIO.getGrade());
        rule.setCount(0.5);               // 异常比例阈值
        rule.setTimeWindow(10);           // 熔断时长 (秒)
        rule.setMinRequestAmount(5);      // 最小请求数
        rule.setStatIntervalMs(5000);     // 统计窗口
        DegradeRuleManager.loadRules(List.of(rule));
    }
}
```

### 3.6 分布式事务 Seata

```xml
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-seata</artifactId>
</dependency>
```

```yaml
# application.yml
seata:
  enabled: true
  application-id: ${spring.application.name}
  tx-service-group: ${spring.application.name}-group
  service:
    vgroup-mapping:
      user-service-group: default
  registry:
    type: nacos
    nacos:
      server-addr: 192.168.1.10:8848
      namespace: seata
  config:
    type: nacos
    nacos:
      server-addr: 192.168.1.10:8848
```

```java
// AT 模式 (自动事务, 最简单)
// 订单服务: 创建订单 + 扣库存 + 扣余额
@Service
@RequiredArgsConstructor
@Slf4j
public class OrderService {

    private final OrderMapper orderMapper;
    private final StorageFeignClient storageClient;
    private final AccountFeignClient accountClient;

    @GlobalTransactional(name = "createOrder", rollbackFor = Exception.class)
    public void createOrder(OrderDTO dto) {
        log.info("=== 开始全局事务 ===");

        // 1. 创建订单
        Order order = new Order();
        order.setUserId(dto.getUserId());
        order.setProductId(dto.getProductId());
        order.setCount(dto.getCount());
        order.setMoney(dto.getMoney());
        orderMapper.insert(order);
        log.info("1. 订单已创建");

        // 2. 扣减库存 (远程调用)
        storageClient.decrease(dto.getProductId(), dto.getCount());
        log.info("2. 库存已扣减");

        // 3. 扣减余额 (远程调用)
        accountClient.decrease(dto.getUserId(), dto.getMoney());
        log.info("3. 余额已扣减");

        // 4. 修改订单状态
        order.setStatus(1);
        orderMapper.updateById(order);
        log.info("=== 全局事务完成 ===");

        // 如果远程调用失败, Seata 自动回滚所有分支事务
    }
}
```

### 3.7 链路追踪 SkyWalking

```bash
# SkyWalking OAP 部署
docker run -d --name oap \
    -p 11800:11800 -p 12800:12800 \
    -e SW_STORAGE=elasticsearch \
    -e SW_STORAGE_ES_CLUSTER_NODES=192.168.1.10:9200 \
    apache/skywalking-oap-server:9.7.0

# SkyWalking UI
docker run -d --name skywalking-ui \
    -p 8080:8080 \
    -e SW_OAP_ADDRESS=http://192.168.1.10:12800 \
    apache/skywalking-ui:9.7.0

# Java Agent (无侵入)
# 下载 Agent
wget https://archive.apache.org/dist/skywalking/java-agent/9.3.0/apache-skywalking-java-agent-9.3.0.tgz
tar xzf apache-skywalking-java-agent-9.3.0.tgz -C /opt/

# 启动应用时挂载 Agent
java -javaagent:/opt/skywalking-agent/skywalking-agent.jar \
     -Dskywalking.agent.service_name=user-service \
     -Dskywalking.collector.backend_service=192.168.1.10:11800 \
     -jar user-service.jar

# 或 Dockerfile:
# ENV JAVA_OPTS="-javaagent:/opt/skywalking-agent/skywalking-agent.jar \
#   -Dskywalking.agent.service_name=user-service \
#   -Dskywalking.collector.backend_service=192.168.1.10:11800"
# ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar /app.jar"]
```

---

## 四、JVM 调优

### 4.1 JVM 内存模型

```
JVM 内存结构 (JDK 21):

  ┌─────────────────────────────────────────────────────────┐
  │                     JVM 进程内存                          │
  │                                                         │
  │  ┌───────────────────────────────────────────────────┐ │
  │  │              Heap (堆内存)                         │ │
  │  │                                                   │ │
  │  │  ┌──────────────────┐  ┌────────────────────────┐│ │
  │  │  │  Young Generation │  │  Old Generation        ││ │
  │  │  │  (年轻代)          │  │  (老年代)              ││ │
  │  │  │                  │  │                        ││ │
  │  │  │  ┌─────────────┐ │  │  -XX:OldSize=          ││ │
  │  │  │  │   Eden      │ │  │                        ││ │
  │  │  │  │  (新生区)    │ │  │  长期存活的对象          ││ │
  │  │  │  └─────────────┘ │  │                        ││ │
  │  │  │  ┌──────┐┌──────┐│  │  -XX:MaxTenuringThresh││ │
  │  │  │  │S0    ││S1    ││  │    old=15              ││ │
  │  │  │  │Survivor││Survivor││  │                    ││ │
  │  │  │  └──────┘└──────┘│  │                        ││ │
  │  │  └──────────────────┘  └────────────────────────┘│ │
  │  └───────────────────────────────────────────────────┘ │
  │                                                         │
  │  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐ │
  │  │ Metaspace│  │Code Cache│  │ Direct Memory        │ │
  │  │ (类元数据) │  │(JIT 编译)│  │ (NIO/Netty 堆外内存)  │ │
  │  └──────────┘  └──────────┘  └──────────────────────┘ │
  │                                                         │
  │  ┌───────────────────────────────────────────────────┐ │
  │  │  Thread Stack × N (线程栈, 默认 1MB/线程)          │ │
  │  └───────────────────────────────────────────────────┘ │
  └─────────────────────────────────────────────────────────┘

  GC 流程:
  1. 对象分配在 Eden
  2. Eden 满 → Minor GC (YGC)
     存活对象 → S0, 年龄+1
     Eden 清空, 继续分配
  3. 下次 Minor GC
     Eden + S0 存活对象 → S1, 年龄+1
     (S0 和 S1 交替使用)
  4. 年龄 > 15 → 晋升到 Old
  5. Old 满 → Major GC (Full GC)
     STW (Stop The World) 时间长
```

### 4.2 GC 收集器选择

| GC | 特点 | 适用场景 | JDK |
|:---|:---|:---|:---|
| Serial | 单线程, STW | 客户端/小应用 | 8+ |
| Parallel | 多线程, 吞吐优先 | 批处理/计算密集 | 8+ |
| CMS | 低停顿, 并发 | Web 应用 (已废弃) | 8-14 |
| **G1** | Region 化, 可预测停顿 | **通用首选** | 9+ |
| **ZGC** | 超低停顿 (<1ms), 并发 | **低延迟/大堆** | 15+ |
| Shenandoah | 超低停顿, 并发 | 低延迟 (RedHat) | 12+ |

```
GC 选择建议 (JDK 21):
  堆 < 4GB:    G1 (默认, 够用)
  堆 4-32GB:   G1 (调优 Region 和停顿目标)
  堆 > 32GB:   ZGC (大堆低延迟)
  延迟敏感:    ZGC (停顿 < 1ms)
  吞吐优先:    G1 (或 Parallel)

  G1 vs ZGC:
  G1:  停顿 50-200ms, 吞吐高, 成熟稳定
  ZGC: 停顿 < 1ms, 吞吐略低, JDK 21 生产可用
```

### 4.3 生产 JVM 参数

```bash
# === G1 GC (4-16GB 堆, 通用) ===
java \
  -server \
  -Xms4g -Xmx4g \
  -XX:MetaspaceSize=256m \
  -XX:MaxMetaspaceSize=512m \
  -XX:+UseG1GC \
  -XX:MaxGCPauseMillis=200 \
  -XX:G1HeapRegionSize=4m \
  -XX:InitiatingHeapOccupancyPercent=45 \
  -XX:+ParallelRefProcEnabled \
  -XX:+UseStringDeduplication \
  -XX:+HeapDumpOnOutOfMemoryError \
  -XX:HeapDumpPath=/opt/app/heapdump/ \
  -XX:ErrorFile=/opt/app/logs/hs_err_%p.log \
  -XX:+PrintGCDetails \
  -XX:+PrintGCDateStamps \
  -Xlog:gc*:file=/opt/app/logs/gc.log:time,uptime:filecount=10,filesize=100M \
  -Dfile.encoding=UTF-8 \
  -Duser.timezone=Asia/Shanghai \
  -Djava.security.egd=file:/dev/./urandom \
  -jar /opt/app/my-app.jar

# === ZGC (大堆 / 低延迟) ===
java \
  -server \
  -Xms8g -Xmx8g \
  -XX:MetaspaceSize=256m \
  -XX:MaxMetaspaceSize=512m \
  -XX:+UseZGC \
  -XX:ZCollectionInterval=120 \
  -XX:ZAllocationSpikeTolerance=5 \
  -XX:+HeapDumpOnOutOfMemoryError \
  -XX:HeapDumpPath=/opt/app/heapdump/ \
  -Xlog:gc*:file=/opt/app/logs/gc.log:time,uptime:filecount=10,filesize=100M \
  -jar /opt/app/my-app.jar

# === JDK 21 虚拟线程 (高并发) ===
java \
  -server \
  -Xms2g -Xmx2g \
  -XX:+UseZGC \
  -Djdk.virtualThreadScheduler.parallelism=200 \
  -Djdk.virtualThreadScheduler.maxPoolSize=1000 \
  -jar /opt/app/my-app.jar
# Spring Boot 3.2+ 开启: spring.threads.virtual.enabled=true

# 参数说明:
# -Xms == -Xmx         初始堆 = 最大堆 (避免动态扩容)
# -XX:+UseG1GC          使用 G1 收集器
# MaxGCPauseMillis      目标停顿时间 (G1 尽力达到)
# G1HeapRegionSize      Region 大小 (1/2/4/8/16/32MB)
# IHOP                  堆占用率到 45% 时触发并发标记
# HeapDumpOnOOM         OOM 时自动 dump
# UseStringDeduplication 字符串去重 (减少堆占用)
# UseStringDeduplication 字符串去重 (减少堆占用)
```

### 4.4 JDK 21 关键特性

```
JDK 21 (LTS) 新特性 (对运维有影响的):

1. 虚拟线程 (Virtual Threads) [正式]
   - 轻量级线程, 由 JVM 调度 (非 OS 线程)
   - 每个虚拟线程占用 ~KB 级内存 (平台线程 ~1MB)
   - 可创建百万级虚拟线程
   - Spring Boot 3.2+: spring.threads.virtual.enabled=true
   - Tomcat/Undertow 自动使用虚拟线程处理请求
   - 适合 IO 密集型 (HTTP 调用/DB 查询)
   - 不适合 CPU 密集型 (虚拟线程不提升计算性能)

2. ZGC [正式]
   - 停顿 < 1ms (不随堆大小增长)
   - 支持 TB 级堆
   - 并发标记/转移/重定位

3. 分代 ZGC [正式, JDK 21]
   - 分代收集 (年轻代/老年代)
   - 进一步降低开销

4. Pattern Matching for switch [正式]
   - 代码层面, 对运维无直接影响

JDK 版本选择:
  JDK 8:  遗留系统 (2026 仍有大量使用)
  JDK 11: 过渡 LTS (逐步迁移)
  JDK 17: 主流 LTS (Spring Boot 3 最低要求)
  JDK 21: 最新 LTS (推荐新项目)
  JDK 25: 下一个 LTS (2025.09)
```

---

## 五、容器化部署

### 5.1 Dockerfile

```dockerfile
# === 多阶段构建 ===

# 阶段 1: 构建
FROM maven:3.9-eclipse-temurin-21 AS builder
WORKDIR /build
COPY pom.xml .
# 先下载依赖 (利用 Docker 缓存)
RUN mvn dependency:go-offline
COPY src/ ./src/
RUN mvn clean package -DskipTests

# 阶段 2: 运行
FROM eclipse-temurin:21-jre-alpine
LABEL maintainer="ops@example.com"

# 安装必要工具
RUN apk add --no-cache curl tzdata && \
    cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone

# SkyWalking Agent (可选)
COPY --from=apache/skywalking-java-agent:9.3.0-java21 /skywalking/agent /opt/skywalking-agent

# 应用
WORKDIR /app
COPY --from=builder /build/target/*.jar app.jar

# JVM 参数
ENV JAVA_OPTS="-XX:+UseZGC \
    -XX:MaxRAMPercentage=75.0 \
    -XX:+HeapDumpOnOutOfMemoryError \
    -XX:HeapDumpPath=/app/heapdump/ \
    -Dfile.encoding=UTF-8 \
    -Duser.timezone=Asia/Shanghai \
    -Djava.security.egd=file:/dev/./urandom"

# SkyWalking Agent (可选)
ENV SW_AGENT_NAME="my-app"
ENV SW_COLLECTOR_BACKEND_SERVICES="192.168.1.10:11800"
ENV JAVA_OPTS="$JAVA_OPTS -javaagent:/opt/skywalking-agent/skywalking-agent.jar"

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/actuator/health || exit 1

# 非 root 用户
RUN addgroup -S app && adduser -S app -G app
USER app

EXPOSE 8080
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
```

```bash
# 构建
docker build -t my-app:1.0.0 .

# 运行
docker run -d --name my-app \
    -p 8080:8080 \
    -e PROFILE=prod \
    -e MYSQL_HOST=192.168.1.10 \
    -e REDIS_HOST=192.168.1.10 \
    -e KAFKA_SERVERS=192.168.1.10:9092 \
    -v /data/app/logs:/app/logs \
    -v /data/app/heapdump:/app/heapdump \
    --memory=4g --memory-swap=4g \
    --cpus=2 \
    --restart=unless-stopped \
    my-app:1.0.0
```

### 5.2 Kubernetes 部署

```yaml
# === Deployment ===
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
  namespace: production
  labels:
    app: user-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: user-service
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1              # 滚动更新: 最多多 1 个 Pod
      maxUnavailable: 0        # 不允许减少 (零停机)
  template:
    metadata:
      labels:
        app: user-service
    spec:
      containers:
      - name: user-service
        image: registry.example.com/user-service:1.0.0
        ports:
        - containerPort: 8080
            name: http

        env:
        - name: PROFILE
          value: "prod"
        - name: MYSQL_HOST
          valueFrom:
            configMapKeyRef:
              name: db-config
              key: mysql-host
        - name: MYSQL_PASS
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: mysql-password
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_IP
          valueFrom:
            fieldRef:
              fieldPath: status.podIP

        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "2000m"
            memory: "2Gi"

        # JVM 使用 cgroup 内存限制
        # MaxRAMPercentage=75.0 → 2Gi × 75% = 1.5Gi 堆

        readinessProbe:
          httpGet:
            path: /actuator/health/readiness
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          failureThreshold: 3

        livenessProbe:
          httpGet:
            path: /actuator/health/liveness
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 20
          failureThreshold: 5

        volumeMounts:
        - name: logs
          mountPath: /app/logs
        - name: heapdump
          mountPath: /app/heapdump

      volumes:
      - name: logs
        emptyDir: {}
      - name: heapdump
        emptyDir:
          sizeLimit: 1Gi

      # 优雅终止
      terminationGracePeriodSeconds: 60

---
# === Service ===
apiVersion: v1
kind: Service
metadata:
  name: user-service
  namespace: production
spec:
  selector:
    app: user-service
  ports:
  - port: 80
    targetPort: 8080
    name: http

---
# === HPA (自动扩缩容) ===
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: user-service
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: user-service
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70          # CPU > 70% 扩容
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80          # 内存 > 80% 扩容
```

### 5.3 优雅启动与终止

```java
// 优雅启动: Spring Boot 3 + Actuator
// readiness 探针: 应用就绪前不接收流量
// management.endpoint.health.group.readiness.enabled=true

// 优雅终止
@SpringBootApplication
public class MyAppApplication {
    public static void main(String[] args) {
        SpringApplication app = new SpringApplication(MyAppApplication.class);
        // 注册关闭钩子
        app.registerShutdownHook();
        // 优雅关闭超时
        app.setShutdownHookThreadName("shutdown-hook");
        app.run(args);
    }
}

// application.yml
/*
spring:
  lifecycle:
    timeout-per-shutdown-phase: 30s    # 优雅关闭超时

server:
  shutdown: graceful                    # 优雅关闭 (等待请求处理完)
  tomcat:
    threads:
      max: 200
      min-spare: 20
    accept-count: 100
    max-connections: 8192
    connection-timeout: 20000
*/

// 线程池优雅关闭
@Configuration
public class ThreadPoolConfig {

    @Bean(destroyMethod = "shutdown")
    public ThreadPoolTaskExecutor taskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(10);
        executor.setMaxPoolSize(50);
        executor.setQueueCapacity(200);
        executor.setKeepAliveSeconds(60);
        executor.setThreadNamePrefix("task-");
        // 优雅关闭: 等待任务完成
        executor.setWaitForTasksToCompleteOnShutdown(true);
        executor.setAwaitTerminationSeconds(30);
        return executor;
    }
}
```

---

## 六、CI/CD

### 6.1 Jenkins Pipeline

```groovy
// Jenkinsfile
pipeline {
    agent any

    environment {
        REGISTRY = 'registry.example.com'
        IMAGE = "${REGISTRY}/${env.SERVICE_NAME}"
        VERSION = "${env.BUILD_NUMBER}"
        KUBECONFIG = credentials('kubeconfig-prod')
    }

    parameters {
        choice(name: 'SERVICE_NAME', choices: ['user-service', 'order-service', 'pay-service'], description: '服务名')
        choice(name: 'ENV', choices: ['staging', 'production'], description: '环境')
        string(name: 'BRANCH', defaultValue: 'main', description: '分支')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Test') {
            steps {
                sh 'mvn test -pl ${SERVICE_NAME}'
            }
            post {
                always {
                    junit '**/target/surefire-reports/*.xml'
                    jacoco(execPattern: '**/target/jacoco.exec')
                }
            }
        }

        stage('Build') {
            steps {
                sh 'mvn clean package -DskipTests -pl ${SERVICE_NAME}'
            }
        }

        stage('SonarQube') {
            steps {
                withSonarQubeEnv('sonar') {
                    sh """
                        mvn sonar:sonar \
                          -pl ${SERVICE_NAME} \
                          -Dsonar.projectKey=${SERVICE_NAME} \
                          -Dsonar.projectName=${SERVICE_NAME}
                    """
                }
            }
        }

        stage('Docker Build & Push') {
            steps {
                sh """
                    docker build -t ${IMAGE}:${VERSION} -t ${IMAGE}:latest \
                        --build-arg JAR_FILE=${SERVICE_NAME}/target/*.jar \
                        ${SERVICE_NAME}/
                    docker push ${IMAGE}:${VERSION}
                    docker push ${IMAGE}:latest
                """
            }
        }

        stage('Deploy to K8s') {
            when {
                expression { params.ENV == 'production' }
            }
            steps {
                sh """
                    kubectl set image deployment/${SERVICE_NAME} \
                        ${SERVICE_NAME}=${IMAGE}:${VERSION} \
                        -n ${params.ENV}
                    kubectl rollout status deployment/${SERVICE_NAME} \
                        -n ${params.ENV} --timeout=300s
                """
            }
        }

        stage('Smoke Test') {
            steps {
                sh """
                    sleep 10
                    curl -f http://${SERVICE_NAME}.${params.ENV}/actuator/health
                """
            }
        }
    }

    post {
        failure {
            dingtalk(robot: 'ops-robot', type: 'MARKDOWN',
                title: "部署失败: ${SERVICE_NAME}",
                text: "## ❌ 部署失败\n**服务**: ${SERVICE_NAME}\n**版本**: ${VERSION}\n**环境**: ${params.ENV}\n[查看详情](${env.BUILD_URL})")
            // 回滚
            sh """
                kubectl rollout undo deployment/${SERVICE_NAME} -n ${params.ENV}
            """
        }
        success {
            dingtalk(robot: 'ops-robot', type: 'MARKDOWN',
                title: "部署成功: ${SERVICE_NAME}",
                text: "## ✅ 部署成功\n**服务**: ${SERVICE_NAME}\n**版本**: ${VERSION}\n**环境**: ${params.ENV}")
        }
    }
}
```

---

## 七、监控与运维

### 7.1 JVM 监控

```bash
# === Prometheus + Micrometer ===
# Spring Boot Actuator 已暴露 /actuator/prometheus
# Prometheus 抓取配置:
# - job_name: 'java-app'
#   metrics_path: /actuator/prometheus
#   static_configs:
#     - targets: ['192.168.1.10:8080']

# 关键指标:
# jvm_memory_used_bytes           JVM 内存使用
# jvm_memory_committed_bytes      JVM 已分配内存
# jvm_gc_pause_seconds_count      GC 次数
# jvm_gc_pause_seconds_sum        GC 总耗时
# jvm_threads_live_threads        活跃线程数
# jvm_threads_states_threads      线程状态分布
# process_cpu_usage               CPU 使用率
# http_server_requests_seconds    HTTP 请求延迟

# Grafana 仪表盘:
# JVM (Micrometer): ID 4701
# Spring Boot Statistics: ID 11378
# Spring Boot 2.1 System Monitor: ID 12346
```

### 7.2 JVM 诊断工具

```bash
# === JDK 自带工具 ===

# jps: 查看 Java 进程
jps -lvm

# jstat: GC 统计 (每秒刷新)
jstat -gcutil <pid> 1000

#  S0     S1     E      O      M     CCS    YGC   YGCT   FGC  FGCT   GCT
# 0.00  45.23  67.89  34.56  95.12  91.34   23   0.234    2  0.456  0.690

# jstack: 线程栈 (排查死锁/CPU 高)
jstack <pid> > thread_dump.txt

# jmap: 堆内存分析
jmap -heap <pid>                    # 堆内存概况
jmap -histo:live <pid> | head -20   # 对象统计 (Top 20)
jmap -dump:format=b,file=heap.hprof <pid>  # 堆 dump

# === JDK 21 jcmd ===
jcmd <pid> VM.flags                 # JVM 参数
jcmd <pid> GC.heap_info             # 堆信息
jcmd <pid> Thread.print             # 线程栈
jcmd <pid> GC.class_histogram       # 类统计
jcmd <pid> GC.dump_heap /tmp/heap.hprof  # 堆 dump
jcmd <pid> Thread.dump_to_file /tmp/threads.txt  # 线程 dump

# === CPU 高排查 ===
# 1. 找到 CPU 高的 Java 进程
top -c
# 假设 PID = 12345

# 2. 找到 CPU 高的线程
top -Hp 12345
# 假设线程 PID = 12350

# 3. 线程 ID 转十六进制
printf "%x\n" 12350
# 输出: 303e

# 4. 在 jstack 中找到对应线程
jstack 12345 | grep "0x303e" -A 30

# === 内存泄漏排查 ===
# 1. 触发堆 dump
jcmd <pid> GC.dump_heap /tmp/heap.hprof

# 2. 使用 MAT (Eclipse Memory Analyzer) 分析
# 或在线分析: https://heaphero.io/

# 3. 查看大对象
jmap -histo:live <pid> | head -20

# === Arthas (阿里诊断工具, 强烈推荐) ===
# 安装
curl -O https://arthas.aliyun.com/arthas-boot.jar
java -jar arthas-boot.jar

# 常用命令:
dashboard                          # 实时面板 (线程/内存/GC)
thread                             # 线程列表
thread <id>                        # 查看线程栈
thread -n 3                        # CPU 最高的 3 个线程
jad com.example.UserService        # 反编译类
watch com.example.UserService getById '{params, returnObj}' '#cost>100'  # 观察方法
trace com.example.UserService getById  # 调用链耗时
monitor com.example.UserService getById 10  # 方法执行统计
heapdump /tmp/heap.hprof           # 堆 dump
vmtool --action getInstances --className java.lang.String --limit 10  # 查看对象
```

### 7.3 GC 日志分析

```bash
# GC 日志格式 (JDK 21, ZGC)
# 使用 GCEasy (https://gceasy.io/) 在线分析

# 关键指标:
# - Throughput (吞吐量): 应用运行时间 / 总时间 > 95%
# - Average GC Pause: < 200ms
# - Max GC Pause: < 500ms
# - GC 频率: YGC < 10次/分钟, FGC < 1次/小时

# GC 日志关键行:
# [gc] GC(12) Pause Young 200M->100M(500M) 15.234ms  # Minor GC
# [gc] GC(15) Pause Full 800M->400M(1G) 500.123ms    # Full GC (需要关注)
```

### 7.4 日志配置

```xml
<!-- logback-spring.xml -->
<configuration>
    <springProperty scope="context" name="APP_NAME" source="spring.application.name"/>

    <!-- 控制台 (K8s 环境, 容器 stdout) -->
    <appender name="CONSOLE" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %highlight(%-5level) %cyan(%logger{36}) - %msg%n</pattern>
        </encoder>
    </appender>

    <!-- 文件 (滚动) -->
    <appender name="FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>/opt/app/logs/${APP_NAME}.log</file>
        <rollingPolicy class="ch.qos.logback.core.rolling.SizeAndTimeBasedRollingPolicy">
            <fileNamePattern>/opt/app/logs/${APP_NAME}.%d{yyyy-MM-dd}.%i.log.gz</fileNamePattern>
            <maxFileSize>100MB</maxFileSize>
            <maxHistory>30</maxHistory>
            <totalSizeCap>10GB</totalSizeCap>
        </rollingPolicy>
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>

    <!-- 错误日志单独输出 -->
    <appender name="ERROR_FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>/opt/app/logs/${APP_NAME}-error.log</file>
        <filter class="ch.qos.logback.classic.filter.ThresholdFilter">
            <level>ERROR</level>
        </filter>
        <rollingPolicy class="ch.qos.logback.core.rolling.SizeAndTimeBasedRollingPolicy">
            <fileNamePattern>/opt/app/logs/${APP_NAME}-error.%d{yyyy-MM-dd}.%i.log.gz</fileNamePattern>
            <maxFileSize>100MB</maxFileSize>
            <maxHistory>90</maxHistory>
        </rollingPolicy>
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>

    <!-- 异步日志 (提升性能) -->
    <appender name="ASYNC_FILE" class="ch.qos.logback.classic.AsyncAppender">
        <queueSize>1024</queueSize>
        <discardingThreshold>0</discardingThreshold>
        <neverBlock>true</neverBlock>
        <appender-ref ref="FILE"/>
    </appender>

    <root level="INFO">
        <appender-ref ref="CONSOLE"/>
        <appender-ref ref="ASYNC_FILE"/>
        <appender-ref ref="ERROR_FILE"/>
    </root>
</configuration>
```

---

## 八、故障排查手册

### 8.1 常见故障

| 故障 | 现象 | 排查 | 解决 |
|:---|:---|:---|:---|
| OOM | 进程退出, heap dump | `jmap -histo`, MAT 分析 | 修复内存泄漏 / 加内存 |
| CPU 100% | 响应慢, load 高 | `top -Hp`, `jstack` | 优化代码 / 加节点 |
| Full GC 频繁 | STW 停顿, 响应慢 | GC 日志, `jstat` | 调整堆/GC 参数 |
| 线程死锁 | 请求超时, 无响应 | `jstack`, 查 deadlock | 修复锁顺序 |
| 连接池耗尽 | 请求超时 | Druid 监控页 | 加大连接池 / 排查慢 SQL |
| 启动慢 | 启动 > 60s | 启动日志, Spring Bean 分析 | 关闭不必要的自动配置 |
| 服务注册失败 | Nacos 看不到服务 | Nacos 日志, 网络 | 检查 namespace/网络 |
| Feign 调用超时 | 服务间调用失败 | Feign 日志 | 调超时 / 熔断降级 |

### 8.2 OOM 排查

```bash
# 1. 确认 OOM 类型
# java.lang.OutOfMemoryError: Java heap space      → 堆内存不足
# java.lang.OutOfMemoryError: Metaspace            → 元空间不足
# java.lang.OutOfMemoryError: Direct buffer memory → 堆外内存不足
# java.lang.OutOfMemoryError: unable to create new native thread → 线程数过多

# 2. 堆 OOM 排查
# 查看堆 dump (OOM 时自动生成)
ls -la /opt/app/heapdump/
# 使用 MAT 分析:
# - Leak Suspects (泄漏嫌疑)
# - Dominator Tree (对象引用树)
# - Top Consumers (大对象)

# 3. 线程数过多排查
jstack <pid> | grep "java.lang.Thread.State" | wc -l
# 查看线程分布
jstack <pid> | grep "java.lang.Thread.State" | sort | uniq -c | sort -rn

# 4. 堆外内存排查 (NIO/Netty)
# 使用 Native Memory Tracking
java -XX:NativeMemoryTracking=detail -jar app.jar
jcmd <pid> VM.native_memory summary
```

### 8.3 GC 调优

```bash
# 1. 收集 GC 日志
# 启动时添加: -Xlog:gc*:file=gc.log:time,uptime

# 2. 分析 GC 日志
# 上传到 https://gceasy.io/ 分析
# 关注: 吞吐量 / 平均停顿 / 最大停顿 / GC 频率

# 3. 常见调优

# Young GC 频繁:
#   原因: Eden 太小
#   方案: 增大年轻代 (-XX:NewRatio=2 → NewRatio=1)
#         或增大整体堆 (-Xmx)

# Full GC 频繁:
#   原因: 老年代太小 / 内存泄漏 / 大对象直接进老年代
#   方案:
#     - 检查是否有大对象 (jmap -histo)
#     - 增大老年代 (-Xmx)
#     - 调大晋升阈值 (-XX:MaxTenuringThreshold=15)
#     - 检查是否有内存泄漏 (MAT)

# GC 停顿长:
#   G1:  降低 -XX:MaxGCPauseMillis (但吞吐会降)
#   切换: ZGC (停顿 < 1ms)

# 4. 验证调优效果
# 对比调优前后的 GC 日志 (gceasy.io)
```

---

## 九、对比总结

### 9.1 单体 vs 微服务运维对比

| 维度 | 单体应用 | 微服务 |
|:---|:---|:---|
| 部署 | 单包部署 (JAR/WAR) | 多服务独立部署 (Docker/K8s) |
| 配置 | application.yml | Nacos 配置中心 |
| 服务发现 | 无需 | Nacos/Eureka |
| 网关 | Nginx | Spring Cloud Gateway |
| 通信 | 方法调用 | OpenFeign/gRPC |
| 事务 | 本地事务 (@Transactional) | Seata 分布式事务 |
| 熔断 | 无需 | Sentinel |
| 追踪 | 无需 | SkyWalking/Zipkin |
| CI/CD | 单流水线 | 多服务流水线 |
| 监控 | 单应用监控 | 全链路监控 |
| 日志 | 单机日志 | ELK/Loki 集中日志 |
| 扩展 | 整体扩容 | 按需独立扩缩容 (HPA) |
| 故障排查 | 单进程 (jstack/jmap) | 全链路 (SkyWalking) |

### 9.2 运维检查清单

```
部署前检查:
  □ JVM 参数配置正确 (-Xms == -Xmx, GC 选择)
  □ 健康检查端点 (/actuator/health)
  □ 优雅关闭配置 (server.shutdown=graceful)
  □ 日志输出格式 (JSON 或结构化)
  □ 监控端点暴露 (/actuator/prometheus)
  □ SkyWalking Agent 挂载
  □ Nacos 注册正确 (namespace/group/cluster)
  □ 配置中心连接 (Nacos Config)
  □ 数据库连接池参数 (Druid)
  □ Redis 连接池参数 (Lettuce)
  □ 线程池配置 (core/max/queue)
  □ 超时配置 (Feign/RestTemplate/DB)
  □ 熔断限流规则 (Sentinel)
  □ 资源限制 (K8s requests/limits)

日常巡检:
  □ JVM 内存使用率 < 80%
  □ GC 停顿 < 200ms
  □ Full GC 频率 < 1次/小时
  □ 线程数正常 (< 500)
  □ 连接池使用率 < 80%
  □ HTTP P99 < 1s
  □ 错误率 < 0.1%
  □ 日志磁盘空间 < 80%
  □ Nacos 服务列表完整
  □ SkyWalking 链路完整
```

---

## 十、配置文件速查表

| 组件 | 配置文件 | 默认端口 |
|:---|:---|:---|
| Spring Boot | `application.yml` / `bootstrap.yml` | 8080 |
| Nacos | `/opt/nacos/conf/application.properties` | 8848, 9848 (gRPC) |
| Sentinel Dashboard | Docker 参数 | 8858 |
| Seata Server | `/opt/seata/conf/application.yml` | 8091 |
| SkyWalking OAP | Docker 参数 | 11800 (gRPC), 12800 (HTTP) |
| SkyWalking UI | Docker 参数 | 8080 |
| Gateway | `application.yml` | 8080 |
| Druid | `application.yml` (spring.datasource.druid) | - |
| Arthas | 交互式 CLI | 3658 (telnet) |
| Jenkins | `/etc/sysconfig/jenkins` | 8080 |

---

*最后更新: 2026-07-11*
