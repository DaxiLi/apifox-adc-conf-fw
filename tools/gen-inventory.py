#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置总览生成工具（gen-inventory.py）—— 把分散在 configs/** 的当前生效配置，
汇总成「一份文件看清全部」的总览，支持搜索查看，不必逐一翻配置文件。

输出：
    1. configs/sites/INVENTORY.md     —— 完整配置总览 Markdown（总览速览 + 每站完整配置 +
                                         全局资源 + 分区规则；可提交仓库，勿手改）
    2. configs/sites/INVENTORY.html   —— 可搜索面板（--html；自包含单文件，浏览器打开，
                                        搜索框即时过滤；已 gitignore，本地查看用）
    3. 终端 --query <关键词>          —— 搜索并打印命中的配置片段（无需浏览器）

用法：
    python tools/gen-inventory.py                  # 生成 INVENTORY.md + 打印总览
    python tools/gen-inventory.py --html           # 额外生成 INVENTORY.html 搜索面板
    python tools/gen-inventory.py --no-file        # 只打印不写文件
    python tools/gen-inventory.py --query 讯飞     # 搜索关键词（域名/服务名/后端/负责人/插件…）
    python tools/gen-inventory.py --query key-auth
    python tools/gen-inventory.py --json           # 输出结构化 JSON

依赖：python3 + PyYAML；--live 需网关可达（调 adc dump）。
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_SITES = ROOT / "configs" / "sites"
CONFIG_GLOBAL = ROOT / "configs" / "global"
CONFIG_TEMPLATES = ROOT / "configs" / "_templates"
OUT_MD = CONFIG_SITES / "INVENTORY.md"
OUT_HTML = CONFIG_SITES / "INVENTORY.html"
ADC_EXE = ROOT / ".bin" / "adc" / "adc.exe"

ZONE_CN = {"intranet": "内网", "extranet": "外网", "public": "公网", "shared": "共用"}
AUTH_PLUGINS = ("key-auth", "basic-auth", "jwt-auth", "hmac-auth")
LIVE_TMP = ROOT / ".inventory-live.yaml"


# ---------------------------------------------------------------------------
# 数据收集
# ---------------------------------------------------------------------------

