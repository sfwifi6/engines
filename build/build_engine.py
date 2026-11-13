#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 Termux 官方源构建 APP 引擎包。

用法：
    python3 build_engine.py <引擎名>           # 构建单个
    python3 build_engine.py <引擎名> --list    # 只列依赖不下载

产物：
    <引擎名>-engine.tar.gz   （APP 直接安装的包）
    <引擎名>-info.json       （大小 / md5 / 包列表）

包内结构（APP 约定）：
    ./manifest.json
    ./data/data/com.termux/files/usr/bin/...
    ./data/data/com.termux/files/usr/lib/...
"""
import os
import sys
import json
import re
import time
import hashlib
import subprocess
import urllib.request
from concurrent.futures import ThreadPoolExecutor

MIRROR = os.environ.get('TERMUX_MIRROR',
                        'https://mirrors.tuna.tsinghua.edu.cn/termux/apt/termux-main')
ARCH = os.environ.get('TERMUX_ARCH', 'aarch64')
PREFIX = '/data/data/com.termux/files/usr'
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36'

# 这些是 Termux 运行环境专属，APP 里没有对应 socket，装了也没用还会让依赖树膨胀
SKIP = {'termux-am', 'termux-am-socket', 'termux-exec',
        'termux-keyring', 'dpkg', 'apt', 'libapt-pkg-perl'}

WORK = 'work'
CACHE = 'cache'


def log(*a):
    print(*a, flush=True)


def fetch(url, dest, retries=6, quiet=False):
    """带重试的下载"""
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return True
    os.makedirs(os.path.dirname(dest) or '.', exist_ok=True)
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=180) as r:
                tmp = dest + '.part'
                with open(tmp, 'wb') as f:
                    while True:
                        chunk = r.read(1 << 20)
                        if not chunk:
                            break
                        f.write(chunk)
                os.replace(tmp, dest)
            return True
        except Exception as e:
            if not quiet:
                log(f'   重试 {i+1}/{retries}  {os.path.basename(dest)}  {e}')
            time.sleep(3 + i * 2)
    return False


def load_index():
    path = os.path.join(CACHE, 'Packages')
    os.makedirs(CACHE, exist_ok=True)
    if not (os.path.exists(path) and os.path.getsize(path) > 100000):
        url = f'{MIRROR}/dists/stable/main/binary-{ARCH}/Packages'
        log(f'拉取索引 {url}')
        if not fetch(url, path):
            sys.exit('索引下载失败')
    txt = open(path, encoding='utf-8', errors='replace').read()
    idx = {}
    for block in txt.split('\n\n'):
        if not block.strip():
            continue
        d = {}
        for line in block.split('\n'):
            if ':' in line and not line.startswith(' '):
                k, v = line.split(':', 1)
                d[k.strip()] = v.strip()
        if 'Package' in d:
            idx[d['Package']] = d
    log(f'索引包数 {len(idx)}')
    return idx


def parse_depends(s):
    """Depends 字段 → 包名列表（多选取第一个，去掉版本约束）"""
    if not s:
        return []
    out = []
    for item in s.split(','):
        item = item.strip()
        if not item:
            continue
        first = item.split('|')[0].strip()
        name = re.sub(r'\s*\(.*?\)', '', first).strip()
        if name:
            out.append(name)
    return out


def resolve(top, idx):
    """递归解析依赖"""
    seen, order, queue, missing = set(), [], list(top), []
    while queue:
        p = queue.pop(0)
        if p in seen or p in SKIP:
            continue
        seen.add(p)
        e = idx.get(p)
        if not e:
            missing.append(p)
            continue
        order.append(p)
        for d in parse_depends(e.get('Depends', '')):
            if d not in seen and d not in SKIP:
                queue.append(d)
    return order, missing


def download_debs(pkgs, idx):
    """并发下载所有 .deb"""
    os.makedirs(CACHE, exist_ok=True)
    jobs = []
    for p in pkgs:
        e = idx[p]
        fn = e.get('Filename')
        if not fn:
            log(f'   {p} 无 Filename 字段，跳过')
            continue
        dest = os.path.join(CACHE, os.path.basename(fn))
        jobs.append((p, f'{MIRROR}/{fn}', dest))

    log(f'需要下载 {len(jobs)} 个 deb')

    def one(j):
        p, url, dest = j
        ok = fetch(url, dest, quiet=True)
        return p, ok, os.path.getsize(dest) if ok and os.path.exists(dest) else 0

    total = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        for i, (p, ok, sz) in enumerate(ex.map(one, jobs), 1):
            if ok:
                total += sz
                if i % 10 == 0 or i == len(jobs):
                    log(f'   {i}/{len(jobs)}  累计 {total/1048576:.1f}MB')
            else:
                log(f'   ✗ 下载失败 {p}')
    return total


def unpack(pkgs, idx):
    """dpkg-deb -x 解压到 work/"""
    if os.path.exists(WORK):
        subprocess.run(['rm', '-rf', WORK], check=False)
    os.makedirs(WORK, exist_ok=True)
    ok, fail = 0, []
    for p in pkgs:
        fn = idx[p].get('Filename')
        if not fn:
            continue
        deb = os.path.join(CACHE, os.path.basename(fn))
        if not os.path.exists(deb):
            fail.append(p)
            continue
        r = subprocess.run(['dpkg-deb', '-x', deb, WORK],
                           capture_output=True, text=True)
        if r.returncode == 0:
            ok += 1
        else:
            fail.append(p)
            log(f'   解包失败 {p}: {r.stderr[:120]}')
    log(f'解包成功 {ok}，失败 {len(fail)}')
    return ok, fail


def slim():
    """删掉文档和 man，明显减体积"""
    root = os.path.join(WORK, 'data/data/com.termux/files/usr')
    saved = 0
    for sub in ('share/man', 'share/doc', 'share/info', 'share/gtk-doc', 'share/locale'):
        d = os.path.join(root, sub)
        if os.path.isdir(d):
            for dp, _, fns in os.walk(d):
                for f in fns:
                    try:
                        saved += os.path.getsize(os.path.join(dp, f))
                    except OSError:
                        pass
            subprocess.run(['rm', '-rf', d], check=False)
    log(f'清理文档 {saved/1048576:.1f}MB')


def make_manifest(name, cfg, pkgs, idx):
    ver = idx[cfg['pkgs'][0]].get('Version', '1.0') if cfg['pkgs'] else '1.0'
    ver = re.sub(r'^\d+:', '', ver)
    m = {
        'name': name,
        'version': f'{ver}-eng1',
        'bin': cfg.get('bin', ''),
        'desc': cfg.get('desc', ''),
        'prefix': PREFIX,
        'built': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'packages': pkgs,
    }
    p = os.path.join(WORK, 'manifest.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    return m


def pack(name):
    out = f'{name}-engine.tar.gz'
    if os.path.exists(out):
        os.remove(out)
    cmd = ['tar', '-czf', out, '--owner=0', '--group=0', '--numeric-owner',
           '-C', WORK, './manifest.json', './data']
    log('打包 ' + ' '.join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        log(r.stderr[:500])
        sys.exit('tar 打包失败')
    return out


def md5sum(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def main():
    if len(sys.argv) < 2:
        sys.exit('用法: python3 build_engine.py <引擎名>')
    name = sys.argv[1]

    cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'engines.json')
    allcfg = json.load(open(cfg_path, encoding='utf-8'))['engines']
    if name not in allcfg:
        sys.exit(f'未知引擎 {name}，可选：{", ".join(allcfg)}')
    cfg = allcfg[name]

    log('=' * 60)
    log(f'构建引擎 {name}  —  {cfg.get("desc","")}')
    log('=' * 60)

    idx = load_index()
    pkgs, missing = resolve(cfg['pkgs'], idx)
    if missing:
        log(f'⚠ 缺失包（已跳过）：{missing}')
    log(f'依赖解析完成，共 {len(pkgs)} 个包')

    if '--list' in sys.argv:
        for p in pkgs:
            log(f'   {p:28s} {idx[p].get("Installed-Size","?"):>9s}KB')
        return

    total = download_debs(pkgs, idx)
    log(f'下载完成 {total/1048576:.1f}MB')

    ok, fail = unpack(pkgs, idx)
    if ok == 0:
        sys.exit('全部解包失败')

    slim()

    usr = os.path.join(WORK, 'data/data/com.termux/files/usr')
    if not os.path.isdir(usr):
        sys.exit(f'解包后找不到 prefix 目录 {usr}')

    man = make_manifest(name, cfg, pkgs, idx)
    out = pack(name)

    size = os.path.getsize(out)
    md5 = md5sum(out)
    info = {
        'name': name,
        'file': out,
        'size': size,
        'md5': md5,
        'version': man['version'],
        'desc': man['desc'],
        'bin': man['bin'],
        'packages': pkgs,
        'failed': fail,
    }
    with open(f'{name}-info.json', 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=1)

    log('')
    log(f'✓ {out}')
    log(f'  大小 {size} 字节 ({size/1048576:.1f}MB)')
    log(f'  MD5  {md5}')
    log(f'  版本 {man["version"]}')


if __name__ == '__main__':
    main()
