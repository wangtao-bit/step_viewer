# STEP 模型查看器 · 二次开发

本地桌面程序，使用 Python、PyQt5、VTK 和 FreeCAD。已验证环境是 Ubuntu 22.04 桌面。源码可以放在任意目录运行，无需先安装查看器的 `.deb`。

## 开始开发

在新电脑上先安装开发所需的系统包（已有依赖可跳过）：

```sh
sudo apt update
sudo apt install make dpkg python3 python3-pyqt5 python3-vtk9 python3-numpy libqt5svg5 freecad-python3 shared-mime-info
```

解压源码包，进入有 `Makefile` 的 `step-viewer` 文件夹，在终端执行：

```sh
make run                         # 打开内置的 F330 示例
make run FILE="/路径/模型.stp"   # 或者启动时打开自己的文件
make test                        # 自动检查，无需图形桌面
```

改完 `.py` 文件并保存后，关闭开发窗口，再执行 `make run`。运行开发版无需 `sudo`。应用菜单里用 `.deb` 安装的版本不会随源码修改；用 `make run` 可以确定正在运行手头的源码。

用 VS Code 调试：直接打开本项目文件夹，安装 Python 和 Python Debugger 扩展，按 F5 选择「调试 STEP 查看器」。在 PyCharm 中把项目解释器设置成 `/usr/bin/python3`，启动脚本选择 `viewer.py`。STEP 导入发生在独立进程；单独调试导入时，运行 `import_file.py 输入.step 输出.mesh`。

## 从哪里改

| 需求 | 文件和入口 |
| --- | --- |
| 新增工具栏按钮、快捷键和切换状态 | `tools.py` 的 `install_tools(viewer, toolbar)`；现成的「线框」按钮演示了模型替换时如何保留状态 |
| 改零件列表、拖放、菜单、标准视角 | `viewer.py` 的 `Viewer` 和 `VIEWS` |
| 改模型配色、材质、网格到 VTK 的映射 | `scene.py` 的 `read_scene()` 和 `PartView` |
| 改 STEP 读取、零件拆分、三角化精度 | `convert.py` 的 `convert()`；`import_file.py` 负责导入入口及已知文件缓存 |

例如，要增加一个「后视」方向，可以在 `viewer.py` 的 `VIEWS` 字典中添加 `'后视': ((0, 1, 0), (0, 0, 1))`，重启后它就会出现在视角菜单里。新增工具则从 `tools.py` 入手：`viewer.scene` 包含当前部件，`part.actor` 是 VTK 显示对象；换模型后 `viewer.scene_changed` 会通知工具重新应用显示设置。这里只修改显示状态。要编辑并保存 STEP 几何，需要在 FreeCAD 几何层处理并导出文件，不能只改显示网格。

## 分发自己的版本

修改 `packaging/control` 的 `Version`，运行 `make test`，再根据接收方选择：

- `make source`：生成可继续开发的源码压缩包，包含示例、测试和调试配置。
- `make deb`：生成给 Ubuntu 用户安装的 `.deb`。用 `sudo apt install ./安装包文件名.deb` 安装或升级。

两类文件都在 `dist/`。项目不依赖 Onshape 或网页服务；源码包未附 Ubuntu 软件依赖。内置 F330 示例来自同版 FCStd 的显示缓存，只有摘要匹配的原始总装 STEP 才使用这个缓存。
