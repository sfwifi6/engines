#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""做 html / androidapp 两个非 Termux 引擎包"""
import os, sys, json, shutil, subprocess, hashlib, time

PREFIX = '/data/data/com.termux/files/usr'
WORK = 'work'
CACHE = 'cache'
OUT = 'out'

LIBS = [
    # (本地相对路径, 下载地址)
    ('vue/vue.global.prod.js',        'https://cdn.jsdelivr.net/npm/vue@3.5.13/dist/vue.global.prod.js'),
    ('react/react.production.min.js', 'https://cdn.jsdelivr.net/npm/react@18.3.1/umd/react.production.min.js'),
    ('react/react-dom.production.min.js','https://cdn.jsdelivr.net/npm/react-dom@18.3.1/umd/react-dom.production.min.js'),
    ('babel/babel.min.js',            'https://cdn.jsdelivr.net/npm/@babel/standalone@7.26.4/babel.min.js'),
    ('tailwind/tailwind.js',          'https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4/dist/index.global.js'),
    ('codemirror/codemirror.js',      'https://cdn.jsdelivr.net/npm/codemirror@5.65.18/lib/codemirror.js'),
    ('codemirror/codemirror.css',     'https://cdn.jsdelivr.net/npm/codemirror@5.65.18/lib/codemirror.css'),
    ('codemirror/javascript.js',      'https://cdn.jsdelivr.net/npm/codemirror@5.65.18/mode/javascript/javascript.js'),
    ('codemirror/xml.js',             'https://cdn.jsdelivr.net/npm/codemirror@5.65.18/mode/xml/xml.js'),
    ('codemirror/css.js',             'https://cdn.jsdelivr.net/npm/codemirror@5.65.18/mode/css/css.js'),
    ('codemirror/htmlmixed.js',       'https://cdn.jsdelivr.net/npm/codemirror@5.65.18/mode/htmlmixed/htmlmixed.js'),
    ('codemirror/dracula.css',        'https://cdn.jsdelivr.net/npm/codemirror@5.65.18/theme/dracula.css'),
    ('chartjs/chart.umd.js',          'https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.js'),
    ('marked/marked.min.js',          'https://cdn.jsdelivr.net/npm/marked@15.0.4/marked.min.js'),
    ('hljs/highlight.min.js',         'https://cdn.jsdelivr.net/npm/@highlightjs/cdn-assets@11.11.1/highlight.min.js'),
    ('hljs/github-dark.min.css',      'https://cdn.jsdelivr.net/npm/@highlightjs/cdn-assets@11.11.1/styles/github-dark.min.css'),
    ('jquery/jquery.min.js',          'https://cdn.jsdelivr.net/npm/jquery@3.7.1/dist/jquery.min.js'),
    ('alpine/cdn.min.js',             'https://cdn.jsdelivr.net/npm/alpinejs@3.14.8/dist/cdn.min.js'),
    ('axios/axios.min.js',            'https://cdn.jsdelivr.net/npm/axios@1.7.9/dist/axios.min.js'),
    ('dayjs/dayjs.min.js',            'https://cdn.jsdelivr.net/npm/dayjs@1.11.13/dayjs.min.js'),
    ('three/three.min.js',            'https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.min.js'),
    ('mermaid/mermaid.min.js',        'https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js'),
    ('lucide/lucide.min.js',          'https://cdn.jsdelivr.net/npm/lucide@0.469.0/dist/umd/lucide.min.js'),
]

def log(m): print(m, flush=True)

def fetch(url, dest, retries=4):
    if os.path.exists(dest) and os.path.getsize(dest) > 0: return True
    os.makedirs(os.path.dirname(dest) or '.', exist_ok=True)
    tmp = dest + '.part'
    for i in range(retries):
        r = subprocess.run(['curl','-fsSL','--retry','3','--retry-all-errors',
                            '--connect-timeout','20','--max-time','300','-o',tmp,url],
                           capture_output=True, text=True)
        if r.returncode == 0 and os.path.exists(tmp) and os.path.getsize(tmp) > 200:
            os.replace(tmp, dest); return True
        log(f'   重试 {i+1}/{retries} {os.path.basename(dest)} rc={r.returncode}')
        if os.path.exists(tmp): os.remove(tmp)
        time.sleep(2 + i*2)
    return False

