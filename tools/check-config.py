#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置检查工具（check-config.py）—— 补 adc lint 查不出的仓库语义错误。

背景：scripts/sync.ps1 只做 lint → diff → sync，lint 通过不代表 sync 推送一定成功。
本工具在 lint 之上做「仓库规范语义检查」，可选 --backend 追加 adc validate（后端真实校验），
把「推送时才炸」的错误提前到提交前拦下来。

用法：
    python tools/check-config.py                 # 只做静态语义检查（不联网）
    python tools/check-config.py --backend       # 追加 adc validate（后端校验，需网关可达）
    python tools/check-config.py --lint          # 先跑 adc lint 再静态检查
    python tools/check-config.py --skip-env      # 跳过 ${ENV} 环境变量存在性检查（CI 等场景）
    python tools/check-config.py --json          # 输出 JSON（机器可读）

退出码：0 = 通过；1 = 发现错误；2 = 工具自身/输入错误。
覆盖范围：configs/global/** 与 configs/sites/**（与 sync 作用域一致；_templates 天然排除）。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_GLOBAL = ROOT / "configs" / "global"
CONFIG_SITES = ROOT / "configs" / "sites"
ADC_EXE = ROOT / ".bin" / "adc" / "adc.exe"  # Windows 便携二进制；Linux/macOS 下用 --adc 指定

VALID_ZONES = {"intranet", "extranet", "public", "shared"}
VALID_SITE_TYPES = {"www", "api", "ws", "static", "admin", "partner", "internal"}
VALID_ENVS = {"prod", "staging", "dev"}
REQUIRED_LABELS = ("site", "zone", "site_type", "env", "owner")

INTRANET_PP_PORTS = {"9181", "9182"}   # 内网 PP 端口（HTTP/HTTPS + PROXY protocol）
NORMAL_PORTS = {"80", "443"}           # 外网/公网标准监听口（不走 PP）

SKIP_LABEL = "x-check-skip"            # 资源级豁免标签：值 = 逗号分隔的 rule_id 列表，或 "all"
PLACEHOLDER_RE = re.compile(r"<\s*[a-zA-Z][a-zA-Z0-9_.\-/]*\s*>")
ENV_REF_RE = re.compile(r"(?<!\\)\$\{([A-Za-z_][A-Za-z0-9_]*)\}")   # ${ENV}（ADC 侧解析）；\${} 是 nginx 内置变量，跳过
DP_ENV_RE = re.compile(r"\$env://([A-Za-z_][A-Za-z0-9_]*)")          # $env://（数据面解析，本地无法校验，仅提示）

SEV_ERROR, SEV_WARN = "ERROR", "WARN"


def eprint(*a, **kw):
    print(*a, file=sys.stderr, **kw)


# ---------------------------------------------------------------------------
# 收集
# ---------------------------------------------------------------------------

def find_config_files():
    """与 sync 作用域一致：configs/global/** 与 configs/sites/** 下所有 yaml（_templates 天然在外）。"""
    files = []
    for base in (CONFIG_GLOBAL, CONFIG_SITES):
        if base.is_dir():
            files.extend(sorted(base.rglob("*.yaml")))
    return files


def load_yaml(path: Path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as exc:
        return exc  # 由调用方上报


def zone_of_file(path: Path):
    """文件位于 sites/<zone>/<site>/... 时返回 zone，否则 None（global/ 下返回 'global'）。"""
    rel = path.relative_to(ROOT).as_posix()
    if rel.startswith("configs/sites/"):
        parts = rel.split("/")
        if len(parts) >= 3:
            return parts[2]
        return None  # 直接挂在 sites/ 下的文件（不合规，由 E3 上报）
    return "global"


class Resource:
    def __init__(self, kind, name, data, path, zone, service_name=None):
        self.kind = kind          # service / route / consumer / credential / ssl / consumer_group
        self.name = name
        self.data = data
        self.path = path
        self.zone = zone          # intranet/extranet/public/shared/global/None
        self.service_name = service_name
        self.labels = (data or {}).get("labels") or {}
        self.skips = set()
        raw = self.labels.get(SKIP_LABEL)
        if raw:
            if str(raw).strip().lower() == "all":
                self.skips = {"all"}
            else:
                self.skips = {x.strip() for x in str(raw).split(",") if x.strip()}

    def skip(self, rule_id):
        return "all" in self.skips or rule_id in self.skips


def collect(path: Path):
    """解析单个文件，产出资源对象列表与原始文本。"""
    raw_text = path.read_text(encoding="utf-8")
    obj = load_yaml(path)
    if isinstance(obj, yaml.YAMLError):
        return [], raw_text, obj
    if obj is None:
        return [], raw_text, None
    zone = zone_of_file(path)
    out = []
    for svc in obj.get("services") or []:
        svc_res = Resource("service", svc.get("name"), svc, path, zone)
        out.append(svc_res)
        svc_name = svc.get("name")
        for rt in svc.get("routes") or []:
            rt_res = Resource("route", rt.get("name"), rt, path, zone, service_name=svc_name)
            rt_res.skips.update(svc_res.skips)   # route 继承 service 级 x-check-skip 豁免
            out.append(rt_res)
    for grp in obj.get("consumer_groups") or []:
        out.append(Resource("consumer_group", grp.get("name"), grp, path, zone))
    for c in obj.get("consumers") or []:
        out.append(Resource("consumer", c.get("username"), c, path, zone))
        cname = c.get("username")
        for cred in c.get("credentials") or []:
            out.append(Resource("credential", cred.get("name"), cred, path, zone, service_name=cname))
    for s in obj.get("ssls") or []:
        snis = s.get("snis") or []
        out.append(Resource("ssl", ",".join(snis), s, path, zone))
    return out, raw_text, None


# ---------------------------------------------------------------------------
# 检查器
# ---------------------------------------------------------------------------

class Reporter:
    def __init__(self):
        self.items = []  # (severity, rule_id, file, message)

    def error(self, rule, file, msg):
        self.items.append((SEV_ERROR, rule, file, msg))

    def warn(self, rule, file, msg):
        self.items.append((SEV_WARN, rule, file, msg))

    @property
    def errors(self):
        return [i for i in self.items if i[0] == SEV_ERROR]

    @property
    def warnings(self):
        return [i for i in self.items if i[0] == SEV_WARN]


def check_e1_name_uniqueness(res, rep: Reporter):
    """资源名全局唯一（ID = sha1(name)，重名 = 删旧建新/静默覆盖）。"""
    seen_service, seen_consumer, seen_group, seen_route, seen_cred, seen_snis = {}, {}, {}, {}, {}, {}
    for r in res:
        if r.name is None:
            rep.warn("e1", r.path, f"{r.kind} 缺少 name/username，无法校验唯一性")
            continue
        if r.kind == "service":
            if r.name in seen_service:
                rep.error("e1", r.path, f"service.name 重复：{r.name!r}（另见 {seen_service[r.name]}）→ 资源 ID 冲突")
            seen_service[r.name] = r.path
        elif r.kind == "consumer":
            if r.name in seen_consumer:
                rep.error("e1", r.path, f"consumer.username 重复：{r.name!r}（另见 {seen_consumer[r.name]}）")
            seen_consumer[r.name] = r.path
        elif r.kind == "consumer_group":
            if r.name in seen_group:
                rep.error("e1", r.path, f"consumer_group.name 重复：{r.name!r}（另见 {seen_group[r.name]}）")
            seen_group[r.name] = r.path
        elif r.kind == "route":
            key = (r.service_name, r.name)
            if key in seen_route:
                rep.error("e1", r.path, f"route.name 在同一 service 内重复：service={r.service_name!r} route={r.name!r}（另见 {seen_route[key]}）")
            seen_route[key] = r.path
        elif r.kind == "credential":
            key = (r.service_name, r.name)
            if key in seen_cred:
                rep.error("e1", r.path, f"credential.name 在同一 consumer 内重复：consumer={r.service_name!r} credential={r.name!r}")
            seen_cred[key] = r.path
        elif r.kind == "ssl":
            if r.name in seen_snis:
                rep.error("e1", r.path, f"ssl snis 组合重复：{r.name!r}（另见 {seen_snis[r.name]}）→ 证书 ID 冲突")
            seen_snis[r.name] = r.path


def check_e2_placeholders(path, raw_text, rep: Reporter):
    """真实配置不得出现 <...> 模板占位符（只有 _templates 允许）。"""
    for m in PLACEHOLDER_RE.finditer(raw_text):
        rep.error("e2", path, f"发现模板占位符 {m.group(0)!r}——真实配置禁止占位符，请替换为实际值")


def check_zone_consistency(res, rep: Reporter):
    """zone 标签合法、与目录一致；sites/ 下必须按网络区分目录。"""
    for r in res:
        zone = r.labels.get("zone")
        # 目录必须是合法网络区
        if r.path.is_relative_to(CONFIG_SITES):
            if r.zone not in VALID_ZONES or r.zone == "shared":
                rep.error("e3", r.path, f"站点文件必须位于 configs/sites/<intranet|extranet|public>/ 下（当前目录 zone={r.zone!r}）")
                continue
            if r.kind in ("service", "consumer", "ssl") and zone and zone != r.zone:
                rep.error("e3", r.path, f"labels.zone={zone!r} 与目录 zone={r.zone!r} 不一致——内网/外网/公网配置禁止混放")
        # 标签值合法性
        if zone is not None and zone not in VALID_ZONES:
            rep.error("e4", r.path, f"labels.zone 非法：{zone!r}（合法：{sorted(VALID_ZONES)}）")


def check_labels_complete(res, rep: Reporter):
    for r in res:
        if r.kind in ("route", "credential", "consumer_group"):
            continue  # 这些层级不打 labels（约定）
        for lb in REQUIRED_LABELS:
            if not r.labels.get(lb):
                rep.error("e10", r.path, f"{r.kind} {r.name!r} 缺少必填标签 labels.{lb}")
        st = r.labels.get("site_type")
        if st and st not in VALID_SITE_TYPES:
            rep.warn("w2", r.path, f"{r.kind} {r.name!r} 的 site_type={st!r} 不在约定枚举 {sorted(VALID_SITE_TYPES)} 内")
        ev = r.labels.get("env")
        if ev and ev not in VALID_ENVS:
            rep.warn("w2", r.path, f"{r.kind} {r.name!r} 的 env={ev!r} 不在约定枚举 {sorted(VALID_ENVS)} 内")
        if not r.labels.get("contact"):
            rep.warn("w1", r.path, f"{r.kind} {r.name!r} 缺少建议标签 labels.contact（找不到负责人）")


def vars_conditions(route_data):
    """把 route.vars 展平成 [(var, op, value), ...]。"""
    out = []
    for cond in route_data.get("vars") or []:
        if isinstance(cond, list) and len(cond) >= 3:
            out.append((str(cond[0]), str(cond[1]), cond[2]))
    return out


def check_e9_vars_types(route, rep: Reporter):
    """nginx 变量都是字符串；`in` 严格比较，数字列表永不匹配（9181 vs "9181" 的老坑）。"""
    for var, op, val in vars_conditions(route.data):
        if op == "in":
            if not isinstance(val, list):
                rep.error("e9", route.path, f"route {route.name!r} 的 vars: {var} {op} 右侧必须是列表")
                continue
            for item in val:
                if not isinstance(item, str):
                    rep.error("e9", route.path,
                              f"route {route.name!r} 的 vars: {var} {op} 列表元素 {item!r} 是 {type(item).__name__}，"
                              f"应为字符串（nginx 变量是字符串，`in` 严格比较，数字永不匹配）")
        elif op in ("==", "!=", ">", ">=", "<", "<="):
            pass  # 标量比较类型多样，不做强制


def route_ports(route):
    """返回该路由命中的端口集合与匹配方式（server_port / proxy_protocol_server_port）。"""
    ports, mode = set(), None
    for var, op, val in vars_conditions(route.data):
        if var in ("server_port", "proxy_protocol_server_port"):
            mode = var
            vals = val if isinstance(val, list) else [val]
            ports.update(str(v) for v in vals)
    return ports, mode


def check_zone_rules(res, rep: Reporter):
    """内网强制 PP+IP 白名单；外网/公网禁止使用内网 PP 端口。"""
    for r in res:
        if r.kind != "route" or r.zone not in VALID_ZONES:
            continue
        zone = r.labels.get("zone") or r.zone
        ports, mode = route_ports(r)
        plugins = r.data.get("plugins") or {}

        if zone == "intranet":
            # E5：必须走 PP（server_port∈[9181,9182]，或按 PROXY 目标端口匹配）
            pp_ok = (mode == "server_port" and ports & INTRANET_PP_PORTS) or mode == "proxy_protocol_server_port"
            if not r.skip("intranet-pp") and not pp_ok:
                rep.error("e5", r.path, f"内网 route {r.name!r} 必须走 PROXY protocol："
                                        f"vars 需含 server_port∈[9181,9182] 或 proxy_protocol_server_port（当前: {ports or '无'}）")
            # E6：必须 real-ip（从 PROXY 头取真实 IP）
            realip = plugins.get("real-ip")
            if not r.skip("intranet-realip") and not realip:
                rep.error("e6", r.path, f"内网 route {r.name!r} 必须带 real-ip 插件（PROXY protocol 取真实客户端 IP）")
            elif realip and realip.get("source") != "proxy_protocol_addr":
                rep.warn("w3", r.path, f"内网 route {r.name!r} 的 real-ip.source={realip.get('source')!r}，"
                                       f"约定为 proxy_protocol_addr（走 PP 才拿得到真实 IP）")
            # E7：必须 ip-restriction 白名单（不允许留空）
            ipr = plugins.get("ip-restriction")
            wl = (ipr or {}).get("whitelist") or []
            if not r.skip("intranet-ip") and (not ipr or not wl):
                rep.error("e7", r.path, f"内网 route {r.name!r} 必须带 ip-restriction 白名单（不允许留空）")
            # W4：端口与约定不符
            if mode == "server_port" and ports and not (ports & INTRANET_PP_PORTS):
                rep.warn("w4", r.path, f"内网 route {r.name!r} 的 server_port={sorted(ports)} 不在约定内网 PP 端口 9181/9182")
        else:  # extranet / public
            # E8：禁止引用内网 PP 端口（内网/外网隔离）
            if ports & INTRANET_PP_PORTS:
                rep.error("e8", r.path, f"外网/公网 route {r.name!r} 的端口匹配包含内网 PP 端口 {sorted(ports & INTRANET_PP_PORTS)}——"
                                        f"内网/外网配置禁止混用")
            # W4：外网/公网约定标准端口 80/443
            if mode == "server_port" and ports and ports != NORMAL_PORTS:
                rep.warn("w4", r.path, f"外网/公网 route {r.name!r} 的 server_port={sorted(ports)} 与约定 80/443 不一致")
            # W3：外网/公网不该有 real-ip（不走 PP）
            if plugins.get("real-ip"):
                rep.warn("w3", r.path, f"外网/公网 route {r.name!r} 带 real-ip 插件——外网/公网不走 PP，"
                                       f"real-ip 取不到真实 IP（若前置确有 PROXY 转发则忽略本提示）")


def check_env_refs(path, raw_text, rep: Reporter, skip_env: bool, env_defs: set):
    for m in ENV_REF_RE.finditer(raw_text):
        name = m.group(1)
        if not skip_env and name not in os.environ and name not in env_defs:
            rep.error("e11", path, f"${'{'}{name}{'}'} 引用的环境变量未定义（本机 os.environ / .env 均无）——sync 加载时会失败")
    for m in DP_ENV_RE.finditer(raw_text):
        rep.warn("w5", path, f"$env://{m.group(1)} 为数据面变量，本地无法校验——请确认网关节点已配置该环境变量")


def load_dotenv(rep: Reporter) -> set:
    """读取 .env（KEY=VALUE），用于 ${ENV} 存在性判定；不回显任何值。"""
    names = set()
    dotenv = ROOT / ".env"
    if not dotenv.exists():
        return names
    try:
        for line in dotenv.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key = line.split("=", 1)[0].strip()
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
                names.add(key)
    except OSError as exc:
        rep.warn("w5", dotenv, f"读取 .env 失败（{exc}），跳过 env 存在性判定")
    return names


# ---------------------------------------------------------------------------
# adc 子命令（--lint / --backend）
# ---------------------------------------------------------------------------

def adc_command(adc_path):
    if adc_path:
        return [str(Path(adc_path).resolve())]
    if os.name == "nt" and ADC_EXE.exists():
        return [str(ADC_EXE)]
    return ["adc"]  # 回退到 PATH


def run_adc(adc_path, args):
    cmd = adc_command(adc_path) + args
    print(f"\n[adc] {' '.join(cmd)}", flush=True)
    proc = subprocess.run(cmd, cwd=str(ROOT))
    return proc.returncode


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description="APISIX/ADC 配置语义检查（补 lint 之不足）")
    ap.add_argument("--backend", action="store_true", help="追加 adc validate（后端真实校验，需网关可达）")
    ap.add_argument("--lint", action="store_true", help="先运行 adc lint")
    ap.add_argument("--skip-env", action="store_true", help="跳过 ${ENV} 存在性检查")
    ap.add_argument("--adc", help="adc 可执行文件路径（默认 .bin/adc/adc.exe 或 PATH）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args(argv)

    rep = Reporter()
    files = find_config_files()
    if not files:
        eprint("未找到配置文件（configs/global、configs/sites 为空？）")
        return 2

    env_defs = load_dotenv(rep)
    resources = []
    load_errors = 0
    for f in files:
        res, raw_text, err = collect(f)
        if err is not None:
            load_errors += 1
            rep.error("e12", f, f"YAML 解析失败：{err}")
            continue
        resources.extend(res)
        check_e2_placeholders(f, raw_text, rep)
        check_env_refs(f, raw_text, rep, args.skip_env, env_defs)

    check_e1_name_uniqueness(resources, rep)
    check_zone_consistency(resources, rep)
    check_labels_complete(resources, rep)
    for r in resources:
        if r.kind == "route":
            check_e9_vars_types(r, rep)
    check_zone_rules(resources, rep)

    # adc 子命令
    if args.lint:
        rc = run_adc(args.adc, ["lint", "-f", "configs/global/**/*.yaml", "-f", "configs/sites/**/*.yaml"])
        if rc != 0:
            eprint("[adc] lint 失败，中止")
            return 1
    if args.backend:
        rc = run_adc(args.adc, ["validate", "-f", "configs/global/**/*.yaml", "-f", "configs/sites/**/*.yaml", "--timeout", "60s"])
        if rc != 0:
            eprint("[adc] validate 失败——后端拒绝了部分配置（lint 查不出的类型），请按上方报错修正")
            return 1

    # 汇总输出
    if args.json:
        print(json.dumps({
            "files": [str(f.relative_to(ROOT)) for f in files],
            "errors": [{"severity": s, "rule": r_, "file": str(f_.relative_to(ROOT)), "message": m} for s, r_, f_, m in rep.errors],
            "warnings": [{"severity": s, "rule": r_, "file": str(f_.relative_to(ROOT)), "message": m} for s, r_, f_, m in rep.warnings],
        }, ensure_ascii=False, indent=2))
    else:
        for sev, rule, fpath, msg in rep.items:
            rel = fpath.relative_to(ROOT) if fpath.is_relative_to(ROOT) else fpath
            tag = "[ERROR]" if sev == SEV_ERROR else "[WARN ]"
            color = "\033[31m" if sev == SEV_ERROR else "\033[33m"
            print(f"{color}{tag}\033[0m {rule:<22} {rel}: {msg}")
        n_e, n_w = len(rep.errors), len(rep.warnings)
        print(f"\n检查完成：{len(files)} 个文件，{n_e} 错误，{n_w} 警告")
        if n_e:
            print("存在错误——请修正后重试（--backend 可提前拦截后端拒绝）")
            return 1
        print("通过（无错误）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
