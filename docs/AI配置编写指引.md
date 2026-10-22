# AI 配置编写指引（APISIX / ADC）

> 读者：被要求**编写/修改本仓库网关配置**的 AI 代理。
> 配套：仓库根 [`AGENTS.md`](../AGENTS.md)（AI 工具自动读取的简洁版）、
> [`docs/配置仓库结构设计.md`](./配置仓库结构设计.md)（设计全文）、[`docs/official/INDEX.md`](./official/INDEX.md)（官方文档本地镜像索引）。

---

## 1. 心智模型（先懂这个再动手）

```
configs/**/*.yaml  ←— 唯一真相来源（GitOps）
        │  lint（本地 schema 校验）/ validate（后端校验）/ diff（对照网关）
        ▼
   adc sync ──→ 网关被对账成与文件【完全一致】
```

- 仓库用 **ADC v0.30.3** 管理 **Apache APISIX** 网关；`.env` 里的 `ADC_BACKEND=apisix`、`ADC_SERVER`、`ADC_TOKEN` 是连接信息（**不要动、不要提交**）。
- **`sync` 是全量对账**：命令作用域内、文件里没有的远端资源会被删除。所以：AI **默认不执行 sync**，最多做到 `diff`；sync 由人工确认。
- 你的输出物只有一样：`configs/` 下正确、可 lint 的 YAML。

---

## 2. 动手前：信息收集（缺了就问，禁止编造）

| 任务 | 必须拿到 | 缺了怎么办 |
| ---- | ---- | ---- |
| 新增站点 | 站点代码（主域名去 www）、域名列表、后端地址:端口、站点类型、**网络分区 zone（intranet/extranet/public）**、负责团队 | **问用户**；不要用 `<占位>` 同步 |
| 加插件 | 插件名、参数取值（阈值/路径/密钥策略） | 参数查官方插件文档；取值不明确就问 |
| 换证书 | 新证书 PEM（fullchain + key） | 让用户提供文件内容或 secret 引用 |
| 加消费者 | username、凭证类型、密钥 | 问；密钥不要编造 |

> 禁止把模板里的 `<site-code>`、`<team>` 等占位符原样写进真实配置。

---

## 3. 查询方法（先查后写，字段以官方为准）

按顺序查，不要凭记忆：

1. **`docs/official/INDEX.md`** —— 「我要写 X → 打开哪个文件」总表
2. **`docs/official/adc/configuration.md`** —— ADC 配置格式：顶层 6 键、必填字段、变量语法
3. **`docs/official/adc/schema.json`** —— **lint 的校验依据**，字段合法性最终裁决（每个字段的 type/required/enum/default 都在这里）
4. **`docs/official/apisix/admin-api.md`** —— 各资源字段全表（Route/Service/Upstream/Consumer/SSL 的 Request Body 表）
5. **`docs/official/apisix/plugins/<插件名>.md`** —— 插件参数（属性表）
6. **`configs/_templates/*.yaml`** —— 类型模板（复制起点，**只读不修改**）
7. **`configs/sites/*/` 现有文件** —— 与本仓库风格对齐

---

## 4. 编写规范

### 4.1 目录与放置

| 资源 | 放哪 |
| ---- | ---- |
| service（含 routes/upstream） | `configs/sites/<zone>/<site-code>/service.yaml`（zone = intranet/extranet/public） |
| 站点证书 | `configs/sites/<zone>/<site-code>/ssl.yaml` |
| 通配/多站共用证书 | `configs/global/ssls/`（一张证书只定义一次） |
| 公共消费者 | `configs/global/consumers/`；站点专属 → 站点目录 |
| global_rules / plugin_metadata | `configs/global/`（影响全网关，谨慎） |

`configs/_templates/` 是模板目录，**在 sync 作用域外**：只复制、不修改。

### 4.2 命名（ADC 按名字生成资源 ID）

| 对象 | 规则 |
| ---- | ---- |
| 站点目录 | `<site-code>/`（主域名去 www，小写连字符） |
| `service.name` | `<site-code>-<用途>`，全局唯一 |
| `route.name` | `<site-code>-<路径/用途>`，service 内唯一 |
| `consumer.username` | `<site-code>-<用途>`，全局唯一 |

> **改名 = 删旧建新**（ID = sha1(name)）。已上线的资源不要改名；确需改名先 `adc dump --with-id` 保住 ID。

### 4.3 labels（每个 service/consumer/ssl 必填 5 个）

```yaml
labels:
  site: <site-code>
  zone: intranet        # 网络分区（必填）：intranet/extranet/public，必须与目录一致
  site_type: www        # www/api/ws/static/admin/partner/internal
  env: prod
  owner: <team>
```