def load(path: Path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as exc:  # noqa: BLE001
        return {"__error__": str(exc)}


def collect_sites():
    """解析 configs/sites/<zone>/<site>/*.yaml → 站点分组结构。"""
    sites = []
    if not CONFIG_SITES.is_dir():
        return sites
    for zone_dir in sorted(CONFIG_SITES.iterdir()):
        if not zone_dir.is_dir() or zone_dir.name.startswith("."):
            continue
        zone = zone_dir.name
        for site_dir in sorted(zone_dir.iterdir()):
            if not site_dir.is_dir():
                continue
            site = {"zone": zone, "zone_cn": ZONE_CN.get(zone, zone), "site": site_dir.name,
                    "services": [], "consumers": [], "ssls": [], "errors": []}
            for yf in sorted(site_dir.glob("*.yaml")):
                obj = load(yf)
                if "__error__" in obj:
                    site["errors"].append(f"{yf.name}: {obj['__error__']}")
                    continue
                site["services"].extend(obj.get("services") or [])
                site["consumers"].extend(obj.get("consumers") or [])
                site["ssls"].extend(obj.get("ssls") or [])
            sites.append(site)
    return sites


def collect_global():
    g = {"global_rules": {}, "plugin_metadata": {}, "consumers": [], "ssls": [], "consumer_groups": [], "errors": []}
    if not CONFIG_GLOBAL.is_dir():
        return g
    for yf in sorted(CONFIG_GLOBAL.rglob("*.yaml")):
        obj = load(yf)
        if "__error__" in obj:
            g["errors"].append(f"{yf.relative_to(ROOT)}: {obj['__error__']}")
            continue
        g["global_rules"].update(obj.get("global_rules") or {})
        g["plugin_metadata"].update(obj.get("plugin_metadata") or {})
        g["consumers"].extend(obj.get("consumers") or [])
        g["ssls"].extend(obj.get("ssls") or [])
        g["consumer_groups"].extend(obj.get("consumer_groups") or [])
    return g


def collect_templates():
    if not CONFIG_TEMPLATES.is_dir():
        return []
    return [p.name for p in sorted(CONFIG_TEMPLATES.glob("*.yaml"))]


def collect_all():
    return {
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "sites": collect_sites(),
        "global": collect_global(),
        "templates": collect_templates(),
    }


# ---------------------------------------------------------------------------
# 摘要辅助
# ---------------------------------------------------------------------------

def yaml_block(obj, indent=0):
    """把配置对象转成可读 YAML 文本（键排序、中文不转义）。"""
    text = yaml.dump(obj, allow_unicode=True, default_flow_style=False,
                     sort_keys=True, width=120).rstrip("\n")
    pad = "  " * indent
    return "\n".join(pad + line for line in text.split("\n"))


def vars_summary(route):
    parts = []
    for cond in route.get("vars") or []:
        if not (isinstance(cond, list) and len(cond) >= 3):
            continue
        var, op, val = str(cond[0]), str(cond[1]), cond[2]
        if var in ("server_port", "proxy_protocol_server_port"):
            if isinstance(val, list):
                parts.append(f"{var} {op} [{','.join(str(v) for v in val)}]")
            else:
                parts.append(f"{var} {op} {val}")
    return "；".join(parts) or "—"


def auth_summary(route):
    out = []
    for name in AUTH_PLUGINS:
        cfg = (route.get("plugins") or {}).get(name)
        if cfg is None:
            continue
        s = name
        if name == "key-auth" and isinstance(cfg, dict) and cfg.get("header"):
            s += f"(header={cfg['header']})"
        out.append(s)
    return "，".join(out) or "—"


def ip_summary(route):
    ipr = (route.get("plugins") or {}).get("ip-restriction") or {}
    wl, bl = ipr.get("whitelist") or [], ipr.get("blacklist") or []
    out = []
    if wl:
        shown = ", ".join(str(x) for x in wl[:3]) + (" …" if len(wl) > 3 else "")
        out.append(f"白名单({len(wl)}): {shown}")
    if bl:
        out.append(f"黑名单({len(bl)}): {', '.join(str(x) for x in bl[:3])}")
    return "；".join(out) or "—"


def upstream_summary(upstream):
    if not upstream:
        return "—"
    scheme = upstream.get("scheme") or "http"
    nodes = upstream.get("nodes") or []
    hosts = [f"{n['host']}:{n.get('port', '')}" for n in nodes if isinstance(n, dict) and n.get("host")]
    return f"{scheme}://" + ",".join(hosts) if hosts else str(upstream.get("type", "—"))


def service_summary(svc):
    """一行速览（用于总览表）。"""
    labels = svc.get("labels") or {}
    routes = svc.get("routes") or []
    hosts = sorted({h for rt in routes for h in (rt.get("hosts") or [])})
    auths = "，".join(dict.fromkeys(a for rt in routes for a in [auth_summary(rt)] if a != "—")) or "—"
    ips = "；".join(dict.fromkeys(ip_summary(rt) for rt in routes if ip_summary(rt) != "—")) or "—"
    ports = "；".join(dict.fromkeys(vars_summary(rt) for rt in routes if vars_summary(rt) != "—")) or "—"
    return {
        "zone_cn": ZONE_CN.get(labels.get("zone") or "", ""),
        "service": svc.get("name"),
        "hosts": ", ".join(hosts) or "—",
        "backend": upstream_summary(svc.get("upstream")),
        "site_type": labels.get("site_type", "—"),
        "owner": labels.get("owner", "—"),
        "auth": auths, "ip": ips, "ports": ports,
        "ws": "是" if any(rt.get("enable_websocket") for rt in routes) else "—",
    }


def compute_summary(data):
    sites, g = data["sites"], data["global"]
    zone_count = {"intranet": 0, "extranet": 0, "public": 0}
    type_count, auth_count = {}, {}
    svc_rows, n_routes, n_consumers, n_ssls = [], 0, 0, 0
    for site in sites:
        zone = site["zone"]
        if zone in zone_count:
            zone_count[zone] += 1
        for svc in site["services"]:
            rows = service_summary(svc)
            if "_live" in svc:
                rows["_live"] = svc["_live"]
            rows["site"], rows["zone"] = site["site"], site["zone"]
            svc_rows.append(rows)
            st = rows["site_type"]
            type_count[st] = type_count.get(st, 0) + 1
            n_routes += len(svc.get("routes") or [])
            for rt in svc.get("routes") or []:
                for a in auth_summary(rt).split("，"):
                    if a and a != "—":
                        key = a.split("(")[0]
                        auth_count[key] = auth_count.get(key, 0) + 1
        n_consumers += len(site["consumers"])
        n_ssls += len(site["ssls"])
    return {
        "zone_count": zone_count,
        "type_count": dict(sorted(type_count.items())),
        "auth_count": dict(sorted(auth_count.items())),
        "svc_rows": svc_rows,
        "n_sites": len(sites),
        "n_services": len(svc_rows),
        "n_routes": n_routes,
        "n_consumers_site": n_consumers,
        "n_ssls_site": n_ssls,
        "n_consumers_global": len(g["consumers"]),
        "n_ssls_global": len(g["ssls"]),
        "n_groups_global": len(g["consumer_groups"]),
    }


# ---------------------------------------------------------------------------
# 生效状态（--live：本地配置 vs 网关 adc dump）
# ---------------------------------------------------------------------------

def fetch_live_state():
    """返回 (remote_service_names:set, remote_route_keys:set, remote_consumers:set, remote_ssls:set, error|None)。"""
    cmd = [str(ADC_EXE) if ADC_EXE.exists() else "adc", "dump", "-o", str(LIVE_TMP)]
    try:
        proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=90)
        if proc.returncode != 0:
            return None, None, None, None, f"adc dump 失败：{proc.stderr.strip()[-300:]}"
        obj = load(LIVE_TMP)
    except Exception as exc:  # noqa: BLE001
        return None, None, None, None, f"adc dump 异常：{exc}"
    finally:
        LIVE_TMP.unlink(missing_ok=True)
    svc_names = {s.get("name") for s in obj.get("services") or [] if s.get("name")}
    route_keys = {(s.get("name"), r.get("name")) for s in obj.get("services") or []
                  for r in (s.get("routes") or []) if s.get("name") and r.get("name")}
    consumers = {c.get("username") for c in obj.get("consumers") or [] if c.get("username")}
    ssls = {",".join(s.get("snis") or []) for s in obj.get("ssls") or []}
    return svc_names, route_keys, consumers, ssls, None