MIRROR = os.environ.get('TERMUX_MIRROR', 'https://mirrors.tuna.tsinghua.edu.cn/termux/apt/termux-main')
ARCH = os.environ.get('TERMUX_ARCH', 'aarch64')
_deb_index = None

def deb_filename(pkg):
    """从 Packages 索引里查某个包的 Filename"""
    global _deb_index
    if _deb_index is None:
        os.makedirs(CACHE, exist_ok=True)
        idx = os.path.join(CACHE, 'Packages')
        if not fetch(f'{MIRROR}/dists/stable/main/binary-{ARCH}/Packages', idx):
            log('✗ Packages 索引下载失败'); return None
        _deb_index = {}
        cur = {}
        for line in open(idx, encoding='utf-8', errors='replace'):
            line = line.rstrip('\n')
            if line.startswith('Package: '): cur = {'name': line[9:].strip()}
            elif line.startswith('Filename: ') and cur: cur['file'] = line[10:].strip()
            elif line.startswith('Version: ') and cur: cur['ver'] = line[9:].strip()
            elif not line.strip() and cur:
                if 'name' in cur and 'file' in cur: _deb_index[cur['name']] = cur
                cur = {}
        log(f'索引解析完成，{len(_deb_index)} 个包')
    return _deb_index.get(pkg)

def ensure_deb(pkg):
    """确保 cache 里有这个包的 deb，没有就下"""
    os.makedirs(CACHE, exist_ok=True)
    for f in os.listdir(CACHE):
        if f.startswith(pkg + '_') and f.endswith('.deb'):
            return os.path.join(CACHE, f)
    info = deb_filename(pkg)
    if not info:
        log(f'✗ 索引里找不到 {pkg}'); return None
    dest = os.path.join(CACHE, os.path.basename(info['file']))
    if not fetch(f"{MIRROR}/{info['file']}", dest):
        log(f'✗ 下载 {pkg} 失败'); return None
    return dest

def unpack_proot(usr):
    """从 deb 里解 proot 和它的依赖，保证 APP 自检通过"""
    tmpd = 'proot_tmp'
    shutil.rmtree(tmpd, ignore_errors=True); os.makedirs(tmpd)
    for pkg in ['proot', 'libtalloc', 'libandroid-shmem']:
        p = ensure_deb(pkg)
        if not p:
            log(f'✗ 缺 {pkg} 的 deb'); return False
        log(f'  解包 {os.path.basename(p)}')
        subprocess.run(['dpkg-deb','-x',p,tmpd], check=True)
    # 把 proot_tmp 里的 usr/* 合并进目标 usr
    src = os.path.join(tmpd, 'data/data/com.termux/files/usr')
    for root, dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        dst = os.path.join(usr, rel) if rel != '.' else usr
        os.makedirs(dst, exist_ok=True)
        for f in files:
            s = os.path.join(root, f); t = os.path.join(dst, f)
            if os.path.lexists(t): os.remove(t)
            shutil.copy2(s, t, follow_symlinks=False)
        for d2 in dirs:
            s = os.path.join(root, d2); t = os.path.join(dst, d2)
            if os.path.islink(s):
                if os.path.lexists(t): os.remove(t)
                os.symlink(os.readlink(s), t)
    shutil.rmtree(tmpd, ignore_errors=True)
    proot = os.path.join(usr, 'bin', 'proot')
    if not os.path.exists(proot):
        log('✗ 致命：proot 没解出来'); return False
    os.chmod(proot, 0o700)
    log(f'✓ proot 就位 {os.path.getsize(proot)} 字节')
    return True

def pack(name, usr, version, desc, binpath):
    mf = os.path.join(WORK, 'manifest.json')
    json.dump({'name': name, 'version': version, 'bin': binpath, 'desc': desc, 'prefix': PREFIX},
              open(mf,'w',encoding='utf-8'), ensure_ascii=False, indent=1)
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, f'{name}-engine.tar.gz')
    subprocess.run(['tar','-czf',out,'--owner=0','--group=0','--numeric-owner',
                    '-C',WORK,'./manifest.json','./data'], check=True)
    size = os.path.getsize(out)
    md5 = hashlib.md5(open(out,'rb').read()).hexdigest()
    log(f'\n✓ {name}-engine.tar.gz\n  大小 {size} 字节 ({size/1048576:.1f}MB)\n  MD5  {md5}\n  版本 {version}')
    json.dump({'file':f'{name}-engine.tar.gz','size':size,'md5':md5,'version':version,'desc':desc,'bin':binpath},
              open(os.path.join(OUT,f'{name}-info.json'),'w',encoding='utf-8'), ensure_ascii=False, indent=1)
    return size, md5

