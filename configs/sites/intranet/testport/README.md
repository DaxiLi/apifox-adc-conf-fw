# 站点：testport（示例站点：按 PROXY protocol 目标端口匹配）

| 项 | 值 |
| ---- | ---- |
| 访问方式 | PROXY protocol 目标端口 `10001`（经 APISIX 9181/9182 监听口） |
| 后端 | `http://172.32.100.11:80` |
| 网络区 | intranet（内网，`configs/sites/intranet/`） |
| 站点类型 | www（示例） |
| 负责人 | test（示例） |
| 匹配规则 | route vars：`proxy_protocol_server_port == "10001"` |

## 说明

- 示例站点：演示「按 HAProxy PROXY 头里的目标端口匹配服务」。
- 不约束 host：`uris: [/*]`、不写 `hosts`，只要 PROXY 头目标端口是 10001 即命中；
  普通监听口上 `$proxy_protocol_server_port` 为空，天然不会误匹配。
- 前置链路：HAProxy 前端监听 10001 → 后端 `send-proxy-v2` 指向 APISIX 9181/9182
  （网关 `config.yaml` 的 `apisix.proxy_protocol.listen_http_port/listen_https_port`）
  → nginx 解析 PROXY 头 → route vars 匹配。
- 注意：PROXY 头里的目标端口 = 客户端连 HAProxy 时用的端口；HAProxy 前端只监听一个端口时
  该值恒定，无法靠端口区分多服务。

## 变更记录

| 日期 | 内容 | 原因 |
| ---- | ---- | ---- |
| 2026-09-21 | 重构：迁入 `configs/sites/intranet/`，service 加 `zone: intranet` 标签 | 配置按网络区分区（内网/外网/公网），内网必须 PROXY + IP 白名单；资源名不变，ID 不变 |
| 2026-09-21 | labels 加 `x-check-skip: "intranet-ip,intranet-realip"` | 示例站仅演示 PROXY 目标端口匹配，无真实 IP 白名单/real-ip；显式豁免 `tools/check-config.py` 的内网强制检查 |
| 2026-09-20 | 新增站点：service.yaml（pp 端口 10001 → 172.32.100.11:80）+ 本 README | 示例：验证按 PROXY 目标端口匹配路由 |
