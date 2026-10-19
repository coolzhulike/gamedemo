# 原始男女高模（最新女性版本）

这里只恢复用户上传的两个原始 GLB。原字节保留，不修改几何、材质、纹理或骨骼；两份原件本身都没有绑定和动作。

## 一条命令恢复

需要 Python 3.9 或更新版本，仅使用标准库。克隆仓库或下载本目录的 `restore_originals.py` 与 `originals_manifest.json` 后运行：

```sh
python3 project_resources/assets/original_character_models/restore_originals.py
```

Windows 可以双击 `restore_windows.cmd`（需已安装 Python）。

输出到本目录的 `models/`，可直接导入 Blender 或支持 GLB 的工具：

- 男性：`models/wuxia robe 3d model.glb`
- 最新女性：`models/black hanfu dress 3d model.glb`

也可指定一个新的空目录：

```sh
python3 restore_originals.py --output ./my_original_models
```

已有输出只有在名称、大小及 SHA-256 都匹配时才复用；不会覆盖不同文件，也拒绝混有其他文件的输出目录。

## 下载范围

原始字节已随 PR #2 进入 main，本 PR 不重复上传大包。本入口仅从既有 ZIP 分卷读取两个原模所在的数据段，不解压动作工程。

- 首次在线恢复只需要既有分卷 `.001–.016` 和 `.086`，共 **69,441,099 字节（约 66.22 MiB）**
- 完整克隆若已带这些分卷，直接本地读取，无须再下载
- 下载源固定到提交 `575c9edbf7bb91c8614d79236adf20748f3b2ebe`，不依赖可变分支
- 每个使用的分卷先校验大小及 SHA-256；再校验 ZIP 成员 CRC、原件大小与 SHA-256
- 缓存在 `.cache/`；`--offline` 可强制只用本地分卷
- 不需要下载或恢复其余动作、骑马、椅子及 review 加工文件
- 原件合计 125,656,304 字节；首次在线恢复建议预留至少 400 MB 可用空间

## 原件身份与校验

2026-10-19 从用户原上传的男女两组 ZIP 分卷重新解包，实测 GLB 哈希与 main 归档清单一致。女性采用 2026-10-17 00:12 UTC 上传、明确替换此前女性版本的那组。

| 原件 | 字节数 | 顶点 | 三角形 |
| --- | ---: | ---: | ---: |
| wuxia robe 3d model.glb | 63,153,404 | 1,007,328 | 1,915,531 |
| black hanfu dress 3d model.glb | 62,502,900 | 1,018,133 | 1,956,132 |

男性 SHA-256：
`804b03465b0b223e5aeb33e762f69181b3f134c28b24a0f1cb1be665177b084a`

女性 SHA-256：
`a8ac4d8ac18af00c782a14c9417712159a7b6fab06be78397ddb9550dc7001f8`

完整来源、上传 ZIP 哈希、必要分卷哈希在 `originals_manifest.json`。该清单保留全部分卷的索引以支持 ZIP 随机读取，脚本只取实际访问的分卷。

## 验证

- 实际用上述 17 个分卷离线恢复两个 GLB，逐字节 SHA-256 与原始上传一致
- 输出目录仅含上述两个 GLB；重复运行通过
- 自动测试覆盖缺卷、损坏卷、原件哈希错误、已有文件保护、非空目录及路径穿越拒绝

```sh
python3 -m unittest discover -s project_resources/assets/original_character_models -p 'test_restore_originals.py'
```
