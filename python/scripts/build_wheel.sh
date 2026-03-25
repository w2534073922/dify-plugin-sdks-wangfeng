#!/bin/bash
# 将本仓库修改后的 dify_plugin SDK 打包为 .whl 文件。
#
# 用途：当你需要在插件项目中使用尚未发布到 PyPI 的自定义 SDK 版本时，
#       可用此脚本先构建 wheel，再将 .whl 文件放入插件项目并在
#       requirements.txt 中引用。
#
# 用法：
#   cd python/
#   ./scripts/build_wheel.sh
#
# 输出：dist/ 目录下生成 dify_plugin-*.whl 文件

set -ex
set -o pipefail

SCRIPT_DIR="$(dirname "$0")"
PYTHON_SDK_DIR="$(dirname "${SCRIPT_DIR}")"

function main {
    cd "${PYTHON_SDK_DIR}"
    pdm build --no-sdist
    echo ""
    echo "✅ 构建成功！wheel 文件位于："
    ls -1 dist/*.whl
    echo ""
    echo "接下来请参考 README.md「在插件项目中使用自定义 SDK」章节，"
    echo "将 .whl 文件放入你的插件项目并更新 requirements.txt。"
}

main