# ============ html ============
def build_html():
    log('\n========== html 引擎（前端离线库）==========')
    shutil.rmtree(WORK, ignore_errors=True)
    usr = os.path.join(WORK, 'data/data/com.termux/files/usr')
    libdir = os.path.join(usr, 'share', 'html-libs')
    os.makedirs(libdir, exist_ok=True)
    os.makedirs(os.path.join(usr,'bin'), exist_ok=True)
    if not unpack_proot(usr): return False

    ok, fail = 0, []
    for rel, url in LIBS:
        dest = os.path.join(libdir, rel)
        if fetch(url, dest): ok += 1
        else: fail.append(rel)
    log(f'下载成功 {ok}，失败 {len(fail)}')
    if fail: log('  失败清单: ' + ', '.join(fail))

    # 索引页：告诉用户本地怎么引用
    idx = '''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>前端离线库 · 本地引用手册</title>
<style>body{font:14px/1.7 -apple-system,system-ui,sans-serif;max-width:860px;margin:0 auto;padding:20px;color:#1f2328;background:#fff}
h1{font-size:20px;border-bottom:2px solid #0969da;padding-bottom:8px}
code{background:#f6f8fa;padding:2px 6px;border-radius:5px;font-size:12.5px;color:#cf222e}
pre{background:#0d1117;color:#c9d1d9;padding:12px;border-radius:8px;overflow-x:auto;font-size:12.5px}
pre code{background:none;color:inherit;padding:0}
table{border-collapse:collapse;width:100%;margin:12px 0;font-size:13px}
th,td{border:1px solid #d0d7de;padding:6px 9px;text-align:left}
th{background:#f6f8fa}
</style></head><body>
<h1>前端离线库 · 本地引用手册</h1>
<p>这些库都在你手机的引擎目录里，<b>完全离线</b>，不用联网、不用 CDN。</p>
<p>路径：<code>/data/data/com.shoujibiancheng.app/files/engines/html/data/data/com.termux/files/usr/share/html-libs/</code></p>

<h2>怎么引用</h2>
<p>写网页时用相对路径 <code>../html-libs/xxx</code>，或者直接把库文件复制到你的项目目录里。</p>

<h2>库清单</h2>
<table>
<tr><th>库</th><th>文件</th><th>用法</th></tr>
<tr><td>Vue 3</td><td>vue/vue.global.prod.js</td><td><code>&lt;script src="vue/vue.global.prod.js"&gt;&lt;/script&gt;</code></td></tr>
<tr><td>React 18</td><td>react/react.production.min.js<br>react/react-dom.production.min.js</td><td>两个都要引，再引 babel 就能写 JSX</td></tr>
<tr><td>Babel</td><td>babel/babel.min.js</td><td>浏览器里直接跑 JSX：<code>&lt;script type="text/babel"&gt;</code></td></tr>
<tr><td>Tailwind 4</td><td>tailwind/tailwind.js</td><td><code>&lt;script src="tailwind/tailwind.js"&gt;&lt;/script&gt;</code></td></tr>
<tr><td>CodeMirror 5</td><td>codemirror/codemirror.js + .css</td><td>代码编辑器，带 JS/HTML/CSS 高亮 + Dracula 主题</td></tr>
<tr><td>Chart.js 4</td><td>chartjs/chart.umd.js</td><td>折线、柱状、饼图</td></tr>
<tr><td>marked</td><td>marked/marked.min.js</td><td>Markdown 转 HTML</td></tr>
<tr><td>highlight.js</td><td>hljs/highlight.min.js + .css</td><td>代码高亮</td></tr>
<tr><td>jQuery 3</td><td>jquery/jquery.min.js</td><td>老项目兼容</td></tr>
<tr><td>Alpine.js</td><td>alpine/cdn.min.js</td><td>轻量响应式，写小页面比 Vue 还快</td></tr>
<tr><td>axios</td><td>axios/axios.min.js</td><td>HTTP 请求</td></tr>
<tr><td>dayjs</td><td>dayjs/dayjs.min.js</td><td>日期处理</td></tr>
<tr><td>Three.js</td><td>three/three.min.js</td><td>3D 渲染</td></tr>
<tr><td>Mermaid</td><td>mermaid/mermaid.min.js</td><td>流程图、时序图、甘特图</td></tr>
<tr><td>Lucide</td><td>lucide/lucide.min.js</td><td>图标库</td></tr>
</table>

<h2>最小可跑例子</h2>
<pre><code>&lt;!DOCTYPE html&gt;
&lt;html&gt;&lt;head&gt;&lt;meta charset="utf-8"&gt;
&lt;script src="vue/vue.global.prod.js"&gt;&lt;/script&gt;
&lt;script src="tailwind/tailwind.js"&gt;&lt;/script&gt;
&lt;/head&gt;&lt;body&gt;
&lt;div id="app" class="p-6"&gt;
  &lt;h1 class="text-2xl font-bold"&gt;{{ msg }}&lt;/h1&gt;
  &lt;button @click="n++" class="mt-3 px-4 py-2 bg-blue-600 text-white rounded"&gt;
    点了 {{ n }} 次
  &lt;/button&gt;
&lt;/div&gt;
&lt;script&gt;
Vue.createApp({
  data(){ return { msg:'离线也能跑', n:0 } }
}).mount('#app');
&lt;/script&gt;
&lt;/body&gt;&lt;/html&gt;</code></pre>
<p style="color:#8b949e;font-size:12px;margin-top:24px">全部文件都在本地，断网也能用。</p>
</body></html>'''
    open(os.path.join(libdir,'index.html'),'w',encoding='utf-8').write(idx)

    total = sum(os.path.getsize(os.path.join(r,f)) for r,_,fs in os.walk(libdir) for f in fs)
    log(f'库总体积 {total/1048576:.1f}MB')
    return pack('html', usr, '1.0.0-eng1',
                '前端离线库合集（Vue/React/Tailwind/CodeMirror/Chart.js/Mermaid 等 15 套）',
                'bin/proot')

