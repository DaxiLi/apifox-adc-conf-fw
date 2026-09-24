# 配置总览（自动生成，请勿手改）

> 由 `tools/gen-inventory.py` 生成｜重新生成：`python tools/gen-inventory.py [--html] [--live]`
> 生成时间：2026-09-24 08:08

## 一、总览

- 站点：**6** 个（内网 4 ｜ 外网 2 ｜ 公网 0）
- service：**6** 个，route **6** 条
- 站点类型分布：partner 3, ws 1, www 2
- 认证使用：key-auth 1
- 消费者：站点级 1 个 / 全局 0 个
- 证书：站点级 0 张 / 全局 1 张

| 网络区 | 站点 | service | 域名(hosts) | 后端 | 类型 | 认证 | IP 白名单 | 端口匹配 | WS | 负责人 |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| 外网 | oms-ejinshui-cloud | oms-ejinshui-cloud-partner | www-oms-ejinshui--cloud-com.ynfwyy.com | https://www.oms.ejinshui-cloud.com:443 | partner | — | 白名单(1): 172.32.5.23 | server_port in [80,443] | — | 陈曦 |
| 外网 | ynfwyy | ynfwyy-www | www.ynfwyy.com | http://172.32.100.11:80 | www | key-auth(header=token) | — | server_port in [80,443] | — | test |
| 内网 | rtasr-xfyun-cn.ynfwyy.com | rtasr-xfyun-cn.ynfwyy.com-ws | rtasr-xfyun-cn.ynfwyy.com | https://rtasr.xfyun.cn:443 | ws | — | 白名单(30): 10.105.202.101, 10.106.11.69, 10.106.150.101 … | server_port in [9181,9182] | 是 | 邓儇 |
| 内网 | ss-admin.ynfwyy.com | ss-admin.ynfwyy.com-partner | ss-admin.ynfwyy.com | http://172.32.98.41:85 | partner | — | 白名单(1): 10.106.150.107 | server_port in [9181,9182] | — | 窦坤-邢玉瑞 |
| 内网 | ss-dz.ynfwyy.com | ss-dz.ynfwyy.com-partner | ss-dz.ynfwyy.com | http://172.32.98.41:83 | partner | — | 白名单(1): 10.106.150.107 | server_port in [9181,9182] | — | 窦坤-邢玉瑞 |
| 内网 | testport | testport-www | — | http://172.32.100.11:80 | www | — | — | proxy_protocol_server_port == 10001 | — | test |

## 二、站点明细（完整配置）

### [外网] oms-ejinshui-cloud  `sites/extranet/oms-ejinshui-cloud/`

#### service：`oms-ejinshui-cloud-partner`

- 描述：数电发票管理系统反代（HRP 下载电子发票）
- labels：site=oms-ejinshui-cloud, zone=extranet, site_type=partner, env=prod, owner=陈曦, contact=陈曦

**upstream**：

```yaml
nodes:
- host: www.oms.ejinshui-cloud.com
  port: 443
  weight: 100
pass_host: node
scheme: https
type: roundrobin
```

**route：`oms-ejinshui-cloud-root`**