def annotate_live(data):
    """给站点/服务标注生效状态；返回 (data, note)。"""
    svc_remote, route_remote, cons_remote, ssl_remote, err = fetch_live_state()
    if err:
        for site in data["sites"]:
            for svc in site["services"]:
                svc["_live"] = "未知"
        return data, err
    for site in data["sites"]:
        for svc in site["services"]:
            svc["_live"] = "已生效" if svc.get("name") in svc_remote else "待同步(仅本地)"
        for c in site["consumers"]:
            c["_live"] = "已生效" if c.get("username") in cons_remote else "待同步(仅本地)"
        for s in site["ssls"]:
            key = ",".join(s.get("snis") or [])
            s["_live"] = "已生效" if key in ssl_remote else "待同步(仅本地)"
    local_svcs = {s.get("name") for site in data["sites"] for s in site["services"]}
    local_routes = {(site["site"], r.get("name")) for site in data["sites"]
                    for s in site["services"] for r in (s.get("routes") or [])}
    remote_only = sorted(svc_remote - local_svcs)
    note = f"网关比对完成；仅存在于网关（本地配置没有，sync 会删除）的资源：{len(remote_only)} 个"
    if remote_only:
        note += "：" + ", ".join(remote_only[:10])
    return data, note


# ---------------------------------------------------------------------------
# Markdown 渲染（完整配置总览）
# ---------------------------------------------------------------------------

