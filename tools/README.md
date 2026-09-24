# tools/ — 配置检查与站点清单工具

> 独立于 `scripts/`（那是 adc 封装脚本，本目录是额外的质量工具，均为 Python 实现，
> 依赖本机 `python3` + `PyYAML`；Windows 下 `python` 即可）。

## 1. 配置检查工具 `check-config.py`

**为什么需要**：`scripts/sync.ps1` 只做 lint → diff → sync，`adc lint` 只校验字段 schema，
**查不出**语义错误（重名/占位符/内网强制项/vars 类型/未定义变量），也**不跑后端校验**——
这就是"lint 通过但 sync 推送失败"的根源。本工具把这些提前拦在提交前。

```bash
python tools/check-config.py                 # 静态语义检查（不联网）
python tools/check-config.py --backend       # 追加 adc validate（后端真实校验，需网关可达）
python tools/check-config.py --lint          # 先跑 adc lint 再静态检查
python tools/check-config.py --skip-env      # 跳过 ${ENV} 存在性检查（CI 等无 secrets 环境）
python tools/check-config.py --json          # JSON 输出（CI 用）
```

退出码：`0` 通过｜`1` 有错误｜`2` 工具自身问题。

### 检查项清单（rule id）

| rule | 严重级 | 含义 |
| ---- | ---- | ---- |
| `e1` | ERROR | 资源名全局唯一（service/consumer/route/credential/snis）——重名 = 资源 ID 冲突/静默覆盖 |
| `e2` | ERROR | 真实配置出现 `<...>` 模板占位符（仅 `_templates/` 允许） |
| `e3` | ERROR | 站点必须放 `configs/sites/<zone>/` 且 `labels.zone` 与目录一致——内网/外网/公网禁止混放 |
| `e4` | ERROR | `labels.zone` 取值非法（intranet/extranet/public/shared） |
| `e5` | ERROR | 内网路由必须走 PP：`server_port∈[9181,9182]` 或 `proxy_protocol_server_port` |
| `e6` | ERROR | 内网路由必须带 `real-ip`（source=proxy_protocol_addr） |
| `e7` | ERROR | 内网路由必须带 `ip-restriction` 白名单（不允许留空） |
| `e8` | ERROR | 外网/公网路由禁止引用内网 PP 端口 9181/9182（隔离） |
| `e9` | ERROR | `server_port` 等 vars 值必须为字符串——nginx 变量是字符串，`in` 严格比较，`[9181,9182]` 永不匹配 |
| `e10` | ERROR | 缺必填标签（site/zone/site_type/env/owner） |
| `e11` | ERROR | `${ENV}` 引用在本机（os.environ + .env）未定义 |
| `e12` | ERROR | YAML 解析失败 |
| `w1` | WARN | 缺建议标签 `contact` |
| `w2` | WARN | site_type/env 不在约定枚举 |
| `w3` | WARN | 内网 real-ip.source 非 proxy_protocol_addr；或外网/公网带了 real-ip（不走 PP） |
| `w4` | WARN | 端口与所在网络区约定不符（内网 9181/9182；外网/公网 80/443） |
| `w5` | WARN | `$env://` 为数据面变量本地无法校验；或 .env 读取失败 |

### 豁免（例外）机制

某些资源确有理由不满足个别检查（如示例站点无真实 IP 白名单），可在该资源 `labels` 加
`x-check-skip`，值为逗号分隔的 rule id 或 `all`：

```yaml
labels:
  x-check-skip: "intranet-ip,intranet-realip"   # 理由写注释
```

> 建议尽量少用；每次豁免都应写清"为什么"。

### 接入建议（可选）

`sync` 前加一道门：`python tools/check-config.py --backend`（会顺带 `adc validate`，
把后端拒绝提前拦下）。如希望把该检查自动并入 `sync`，需要改 `scripts/sync.ps1`
（当前按仓库约定 `scripts/` 不手改，由人工决定是否接线）。

## 2. 配置总览生成工具 `gen-inventory.py`

把分散在 `configs/**` 的**当前生效配置**汇总成「一份文件看清全部」的总览，并支持搜索查看，
不必逐一翻配置文件。

```bash
python tools/gen-inventory.py                  # 生成 configs/sites/INVENTORY.md（完整总览）
python tools/gen-inventory.py --html           # 额外生成 INVENTORY.html 可搜索面板（浏览器打开，
                                               #   搜索框即时过滤，点击行展开该 service 完整配置）
python tools/gen-inventory.py --live           # 用 adc dump 比对网关，标注「已生效/待同步」（需网关可达）
python tools/gen-inventory.py --query <关键词> # 终端搜索并打印命中的完整配置片段（域名/service/后端/负责人/插件…）
python tools/gen-inventory.py --json           # 结构化 JSON 输出
```

- `INVENTORY.md`：**一、总览**（站点/类型/认证分布 + 速览表）；**二、站点明细**（每站完整配置：
  service、labels、upstream、每条 route 的 hosts/uris/methods/vars/plugins、consumers、ssls）；
  **三、全局资源**（global_rules、plugin_metadata、全局消费者/证书）；**四、分区规则速查**。
  可提交进仓库，站点变更后重新生成即可（**勿手改**）。
- `INVENTORY.html`：自包含单文件、可搜索的交互面板；生成时间戳会变动，已加入 `.gitignore`
  仅作本地查看（重新生成即可）。
- `--live` 的「生效状态」= 配置状态（本地 vs 网关 adc dump），不是健康检查等运行时指标。
- 站点新增/变更后：`python tools/gen-inventory.py --html` 重新生成。

## 3. 运行前提

- `python3`（Windows 用 `python`）+ `PyYAML`（`pip install pyyaml`）。
- `--backend`/`--lint`/`--live` 需要仓库根目录的 adc 可执行（默认 `.bin/adc/adc.exe`，可用 `--adc` 指定）。
- `--backend`/`--live` 需要网关 Admin API 可达（同 `scripts/validate.ps1`）。