> **网络分区（zone）决定安全姿态**：内网（`intranet/`）必须走 PROXY protocol（PP）
> （`vars: server_port in ["9181","9182"]` + `real-ip` 插件）且必须带 `ip-restriction`
> 白名单；外网**不走 PP**（`vars: server_port in ["18080","19443"]`，外网专属监听口，
> 前置 LB 为 DNAT 保留源 IP），IP 限制可选；公网/互联网**不走 PP**
> （`vars: server_port in ["80","443"]`，标准监听口），不要求 IP 限制。
> 内网（9181/9182）、外网（18080/19443）、公网（80/443）三区端口互不重叠 →
> 任一区请求命中不了其他区路由。模板：`_templates/intranet|extranet|public.yaml`；
> 详见 `docs/配置仓库结构设计.md` §4.3。

### 4.4 ADC 特有字段差异（易错）

| 主题 | 正确写法（ADC） | 别写成 |
| ---- | ---- | ---- |
| 上游节点 | `nodes: [{host, port, weight, priority}]`（**数组**） | `"ip:port": weight`（那是 Admin API 的键值对） |
| 描述字段 | `description` | `desc`（Admin API 字段，ADC 不认） |
| route 必填 | `name` + `uris` | 只有 `uri` 字符串 |
| 文件路径 | **正斜杠** `configs/global/**/*.yaml` | 反斜杠（adc 会崩溃） |
| 变量语法 | `$env://`（数据面）/ `${ENV}`（ADC 侧）/ `\${}`（内置变量） | 混用/忘记转义（见 configuration.md §Variables） |

### 4.5 插件差异与路由颗粒度（站点差异的表达方式）

- 插件合并优先级（官方）：`Consumer > Consumer Group > Route > Plugin Config > Service`；**global_rules 与本地同名插件都会执行**（不是覆盖）。
- 挂载层选择：全站通用 → service 级；仅某路径 → route 级；全网关 → global_rules。
- 颗粒度自定：差异按路径分 → 拆多条 route 各挂插件；全站一致 → 一条 `/*` + service 插件。
- 匹配：精确路径自动优先于通配；同 uri 多条路由比 `priority`（大者先）。
- ⚠️ **ADC 声明式 YAML 不支持 `plugin_config`**；跨站复用插件组合 = 复制到各站 / service 级 / consumer_groups。

### 4.6 可读性与可维护性（人读、人审、人改）

> 配置文件最终由**人**阅读、审查、手动修改。AI 写完后要以"人类审查者"的视角自查：
> **不看文档能不能读懂每个字段？diff 是不是最小、最好审？**

**字段顺序（与模板一致，全仓库统一）**

```
service:  name → description → labels → upstream → routes
route:    name → uris → hosts → methods → priority → enable_websocket → plugins
upstream: type → scheme → pass_host → nodes → checks → timeout
plugins:  键按字母序
```

**注释**

- 每个站点文件**必须有头部注释块**：站点身份、类型、负责人、后端地址（人看的第一眼）。
- 行内注释只加在"不显然"的值上：业务含义 / 为什么这样（`count: 600  # 每IP每分钟600次`）。
- routes 多时用分区注释 `# ---- 前台路由 ----` 分段。
- **不注释**显而易见的内容（`name:`/`uris:` 不用解释）；优先注释"为什么"。

**YAML 语法（可读性优先）**

- 2 空格缩进，禁 tab；短数组内联（`methods: [GET, POST]`）、长数组用 `- item` 列表。
- 含特殊字符（`: # { } [ ]`）的字符串**必须**引号；中文字符串建议引号。
- 布尔 `true/false`、数字裸写；PEM 证书用 `|` 块状。

**可维护性（写之前就想好怎么被改）**

- 一个站点一个 `service.yaml`，单文件 ≤ ~200 行；超过用分区注释组织。
- **最小 diff**：一次只改一件事，不顺手重排/改名/美化无关部分。
- **删除即删除**，不留大段注释掉的旧配置。
- 站点 `README.md` 维护变更记录（日期/内容/原因）。
- `owner`/`contact` 标签必填（人找得到负责人）。
- 魔法值（限流阈值、超时、priority、`verify: false`）旁边写明业务依据。

---

## 5. 验证流程（写完后必走，缺一不可）

```powershell
.\scripts\lint.ps1        # ① 本地 schema 校验 —— 必须 0 错误
.\scripts\validate.ps1    # ② 后端校验（需网关可达）—— 尽量通过
.\scripts\diff.ps1        # ③ 对照网关 —— 必须只含预期的 create/update
```

- ③ 出现**无关的 delete**：立即停下排查（大概率是文件没写全或动了不该动的资源）。
- ④ **sync 由人工执行**（`.\scripts\sync.ps1`）；除非用户明确授权，AI 不运行 sync。

