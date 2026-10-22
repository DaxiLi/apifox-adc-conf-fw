# 站点：mirror-ts（清华开源镜像站反代，仅供软件源下载）

| 项 | 值 |
| ---- | ---- |
| 访问域名 | `https://mirror-ts.ynfwyy.com` / `http://mirror-ts.ynfwyy.com` |
| 后端 | `https://mirrors.tuna.tsinghua.edu.cn:443`（清华大学开源软件镜像站） |
| 网络区 | public（公网，`configs/sites/public/`） |
| 站点类型 | static（静态资源/文件镜像） |
| 负责人 | admin |
| 方法限制 | 仅 `GET` / `HEAD`（软件源只读下载） |
| 路径限制 | 仅放行下方软件源目录白名单；网页界面（`/`、`/help/`、`/static/`、`/status/` 等）一律 404 |
| 匹配规则 | route vars：`server_port in ["80", "443"]`（APISIX 标准 HTTP/HTTPS 监听口） |

## 说明

- 站点代码 `mirror-ts` 取自访问域名 `mirror-ts.ynfwyy.com`（一级子域，受 `*.ynfwyy.com` 通配证书覆盖，无需单独 ssl.yaml）。
- **"只能作为软件源"的实现**：
  1. route `uris` 只匹配放行的软件源目录前缀（`*` 结尾前缀匹配），未列出的路径（含网页界面）因无路由命中而 404；
  2. `methods` 仅 `GET/HEAD`，拦截 POST/PUT/DELETE 等写方法；
  3. `pass_host: node` 透传 Host=`mirrors.tuna.tsinghua.edu.cn`（后端按虚拟主机路由）。
- **白名单目录取自 tuna 实时镜像列表（2026-10 核对）**；当前不在 tuna 上的常见目录
  （如 `/almalinux/`、`/rocky/`、`/npm/`、`/helm/`）**未列入**——放行也只会 404，需要时先确认 tuna 已恢复再增补。
- 公网不走 PROXY protocol：请求直达 APISIX 80/443；与内网 9181/9182、外网 18080/19443 端口隔离（三区端口互不重叠）。
- 未加限流/缓存：镜像批量拉取（apt update / 同步）易触发限流或缓存失效，故不启用 limit-count/proxy-cache。

## 变更记录

| 日期 | 内容 | 原因 |
| ---- | ---- | ---- |
| 2026-09-24 | 新增站点：service.yaml（https 反代 + 软件源目录白名单 + 仅 GET/HEAD）+ 本 README | 提供对内软件源入口，限制仅作软件源使用 |
| 2026-10-16 | README 端口说明更新：公网独占 80/443（外网已迁至 18080/19443） | 新约束：三区端口彻底隔离，端口约定文档同步 |
