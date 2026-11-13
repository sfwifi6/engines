# 编程专家 · 引擎包仓库

自己的语言引擎安装包仓库，替代原来会过期的临时链接。手机 APP 从这里直接下载引擎。

## 已上线（Release v1）

下载地址统一格式：

```
https://github.com/sfwifi6/engines/releases/download/v1/<文件名>
```

| 引擎 | 文件 | 大小 | MD5 |
|---|---|---|---|
| Python 3.14 + LSP 网关 | `python-engine.tar.gz` | 16.6 MB | `5c0749f7843000b1ecee176ff84575d9` |
| C/C++ 编译器（clang 全套） | `clang-engine.tar.gz` | 142.9 MB | `8dd063983f4f12fb2d14d2a2252d9497` |
| Go 编译器（官方） | `golang-engine.tar.gz` | 200.0 MB | `7805fc09024b07f986c8f58dcc726c5c` |
| Java 编译器+运行时（OpenJDK 17） | `openjdk-engine.tar.gz` | 133.1 MB | `956241d3cf432260b4e822dc1a83d164` |

直链例子：

- https://github.com/sfwifi6/engines/releases/download/v1/python-engine.tar.gz
- https://github.com/sfwifi6/engines/releases/download/v1/clang-engine.tar.gz
- https://github.com/sfwifi6/engines/releases/download/v1/golang-engine.tar.gz
- https://github.com/sfwifi6/engines/releases/download/v1/openjdk-engine.tar.gz

**整包，不分卷。** GitHub Release 单文件上限 2GB，不需要再切 95MB 小片，下载一次成功率高很多。

## APP 里怎么用

打开 APP → 底部「引擎」→ 滚到最下面「🌐 引擎源地址」，填：

```
https://github.com/sfwifi6/engines/releases/download/v1/
```

点保存。之后所有引擎下载都走这里，不再依赖任何临时链接。
将来换成自己的服务器，只改这一格，APP 不用重装。

## 待补的引擎

nodejs、apkbuild、git、php、kotlin、mysql、rust、sysbase、sqlite、nginx、redis、ssh、vim、mpweixin、mpdouyin、mpalipay、ai、aiagent、html、androidapp

这些包还没做出来。做出来后按同名规则上传到 Release，APP 里就能直接装。

## 自动搬运

`.github/workflows/fetch-engines.yml` 可以从临时链接把包搬进来并自动发布到 Release。

触发方式：改 `trigger/run.txt` 任意内容并 push（公开仓库 Actions 免费不限量）。

运行结果会写进 `diag2.txt`，能直接看到每个包下载耗时、大小、MD5 和上传结果。

## 后续：自己的服务器 + 域名

引擎包放在 GitHub Release 已经够用很久。等要做「云端编译」「在线运行代码」时再上服务器：

1. 买一台 2 核 4G 云服务器（阿里云/腾讯云轻量，约 60~100 元/年）
2. 域名备案 + 解析到服务器
3. Nginx 反代 + HTTPS（Let's Encrypt 免费证书）
4. 把引擎包目录挂到 Nginx，地址就变成 `https://你的域名/engines/`
5. APP 里把「引擎源地址」改成 `https://你的域名/engines/`

到那一步只要改一个字，APP 源码一行都不用动。