# ============ androidapp ============
def build_android():
    log('\n========== androidapp 引擎（Android 工程模板）==========')
    shutil.rmtree(WORK, ignore_errors=True)
    usr = os.path.join(WORK, 'data/data/com.termux/files/usr')
    tpl = os.path.join(usr, 'share', 'android-template')
    os.makedirs(tpl, exist_ok=True)
    os.makedirs(os.path.join(usr,'bin'), exist_ok=True)
    if not unpack_proot(usr): return False

    files = {}

    files['settings.gradle'] = '''pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "MyApp"
include ':app'
'''

    files['build.gradle'] = '''// 顶层构建文件
plugins {
    id 'com.android.application' version '8.7.3' apply false
}
'''

    files['gradle.properties'] = '''org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
android.nonTransitiveRClass=true
'''

    files['app/build.gradle'] = '''plugins {
    id 'com.android.application'
}

android {
    namespace 'com.example.myapp'
    compileSdk 35

    defaultConfig {
        applicationId "com.example.myapp"
        minSdk 24
        targetSdk 35
        versionCode 1
        versionName "1.0"
    }

    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }

    compileOptions {
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }
}

dependencies {
    implementation 'androidx.appcompat:appcompat:1.7.0'
    implementation 'com.google.android.material:material:1.12.0'
    implementation 'androidx.constraintlayout:constraintlayout:2.2.0'
}
'''

    files['app/proguard-rules.pro'] = '''# 混淆规则，默认不混淆
-keep class com.example.myapp.** { *; }
'''

    files['app/src/main/AndroidManifest.xml'] = '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:supportsRtl="true"
        android:theme="@style/Theme.MyApp">

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:configChanges="orientation|screenSize|keyboardHidden">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
'''

    files['app/src/main/java/com/example/myapp/MainActivity.java'] = '''package com.example.myapp;

