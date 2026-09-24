# 站点：www.ynfwyy.com（外网站点：key-auth 认证反代）

| 项 | 值 |
| ---- | ---- |
| 访问域名 | `https://www.ynfwyy.com` / `http://www.ynfwyy.com` |
| 后端 | `http://172.32.100.11:80` |
| 网络区 | extranet（外网，`configs/sites/extranet/`） |
| 站点类型 | www（官网） |
| 负责人 | test |
| 认证 | key-auth，认证头 `token`，密钥 `aaaabbbb`（consumer：`ynfwyy-www`，见 consumers.yaml） |
| 匹配规则 | route vars：`server_port in ["80", "443"]`（APISIX 标准 HTTP/HTTPS 监听口） |

## 说明

- 由 `testport`（内网示例）复制改造：域名改为 www.ynfwyy.com，端口匹配从 PROXY 目标端口 10001 改为 APISIX 标准监听口 80/443。
- **外网不走 PROXY protocol**：请求直达 APISIX 80/443；只有内网才走 PP（9181/9182）。
  内网入口（9181/9182）的请求不满足本路由的 `server_port` 条件，不会命中（端口隔离）。
- 调用方式：请求头带 `token: aaaabbbb`，否则返回 401。
- 证书：Let's Encrypt `*.ynfwyy.com` 通配（`configs/global/ssls/wildcard.yaml`，
  `snis: ["*.ynfwyy.com"]` 覆盖本站 TLS）。

## 变更记录

| 日期 | 内容 | 原因 |
| ---- | ---- | ---- |
| 2026-09-21 | 新增站点：service.yaml（key-auth + 80/443 匹配）+ consumers.yaml + 本 README | 由 testport 复制到外网区，域名 www.ynfwyy.com，指定消费者 key-auth 认证（头 token，值 aaaabbbb） |
| 2026-09-21 | 匹配修正：`proxy_protocol_server_port` → `server_port in ["80","443"]` | 外网不走 PROXY protocol，直连 APISIX 80/443 标准监听口；只有内网才走 PP（9181/9182） |
