# 网络区：extranet（外网）

本目录只放**对外合作 / 受限访问**的站点。每个站点目录 = `service.yaml`（必选）+ 可选 `ssl.yaml` / `consumers.yaml` / `README.md`。

## 规则

1. `labels.zone` 必须为 `extranet`，且站点目录必须在本目录下（zone 与目录一致，禁止混放）。
2. **不走 PROXY protocol**（只有内网才走 PP，端口 9181/9182）：外网请求直达 APISIX 标准
   HTTP/HTTPS 监听口 **80/443**，路由用 `vars: server_port in ["80", "443"]` 匹配。
3. **IP 限制非必须**（可选；内网 zone 才强制）。
4. 新站起点：复制 `configs/_templates/extranet.yaml`。

## 端口约定（外网/公网共用 80/443，不走 PP）

| 端口 | 用途 |
| ---- | ---- |
| 80 | HTTP（APISIX 标准监听口，不走 PROXY protocol） |
| 443 | HTTPS（APISIX 标准监听口，不走 PROXY protocol） |

> 外网与公网共用 80/443，靠 `hosts` 区分路由；内网走 PP 的 9181/9182 入口请求不满足
> 本区路由的 `server_port` 条件，不会命中（端口隔离）。前提：网关 `config.yaml` 的
> `node_listen` 需监听 80/443。

## 当前站点

- `oms-ejinshui-cloud/` — 数电发票管理系统反代（HRP 下载电子发票；IP 白名单 172.32.5.23）
