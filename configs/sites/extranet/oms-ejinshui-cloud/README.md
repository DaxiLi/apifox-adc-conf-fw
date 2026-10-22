# 站点：oms-ejinshui-cloud（数电发票管理系统反代，供 HRP 下载电子发票）

| 项 | 值 |
| ---- | ---- |
| 访问域名 | `https://www-oms-ejinshui--cloud-com.ynfwyy.com` / `http://www-oms-ejinshui--cloud-com.ynfwyy.com` |
| 后端 | `https://www.oms.ejinshui-cloud.com:443`（数电发票管理系统） |
| 网络区 | extranet（外网，`configs/sites/extranet/`） |
| 站点类型 | partner（第三方厂家系统反代） |
| 负责人 | 陈曦 |
| 用途 | HRP 系统从数电发票管理系统下载电子发票 |
| IP 白名单 | `172.32.5.23`（ip-restriction，其余来源 403） |
| 转发路径 | 仅 `/fp/statics/*`（前端静态资源）、`/prod-api/*`（后端接口），其余路径不转发 |
| 匹配规则 | route vars：`server_port in ["18080", "19443"]`（APISIX 外网专属 HTTP/HTTPS 监听口） |

## 说明

- 站点代码 `oms-ejinshui-cloud` 取自真实主域名 `www.oms.ejinshui-cloud.com`（去 `www.`、小写连字符）；
  访问域名 `www-oms-ejinshui--cloud-com.ynfwyy.com` 是 `www.oms.ejinshui-cloud.com` 的点转横线形式（一级子域，受 `*.ynfwyy.com` 通配证书覆盖）。
- **外网不走 PROXY protocol**：请求经前置 LB（DNAT，保留源 IP）直达 APISIX 外网专属
  监听口 18080/19443；只有内网才走 PP（9181/9182）。内网入口（9181/9182）的请求
  不满足本路由的 `server_port` 条件，不会命中（端口隔离）。
- `pass_host: node`：Host 透传为 `www.oms.ejinshui-cloud.com`——后端为公网虚拟主机站点，
  必须按自身域名匹配 vhost，否则返回默认站点/404。
- IP 白名单仅放行 `172.32.5.23`：前置 LB 为 DNAT（保留源 IP），ip-restriction 按 `remote_addr`（客户端 IP）判定，白名单不受影响。
- **转发路径限制**：route `uris` 仅匹配 `/fp/statics/*` 与 `/prod-api/*`（前缀匹配，`*` 结尾）；
  其余路径（如 `/`、`/login` 等）一律 404，不转发到后端。
- 证书：Let's Encrypt `*.ynfwyy.com` 通配（`configs/global/ssls/wildcard.yaml`，
  `snis: ["*.ynfwyy.com"]`）覆盖本访问域名 TLS，本站点无需单独 ssl.yaml。

## 变更记录

| 日期 | 内容 | 原因 |
| ---- | ---- | ---- |
| 2026-09-24 | 新增站点：service.yaml（https 反代 + 80/443 匹配 + IP 白名单 172.32.5.23）+ 本 README | HRP 需经外网反代访问数电发票管理系统下载电子发票 |
| 2026-09-24 | 转发限制：route uris 从 `/*` 收窄为 `/fp/statics/*` + `/prod-api/*`，路由名定为 `oms-ejinshui-cloud-fp-api` | 仅转发前端静态资源与后端接口，减少暴露面 |
| 2026-10-16 | 端口迁移：route vars 由 `["80","443"]` 迁至 `["18080","19443"]`（外网专属监听口，前置 LB 为 DNAT） | 新约束：外网固定 18080/19443、互联网 80/443，三区端口彻底隔离 |
