# api-cluster — APISIX 配置仓库（GitOps / ADC）

用 **ADC（API Declarative CLI, v0.30.3）** 以声明式方式管理 **Apache APISIX** 网关。
`configs/` 下的 YAML 是**唯一真相来源**；`sync` 会把网关对账成与文件完全一致。

> 🤖 AI 写配置前必读：`AGENTS.md` ＋ `docs/AI配置编写指引.md`

## 快速开始

```bash
# ① 安装 ADC 工具（已安装同版本会自动跳过）
#    Windows:  .\scripts\install-adc.ps1
#    Linux/macOS:  ./scripts/install-adc.sh

# ② 配置连接（复制 .env.example 为 .env 并填写；.env 勿提交）
cp .env.example .env

# ③ 校验 → 差异 → （人工确认后）同步
#    Windows:            .\scripts\lint.ps1 → .\scripts\diff.ps1 → .\scripts\sync.ps1
#    Linux/macOS (bash): ./scripts/lint.sh  → ./scripts/diff.sh  → ./scripts/sync.sh
#    （.ps1 需 pwsh，三平台通用；.sh 需 bash）
```

网关入口：Windows 用 `adc.cmd`，Linux/macOS 用 `./adc`（等价，都指向 `.bin/adc/` 下的二进制）。
安装工具：Windows `.\scripts\install-adc.ps1`；Linux/macOS `./scripts/install-adc.sh`。

## 目录结构

```
configs/
├── _templates/     # 站点类型模板（www/api/ws/static/admin/ssl；在 sync 作用域外，只复制）
├── global/         # 全局规则 / 插件元数据 / 公共消费者 / 通配证书
└── sites/<code>/   # 每站一个目录：service.yaml（+ ssl.yaml / consumers.yaml / README.md）
docs/               # 设计、AI 指引、轮换手册、官方文档本地镜像、审视报告
scripts/            # lint / validate / diff / sync（.ps1 通用 + .sh 原生）/ install-adc（跨平台）
```

## 文档导航

| 文档 | 内容 |
| ---- | ---- |
| `AGENTS.md` | AI 写配置自动读取的须知（红线 + 流程） |
| `docs/AI配置编写指引.md` | AI 完整操作手册（查询/规范/流程/限制/自检清单） |
| `docs/配置仓库结构设计.md` | 目录与命名设计、插件/证书/可读性规范 |
| `docs/official/INDEX.md` | 官方文档本地镜像（离线查询） |
| `docs/证书轮换操作手册.md` | 证书定期更换流程 |
| `docs/项目审视报告.md` | 审视结论与行动清单 |

## 红线（违反会报错或误删网关）

1. 路径用**正斜杠**；严禁 `configs/**/*.yaml`（会吞模板；脚本已有守卫拦截）。
2. **不改资源名**（ID = sha1(name)，改名 = 删旧建新）；轮换证书保持 `snis` 不变。
3. **sync 永远全量 + 人工确认**；`diff` 出现无关 delete 立即停下。
4. 不手动改 Admin API / Dashboard；一切变更走 YAML。
   ⚠️ `global/` 下的**空资源文件 = 所有权声明**：手工创建的消费者/证书/全局规则会被下次 sync 删除。
5. `.env` 含 Token，永不提交；网关基线备份在 `backups/`（gitignore，可能含密钥）。

完整规范见 `docs/AI配置编写指引.md` 与 `docs/配置仓库结构设计.md`。
