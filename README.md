# 编程专家 · 引擎包托管

24 个语言引擎的安装包仓库。用 GitHub Releases 做永久下载源，链接不会像临时短链那样过期。

## 地址

```
https://github.com/sfwifi6/engines/releases/download/v1/
```

填进 APP「语言引擎中心 → 🌐 引擎源地址」，保存后所有引擎下载都走这里。

## 怎么把包传上来

### 方式一：点一下就行（推荐）

1. 打开 [Actions → 搬引擎包到 Releases](../../actions/workflows/fetch-engines.yml)
2. 点右侧 **Run workflow**，tag 填 `v1`
3. 等 3~5 分钟，四个包自动下载、合并分卷、校验大小、发布 Release

### 方式二：本地传

```bash
gh auth login
./upload.sh sfwifi6 engines v1 ./包所在目录
```

## 已托管 / 待补

| 引擎 | 大小 | 状态 |
|---|---|---|
| python | 16.6MB | ✅ 可搬 |
| clang | 136MB | ✅ 可搬（原 2 卷合并） |
| golang | 191MB | ✅ 可搬（原 3 卷合并） |
| openjdk | 127MB | ✅ 可搬（原 2 卷合并） |
| nodejs | 37MB | ⚠️ 源站已停，需重打 |
| apkbuild | 22MB | ⚠️ 源站已停，需重打 |
| git / php / kotlin / mysql / rust | — | ⚠️ 待打包 |
| sysbase / sqlite / nginx / redis / ssh / vim | — | ⚠️ 待打包 |
| 微信 / 抖音 / 支付宝小程序 | — | ⚠️ 待打包 |
| ai / aiagent | — | ⚠️ 待打包 |
| html / androidapp | — | ⚠️ 待打包 |

## 文件说明

- `engines.json` — 引擎清单（名称、字节数、MD5、文件名），APP 和脚本都读这个
- `upload.sh` — 本地一键上传脚本（用 GitHub CLI）
- `.github/workflows/fetch-engines.yml` — 云端自动搬运（点按钮触发）

## 为什么不用分卷

GitHub Release 单文件上限 **2GB**。原来 clang 要切 2 卷、golang 切 3 卷、openjdk 切 2 卷，是因为旧平台限 95MB。这里全部整包传，一个文件一个链接，下载中断可以续传，不会像分卷那样少一卷就废。

## 后续

想上自己的服务器和域名时，把包放 Nginx 或 Cloudflare R2，APP 里换个地址就行，不用重打包：

- 轻量服务器 2核2G：约 60~100 元/年，配 Nginx + Let's Encrypt 免费 HTTPS
- Cloudflare R2：10GB 存储免费，出流量永久免费，绑自己域名自带 CDN

全部引擎加起来约 1.5GB，R2 免费额度就够。
