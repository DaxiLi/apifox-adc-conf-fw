# 官方文档本地资料库索引（INDEX）

> **给 Agent 的说明**：本目录是 Apache APISIX + ADC 官方文档的**本地离线镜像**。
> 写配置（`configs/**/*.yaml`）之前，先按下面的「快速查询表」找到对应文件，再打开文件查字段/参数；
> 不要凭空猜测字段名，一切以本资料库（或线上官方文档）为准。
>
> - 抓取日期：2026-09-17 ｜ 源：ADC = api7/adc（main 分支），APISIX = apache/apisix（release/3.18，docs/en/latest）
> - 完整清单（含每个文件的源 URL 与字节数）：[MANIFEST.json](./MANIFEST.json)
> - 更新方法：`python docs/official/download_official_docs.py`（需外网）
> - 人工速查版：[docs/官方文档资料库.md](../官方文档资料库.md)

---

## 1. 快速查询表（任务 → 打开哪个文件）

### 1.1 我要"写"一个资源配置（怎么写）

| 我要写… | 先看这里（ADC 配置格式） | 再看这里（字段全表 / 概念） |
| ---- | ---- | ---- |
| `services:` 下的 service | [adc/configuration.md](./adc/configuration.md) §Schema Reference·Service | [apisix/admin-api.md](./apisix/admin-api.md) §Service ｜ [apisix/terminology/service.md](./apisix/terminology/service.md) |
| service 里的 `routes:`（route） | [adc/configuration.md](./adc/configuration.md) §Schema Reference·Route | [apisix/admin-api.md](./apisix/admin-api.md) §Route ｜ [apisix/terminology/route.md](./apisix/terminology/route.md) |
| `upstream:`（上游） | [adc/configuration.md](./adc/configuration.md) §Schema Reference·Upstream | [apisix/admin-api.md](./apisix/admin-api.md) §Upstream ｜ [apisix/terminology/upstream.md](./apisix/terminology/upstream.md) |
| `consumers:` + `credentials:` | [adc/configuration.md](./adc/configuration.md) §Schema Reference·Consumer/Credential | [apisix/admin-api.md](./apisix/admin-api.md) §Consumer ｜ [apisix/terminology/consumer.md](./apisix/terminology/consumer.md)、[credential.md](./apisix/terminology/credential.md) |
| `ssls:`（TLS 证书） | [adc/configuration.md](./adc/configuration.md) §Schema Reference | [apisix/certificate.md](./apisix/certificate.md) ｜ [apisix/admin-api.md](./apisix/admin-api.md) §SSL |
| `global_rules:`（全局插件） | [adc/configuration.md](./adc/configuration.md) §Global Rules | [apisix/terminology/global-rule.md](./apisix/terminology/global-rule.md) |
| `plugin_metadata:` | [adc/configuration.md](./adc/configuration.md) §Plugin Metadata | [apisix/terminology/plugin-metadata.md](./apisix/terminology/plugin-metadata.md) |
| `consumer_groups:` | [adc/configuration.md](./adc/configuration.md)（schema.json 有定义） | [apisix/terminology/consumer-group.md](./apisix/terminology/consumer-group.md) |
| 健康检查 `checks:` | [adc/configuration.md](./adc/configuration.md)（upstream 字段） | [apisix/terminology/upstream.md](./apisix/terminology/upstream.md) |
| 字段能不能用、必填吗、格式对不 | [adc/schema.json](./adc/schema.json)（`lint` 的校验依据，最权威） | — |

### 1.2 我要"配"一个插件（插件参数）

