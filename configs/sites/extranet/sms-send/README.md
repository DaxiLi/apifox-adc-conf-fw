# 站点：sms-send（短信发送服务反代，公开访问）

| 项 | 值 |
| ---- | ---- |
| 访问域名 | `https://sms-send.ext.ynfwyy.com` / `http://sms-send.ext.ynfwyy.com` |
| 后端 | `http://172.32.100.49:18888`（短信发送服务） |
| 网络区 | extranet（外网，`configs/sites/extranet/`） |
| 站点类型 | api（对外接口） |
| 负责人 | 袁杰 |
| IP 限制 | 无（公开访问，不限制 IP） |
| 匹配规则 | route vars：`server_port in ["18080", "19443"]`（APISIX 外网专属 HTTP/HTTPS 监听口） |

## 说明

- 站点代码 `sms-send` 取自访问域名 `sms-send.ext.ynfwyy.com`（受 `*.ext.ynfwyy.com` 通配证书覆盖，
  见 `configs/global/ssls/wildcard-ext.yaml`）。
- **外网不走 PROXY protocol**：请求经前置 LB（DNAT，保留源 IP）直达 APISIX 外网专属监听口 18080/19443；只有内网才走 PP（9181/9182）。
- 后端为内网 IP（`172.32.100.49:18888`），`pass_host: pass` 透传客户端原始 Host；如后端需要指定 Host 可改为 `node`/`rewrite`。
- 公开访问、不限制 IP：未配置 ip-restriction / 认证插件。

## 变更记录

| 日期 | 内容 | 原因 |
| ---- | ---- | ---- |
| 2026-09-24 | 新增站点：service.yaml（http 反代 + 80/443 匹配，公开访问）+ 本 README | 提供对外短信发送入口 |
| 2026-10-16 | 端口迁移：route vars 由 `["80","443"]` 迁至 `["18080","19443"]`（外网专属监听口，前置 LB 为 DNAT） | 新约束：外网固定 18080/19443、互联网 80/443，三区端口彻底隔离 |
| 2026-10-16 | 域名修正：`sms-send.ynfwyy.com` → `sms-send.ext.ynfwyy.com`，新增 `*.ext.ynfwyy.com` 通配证书（wildcard-ext.yaml） | 外网访问域名改走 ext 子域家族 |
