# configs/ 目录规范速查

本目录是网关配置的**唯一真相来源**（GitOps，ADC 声明式管理）。完整设计见
[docs/配置仓库结构设计.md](../docs/配置仓库结构设计.md)，字段/插件查
[docs/official/INDEX.md](../docs/official/INDEX.md)。

> 🤖 **AI 写配置前必读**：[AGENTS.md](../AGENTS.md)（仓库根，AI 工具自动读取）＋
> [docs/AI配置编写指引.md](../docs/AI配置编写指引.md)（流程/规范/限制/自检清单）。

> 📖 **人读人审**：配置文件最终由人阅读、审查、手动修改。书写约定（字段顺序、注释规范、
> 最小 diff、魔法值注释）见设计文档 5.3 节；`_templates/` 是范本，站点文件应与模板同构。

## 目录结构

```
configs/
├── _templates/          # 站点类型模板（脚手架；在 sync 作用域【外】，仅复制用）
├── global/              # 全局共享资源（改动影响全网关，需评审）
│   ├── global-rules.yaml
│   ├── plugin-metadata.yaml
│   ├── consumers/       # 公共消费者（internal.yaml / partner.yaml）
│   └── ssls/            # 跨站通配证书（wildcard.yaml）
└── sites/               # 按站点组织（每站一个目录）
    └── <site-code>/     # service.yaml（必选）+ ssl.yaml + consumers.yaml + README.md
```

## 新增一个站点（标准流程）

```powershell
# ① 复制对应类型模板，替换 <...> 占位符（模板在 configs/_templates/）
Copy-Item configs\_templates\api.yaml configs\sites\<site-code>\service.yaml
#    命名：site-code = 主域名去 www；service.name = <site-code>-<用途>；打全 labels

# ② 本地校验 → ③ 后端校验 → ④ 看差异 → ⑤ 确认后全量同步
.\scripts\lint.ps1
.\scripts\validate.ps1
.\scripts\diff.ps1
.\scripts\sync.ps1        # 内部会再 lint→diff→输入 YES 确认后 sync
```

## 安全红线（违反会误删网关配置）

1. **sync 永远全量**（`configs/global/**` + `configs/sites/**`）。
   **严禁 `configs/**/*.yaml`**——模板目录 `configs/_templates/` 必须在作用域外。
2. **禁手工改 Admin API / Dashboard**——下次 sync 会被抹掉；一切变更走 YAML。
3. **不要随意改资源名**（ADC 按名字生成 ID，改名 = 删旧建新）；确需改名先 `adc dump --with-id`。
4. **`global_rules` / `plugin_metadata` 改动 = 影响全网关**，需变更评审。
5. 上线前必须 `diff`，看到**无关的 delete 一律停下排查**。
6. `.env` 含 Token，永不提交；密钥用 `${ENV}` 注入。

## 标签规范（每个 service/consumer/ssl 必填）

```yaml
labels:
  site: <site-code>      # 站点代码（必填）
  site_type: www         # www / api / ws / static / admin / partner / internal
  env: prod              # prod / staging / dev
  owner: <team>          # 负责团队（必填，多团队分区依据）
  contact: <邮箱>        # 责任人（建议）
```

## 证书（SSL）放哪

| 场景 | 文件 |
| ---- | ---- |
| 站点独有证书 | `sites/<site-code>/ssl.yaml` |
| 通配证书（`*.example.com`） | `global/ssls/wildcard.yaml` |
| 多站共用多 SAN 证书 | `global/ssls/shared-<名称>.yaml`（只定义一次） |

- 模板：`_templates/ssl.yaml`（内联 / `$env://` / `$secret://` 三种写法）
- 轮换：**保持 `snis` 不变** → 原地更新不中断；流程见 `docs/证书轮换操作手册.md`
- 证书 ID = `sha1(snis)`，同一组 snis 只允许出现一次

## 插件与路由颗粒度（站点差异怎么表达）

- 插件挂哪层决定作用范围：`global_rules`（全网关；与本地同名插件**都执行**，不是覆盖）→ service（全站）→ route（该路由，覆盖 service）→ consumer（按调用方）。
- 合并优先级（官方）：`Consumer > Consumer Group > Route > Plugin Config > Service`。
- 颗粒度自定：差异按路径/方法分 → 拆多条 route 各挂插件；全站一致 → 一条 `/*` + service 级插件。
- 精确匹配 > 通配匹配（自动）；同 uri 多条路由靠 `priority` 区分。
- ⚠️ ADC 声明式 YAML **不支持 `plugin_config`**；跨站复用插件组合 = 复制到各站 / service 级 / consumer_groups。
- 详见 `docs/配置仓库结构设计.md` 5.2 节。