---

## 6. 限制与红线（违反 = 报错或误删网关配置）

1. **严禁 `configs/**/*.yaml` 全量 glob** —— 会把 `configs/_templates/`（含占位符）吞进同步。只准 `configs/global/**/*.yaml` + `configs/sites/**/*.yaml`。
2. **不改资源名**（改名=删旧建新）；**轮换证书保持 `snis` 不变**（ssl ID = sha1(snis)）。
3. **不手动改 Admin API / Dashboard** —— 下次 sync 会被抹掉。
4. **不动 `.env`**（含 Token，永不提交）；密钥用 `${ENV}` 或 `$env://` 或 `$secret://` 注入，除非用户明确要求内联。
5. **`global_rules` / `plugin_metadata` 影响全网关** —— 改动前说明影响面。
6. **缺信息就问，不编造**；模板占位符不得进入真实配置。
7. **字段不猜**：`Unrecognized key: "xxx"` = 字段名错或该字段不存在，对照 schema.json / 官方文档修改。
8. **`$env://` / `$secret://` 引用会跳过该字段的 schema 校验**（官方 secret.md）——引用必须可解析，否则字面串被当值用。
9. **内联证书 PEM 有长度/格式约束**（certificate ≥128 字符、key ≥32 字符，含 `-----BEGIN/END-----` 行）。
10. **反斜杠路径、`-f a b` 一次传多文件**都会让 adc 失败 —— 用 `scripts/` 封装（内部已按正斜杠 + 逐个 `-f` 处理）。

---

## 7. 常见任务速查

| 任务 | 怎么做 |
| ---- | ---- |
| 新增站点 | 复制网络区模板 `configs/_templates/intranet|extranet|public.yaml` → `configs/sites/<zone>/<code>/service.yaml`（路由形态参考 www/api/ws/static/admin.yaml），替换占位符、补全 labels（zone 与目录一致）→ 流程见第 5 节 |
| 给路由加插件 | 在对应 `routes[]` 的 `plugins:` 下加；参数查 `docs/official/apisix/plugins/` |
| 全站加插件 | 加在 service 级 `plugins:` |
| 改上游节点 | 改 `upstream.nodes` 数组（增删 host/port/weight） |
| 加消费者 | `configs/global/consumers/` 或站点目录 `consumers.yaml`，配 credentials |
| 换证书 | 改 ssl.yaml 的 certificate/key（**snis 不动**）→ 见 `docs/证书轮换操作手册.md` |
| 加全局规则 | `configs/global/global-rules.yaml`（说明全网关影响） |

---

## 8. 本仓库实测已知坑

| 坑 | 说明 |
| ---- | ---- |
| 反斜杠路径 | adc（node glob）把 `\` 当转义符 → 崩溃；一律正斜杠 |
| `managed-by: adc` 标签 | sync 时 ADC 自动注入到资源上，diff/dump 里出现是**正常现象**，不要删 |
| `-f` 单值 | 一次 `-f` 只接受一个文件/glob；多文件重复 `-f`（脚本已封装） |
| 测试站点 | testport 示例已删除；新站点从 zone 模板建（`configs/_templates/intranet|extranet|public.yaml`） |
| 版本 | ADC v0.30.3；`$env://`/`${ENV}`/`\${}` 分别要求 ≥ v0.12.1/v0.12.0/v0.19.1 |

---

## 9. AI 自检清单（交付前逐项打勾）

- [ ] 路径全部正斜杠
- [ ] 字段都能在 schema.json / 官方文档找到，无 `Unrecognized key`
- [ ] `nodes` 是数组格式；用 `description` 不用 `desc`
- [ ] labels 五个（site/zone/site_type/env/owner）齐全，且 `zone` 与目录一致
- [ ] 内网路由：`server_port in ["9181","9182"]` + `real-ip` + `ip-restriction` 白名单（不允许留空）
- [ ] 外网路由：`server_port in ["18080","19443"]`；公网/互联网路由：`server_port in ["80","443"]`（三区端口不得混用）
- [ ] 命名规范（service/route/consumer 唯一性）符合
- [ ] 未改资源名 / 未动 snis（除非任务是改名/加域名）
- [ ] 模板目录 `_templates/` 未被修改
- [ ] 未用 `configs/**/*.yaml`
- [ ] 密钥/私钥未硬编码（除非明确要求）
- [ ] `lint` 通过；`diff` 只含预期 create/update，无无关 delete
- [ ] 未执行 sync（留给人工）
- [ ] **可读性**：文件头部注释块齐全；字段顺序与模板一致；魔法值有注释；无大段注释掉的旧配置
- [ ] **可维护性**：改动是"最小 diff"（没顺手重排/改名/美化无关部分）；站点 README 变更记录已更新
