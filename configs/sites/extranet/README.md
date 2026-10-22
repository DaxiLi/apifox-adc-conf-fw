# 网络区：extranet（外网）

本目录只放**对外合作 / 受限访问**的站点。每个站点目录 = `service.yaml`（必选）+ 可选 `ssl.yaml` / `consumers.yaml` / `README.md`。

## 规则

1. `labels.zone` 必须为 `extranet`，且站点目录必须在本目录下（zone 与目录一致，禁止混放）。
2. **不走 PROXY protocol**（只有内网才走 PP，端口 9181/9182）：外网请求直达 APISIX 外网专属
   HTTP/HTTPS 监听口 **18080/19443**（前置 LB 为 DNAT，保留客户端源 IP），路由用
   `vars: server_port in ["18080", "19443"]` 匹配。
3. **IP 限制非必须**（可选；内网 zone 才强制）。
4. 新站起点：复制 `configs/_templates/extranet.yaml`。

## 端口约定（外网专属 18080/19443，不走 PP）

| 端口 | 用途 |
| ---- | ---- |
| 18080 | HTTP（APISIX 外网专属监听口，不走 PROXY protocol） |
| 19443 | HTTPS（APISIX 外网专属监听口，不走 PROXY protocol） |

> 外网端口与内网（9181/9182）、公网/互联网（80/443）互不重叠，路由只匹配本区端口 →
> 任一区入口请求不会命中外网路由（端口隔离）。前提：网关 `config.yaml` 的 `node_listen`
> 监听 18080、`ssl.listen` 监听 19443。

## 当前站点

- `oms-ejinshui-cloud/` — 数电发票管理系统反代（HRP 下载电子发票；IP 白名单 172.32.5.23）
- `sms-send/` — 短信发送服务反代（公开访问，不限制 IP）