def render_markdown(data, summary, live_note=None):
    L = []
    L.append("# 配置总览（自动生成，请勿手改）")
    L.append("")
    L.append("> 由 `tools/gen-inventory.py` 生成｜重新生成：`python tools/gen-inventory.py [--html] [--live]`")
    L.append(f"> 生成时间：{data['generated_at']}")
    if live_note:
        L.append(f"> 生效状态：{live_note}")
    L.append("")

    # ---- 一、总览 ----
    L.append("## 一、总览")
    L.append("")
    L.append(f"- 站点：**{summary['n_sites']}** 个（内网 {summary['zone_count'].get('intranet', 0)} ｜ "
             f"外网 {summary['zone_count'].get('extranet', 0)} ｜ 公网 {summary['zone_count'].get('public', 0)}）")
    L.append(f"- service：**{summary['n_services']}** 个，route **{summary['n_routes']}** 条")
    L.append(f"- 站点类型分布：{', '.join(f'{k} {v}' for k, v in summary['type_count'].items()) or '—'}")
    L.append(f"- 认证使用：{', '.join(f'{k} {v}' for k, v in summary['auth_count'].items()) or '无'}")
    L.append(f"- 消费者：站点级 {summary['n_consumers_site']} 个 / 全局 {summary['n_consumers_global']} 个")
    L.append(f"- 证书：站点级 {summary['n_ssls_site']} 张 / 全局 {summary['n_ssls_global']} 张")
    L.append("")
    L.append("| 网络区 | 站点 | service | 域名(hosts) | 后端 | 类型 | 认证 | IP 白名单 | 端口匹配 | WS | 负责人 |" +
             (" 生效 |" if live_note else ""))
    L.append("| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |" +
             (" ---- |" if live_note else ""))
    for r in summary["svc_rows"]:
        extra = f" {r['_live']} |" if "_live" in r else ""
        L.append(f"| {r['zone_cn']} | {r['site']} | {r['service']} | {r['hosts']} | {r['backend']} "
                 f"| {r['site_type']} | {r['auth']} | {r['ip']} | {r['ports']} | {r['ws']} | {r['owner']} |" + extra)
    L.append("")

    # ---- 二、站点明细（完整配置） ----
    L.append("## 二、站点明细（完整配置）")
    L.append("")
    for site in data["sites"]:
        zone, sname = site["zone_cn"], site["site"]
        L.append(f"### [{zone}] {sname}  `sites/{site['zone']}/{sname}/`")
        L.append("")
        if site["errors"]:
            for e in site["errors"]:
                L.append(f"- ⚠️ 解析失败：{e}")
        for svc in site["services"]:
            name = svc.get("name")
            live = f"（{svc['_live']}）" if "_live" in svc else ""
            L.append(f"#### service：`{name}`{live}")
            L.append("")
            if svc.get("description"):
                L.append(f"- 描述：{svc['description']}")
            labels = svc.get("labels") or {}
            L.append(f"- labels：{', '.join(f'{k}={v}' for k, v in labels.items() if k != 'x-check-skip')}"
                     + (f"；x-check-skip={labels.get('x-check-skip')}" if labels.get("x-check-skip") else ""))
            if svc.get("upstream"):
                L.append("")
                L.append("**upstream**：")
                L.append("")
                L.append("```yaml")
                L.append(yaml_block(svc["upstream"]))
                L.append("```")
            for rt in svc.get("routes") or []:
                L.append("")
                L.append(f"**route：`{rt.get('name')}`**")
                L.append("")
                if rt.get("hosts") or rt.get("uris") or rt.get("methods"):
                    L.append(f"- hosts：{', '.join(rt.get('hosts') or []) or '—'}")
                    L.append(f"- uris：{', '.join(rt.get('uris') or []) or '—'}")
                    L.append(f"- methods：{', '.join(rt.get('methods') or []) or '—'}")
                if rt.get("vars"):
                    L.append(f"- vars：{vars_summary(rt)}")
                L.append(f"- priority：{rt.get('priority', 0)}" + ("；enable_websocket：true" if rt.get("enable_websocket") else ""))
                if rt.get("plugins"):
                    L.append("- plugins：")
                    L.append("")
                    L.append("```yaml")
                    L.append(yaml_block(rt["plugins"], indent=1))
                    L.append("```")
        if site["consumers"]:
            L.append("")
            L.append("**consumers**：")
            for c in site["consumers"]:
                live = f"（{c['_live']}）" if "_live" in c else ""
                creds = "，".join(f"{x.get('type')}:{x.get('name')}" for x in (c.get("credentials") or [])) or "—"
                L.append(f"- `{c.get('username')}`{live} —— 凭证：{creds}")
                for x in c.get("credentials") or []:
                    if x.get("config"):
                        L.append("  ```yaml")
                        L.append(yaml_block(x["config"], indent=2))
                        L.append("  ```")
        if site["ssls"]:
            L.append("")
            L.append("**ssls**：")
            for s in site["ssls"]:
                live = f"（{s['_live']}）" if "_live" in s else ""
                L.append(f"- snis：{', '.join(s.get('snis') or [])}{live}")
        L.append("")

    # ---- 三、全局资源 ----
    g = data["global"]
    L.append("## 三、全局资源")
    L.append("")
    L.append("### global_rules（全网关生效）")
    L.append("")
    if g["global_rules"]:
        L.append("```yaml")
        L.append(yaml_block(g["global_rules"]))
        L.append("```")
    else:
        L.append("无。")
    L.append("")
    L.append("### plugin_metadata")
    L.append("")
    if g["plugin_metadata"]:
        L.append("```yaml")
        L.append(yaml_block(g["plugin_metadata"]))
        L.append("```")
    else:
        L.append("无。")
    if g["consumers"]:
        L.append("")
        L.append("### 全局消费者")
        for c in g["consumers"]:
            creds = "，".join(f"{x.get('type')}:{x.get('name')}" for x in (c.get("credentials") or [])) or "—"
            L.append(f"- `{c.get('username')}` —— 凭证：{creds}")
    if g["ssls"]:
        L.append("")
        L.append("### 全局证书")
        for s in g["ssls"]:
            L.append(f"- snis：{', '.join(s.get('snis') or [])}（labels：{yaml_block(s.get('labels') or {})}）")
    if g["errors"]:
        L.append("")
        L.append("### ⚠️ 解析错误")
        for e in g["errors"]:
            L.append(f"- {e}")
    L.append("")

    # ---- 四、分区规则速查 ----
    L.append("## 四、分区规则速查")
    L.append("")
    L.append("| 网络区 | PROXY protocol | IP 限制 | 端口 |")
    L.append("| ---- | ---- | ---- | ---- |")
    L.append("| 内网 intranet | 必走（PP） | 必填白名单 | 9181/9182 |")
    L.append("| 外网 extranet | 不走 | 可选 | 80/443 |")
    L.append("| 公网 public | 不走 | 不要求 | 80/443 |")
    L.append("")
    L.append(f"模板：{', '.join(data['templates']) or '—'}")
    L.append("")
    return "\n".join(L)