- hosts：www-oms-ejinshui--cloud-com.ynfwyy.com
- uris：/*
- methods：GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- vars：server_port in [80,443]
- priority：0
- plugins：

```yaml
  ip-restriction:
    whitelist:
    - 172.32.5.23
```

### [外网] ynfwyy  `sites/extranet/ynfwyy/`

#### service：`ynfwyy-www`

- 描述：外网 www.ynfwyy.com 反代（key-auth）
- labels：site=ynfwyy, zone=extranet, site_type=www, env=prod, owner=test, contact=test

**upstream**：

```yaml
nodes:
- host: 172.32.100.11
  port: 80
  weight: 100
pass_host: pass
scheme: http
type: roundrobin
```

**route：`ynfwyy-www-root`**

- hosts：www.ynfwyy.com
- uris：/*
- methods：GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- vars：server_port in [80,443]
- priority：0
- plugins：

```yaml
  key-auth:
    header: token
```

**consumers**：
- `ynfwyy-www` —— 凭证：key-auth:primary-key
  ```yaml
    key: aaaabbbb
  ```

### [内网] rtasr-xfyun-cn.ynfwyy.com  `sites/intranet/rtasr-xfyun-cn.ynfwyy.com/`

#### service：`rtasr-xfyun-cn.ynfwyy.com-ws`

- 描述：讯飞实时语音听写 WebSocket 反代
- labels：site=rtasr-xfyun-cn.ynfwyy.com, zone=intranet, site_type=ws, env=prod, owner=邓儇, contact=邓儇

**upstream**：

```yaml
nodes:
- host: rtasr.xfyun.cn
  port: 443
  weight: 100
pass_host: pass
scheme: https
timeout:
  connect: 10
  read: 3600
  send: 60
type: roundrobin
```

**route：`rtasr-xfyun-cn.ynfwyy.com-ws-v1`**

- hosts：rtasr-xfyun-cn.ynfwyy.com
- uris：/v1/ws
- methods：GET
- vars：server_port in [9181,9182]
- priority：0；enable_websocket：true
- plugins：

```yaml
  ip-restriction:
    whitelist:
    - 10.105.202.101
    - 10.106.11.69
    - 10.106.150.101
    - 10.106.150.108
    - 10.107.102.31
    - 10.107.102.38
    - 10.107.102.39
    - 10.107.102.41
    - 10.107.102.42
    - 10.107.102.44
    - 10.107.102.45
    - 10.107.102.46
    - 10.107.102.50
    - 10.107.102.56
    - 10.107.102.58
    - 10.107.102.59
    - 10.107.102.60
    - 10.107.102.61
    - 10.107.102.64
    - 10.107.102.66
    - 10.107.102.67
    - 10.107.102.151
    - 10.107.102.152
    - 10.107.102.154
    - 10.107.102.155
    - 10.107.102.214
    - 10.107.102.215
    - 10.107.102.216
    - 10.107.102.217
    - 10.107.102.250
  real-ip:
    source: proxy_protocol_addr
    trusted_addresses:
    - 172.32.9.2
```

### [内网] ss-admin.ynfwyy.com  `sites/intranet/ss-admin.ynfwyy.com/`

#### service：`ss-admin.ynfwyy.com-partner`

- 描述：第三方厂家管理后台反向代理
- labels：site=ss-admin.ynfwyy.com, zone=intranet, site_type=partner, env=prod, owner=窦坤-邢玉瑞, contact=窦坤-邢玉瑞

**upstream**：

```yaml
nodes:
- host: 172.32.98.41
  port: 85
  weight: 100
pass_host: pass
scheme: http
type: roundrobin
```

**route：`ss-admin.ynfwyy.com-root`**

- hosts：ss-admin.ynfwyy.com
- uris：/*
- methods：GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- vars：server_port in [9181,9182]
- priority：0
- plugins：

```yaml
  ip-restriction:
    whitelist:
    - 10.106.150.107
  real-ip:
    source: proxy_protocol_addr
    trusted_addresses:
    - 172.32.9.2
```

### [内网] ss-dz.ynfwyy.com  `sites/intranet/ss-dz.ynfwyy.com/`

#### service：`ss-dz.ynfwyy.com-partner`

- 描述：第三方厂家服务反向代理
- labels：site=ss-dz.ynfwyy.com, zone=intranet, site_type=partner, env=prod, owner=窦坤-邢玉瑞, contact=窦坤-邢玉瑞

**upstream**：

```yaml
nodes:
- host: 172.32.98.41
  port: 83
  weight: 100
pass_host: pass
scheme: http
type: roundrobin
```

**route：`ss-dz.ynfwyy.com-root`**

- hosts：ss-dz.ynfwyy.com
- uris：/*
- methods：GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- vars：server_port in [9181,9182]
- priority：0
- plugins：

```yaml
  ip-restriction:
    whitelist:
    - 10.106.150.107
  real-ip:
    source: proxy_protocol_addr
    trusted_addresses:
    - 172.32.9.2
```

### [内网] testport  `sites/intranet/testport/`

#### service：`testport-www`

- 描述：示例站点：按 PROXY protocol 目标端口 10001 匹配
- labels：site=testport, zone=intranet, site_type=www, env=prod, owner=test, contact=test；x-check-skip=intranet-ip,intranet-realip

**upstream**：

```yaml
nodes:
- host: 172.32.100.11
  port: 80
  weight: 100
pass_host: pass
scheme: http
type: roundrobin
```

**route：`testport-www-root`**

- hosts：—
- uris：/*
- methods：GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- vars：proxy_protocol_server_port == 10001
- priority：0

## 三、全局资源

### global_rules（全网关生效）

```yaml
response-rewrite:
  headers:
    remove:
    - Server
```

### plugin_metadata

无。

### 全局证书
- snis：*.ynfwyy.com（labels：contact: 袁杰
env: prod
owner: 袁杰
site: ynfwyy
site_type: www
zone: shared）

## 四、分区规则速查

| 网络区 | PROXY protocol | IP 限制 | 端口 |
| ---- | ---- | ---- | ---- |
| 内网 intranet | 必走（PP） | 必填白名单 | 9181/9182 |
| 外网 extranet | 不走 | 可选 | 80/443 |
| 公网 public | 不走 | 不要求 | 80/443 |

模板：admin.yaml, api.yaml, extranet.yaml, intranet.yaml, public.yaml, ssl.yaml, static.yaml, websocket.yaml, www.yaml
