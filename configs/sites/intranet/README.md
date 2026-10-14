# 网络区：intranet（内网）

本目录只放**仅内网可访问**的站点。每个站点目录 = `service.yaml`（必选）+ 可选 `ssl.yaml` / `consumers.yaml` / `README.md`。

## 硬性规则（内网必须满足，违反即不合规）

1. `labels.zone` 必须为 `intranet`，且站点目录必须在本目录下（zone 与目录一致，禁止混放）。
2. **必须走 PROXY protocol**：
   - route `vars: server_port in ["9181", "9182"]`（网关 PROXY protocol 监听口，HTTP/HTTPS）
   - `real-ip` 插件从 `proxy_protocol_addr` 取真实客户端 IP（前置 HAProxy 写入 PROXY 头）
3. **必须带 IP 限制**：`ip-restriction` 白名单（不允许留空）。
4. 新站起点：复制 `configs/_templates/intranet.yaml`。

## 隔离机制（内网 ⇏ 外网/公网路由）

内网路由只在 `server_port ∈ {9181, 9182}`（PP 端口）上匹配；外网/公网路由匹配
`server_port ∈ {80, 443}`（标准监听口，不走 PP）。两组端口互不重叠 → 从内网入口
（9181/9182）进来的请求**永远无法命中**外网/公网路由（路由层隔离），
叠加内网白名单与网络层（内网客户端只能到达内网入口）形成纵深防御。

## 端口约定

| 端口 | 用途 |
| ---- | ---- |
| 9181 | HTTP + PROXY protocol |
| 9182 | HTTPS + PROXY protocol |

## 当前站点

- `ss-admin.ynfwyy.com/` — 第三方厂家管理后台反代
- `ss-dz.ynfwyy.com/` — 第三方厂家服务反代
- `rtasr-xfyun-cn.ynfwyy.com/` — 讯飞实时语音听写 WS 反代
