# 站点：ss-admin.ynfwyy.com（第三方厂家管理后台反向代理）

| 项 | 值 |
| ---- | ---- |
| 访问域名 | `https://ss-admin.ynfwyy.com` / `http://ss-admin.ynfwyy.com` |
| 后端 | `http://172.32.98.41:85` |
| 站点类型 | partner（对外合作接口） |
| 负责人 | 窦坤-邢玉瑞 |
| IP 白名单 | `10.106.150.107`（ip-restriction，route 级） |
| 服务端口 | 仅 9181（HTTP）/ 9182（HTTPS），PROXY protocol 端口（vars: server_port） |

## 说明

- 纯反向代理：整站 `/*` 匹配，方法全开；客户端查询串原样透传。
- `pass_host: pass`：上游 Host 头保留客户端的 `ss-admin.ynfwyy.com`。
- 证书：Let's Encrypt `*.ynfwyy.com` 通配（已在 `configs/global/ssls/wildcard.yaml`
  声明一次，`snis: ["*.ynfwyy.com"]`，本站 TLS 由通配 SNI 覆盖；轮换时保持 `snis`
  不变，见 `docs/证书轮换操作手册.md`）。
- 真实 IP 链路：APISIX 前置 HAProxy 走 PROXY protocol，`real-ip` 插件从
  `proxy_protocol_addr` 取真实客户端 IP，`ip-restriction` 白名单按真实 IP 匹配。

## 变更记录

| 日期 | 内容 | 原因 |
| ---- | ---- | ---- |
| 2026-09-20 | 新增站点：service.yaml（partner 反代 + ip-restriction 白名单）+ 本 README | 第三方厂家管理后台经网关反代至 172.32.98.41:85，仅放行 10.106.150.107 |
