---
name: refactor-java
command: refactor-java
user_invocable: true
description: Java 代码重构。处理 Java/Spring 项目的过度设计：God Class、接口泛滥、设计模式滥用、依赖注入过度。输出重构计划交给 /run-plan 执行。
---

# Java 代码重构 (Refactor Java)

> **角色**：Java 代码质量守护者
> **目标**：让 Java 代码保持"恰到好处"的状态
> **原则**：简单、合适、演化
> **思考模式**：启用 ultrathink 深度思考，全面评估 Java 重构影响

---

## 依赖规范

本 Skill 依赖以下规范文件：

| 规范文件 | 覆盖内容 |
|---------|---------|
| `.claude/rules/代码质量.md` | 项目铁律（禁止 Mock 测试） |
| `.claude/rules/代码清洁.md` | 未使用代码检测（PMD、SpotBugs） |
| `.claude/rules/文档规范.md` | 重构计划文档存放位置 |

> **职责分离**：本 Skill 定义重构**流程**，`rules/` 定义**代码标准**。

---

## Java 重构哲学

**"Java 的问题不是代码太少，而是抽象太多"**

Java 开发者容易过度使用：
- 设计模式（Factory、Strategy、Builder...）
- 接口抽象（IXxxService、XxxRepository）
- 分层架构（Controller → Service → Repository → DAO）
- 依赖注入（Spring @Autowired 泛滥）

但也要注意：**必要的抽象是好的**，关键是判断"是否必要"。

---

## 重构方向判断

| 问题类型 | 特征 | 方向 |
|---------|------|------|
| **过度设计** | 接口多实现少、层级多但透传 | 减法 |
| **设计不足** | 职责混乱、重复代码、难扩展 | 加法 |
| **设计不当** | 边界不清、依赖方向错误 | 调整 |

---

## 减法：过度设计模式识别

### 🔴 P0 - 必须处理

| 模式 | 特征 | 重构方法 |
|------|------|---------|
| **空接口** | 接口只有一个实现类 | 删除接口，保留实现类 |
| **God Class** | >1000行，>10个依赖，>20个方法 | 按职责拆分为多个 Service |
| **依赖爆炸** | 一个类 >10 个 @Autowired | 拆分类或合并依赖 |
| **死代码** | 从未调用的方法/类 | 直接删除 |

### 🟡 P1 - 强烈建议处理

| 模式 | 特征 | 重构方法 |
|------|------|---------|
| **假工厂模式** | Factory 只创建一种对象 | 直接 `new` |
| **假策略模式** | Strategy 只有一个实现 | 删除接口，内联逻辑 |
| **假建造者模式** | Builder 只有 2-3 个字段 | 用构造函数或静态工厂 |
| **透传层** | Service 只是调用 Repository | 合并层 |
| **DTO 爆炸** | 每个接口一套 Request/Response | 复用或直接用 Entity |

---

## 加法：设计不足模式识别

### 何时需要加抽象

| 场景 | 建议 |
|------|------|
| 有 **多个实现** 需要切换 | 保留/添加接口 |
| 有 **真实的扩展需求** | 保留/添加扩展点 |
| **重复代码** 出现 3 次以上 | 抽取公共方法/类 |
| **职责混乱**，一个类做太多事 | 拆分职责 |
| 需要 **事务控制** | 保留 Service 层 |

### 示例：何时保留接口

```java
// ✅ 保留接口：有多个实现
public interface PaymentService {
    void pay(Order order);
}

@Service("alipay")
public class AlipayService implements PaymentService { ... }

@Service("wechatpay")
public class WechatPayService implements PaymentService { ... }

// 运行时根据配置切换
@Autowired
@Qualifier("${payment.provider}")
private PaymentService paymentService;
```

---

## 调整：设计不当模式识别

### 常见问题

| 问题 | 特征 | 重构方法 |
|------|------|---------|
| **循环依赖** | A → B → A | 提取公共依赖或调整边界 |
| **依赖方向错误** | 底层依赖上层 | 依赖倒置 |
| **边界不清** | 模块间互相调用 | 重新划分模块边界 |
| **职责不清** | 不知道该放哪个类 | 明确职责，重新分配 |

---

## 具体案例：God Class 拆分

### 识别 God Class

