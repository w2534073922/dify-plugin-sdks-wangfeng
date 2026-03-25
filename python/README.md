# Dify Plugin SDK

A Python SDK for building plugins for Dify.

## Version Management

This SDK follows Semantic Versioning (a.b.c):

- a: Major version - Indicates significant architectural changes or incompatible API modifications
- b: Minor version - Indicates new feature additions while maintaining backward compatibility
- c: Patch version - Indicates backward-compatible bug fixes

### For SDK Users

When depending on this SDK, it's recommended to specify version constraints that:

- Allow patch and minor updates for bug fixes and new features
- Prevent major version updates to avoid breaking changes

Example in your project's dependency management:

```python
dify_plugin>=0.3.0,<0.5.0
```

---

## 在插件项目中使用自定义 SDK（中文指南）

> 适用场景：你 fork 了本仓库并做了修改（例如添加了 `session.run_in_background()`），
> 但改动尚未合并到官方仓库并发布到 PyPI，需要在自己的插件项目中使用这份自定义版本。

以下三种方式任选其一，**推荐程度从高到低**排列。

---

### 方式一：Git URL 直接引用（最简单，推荐）

在插件项目的 `requirements.txt` 中，把原来的 `dify_plugin==x.y.z` 替换为：

```
dify_plugin @ git+https://github.com/<你的用户名>/dify-plugin-sdks-wangfeng.git@<分支名或commit>#subdirectory=python
```

示例（使用本仓库的 `copilot/update-dify-plugin-sdk` 分支）：

```
dify_plugin @ git+https://github.com/w2534073922/dify-plugin-sdks-wangfeng.git@copilot/update-dify-plugin-sdk#subdirectory=python
```

**优点：** 无需手动构建，`pip install -r requirements.txt` 会自动从 GitHub 拉取并安装。
**缺点：** 构建环境需要能访问 GitHub（离线环境不适用）。

---

### 方式二：构建 .whl 文件后本地引用

**步骤 1：** 在本仓库的 `python/` 目录下运行构建脚本：

```bash
cd python/
./scripts/build_wheel.sh
```

构建完成后，`dist/` 目录下会生成 `dify_plugin-*.whl` 文件。

**步骤 2：** 将 `.whl` 文件拷贝到你的插件项目根目录（建议放在 `vendor/` 子目录）：

```bash
mkdir -p /path/to/your-plugin/vendor
cp dist/dify_plugin-*.whl /path/to/your-plugin/vendor/
```

**步骤 3：** 修改插件项目的 `requirements.txt`，把原来的 `dify_plugin==x.y.z` 替换为本地路径：

```
./vendor/dify_plugin-0.7.4-py3-none-any.whl
```

> 文件名以实际生成的为准，可用 `ls vendor/` 查看。

**优点：** 离线可用，文件明确，版本固定。
**缺点：** SDK 有更新时需要重新构建并替换 `.whl` 文件。

---

### 方式三：直接拷贝源码目录（最直接，零工具依赖）

**步骤 1：** 将本仓库的 `python/dify_plugin/` 目录整体拷贝到你的插件项目根目录：

```bash
cp -r /path/to/dify-plugin-sdks-wangfeng/python/dify_plugin /path/to/your-plugin/
```

拷贝后，你的插件项目目录结构如下：

```
your-plugin/
├── dify_plugin/        ← 拷贝进来的自定义 SDK 源码
├── main.py
├── manifest.yaml
├── provider/
├── tools/
└── requirements.txt
```

**步骤 2：** 删除 `requirements.txt` 中的 `dify_plugin` 行（因为源码已在本地，无需 pip 安装）：

```diff
- dify_plugin==0.6.0b10
```

**优点：** 完全离线，无任何外部依赖，调试方便（可直接修改 SDK 源码）。
**缺点：** SDK 更新时需要手动重新拷贝；项目体积会增大。
