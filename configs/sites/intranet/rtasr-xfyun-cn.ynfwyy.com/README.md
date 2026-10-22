# 站点：rtasr-xfyun-cn.ynfwyy.com（讯飞实时语音听写反向代理）

| 项 | 值 |
| ---- | ---- |
| 访问域名 | `wss://rtasr-xfyun-cn.ynfwyy.com/v1/ws?<请求参数>` |
| 后端 | `wss://rtasr.xfyun.cn/v1/ws`（`rtasr.xfyun.cn:443`，上游 scheme `https`） |
| 网络区 | intranet（内网，`configs/sites/intranet/`） |
| 站点类型 | ws（WebSocket / 长连接） |
| 负责人 | 邓儇 |
| IP 白名单 | 30 个客户端 IP（ip-restriction，route 级，详见 service.yaml） |

## 真实 IP 链路（已确认配置）

APISIX 前面是 HAProxy，走 **PROXY protocol**；网关 `config.yaml` 的
`apisix.proxy_protocol.listen_https_port`（HTTPS/PROXY 端口）已开启，
HAProxy 后端指向该端口（已确认）。

- 客户端 → HAProxy（写入 PROXY 头）→ APISIX proxy_protocol 端口解析
  → `$remote_addr` = 真实客户端 IP → `ip-restriction` 白名单按真实 IP 匹配
- 若将来调整 HAProxy 指向普通端口（非 proxy_protocol 端口），请求会失败、
  白名单也会失效，改回 PROXY 端口即可。

## 说明

- 客户端查询串（`?appid=...` 等）由 APISIX 原样透传给后端，无需改写。
- `pass_host: node`：上游 Host 头用节点域名 `rtasr.xfyun.cn`，**不透传代理域名**。
  曾用 `pass` 导致客户端 Host（`rtasr-xfyun-cn.ynfwyy.com`）被原样发往讯飞，讯飞按 Host 识别返回 404。
- `proxy-rewrite`：剥离 `X-Forwarded-For` / `X-Real-IP` / `Forwarded`，客户端内网 IP 不透传给讯飞
  （APISIX 默认会把连接方 IP 追加进 X-Forwarded-For）。
- 证书：Let's Encrypt `*.ynfwyy.com` 通配（已在 `configs/global/ssls/wildcard.yaml`
  声明一次，`snis: ["*.ynfwyy.com"]`，本站 TLS 由通配 SNI 覆盖；轮换时保持 `snis`
  不变，见 `docs/证书轮换操作手册.md`）。

## 变更记录

| 日期 | 内容 | 原因 |
| ---- | ---- | ---- |
| 2026-10-22 | 修复 404：upstream `pass_host: pass` → `node`；新增 `proxy-rewrite` 剥离客户端 IP 头 | 客户端 Host（`rtasr-xfyun-cn.ynfwyy.com`）被原样透传给讯飞，讯飞按 Host 识别返回 404；同时 APISIX 默认把连接方 IP 追加进 X-Forwarded-For，一并剥离，避免内网信息外泄 |
| 2026-09-21 | 重构：迁入 `configs/sites/intranet/`，service 加 `zone: intranet` 标签 | 配置按网络区分区（内网/外网/公网），内网必须 PROXY + IP 白名单；资源名不变，ID 不变 |
| 2026-09-17 | 新增站点：service.yaml（ws 反代 + ip-restriction 白名单）+ ssl.yaml（内联通配证书）+ 本 README | 对外提供讯飞实时听写反代入口；证书文件 cert.pem/key.pem 内联后已删除 |
| 2026-09-17 | 说明更新：确认 HAProxy PROXY protocol + APISIX proxy_protocol 端口均已配置 | 明确真实 IP 链路已就绪，白名单按真实客户端 IP 匹配 |
| 2026-09-17 | 证书调整：本站 ssl.yaml 删除，通配证书移入 global/ssls/wildcard.yaml（snis: *.ynfwyy.com） | 证书为 *.ynfwyy.com 通配，按仓库设计一张证书只定义一次，放全局供所有子域复用 |
| 2026-09-20 | 白名单更新：替换为新的 30 个客户端 IP（原 10.105.27.0/24、10.106.150.107 移除） | 用户提供的最新放行 IP 清单 |
| 2026-09-20 | vars 修复：`server_port in [9181, 9182]` 数字列表改为字符串 `["9181", "9182"]` | `in` 是严格相等比较，数字不会等于 nginx 变量的字符串值，原写法可能永不匹配 |