```java
// 🔴 典型 God Class 特征
@Service
public class MessageCallbackServiceImpl {

    @Autowired private ObjectMapper objectMapper;
    @Autowired private RestTemplate restTemplate;
    @Autowired private ContentProcessChain contentProcessChain;
    // ... 还有 24 个 @Autowired（共 27 个依赖）

    // ... 1983 行代码，45 个方法
}
```

**诊断指标**：
- 代码行数：1983 行（建议 ≤300）
- 方法数：45 个（建议 ≤10）
- 依赖数：27 个（建议 ≤5）

### 拆分策略

**按消息类型/场景拆分**：

```java
// ✅ 拆分后

@Service
public class MessageCallbackService {  // 入口协调，~100 行
    @Autowired private MessageRoutingService routingService;
    @Autowired private GroupMessageService groupService;
    @Autowired private StaffMessageService staffService;

    public void handleCallback(JuziMsgCallbackVO model) {
        if (routingService.isGroupMessage(model)) {
            groupService.handle(model);
        } else if (routingService.isStaffMessage(model)) {
            staffService.handle(model);
        }
        // ...
    }
}

@Service
public class GroupMessageService {  // 群聊处理，~200 行
    // 只注入群聊相关的依赖
}

@Service
public class StaffMessageService {  // 员工消息，~150 行
    // 只注入员工相关的依赖
}
```

---

## 具体案例：删除空接口

### 识别空接口

```java
// 🔴 只有一个实现的接口
public interface IUserService {
    User getUser(Long id);
    void saveUser(User user);
}

@Service
public class UserServiceImpl implements IUserService {
    @Override
    public User getUser(Long id) { ... }
    @Override
    public void saveUser(User user) { ... }
}
```

### 删除接口

```java
// ✅ 直接用类
@Service
public class UserService {
    public User getUser(Long id) { ... }
    public void saveUser(User user) { ... }
}
```

**删除条件**：
- 接口只有一个实现
- 可预见的将来不会有其他实现
- 不是对外暴露的 API 契约

---

## Spring 特定规则

### @Autowired 数量控制

| 依赖数 | 状态 | 行动 |
|-------|------|------|
| 1-5 | ✅ 正常 | 无需处理 |
| 6-10 | ⚠️ 警告 | 考虑拆分 |
| >10 | 🔴 严重 | 必须拆分 |

### 分层判断

| 层有实际逻辑？ | 行动 |
|--------------|------|
| ✅ 有业务逻辑、事务、权限 | 保留 |
| ❌ 只是透传 | 可以合并 |

---

## 执行流程

### Phase 1: 代码诊断

```bash
# 统计代码行数
find . -name "*.java" -exec wc -l {} \; | sort -rn | head -20

# 统计类的方法数
grep -c "public\|private\|protected" XxxService.java

# 统计依赖注入数
grep -c "@Autowired\|@Resource\|@Inject" XxxService.java
```

### Phase 2: 识别问题类型

- [ ] 过度设计？（减法）
- [ ] 设计不足？（加法）
- [ ] 设计不当？（调整）

### Phase 3: 制定重构计划

输出到 `docs/开发文档/plan_重构_[模块名].md`

---

## 危险信号

| 信号 | 行动 |
|------|------|
| 重构后更难理解 | 停，方向可能错了 |
| 引入新复杂度而无收益 | 停，重新评估 |
| 想引入设计模式来"优化" | 停，确认是否真的需要 |
| 拆分后每个类还是 >300 行 | 继续拆分 |

---

## 常见误区

> **规范来源**：`.claude/rules/代码质量.md`（项目铁律三：禁止 Mock）

| 误区 | 正确理解 |
|------|---------|
| "接口方便 Mock 测试" | **铁律禁止 Mock**，用真实数据测试 |
| "工厂方便扩展" | 需要时再加（YAGNI） |
| "分层是最佳实践" | 透传层是浪费 |
| "抽象都是好的" | 过度抽象是坏的 |
| "代码越少越好" | 合适的代码量才是好的 |

---

## 完成检查清单

- [ ] 问题类型明确（过度设计/设计不足/设计不当）
- [ ] 重构方向明确（减法/加法/调整）
- [ ] 符合三原则（简单、合适、演化）
- [ ] 没有 >1000 行的类
- [ ] 没有 >10 个 @Autowired 的类
- [ ] 重构计划已输出