打开 [apisix/plugins/](./apisix/plugins/) 下对应插件文件；没收录的插件先查线上 [Plugin Hub](https://apisix.apache.org/plugins/)。

| 插件 | 本地文档 |
| ---- | ---- |
| `key-auth` 密钥认证 | [apisix/plugins/key-auth.md](./apisix/plugins/key-auth.md) |
| `basic-auth` | [apisix/plugins/basic-auth.md](./apisix/plugins/basic-auth.md) |
| `jwt-auth` | [apisix/plugins/jwt-auth.md](./apisix/plugins/jwt-auth.md) |
| `hmac-auth` | [apisix/plugins/hmac-auth.md](./apisix/plugins/hmac-auth.md) |
| `limit-count` 固定窗口限流 | [apisix/plugins/limit-count.md](./apisix/plugins/limit-count.md) |
| `limit-req` 漏桶限速 | [apisix/plugins/limit-req.md](./apisix/plugins/limit-req.md) |
| `limit-conn` 并发限制 | [apisix/plugins/limit-conn.md](./apisix/plugins/limit-conn.md) |
| `cors` 跨域 | [apisix/plugins/cors.md](./apisix/plugins/cors.md) |
| `gzip` 压缩 | [apisix/plugins/gzip.md](./apisix/plugins/gzip.md) |
| `ip-restriction` IP 白/黑名单 | [apisix/plugins/ip-restriction.md](./apisix/plugins/ip-restriction.md) |
| `consumer-restriction` 消费方限制 | [apisix/plugins/consumer-restriction.md](./apisix/plugins/consumer-restriction.md) |
| `proxy-rewrite` 改写上游 | [apisix/plugins/proxy-rewrite.md](./apisix/plugins/proxy-rewrite.md) |
| `response-rewrite` 改写响应 | [apisix/plugins/response-rewrite.md](./apisix/plugins/response-rewrite.md) |
| `traffic-split` 灰度/分流 | [apisix/plugins/traffic-split.md](./apisix/plugins/traffic-split.md) |
| `proxy-cache` 缓存 | [apisix/plugins/proxy-cache.md](./apisix/plugins/proxy-cache.md) |
| `prometheus` 指标 | [apisix/plugins/prometheus.md](./apisix/plugins/prometheus.md) |
| `server-info` | [apisix/plugins/server-info.md](./apisix/plugins/server-info.md) |
| `http-logger` / `log-rotate` 日志 | [apisix/plugins/http-logger.md](./apisix/plugins/http-logger.md)、[apisix/plugins/log-rotate.md](./apisix/plugins/log-rotate.md) |
| `ai-proxy` AI 网关 | [apisix/plugins/ai-proxy.md](./apisix/plugins/ai-proxy.md) |
| 插件概念 / 插件元数据 | [apisix/terminology/plugin.md](./apisix/terminology/plugin.md)、[plugin-metadata.md](./apisix/terminology/plugin-metadata.md) |

### 1.3 变量语法（配置里的 `$env://` `${ENV}` `\${}`）

→ [adc/configuration.md](./adc/configuration.md) §Variables（含三套语法各自的最低 ADC 版本与转义规则）
→ 内置变量含义：[apisix/apisix-variable.md](./apisix/apisix-variable.md)

### 1.4 我要"用"ADC 命令（怎么执行）

| 我要… | 打开 | 关键章节 |
| ---- | ---- | ---- |
| 看全部命令/参数 | [adc/cli.md](./adc/cli.md) | Commands |
| 连后端（`.env`/环境变量/flag 优先级） | [adc/cli.md](./adc/cli.md) | Configuring ADC / Common Backend Options |
| 标准改配置流程 | [adc/workflow.md](./adc/workflow.md) | 全篇（含 CI 顺序 lint→validate→diff→sync） |
| 接管 UI/手工建的存量资源 | [adc/resource-ids.md](./adc/resource-ids.md) | 全篇（`dump --with-id`） |
| 多团队共用一台网关不互相删 | [adc/label-selector.md](./adc/label-selector.md) | 全篇 |
| OpenAPI 转 ADC | [adc/openapi-converter.md](./adc/openapi-converter.md) | 全篇（`x-adc-*` 扩展表） |
| apisix 后端差异（与 api7ee 的区别） | [adc/backend-apisix.md](./adc/backend-apisix.md) | 全篇 |

### 1.5 网关侧配置（APISIX 服务器上的 `config.yaml`）

| 我要… | 打开 |
| ---- | ---- |
| `config.yaml` 全量字段（含 `deployment.admin.admin_key` / `allow_admin`） | [apisix/conf/config.yaml.example](./apisix/conf/config.yaml.example)（带注释）＋ [apisix/conf/config.yaml](./apisix/conf/config.yaml) |
| Admin API 端口/密钥配置段 | [apisix/admin-api.md](./apisix/admin-api.md) §Configuration |
| 部署模式（traditional/decoupled/standalone） | [apisix/deployment-modes.md](./apisix/deployment-modes.md) |
| 按环境切配置（profile） | [apisix/profile.md](./apisix/profile.md) |
| 自定义 Nginx 配置 | [apisix/customize-nginx-configuration.md](./apisix/customize-nginx-configuration.md) |

---

## 2. 目录结构总览

```
docs/official/
├── INDEX.md                          ← 本索引（先看这个）
├── MANIFEST.json                     ← 机器可读清单（url/local/size/status）
├── download_official_docs.py         ← 重拉/更新脚本（python 执行，需外网）
├── adc/                              ← ADC 官方文档（api7/adc，main）
│   ├── README.md                     ADC 项目主页/安装
│   ├── docs-README.md                ADC 文档总入口
│   ├── configuration.md              ★ 配置文件格式（怎么写）核心
│   ├── cli.md                        ★ 命令参考（怎么用）核心
│   ├── openapi-converter.md          OpenAPI 转 ADC
│   ├── workflow.md                   标准工作流（含 CI）
│   ├── resource-ids.md               资源 ID / 存量接管
│   ├── label-selector.md             标签分区管理
│   ├── backend-apisix.md             APISIX 后端说明
│   └── schema.json                   ★ lint 校验用的全量 JSON Schema
└── apisix/                           ← Apache APISIX 官方文档（release/3.18）
    ├── admin-api.md                  ★ 各资源字段全表（Route/Service/Upstream/Consumer/SSL…）
    ├── getting-started.md            快速上手
    ├── configure-routes.md           配置路由教程
    ├── load-balancing.md             负载均衡教程
    ├── key-authentication.md         key-auth 教程
    ├── rate-limiting.md              限流教程
    ├── deployment-modes.md           部署模式（含 standalone）
    ├── profile.md                    按环境配置
    ├── customize-nginx-configuration.md
    ├── certificate.md                SSL 证书
    ├── apisix-variable.md            内置变量
    ├── FAQ.md                        常见问题
    ├── conf/
    │   ├── config.yaml               网关默认配置
    │   └── config.yaml.example       ★ 全字段带注释示例
    ├── terminology/                  资源概念（route/service/upstream/consumer/…）
    └── plugins/                      插件文档（19 个常用插件，见上表）
```

---

## 3. 按关键词检索（grep 用）

本资料库是纯文本，直接用 grep/搜索即可。常用检索词对应文件示例：

| 想搜 | 大概率命中的文件 |
| ---- | ---- |
| `nodes` / `host` / `port` / `weight` / `priority` | adc/configuration.md、adc/schema.json、apisix/admin-api.md |
| `hash_on` / `chash` / `roundrobin` / `least_conn` / `ewma` | adc/configuration.md、apisix/terminology/upstream.md、apisix/admin-api.md |
| `checks` / `active` / `passive` / 健康检查 | adc/configuration.md、apisix/terminology/upstream.md |
| `uris` / `hosts` / `methods` / `vars` / `priority`（route 匹配） | apisix/admin-api.md §Route、apisix/terminology/route.md |
| `enable_websocket` | apisix/admin-api.md §Route |
| `key_type` / `key` / `remote_addr` / `time_window` / `rejected_code` | apisix/plugins/limit-count.md、limit-req.md |
| `_meta` / `disable` | apisix/terminology/plugin.md、adc/configuration.md |
| `prefer_name` | apisix/plugins/prometheus.md、adc/configuration.md |
| `$env://` / `${ENV}` / `\${` 转义 | adc/configuration.md §Variables |
| `admin_key` / `allow_admin` / `X-API-KEY` | apisix/admin-api.md、apisix/conf/config.yaml.example |
| `--with-id` / `--label-selector` / `--include-resource-type` | adc/cli.md、adc/resource-ids.md、adc/label-selector.md |
| `x-adc-` 扩展 | adc/openapi-converter.md |

---

## 4. 元数据与更新

- **来源**（权威、只读镜像）：
  - ADC：<https://github.com/api7/adc>（main 分支 `docs/` 与根目录 `schema.json`）
  - APISIX：<https://github.com/apache/apisix>（`release/3.18` 分支 `docs/en/latest/` 与 `conf/`）
- **版本对应**：ADC 文档随 main 演进；APISIX 文档对应 3.18.0（官网最新稳定版，右上角可切 3.16/3.15…）。
  本仓库本地 `adc` 为 v0.30.3，其 `--help` 仍指向已归档的 <https://docs.api7.ai/enterprise/reference/adc>，内容与 `adc/` 下实时文档一致。
- **更新**：`python docs/official/download_official_docs.py`（会用 urllib 重新拉取全部文件并重写 MANIFEST.json；需要外网）。
- **注意**：`docs.api7.ai/enterprise/*` 归档版文档所在仓库（api7/docs）当前不可公开访问，故未收录；如需可访问官方原版，用 GitHub 链接（见 MANIFEST.json）。
