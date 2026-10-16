# 网络区：public（公网）

本目录只放**面向公网互联网**的站点。每个站点目录 = `service.yaml`（必选）+ 可选 `ssl.yaml` / `consumers.yaml` / `README.md`。

## 规则

1. `labels.zone` 必须为 `public`，且站点目录必须在本目录下（zone 与目录一致，禁止混放）。
2. **不走 PROXY protocol、不要求 IP 限制**（公网无法枚举客户端 IP；只有内网才走 PP 9181/9182）。
3. 新站起点：复制 `configs/_templates/public.yaml`。

## 端口约定（与外网共用 80/443，不走 PP）

| 端口 | 用途 |
| ---- | ---- |
| 80 | HTTP（APISIX 标准监听口，不走 PROXY protocol） |
| 443 | HTTPS（APISIX 标准监听口，不走 PROXY protocol） |

> 公网与外网共用 80/443，靠 `hosts` 区分路由；内网走 PP 的 9181/9182 入口请求不满足
> `server_port in ["80","443"]` 条件，不会命中（端口隔离）。

## 当前站点

- `mirror-ts/` — 清华开源镜像站反代（仅软件源下载；目录白名单 + 仅 GET/HEAD）
