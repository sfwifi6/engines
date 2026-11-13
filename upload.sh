#!/bin/bash
# ============================================================
# 把引擎包一键传到 GitHub Releases
#
# 用法：
#   1) 装 gh：https://cli.github.com
#   2) gh auth login
#   3) ./upload.sh <用户名> <仓库名> <tag> <包目录>
#
# 例：./upload.sh sfwifi6 engines v1 ~/Downloads/engines
# ============================================================
set -e

USER="${1:?用法: ./upload.sh <GitHub用户名> <仓库名> <tag> <包目录>}"
REPO="${2:?缺少仓库名}"
TAG="${3:-v1}"
DIR="${4:-.}"

echo "→ 目标：github.com/$USER/$REPO   标签：$TAG"
echo "→ 本地目录：$DIR"
echo

if ! gh repo view "$USER/$REPO" >/dev/null 2>&1; then
  echo "仓库不存在，正在创建 $USER/$REPO ..."
  gh repo create "$USER/$REPO" --public --description "编程专家 APP 引擎包托管"
fi

if ! gh release view "$TAG" -R "$USER/$REPO" >/dev/null 2>&1; then
  echo "创建 Release $TAG ..."
  gh release create "$TAG" -R "$USER/$REPO" \
    --title "引擎包 $TAG" \
    --notes "编程专家 APP 语言引擎安装包（整包，不分卷）"
fi

shopt -s nullglob
COUNT=0
for f in "$DIR"/*.tar.gz; do
  SZ=$(stat -c%s "$f" 2>/dev/null || stat -f%z "$f")
  MB=$((SZ/1048576))
  echo "↑ 上传 $(basename "$f")  ${MB}MB ..."
  gh release upload "$TAG" "$f" -R "$USER/$REPO" --clobber
  COUNT=$((COUNT+1))
done
shopt -u nullglob

echo
echo "✅ 传完 $COUNT 个文件"
echo
echo "APP「引擎中心 → 引擎源地址」填："
echo "   https://github.com/$USER/$REPO/releases/download/$TAG/"
echo
echo "手机直连 GitHub 慢的话，前面加加速前缀："
echo "   https://ghproxy.net/https://github.com/$USER/$REPO/releases/download/$TAG/"