# ---------------------------------------------------------------------------
# HTML 渲染（可搜索面板）
# ---------------------------------------------------------------------------

def render_html(data, summary, live_note=None):
    svc_map = {}
    for site in data["sites"]:
        for svc in site["services"]:
            if svc.get("name"):
                svc_map[svc["name"]] = (site, svc)
    cards = []
    for r in summary["svc_rows"]:
        full = {}
        hit = svc_map.get(r.get("service"))
        if hit:
            _, svc = hit
            full = {"name": svc.get("name"), "description": svc.get("description"),
                    "labels": svc.get("labels"), "upstream": svc.get("upstream"),
                    "routes": svc.get("routes")}
        cards.append({
            "zone": r.get("zone_cn", ""), "site": r.get("site", ""), "service": r.get("service"),
            "hosts": r.get("hosts"), "backend": r.get("backend"), "type": r.get("site_type"),
            "auth": r.get("auth"), "ip": r.get("ip"), "ports": r.get("ports"),
            "owner": r.get("owner"), "ws": r.get("ws"), "live": r.get("_live", ""),
            "detail": yaml_block(full) if full else "",
        })
    payload = {
        "generated_at": data["generated_at"],
        "live_note": live_note,
        "summary": {k: v for k, v in summary.items() if k != "svc_rows"},
        "cards": cards,
    }
    data_json = json.dumps(payload, ensure_ascii=False)

    html = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>配置总览（APISIX / ADC）</title>
