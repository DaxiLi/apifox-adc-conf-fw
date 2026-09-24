# ADC 使用指南（APISIX Declarative CLI）

> 适用版本：`adc v0.30.3`（当前仓库便携安装版） | 后端：Apache APISIX

---

## 1. ADC 是什么？

ADC（**API Declarative CLI**，声明式 API 命令行工具）是一个管理 APISIX / API7 网关配置的命令行工具。

传统的 APISIX 配置方式是**手动调用 Admin API**，一个个去创建路由、服务、上游，配置分散、无法审计、容易出错。

ADC 的核心理念是 **GitOps / 配置即代码**：

1. 你把网关的"**期望状态**"写在一个个 **YAML 文件**里（存到 Git 进行版本管理）；
2. ADC 负责把本地文件和**运行中的网关**做比对（`diff`）；
3. 确认无误后执行 `sync`，让网关配置与本地文件**完全一致**。

```
本地 YAML (唯一真相来源)  ──sync──▶  APISIX 网关 (Admin API)
        ▲                                 │
        └──────────dump / diff ◀──────────┘
```

**记住一句话：本地的 YAML 文件说了算。** 网关里凡是本地文件没写的资源，都会被 ADC 删掉。

---

## 2. 本项目环境

### 2.1 目录结构

```
api-cluster/
├── adc.cmd                          # ADC 启动入口（直接调用 .bin 下的可执行文件）
├── .env                             # 网关连接配置（含 Token，已被 .gitignore 排除）
├── .gitignore                       # 忽略 .bin/、.env 等
├── .bin/adc/adc.exe                 # ADC 便携安装（不污染宿主机 PATH）
├── docs/                            # 本文档 + 官方文档本地镜像（docs/official/）
├── scripts/                         # 常用命令封装（lint / validate / diff / sync）
└── configs/                         # 配置唯一真相来源（结构见 docs/配置仓库结构设计.md）
    ├── _templates/                  # 站点模板（网络区 + 站点类型；不在 sync 作用域内）
    ├── global/                      # 全局规则 / 插件元数据 / 公共消费者 / 通配证书
    └── sites/                       # 第一层 = 网络区（intranet/extranet/public）
        └── intranet/                # 内网：PROXY + IP 白名单必开
            └── ss-admin.ynfwyy.com/ # 站点「第三方厂家管理后台反代」
                ├── service.yaml     # 服务 + 路由 + 上游
                └── README.md        # 站点说明
```

### 2.2 怎么调用 ADC

在本仓库根目录下直接使用 `adc.cmd`（等效于完整路径 `.bin\adc\adc.exe`）：

```powershell
# PowerShell / CMD 通用
.\adc.cmd --version        # 查看版本
.\adc.cmd --help           # 查看帮助
```

> 注意：ADC 二进制在 `.bin/adc/`（已 gitignore，不入库）；新环境用 `scripts/install-adc.ps1`（或 `install-adc.sh`）自举安装，日常使用 `adc.cmd`（Windows）/ `./adc`（Linux/macOS）即可。

### 2.3 升级 ADC

