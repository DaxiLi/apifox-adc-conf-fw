# 站点：sms-send（短信发送服务反代，公开访问）

| 项 | 值 |
| ---- | ---- |
| 访问域名 | `https://sms-send.ynfwyy.com` / `http://sms-send.ynfwyy.com` |
| 后端 | `http://172.32.100.49:18888`（短信发送服务） |
| 网络区 | extranet（外网，`configs/sites/extranet/`） |
| 站点类型 | api（对外接口） |
| 负责人 | 袁杰 |
| IP 限制 | 无（公开访问，不限制 IP） |
| 匹配规则 | route vars：`server_port in ["80", "443"]`（APISIX 标准 HTTP/HTTPS 监听口） |

## 说明

- 站点代码 `sms-send` 取自访问域名 `sms-send.ynfwyy.com`（一级子域，受 `*.ynfwyy.com` 通配证书覆盖，无需单独 ssl.yaml）。
- **外网不走 PROXY protocol**：请求直达 APISIX 80/443；只有内网才走 PP（9181/9182）。
- 后端为内网 IP（`172.32.100.49:18888`），`pass_host: pass` 透传客户端原始 Host；如后端需要指定 Host 可改为 `node`/`rewrite`。
- 公开访问、不限制 IP：未配置 ip-restriction / 认证插件。

## 变更记录

| 日期 | 内容 | 原因 |
| ---- | ---- | ---- |
| 2026-09-24 | 新增站点：service.yaml（http 反代 + 80/443 匹配，公开访问）+ 本 README | 提供对外短信发送入口 |