<style>
  body { font-family: "Microsoft YaHei", "Segoe UI", sans-serif; margin: 0; background: #f5f6f8; color: #222; }
  header { background: #1f2937; color: #fff; padding: 16px 24px; position: sticky; top: 0; z-index: 10; }
  header h1 { margin: 0 0 8px; font-size: 18px; }
  #q { width: 100%; max-width: 720px; padding: 10px 14px; font-size: 14px; border-radius: 6px; border: none; box-sizing: border-box; }
  .meta { font-size: 12px; color: #9ca3af; margin-top: 6px; }
  .stats { display: flex; flex-wrap: wrap; gap: 12px; padding: 16px 24px 0; }
  .stat { background: #fff; border-radius: 8px; padding: 10px 16px; box-shadow: 0 1px 3px rgba(0,0,0,.08); font-size: 13px; }
  .stat b { font-size: 20px; display: block; }
  main { padding: 16px 24px 48px; }
  table { width: 100%; border-collapse: collapse; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,.08); border-radius: 8px; overflow: hidden; font-size: 13px; }
  th, td { padding: 8px 10px; border-bottom: 1px solid #eceef1; text-align: left; vertical-align: top; }
  th { background: #f0f2f5; position: sticky; top: 96px; }
  tr.row { cursor: pointer; }
  tr.row:hover { background: #f8fafc; }
  tr.detail td { background: #fafbfc; padding: 0; }
  tr.detail pre { margin: 0; padding: 14px 16px; white-space: pre-wrap; font-size: 12px; line-height: 1.5; }
  .tag { display: inline-block; padding: 1px 8px; border-radius: 10px; font-size: 11px; margin-right: 4px; }
  .z-intranet { background: #dbeafe; color: #1d4ed8; }
  .z-extranet { background: #fef3c7; color: #b45309; }
  .z-public { background: #dcfce7; color: #15803d; }
  .live-ok { color: #15803d; } .live-pending { color: #b45309; } .live-unknown { color: #6b7280; }
  .empty { padding: 40px; text-align: center; color: #6b7280; display: none; }
  @media (max-width: 900px) { th, td { font-size: 12px; } }
</style>
</head>
<body>
<header>
  <h1>配置总览 · APISIX / ADC</h1>
  <input id="q" type="text" placeholder="搜索：域名 / service / 后端 / 负责人 / 认证 / 端口 / 白名单…（支持多个关键词，空格分隔）">
  <div class="meta" id="meta"></div>
</header>
<div class="stats" id="stats"></div>
<main>
  <table id="tbl">
    <thead><tr>
      <th>网络区</th><th>站点</th><th>service</th><th>域名</th><th>后端</th><th>类型</th>
      <th>认证</th><th>IP 白名单</th><th>端口匹配</th><th>负责人</th><th>生效</th>
    </tr></thead>
    <tbody id="body"></tbody>
  </table>
  <div class="empty" id="empty">没有匹配的配置。</div>
</main>
<script>
const DATA = __DATA__;
const zclass = { "内网":"z-intranet", "外网":"z-extranet", "公网":"z-public" };
function liveHtml(l){ if(!l) return ""; const c = l.includes("已生效")?"live-ok":(l.includes("待同步")?"live-pending":"live-unknown"); return `<span class="${c}">${l}</span>`; }
function cardText(c){
  return [c.zone,c.site,c.service,c.hosts,c.backend,c.type,c.auth,c.ip,c.ports,c.owner,c.live,"sites/"+c.site].join(" ");
}
function render(filter){
  const f = (filter||"").toLowerCase().split(/\s+/).filter(Boolean);
  const rows = document.querySelectorAll("#body tr.row");
  let shown = 0;
  rows.forEach(r => {
    const ok = f.every(k => cardText(r._c).toLowerCase().includes(k));
    r.style.display = ok ? "" : "none";
    if (ok) shown++;
  });
  document.getElementById("empty").style.display = shown ? "none" : "";
}
function build(){
  const tbody = document.getElementById("body");
  tbody.innerHTML = "";
  DATA.cards.forEach(c => {
    const tr = document.createElement("tr");
    tr.className = "row"; tr._c = c;
    tr.innerHTML = `
      <td><span class="tag ${zclass[c.zone]||''}">${c.zone}</span></td>
      <td>${c.site}</td><td>${c.service}</td><td>${c.hosts}</td><td>${c.backend}</td>
      <td>${c.type}</td><td>${c.auth}</td><td>${c.ip}</td><td>${c.ports}</td>
      <td>${c.owner}</td><td>${liveHtml(c.live)}</td>`;
    tbody.appendChild(tr);
    // 折叠详情：该 service 的完整配置
    const dt = document.createElement("tr");
    dt.className = "detail"; dt.style.display = "none";
    const pre = document.createElement("pre");
    pre.textContent = cardDetail(c);
    const td = document.createElement("td"); td.colSpan = 11; td.appendChild(pre);
    dt.appendChild(td); tbody.appendChild(dt);
    tr.addEventListener("click", () => { dt.style.display = dt.style.display === "none" ? "" : "none"; });
  });
}
function cardDetail(c){
  return c.detail ? c.detail :
    "【网络区】" + c.zone + "\n【站点】" + c.site + "  sites/" + c.site + "\n" +
    "【service】" + c.service + "\n【域名】" + c.hosts + "\n【后端】" + c.backend +
    "\n【类型】" + c.type + "\n【认证】" + c.auth + "\n【IP 白名单】" + c.ip +
    "\n【端口匹配】" + c.ports + "\n【WebSocket】" + c.ws + "\n【负责人】" + c.owner +
    "\n【生效】" + (c.live || "—") + "\n\n（完整配置见 INVENTORY.md 站点明细 / 原始 YAML）";
}
function init(){
  document.getElementById("q").addEventListener("input", e => render(e.target.value));
  const s = DATA.summary || {};
  document.getElementById("meta").textContent =
    "生成时间：" + DATA.generated_at + (DATA.live_note ? " ｜ " + DATA.live_note : "");
  const st = document.getElementById("stats");
  st.innerHTML = [
    ["站点", s.n_sites], ["service", s.n_services], ["route", s.n_routes],
    ["内网", (s.zone_count||{}).intranet], ["外网", (s.zone_count||{}).extranet], ["公网", (s.zone_count||{}).public],
  ].map(([k,v]) => `<div class="stat"><b>${v ?? "—"}</b>${k}</div>`).join("");
  build(); render("");
}
init();
</script>
</body>
</html>"""
    return html.replace("__DATA__", data_json)


# ---------------------------------------------------------------------------
# 终端搜索
# ---------------------------------------------------------------------------

def search(data, kw):
    kwl = kw.lower()
    hits = []
    for site in data["sites"]:
        for svc in site["services"]:
            blob = {
                "zone": site["zone_cn"], "site": site["site"], "service": svc.get("name"),
                "description": svc.get("description"), "labels": svc.get("labels"),
                "upstream": svc.get("upstream"), "routes": svc.get("routes"),
            }
            text = json.dumps(blob, ensure_ascii=False).lower()
            if kwl in text:
                hits.append((site["zone_cn"], site["site"], blob))
    for c in data["global"]["consumers"]:
        if kwl in json.dumps(c, ensure_ascii=False).lower():
            hits.append(("global", "", {"consumer": c}))
    for s in data["global"]["ssls"]:
        if kwl in json.dumps(s, ensure_ascii=False).lower():
            hits.append(("global", "", {"ssl": s}))
    return hits


def print_hits(hits, kw):
    if not hits:
        print(f"未找到匹配“{kw}”的配置")
        return
    print(f"命中 {len(hits)} 处（关键词：{kw}）：\n")
    for zone, site, blob in hits:
        if "service" in blob:
            print(f"▶ [{zone}] {site} :: service {blob['service']}")
            print(f"  描述：{blob.get('description') or '—'}")
            labels = blob.get("labels") or {}
            print(f"  labels：{json.dumps(labels, ensure_ascii=False)}")
            if blob.get("upstream"):
                print(f"  upstream：{yaml_block(blob['upstream'], indent=2)}")
            for rt in blob.get("routes") or []:
                print(f"  route {rt.get('name')}: hosts={rt.get('hosts')} uris={rt.get('uris')} "
                      f"vars={vars_summary(rt)} plugins={list((rt.get('plugins') or {}).keys())}")
        elif "consumer" in blob:
            print(f"▶ [global] consumer {blob['consumer'].get('username')}")
            print(yaml_block(blob["consumer"], indent=2))
        elif "ssl" in blob:
            print(f"▶ [global] ssl snis={blob['ssl'].get('snis')}")
        print()


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description="生成配置总览（一份文件看清全部当前配置，可搜索）")
    ap.add_argument("--html", action="store_true", help="额外生成 INVENTORY.html 可搜索面板")
    ap.add_argument("--live", action="store_true", help="用 adc dump 比对网关，标注生效状态（需网关可达）")
    ap.add_argument("--no-file", action="store_true", help="只打印不写文件")
    ap.add_argument("--query", metavar="关键词", help="搜索配置并打印命中片段（不生成文件）")
    ap.add_argument("--json", action="store_true", help="输出结构化 JSON")
    args = ap.parse_args(argv)

    data = collect_all()
    summary = compute_summary(data)
    live_note = None
    if args.live:
        data, live_note = annotate_live(data)
        if live_note:
            live_note = "⚠️ " + live_note if live_note.startswith("adc dump") else live_note
        summary = compute_summary(data)

    if args.query:
        print_hits(search(data, args.query), args.query)
        return 0

    if args.json:
        print(json.dumps({"generated_at": data["generated_at"], "summary": {k: v for k, v in summary.items() if k != "svc_rows"},
                          "svc_rows": summary["svc_rows"], "sites": data["sites"], "global": data["global"]},
                         ensure_ascii=False, indent=2))
        return 0

    md = render_markdown(data, summary, live_note)
    if not args.no_file:
        OUT_MD.parent.mkdir(parents=True, exist_ok=True)
        OUT_MD.write_text(md, encoding="utf-8")
        print(f"已写入 {OUT_MD.relative_to(ROOT)}")
        if args.html:
            OUT_HTML.write_text(render_html(data, summary, live_note), encoding="utf-8")
            print(f"已写入 {OUT_HTML.relative_to(ROOT)}（浏览器打开，搜索框即时过滤）")
    print(f"\n总览：{summary['n_sites']} 站点 / {summary['n_services']} service / {summary['n_routes']} route"
          f"（内网 {summary['zone_count'].get('intranet', 0)} / 外网 {summary['zone_count'].get('extranet', 0)}"
          f" / 公网 {summary['zone_count'].get('public', 0)}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