import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {

    private WebView web;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        web = new WebView(this);
        setContentView(web);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(true);
        s.setAllowContentAccess(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);

        web.setWebViewClient(new WebViewClient());
        web.loadUrl("file:///android_asset/index.html");
    }

    @Override
    public void onBackPressed() {
        if (web != null && web.canGoBack()) {
            web.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
'''

    files['app/src/main/assets/index.html'] = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>我的应用</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{
  font:15px/1.7 -apple-system,system-ui,"PingFang SC",sans-serif;
  background:linear-gradient(160deg,#0f172a,#1e293b 60%,#0f172a);
  color:#e2e8f0;min-height:100vh;
  display:flex;align-items:center;justify-content:center;padding:24px;
}
.card{
  background:rgba(30,41,59,.85);border:1px solid rgba(148,163,184,.25);
  border-radius:18px;padding:32px 26px;max-width:400px;width:100%;
  box-shadow:0 20px 60px rgba(0,0,0,.45);text-align:center;
}
h1{font-size:22px;margin-bottom:10px;background:linear-gradient(90deg,#38bdf8,#818cf8);
   -webkit-background-clip:text;-webkit-text-fill-color:transparent}
p{color:#94a3b8;font-size:13.5px;margin-bottom:22px}
button{
  width:100%;padding:13px;border:0;border-radius:11px;font-size:15px;font-weight:600;
  color:#fff;background:linear-gradient(135deg,#3b82f6,#6366f1);cursor:pointer;
  box-shadow:0 6px 20px rgba(59,130,246,.35);
}
button:active{transform:scale(.98)}
#n{margin-top:16px;font-size:13px;color:#64748b}
</style>
</head>
<body>
<div class="card">
  <h1>我的应用</h1>
  <p>模板已跑通，改 assets/index.html 就能开始写你的界面</p>
  <button onclick="document.getElementById('n').textContent='点了 '+(++c)+' 次'">点我</button>
  <div id="n">点一下试试</div>
</div>
<script>var c=0;</script>
</body>
</html>
'''

    files['app/src/main/res/values/strings.xml'] = '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">我的应用</string>
</resources>
'''

    files['app/src/main/res/values/themes.xml'] = '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.MyApp" parent="Theme.MaterialComponents.DayNight.NoActionBar">
        <item name="colorPrimary">#3B82F6</item>
        <item name="colorPrimaryVariant">#2563EB</item>
        <item name="colorOnPrimary">#FFFFFF</item>
    </style>
</resources>
'''

    files['app/src/main/res/xml/backup_rules.xml'] = '''<?xml version="1.0" encoding="utf-8"?>
<full-backup-content>
    <include domain="sharedpref" path="."/>
</full-backup-content>
'''

    files['README.md'] = '''# Android 工程模板

直接能编译的最小工程，改完就能出 APK。

## 目录说明

```
settings.gradle              工程名和模块
build.gradle                 插件版本
gradle.properties            JVM / AndroidX 开关
app/build.gradle             应用 ID、版本号、SDK 版本、依赖
app/src/main/AndroidManifest.xml   权限、Activity 声明
app/src/main/java/.../MainActivity.java   主界面（WebView）
app/src/main/assets/index.html            界面本体，改这里最快
app/src/main/res/values/strings.xml       应用名
app/src/main/res/values/themes.xml        主题色
```

## 改什么

| 想改 | 改哪 |
|---|---|
| 应用名 | `res/values/strings.xml` 的 `app_name` |
| 包名 | `app/build.gradle` 的 `namespace` 和 `applicationId`，同时改 Java 包路径 |
| 版本号 | `app/build.gradle` 的 `versionCode` / `versionName` |
| 界面 | `assets/index.html`（纯网页，改完不用重编 Java） |
| 主题色 | `res/values/themes.xml` |
| 加原生能力 | `MainActivity.java` 里加 `@JavascriptInterface` 方法，网页里用 `window.AndroidXxx.方法名()` 调 |

## 编译

**方式一：AIDE**
把整个目录拷到手机，AIDE 打开，直接 Build → Run。

**方式二：Android Studio**
File → Open 选这个目录，等 Gradle 同步完，点 Run。

**方式三：命令行**
```bash
./gradlew assembleDebug
# 产物 app/build/outputs/apk/debug/app-debug.apk
```

## 签名出正式版

```bash
keytool -genkey -v -keystore my.jks -keyalg RSA -keysize 2048 -validity 36500 -alias mykey
./gradlew assembleRelease
apksigner sign --ks my.jks --out signed.apk app/build/outputs/apk/release/app-release-unsigned.apk
```

**keystore 一定要留好备份**。丢了就再也无法覆盖安装升级，用户必须卸载重装。
'''

    for rel, content in files.items():
        p = os.path.join(tpl, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p,'w',encoding='utf-8',newline='\n').write(content)
    log(f'写入 {len(files)} 个模板文件')

    return pack('androidapp', usr, '1.0.0-eng1',
                'Android 工程模板（Gradle + WebView 骨架，改 assets/index.html 就能出 APK）',
                'bin/proot')

if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if which in ('html','all'):
        build_html()
    if which in ('androidapp','all'):
        build_android()
