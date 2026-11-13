# 编程专家 · 引擎包仓库

自己的语言引擎安装包仓库。手机 APP 从这里直接下载引擎，链接永久有效，不再依赖任何临时地址。

**当前状态：22 个引擎全部构建完成并上线。**

## 怎么用

打开 APP → 底部「引擎」→ 滚到最下面「🌐 引擎源地址」，填：

```
https://github.com/sfwifi6/engines/releases/download/v1/
```

点保存。之后所有引擎都从这里拉。

单个引擎直链格式：

```
https://github.com/sfwifi6/engines/releases/download/v1/<引擎名>-engine.tar.gz
```

## 已上线引擎

| 分类 | 引擎 | 文件 | 大小 |
|---|---|---|---|
| 前端 | HTML 离线库 | `html-engine.tar.gz` | 待补 |
| 前端 | Android 工程模板 | `androidapp-engine.tar.gz` | 待补 |
| 后端 | Python 3.14 + LSP | `python-engine.tar.gz` | 16.6 MB |
| 后端 | Node.js 24 LTS | `nodejs-engine.tar.gz` | 37.4 MB |
| 后端 | PHP 8.5 + FPM | `php-engine.tar.gz` | 53.2 MB |
| 后端 | Go 1.27 | `golang-engine.tar.gz` | 200.0 MB |
| 服务器 | Nginx 1.31 | `nginx-engine.tar.gz` | 4.8 MB |
| 服务器 | Redis 8 | `redis-engine.tar.gz` | 1.8 MB |
| 服务器 | MariaDB 13 | `mysql-engine.tar.gz` | 53.0 MB |
| 服务器 | SQLite 3.54 | `sqlite-engine.tar.gz` | 1.5 MB |
| 服务器 | OpenSSH 10.6 | `ssh-engine.tar.gz` | 9.9 MB |
| 服务器 | Linux 系统工具集 | `sysbase-engine.tar.gz` | 20.8 MB |
| 移动端 | Kotlin 2.4（含 JDK21） | `kotlin-engine.tar.gz` | 234.9 MB |
| 移动端 | OpenJDK 17 | `openjdk-engine.tar.gz` | 133.1 MB |
| 移动端 | APK 打包工具链 | `apkbuild-engine.tar.gz` | 129.9 MB |
| 移动端 | Clang 21 全套 | `clang-engine.tar.gz` | 142.9 MB |
| 小程序 | 微信小程序 | `mpweixin-engine.tar.gz` | 37.4 MB |
| 小程序 | 抖音小程序 | `mpdouyin-engine.tar.gz` | 37.4 MB |
| 小程序 | 支付宝小程序 | `mpalipay-engine.tar.gz` | 37.4 MB |
| 系统级 | Rust 1.99 + cargo | `rust-engine.tar.gz` | 351.6 MB |
| 系统级 | Git 2.56 | `git-engine.tar.gz` | 18.0 MB |
| 系统级 | Neovim 0.12 | `vim-engine.tar.gz` | 14.5 MB |
| AI | AI 应用开发 | `ai-engine.tar.gz` | 13.5 MB |
| AI | AI Agent 框架 | `aiagent-engine.tar.gz` | 13.5 MB |

每个包都自带 `proot`（APP 运行引擎必需），装完直接能用。

## 包结构约定

```
./manifest.json                              ← 引擎元信息
./data/data/com.termux/files/usr/bin/...     ← 可执行文件
./data/data/com.termux/files/usr/lib/...     ← 依赖库
```

`manifest.json` 字段：

```json
{
  "name": "sqlite",
  "version": "3.54.1-1-eng1",
  "bin": "bin/sqlite3",
  "desc": "SQLite 3.54 单文件数据库 + 命令行",
  "prefix": "/data/data/com.termux/files/usr"
}
```

## 自动构建

改 `trigger/build.txt` 任意内容并 push，GitHub Actions 会并行构建全部引擎并发布到 Release。

- 构建脚本：`build/build_engine.py`
- 引擎清单：`build/engines.json`
- 包源：Termux 官方 aarch64 仓库（清华镜像）
- 单个构建产物大小、MD5 记录在 `built/summary.json`

公开仓库 Actions 免费不限量。

## 后续：自己的服务器 + 域名

引擎包放 GitHub Release 已经够用很久。等要做「云端编译」「在线运行代码」时再上服务器：

1. 买一台 2 核 4G 云服务器（阿里云/腾讯云轻量，约 60~100 元/年）
2. 域名备案 + 解析到服务器
3. Nginx 反代 + HTTPS（Let's Encrypt 免费证书）
4. 引擎包目录挂到 Nginx，地址变成 `https://你的域名/engines/`
5. APP 里把「引擎源地址」改成 `https://你的域名/engines/`

到那一步 APP 源码一行都不用改，只改一个字。