到 [api7/adc Releases](https://github.com/api7/adc/releases) 下载对应平台的 zip 包，
解压覆盖 `.bin\adc\adc.exe` 即可（与官网 install 脚本原理一致）。

---

## 3. 连接配置（.env）

ADC 通过 Admin API 连接 APISIX，连接信息写在项目根目录的 `.env` 文件中：

```ini
ADC_BACKEND=apisix
ADC_SERVER=http://172.32.100.200:19180
ADC_TOKEN=你的Admin-API-Key
```

| 变量 | 说明 |
| ---- | ---- |
| `ADC_BACKEND` | 后端类型，本仓库固定为 `apisix`（可选 `api7ee`、`apisix-standalone`） |
| `ADC_SERVER` | APISIX Admin API 地址（默认 `http://localhost:9180`） |
| `ADC_TOKEN` | Admin API 的密钥（在 APISIX `config.yaml` 的 `deployment.admin.admin_key` 中配置） |

`.env` 里是敏感信息（Token），所以已被 `.gitignore` 排除，**不要提交到 Git**。

还有两个常用的 TLS 变量（如果 Admin API 走 HTTPS）：

```ini
ADC_CA_CERT_FILE=证书路径
ADC_TLS_SKIP_VERIFY=false
```

每个命令也都可以用 `--server`、`--token`、`--timeout` 等参数临时覆盖（参数 > .env）。

---

## 4. 常用命令

先看总览：

```
adc
├── ping        检查能否连上后端
├── dump        把后端现有配置导出成本地文件
├── lint        本地语法校验（不需要连后端）
├── validate    交给后端做一次更严的校验（等于 dry-run 同步）
├── diff        本地文件 vs 后端配置的差异
├── sync        把本地配置同步到后端
└── convert     把 OpenAPI 文档转成 ADC 配置
```

### 4.1 ping — 检查连接

```powershell
.\adc.cmd ping
# 成功输出：Connected to the "apisix" backend successfully!
```

连不上的时候先用它排查网络 / Token 问题。

### 4.2 dump — 导出当前网关配置

```powershell
.\adc.cmd dump -o adc-backup.yaml      # 全部导出
.\adc.cmd dump -o routes-only.yaml --include-resource-type route   # 只导出路由
```

> 迁移/备份网关时用 `--with-id` 可以保留资源 ID。

### 4.3 lint — 本地格式校验（不联网）

```powershell
.\adc.cmd lint -f configs/sites/intranet/ss-admin.ynfwyy.com/service.yaml          # 校验单个文件
.\adc.cmd lint -f configs/global/**/*.yaml -f configs/sites/**/*.yaml              # 校验多个
```

- 优点：快、不需要后端在线
- 局限：只查格式，不查业务逻辑（比如插件参数配置对不对）

### 4.4 validate — 后端校验（更严格）

```powershell
.\adc.cmd validate -f configs/sites/intranet/ss-admin.ynfwyy.com/service.yaml --timeout 60s
```

相当于"假装同步一次"，让 APISIX 后端帮你检查，严格程度：**sync > validate > lint**。

### 4.5 diff — 对比本地与后端

```powershell
.\adc.cmd diff -f configs/sites/intranet/ss-admin.ynfwyy.com/service.yaml --timeout 60s
```

输出结果显示将要发生的 **创建 / 更新 / 删除**，同步前必看。

### 4.6 sync — 同步（核心命令，谨慎使用）

```powershell
.\adc.cmd sync -f configs/sites/intranet/ss-admin.ynfwyy.com/service.yaml --timeout 60s
```

**⚠️ sync 是"全量对齐"**：本地文件里没有的资源，网关里会被**删除**。所以：
- 先 `diff` 确认差异符合预期，再 `sync`
- 涉及多个文件时，一次把全部都传给 `-f`，不然没传的文件对应的资源会被删掉

```powershell
# 一次同步所有配置文件
.\adc.cmd sync -f configs/global/**/*.yaml -f configs/sites/**/*.yaml --timeout 60s
```

### 4.7 convert — OpenAPI 转 ADC 配置

```powershell
.\adc.cmd convert openapi -f openapi.yaml -o converted.yaml
```

适合已经有 OpenAPI 规范的团队快速初始化。

### 4.8 通用参数

| 参数 | 说明 |
| ---- | ---- |
| `--timeout <时长>` | 请求超时，如 `30s`、`1h10m`，默认 `10s`。**网络不好时常超时，建议显式给大一点** |
| `--verbose <0|1|2>` | 日志级别，`2` 是 debug |
| `-f, --file` | 指定配置文件（多处 `-f` 可合并） |
| `--no-lint` | sync 时跳过 lint |
| `--include-resource-type` / `--exclude-resource-type` | 只处理指定类型资源，如 `route`、`service`、`global_rule`、`consumer`、`ssl` 等 |

---

## 5. 配置文件怎么写

配置文件是 **YAML**（也可以 JSON）。顶层只有 6 种资源类型：

```yaml
services:           # 服务（service）—— 最常用的容器，内含路由和上游
consumers:          # 消费者（consumer）—— 身份认证的用户
consumer_groups:    # 消费者组
global_rules:       # 全局规则 —— 对所有请求生效的插件
plugin_metadata:    # 插件的元数据
ssls:               # TLS 证书
```

### 5.1 services — 服务（核心）

一个 service 通常 = **路由(routes) + 上游(upstream)**。路由决定"请求匹配什么"，上游决定"转发给谁"。

当前仓库 `configs/sites/intranet/ss-admin.ynfwyy.com/service.yaml` 就是一个完整例子
（示意，字段与真实配置一致）：

```yaml
services:
  - name: 官网服务                    # 服务名（必填，全局唯一）
    upstream:                          # 上游：把请求转发到哪
      type: roundrobin                 # 负载均衡算法
      scheme: http                     # 协议
      pass_host: pass                  # 透传原始 Host
      hash_on: vars
      nodes:                           # 后端节点列表（数组！）
        - host: 172.32.100.11          #   节点 IP
          port: 80                     #   端口
          weight: 1                    #   权重
          priority: 0                  #   优先级
      tls:
        verify: false                  # 上游 TLS 校验关闭
      checks:                          # 健康检查
        active:
          type: http
          timeout: 5
          https_verify_certificate: false
    routes:                            # 该服务下的路由列表
      - name: 官网路由                 # 路由名（必填）
        uris:                          # 匹配的 URI（必填，支持通配符）
          - /*
        hosts:                         # 匹配的域名
          - www.ynfwyy.com
          - m.ynfwyy.com
        methods:                       # 匹配的方法
          - GET
          - POST
          - PUT
          - DELETE
          - PATCH
          - HEAD
          - OPTIONS
          - CONNECT
          - TRACE
          - PURGE
        enable_websocket: true         # 支持 WebSocket
        priority: 0                    # 路由优先级（越大越优先）
        plugins:                       # 该路由专属插件
          limit-count:                 #   限流插件
            count: 10
            time_window: 60
            rejected_code: 429
            key_type: var
            key: remote_addr
```

#### 常用字段速查

**service 常用字段**

| 字段 | 说明 | 是否必填 |
| ---- | ---- | -------- |
| `name` | 服务名，全局唯一 | ✅ |
| `description` | 描述 | |
| `labels` | 标签（`key: value` 或 `key: [v1, v2]`） | |
| `plugins` | 服务级插件，作用于该服务所有路由 | |
| `upstream` | 内联上游 | 服务与上游二选一 |
| `upstreams` | 多个上游（按版本/灰度切换） | |
| `routes` | 该服务下的路由数组 | |
| `path_prefix` / `strip_path_prefix` | 路径前缀处理 | |

**route 常用字段**

| 字段 | 说明 | 是否必填 |
| ---- | ---- | -------- |
| `name` | 路由名 | ✅ |
| `uris` | 匹配的路径数组，支持 `/foo/*` 通配 | ✅ |
| `hosts` | 匹配的域名 | |
| `methods` | 允许的 HTTP 方法 | |
| `priority` | 匹配优先级，大的先命中 | |
| `plugins` | 路由级插件 | |
| `enable_websocket` | 是否支持 WebSocket | |
| `remote_addrs` | 仅允许指定来源 IP/CIDR 访问 | |
| `vars` | 更复杂的匹配条件（基于内置变量） | |

**upstream 常用字段**

| 字段 | 说明 |
| ---- | ---- |
| `type` | `roundrobin`（轮询）、`chash`（一致性哈希）、`least_conn`、`ewma` |
| `nodes` | **数组**：`{host, port, weight, priority}`（注意不是 `host:port:` 格式） |
| `scheme` | `http` / `https` / `grpc` / `grpcs` 等 |
| `hash_on` / `key` | chash 模式下的哈希依据 |
| `timeout` | 连接/发送/读取超时 |
| `checks.active` | 主动健康检查（定时探活） |
| `checks.passive` | 被动健康检查（根据实际请求结果判断） |
| `retries` / `retry_timeout` | 失败重试 |
| `keepalive_pool` | 连接池调优 |

### 5.2 plugins — 插件

插件是一个**对象**，键是插件名，值是插件配置。位置决定作用范围：

```yaml
# 服务级（作用于该服务所有路由）
services:
  - name: my-service
    plugins:
      cors: {}                     # 开启跨域
      limit-count:                 # 限流
        count: 100
        time_window: 60
        rejected_code: 429

# 路由级（只作用于该路由），会覆盖服务级同名插件
    routes:
      - name: my-route
        uris:
          - /api
        plugins:
          key-auth:                # 密钥认证
            header: apikey
```

常用插件举例：`key-auth`（密钥认证）、`limit-count`（限流）、`limit-req`（漏桶限速）、
`cors`（跨域）、`jwt-auth`、`basic-auth`、`ip-restriction`（IP 白/黑名单）、
`proxy-rewrite`（改写上游路径/头）、`response-rewrite`（改写响应）、
`prometheus`（监控指标）、`log-rotate` / `http-logger`（日志）。

> 某个插件要不要开、参数怎么配，以 [APISIX Plugin Hub（插件总览）](https://apisix.apache.org/plugins/) 或对应插件页（如 [limit-count](https://apisix.apache.org/docs/apisix/plugins/limit-count/)）为准。
> 官方文档汇总见 [官方文档资料库.md](./官方文档资料库.md)。

### 5.3 consumers — 消费者（身份认证）

配合 `key-auth` 等认证插件使用：先建消费者和凭证，路由上开对应认证插件即可。

```yaml
consumers:
  - username: Jane                        # 用户名（必填，全局唯一）
    labels:
      organisation: ACME
    credentials:                          # 凭证数组
      - name: primary-key                 # 凭证名
        type: key-auth                    # 凭证类型（key-auth / basic-auth / jwt-auth…）
        config:
          key: c1_yN0nCWousUfiR4EzfH      # 调用方要带的 Key
```

对应路由开启：

```yaml
routes:
  - name: protected-route
    uris:
      - /secure
    plugins:
      key-auth: {}
```

调用方请求时带 `apikey: c1_yN0nCWousUfiR4EzfH` 头即可通过认证。

### 5.4 global_rules — 全局规则

对所有访问网关的请求生效，适合放**基础插件**（如 prometheus、日志、通用拦截）。
注意它是**对象不是数组**：

```yaml
global_rules:
  prometheus: {}                           # 开启 prometheus 指标采集
  server-info: {}
```

如果需要全局执行逻辑，可用 `pre-function` 插件：

```yaml
global_rules:
  pre-function:
    _meta:
      disable: false
    phase: rewrite
    functions:
      - "return function(conf, ctx) local core = require('apisix.core'); core.log.info('pre-function executed') end"
```

### 5.5 ssls — TLS 证书

```yaml
ssls:
  - snis:                                  # 证书绑定的域名
      - www.example.com
    certificates:                          # 证书数组（至少一个）
      - certificate: |
          -----BEGIN CERTIFICATE-----
          ...
          -----END CERTIFICATE-----
        key: |
          -----BEGIN PRIVATE KEY-----
          ...
          -----END PRIVATE KEY-----
    ssl_protocols:
      - TLSv1.2
      - TLSv1.3
```

### 5.6 plugin_metadata — 插件元数据

给某些插件提供全局参数（如 `kafka-logger` 的角色映射、`serverless` 全局函数）：

```yaml
plugin_metadata:
  kafka-logger:
    log_format:
      host: "$host"
      remote_addr: "$remote_addr"
```

---

## 6. 完整实战示例

### 示例 A：限流 + 密钥认证 + 灰度/负载均衡

```yaml
services:
  - name: user-service
    labels:
      deployment: production
    upstream:
      type: roundrobin
      scheme: http
      nodes:
        - host: 10.0.0.11
          port: 8080
          weight: 100
        - host: 10.0.0.12
          port: 8080
          weight: 100
      checks:
        active:
          type: http
          http_path: /health
          healthy:
            interval: 5
            successes: 2
          unhealthy:
            interval: 2
            http_failures: 3
    routes:
      - name: user-get
        uris:
          - /api/v1/user
        methods:
          - GET
        plugins:
          key-auth: {}
          limit-count:
            count: 60
            time_window: 60
            rejected_code: 429
            key_type: var
            key: remote_addr

consumers:
  - username: internal-svc
    credentials:
      - name: kv
        type: key-auth
        config:
          key: callme-maybe

global_rules:
  prometheus: {}
```

### 示例 B：一个服务多个路由、使用变量

```yaml
services:
  - name: shop-service
    upstream:
      type: chash
      hash_on: vars
      key: remote_addr
      nodes:
        - host: 10.0.0.21
          port: 9000
          weight: 1
    routes:
      - name: shop-cart
        uris:
          - /cart
        methods: [GET, POST]
      - name: shop-order
        uris:
          - /order/*
        methods: [GET, POST, PUT, DELETE]
```

> 想让两个路由都共享服务的插件、上游，写成同一个 service 下的两个 routes 即可。

---

## 7. 日常操作流程

推荐的"改配置"标准流程：

```powershell
# ① 修改或新增 YAML（写完后本地校验）
.\adc.cmd lint -f configs/global/**/*.yaml -f configs/sites/**/*.yaml

# ② 可选：后端再校验一次（更严格）
.\adc.cmd validate -f configs/global/**/*.yaml -f configs/sites/**/*.yaml --timeout 60s

# ③ 看差异，确认只有预期的 新增/修改/删除
.\adc.cmd diff -f configs/global/**/*.yaml -f configs/sites/**/*.yaml --timeout 60s

# ④ 确认无误后同步（⚠️ 会全量对齐，没在文件里的会被删）
.\adc.cmd sync -f configs/global/**/*.yaml -f configs/sites/**/*.yaml --timeout 60s
```

常用工作流：

| 场景 | 命令 |
| ---- | ---- |
| 首次接手一个网关 | `dump -o baseline.yaml` → 审阅 → 拆成 configs/ 下多个文件 |
| 改一个小配置 | 改文件 → `lint` → `diff` → `sync` |
| 新网关上线一套配置 | 写好文件 → `lint` → `sync` |
| 出问题想回滚 | `git revert` 恢复旧 YAML → `sync`（本地即真相） |
| 盘点网关现状 | `dump` 或 `diff` |

---

## 8. 变量与敏感信息

### 8.1 ADC 环境变量 `${ENV}`

配置里可以用 `${环境变量名}`，由 ADC 在运行前解析：

```yaml
services:
  - name: ai-proxy
    routes:
      - name: openai
        uris:
          - /v1/*
        plugins:
          ai-proxy:
            auth:
              header:
                Authorization: "Bearer ${OPENAI_API_KEY}"
```

运行时配合 `.env` 或系统环境变量注入，避免把密钥写死在 YAML 里。

### 8.2 数据面环境变量 `$env://`

`$env://` 由运行网关的 APISIX 节点解析（适合懒加载/免重建）。

### 8.3 APISIX 内置变量 `\${}`

路由匹配等场景可用内置变量，如 `\${remote_addr}`、`\${http_user_agent}`。

---

## 9. 常见问题

### Q1：sync 报超时 `timed out after 10000ms`

默认 `--timeout 10s` 太短。加长：`--timeout 60s`。

### Q2：sync 删资源时报 404 `Key not found`

多个资源存在依赖（如 service 删了、其内联 upstream 也随之删除），ADC 再删 upstream 就 404。
**解决：直接重新 sync 一次**，远端已处于同步中状态，本次只做剩余动作，一般即可成功。

### Q3：远程请求偶发 `connect EACCES`

网络瞬时故障。稍等重试即可（`ping` 验证）。

### Q4：`Unrecognized key: "xxx"`

字段名写错了或该字段在 ADC schema 中不存在（例如 APISIX Admin API 里的 `desc` 字段，在 ADC 里应写 `description`）。对照第 5 节字段表，或 `lint` 提示的具体位置修改。

### Q5：`nodes` 报"expected array" 

ADC 的 `nodes` 是**数组**，标准写法是：

```yaml
nodes:
  - host: 127.0.0.1
    port: 8080
    weight: 1
```

不是 `ip:port:` 的键值对写法。

### Q6：我不想让自己手动改过的资源被删

ADC 是全量对齐模型，建议：所有配置都只通过 YAML + `sync` 管理。
研发团队也可以约定给资源打标签 + `--label-selector` 做局部运维。

### Q7：怎么确认同步后真的生效？

`sync` 后再执行一次 `adc diff`，输出无差异即成功；也可以 `dump` 出来人工核对。

---

## 10. 参考链接

- ADC 官方仓库：https://github.com/api7/adc
- ADC 发布页（下载/升级）：https://github.com/api7/adc/releases
- **ADC Command Reference（当前维护版，GitHub）**：https://github.com/api7/adc/blob/main/docs/reference/cli.md
- **ADC Configuration Reference（当前维护版，GitHub）**：https://github.com/api7/adc/blob/main/docs/reference/configuration.md
- Command Reference（归档版，3.9.x）：https://docs.api7.ai/enterprise/reference/adc
- Configuration Reference（归档版，3.9.x）：https://docs.api7.ai/enterprise/reference/configuration-adc
- APISIX 插件总览（Plugin Hub）：https://apisix.apache.org/plugins/
- 官方文档收集汇总（含写法与用法）：[docs/官方文档资料库.md](./官方文档资料库.md)
- AI 写配置须知：[AGENTS.md](../AGENTS.md) ｜ 完整指引：[docs/AI配置编写指引.md](./AI配置编写指引.md)