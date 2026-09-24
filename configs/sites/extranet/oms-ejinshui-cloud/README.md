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
| 匹配规则 | route vars：`server_port in ["80", "443"]`（APISIX 标准 HTTP/HTTPS 监听口） |

## 说明

- 站点代码 `oms-ejinshui-cloud` 取自真实主域名 `www.oms.ejinshui-cloud.com`（去 `www.`、小写连字符）；
  访问域名 `www-oms-ejinshui--cloud-com.ynfwyy.com` 是 `www.oms.ejinshui-cloud.com` 的点转横线形式（一级子域，受 `*.ynfwyy.com` 通配证书覆盖）。
- **外网不走 PROXY protocol**：请求直达 APISIX 80/443；只有内网才走 PP（9181/9182）。
  内网入口（9181/9182）的请求不满足本路由的 `server_port` 条件，不会命中（端口隔离）。
- `pass_host: node`：Host 透传为 `www.oms.ejinshui-cloud.com`——后端为公网虚拟主机站点，
  必须按自身域名匹配 vhost，否则返回默认站点/404。
- IP 白名单仅放行 `172.32.5.23`：外网直连（无 PROXY），ip-restriction 按 `remote_addr`（客户端 IP）判定。
- 证书：Let's Encrypt `*.ynfwyy.com` 通配（`configs/global/ssls/wildcard.yaml`，
  `snis: ["*.ynfwyy.com"]`）覆盖本访问域名 TLS，本站点无需单独 ssl.yaml。

## 变更记录

| 日期 | 内容 | 原因 |
| ---- | ---- | ---- |
| 2026-09-24 | 新增站点：service.yaml（https 反代 + 80/443 匹配 + IP 白名单 172.32.5.23）+ 本 README | HRP 需经外网反代访问数电发票管理系统下载电子发票 |
