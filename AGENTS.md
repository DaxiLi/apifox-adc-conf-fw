# AGENTS.md — AI 写本仓库配置前必读

本仓库用 **ADC（API Declarative CLI, v0.30.3）** 以声明式方式管理 **Apache APISIX** 网关。
`configs/**` 下的 YAML 是**唯一真相来源**；`adc sync` 会把网关对账成与文件完全一致。

## 你的职责

- 写/改 `configs/` 下的 YAML：service（routes/upstream）、consumer、ssl、global_rules、plugin_metadata。
- **不碰**：`.env`（含 Token）、`adc.cmd`、`.bin/`、`scripts/`（封装脚本，直接用）。
- 字段一律以本地官方文档镜像 `docs/official/` 为准，**不要凭记忆猜字段**。

## 必读（按顺序）

1. `docs/official/INDEX.md` —— 任务→文件查询表
2. `docs/AI配置编写指引.md` —— 完整流程/规范/限制/自检清单
3. `docs/配置仓库结构设计.md` —— 目录与命名设计
4. 新写配置：复制 `configs/_templates/` 对应模板（只复制、不修改模板）

## 硬性限制（违反会报错或误删网关）

1. 路径用**正斜杠**（`configs/global/**/*.yaml`）；反斜杠会让 adc 崩溃。
2. **严禁** `configs/**/*.yaml` 全量 glob（会吞掉 `_templates/` 占位符配置）。
3. **不改资源名**（ID = sha1(name)，改名 = 删旧建新）；轮换证书时**保持 `snis` 不变**。
4. 不手动改 Admin API / Dashboard；一切变更走 YAML。
5. 缺信息（域名/后端地址/团队/密钥）就**问用户**，禁止编造占位值同步。
6. **默认不执行 sync**（写网关）：最多做到 `diff`；sync 由人工确认。

## 标准流程

写/改 YAML → `.\scripts\lint.ps1`（必须 0 错；Linux/macOS 用 `./scripts/lint.sh`，有 pwsh 则 ps1 通用）→ `.\scripts\validate.ps1`（或 `./scripts/validate.sh`）→ `.\scripts\diff.ps1`（或 `./scripts/diff.sh`）
（diff 必须只含预期 create/update；出现无关 delete 立即停下）→ 人工 `.\scripts\sync.ps1`（或 `./scripts/sync.sh`）

## 可读性/可维护性（文件最终是人读、人审、人改）

- 字段顺序固定：`name → description → labels → upstream → routes`；route 内 `name → uris → hosts → methods → priority → plugins`；插件键按字母序。
- 每个文件有**头部注释块**（站点身份/类型/负责人/后端）；魔法值（限流阈值、超时、priority）旁注释业务含义；只注释"为什么"，不注释显而易见的。
- 2 空格缩进；短数组内联、长数组列表；含特殊字符的字符串必须引号；PEM 用 `|` 块状。
- **最小 diff**：一次只改一件事，不顺手重排/改名/美化无关部分；删除即删除，不留注释掉的旧配置。
- 站点 `README.md` 维护变更记录（日期/内容/原因）；`owner`/`contact` 标签必填。
- 写完以"人类审查者"视角自查：不看文档能否读懂每个字段？（完整规范见 `docs/AI配置编写指引.md` 4.6 节）

## 关键事实速记

- 上游 `nodes` 是**数组** `[{host, port, weight, priority}]`；描述字段用 `description`（不是 `desc`）。
- labels 必填 4 个：`site` / `site_type` / `env` / `owner`。
- 插件合并优先级：`Consumer > Consumer Group > Route > Plugin Config > Service`；global_rules 与本地同名插件**都执行**。
- ADC 声明式 YAML **不支持 `plugin_config`**；跨站复用插件组合 = 复制 / service 级 / consumer_groups。
- 证书轮换、密钥方案、常见坑：见 `docs/证书轮换操作手册.md` 与 `docs/AI配置编写指引.md` 第 8 节。
