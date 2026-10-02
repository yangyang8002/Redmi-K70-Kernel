# 红米 K70（vermeer）官方内核 · GitHub Actions 自动编译

[![Build Redmi K70 Kernel](https://github.com/yangyang8002/redmi-k70-kernel/actions/workflows/build-kernel.yml/badge.svg)](https://github.com/yangyang8002/redmi-k70-kernel/actions/workflows/build-kernel.yml)

本仓库使用 GitHub Actions 从**小米官方开源内核仓库**编译红米 K70 的官方内核源码。

- 设备：小米 红米 K70（代号 `vermeer`，骁龙 8 Gen 2 / SM8550；海外对应 POCO F6 Pro）
- 源码：[MiCode/Xiaomi_Kernel_OpenSource](https://github.com/MiCode/Xiaomi_Kernel_OpenSource) 分支 `bsp-vermeer-t-oss`
  - 该分支 HEAD 提交：*"Kernel: Xiaomi kernel changes for Redmi K70 Android U"*（基于高通 TAG `LA.VENDOR.13.2.0.r1-14800-r1.0.r1_00043.0`）
  - 内核版本：**5.15**（GKI 2.0 / android13-5.15 基线，基于 SM8550 Kalama BSP）

## 构建流程（与内核树自带的官方流程一致）

小米量产机使用的 `vermeer_user_defconfig` 并未包含在开源树中，因此本仓库完全按照内核树自带的官方构建配置 `build.config.msm.gki`（`VARIANT=gki`）执行：

1. 用官方 `scripts/kconfig/merge_config.sh -m -r -y` 将 `gki_defconfig` + `vendor/vermeer_GKI.config` 合并为 `vendor/vermeer-gki_defconfig`
2. `make O=out ARCH=arm64 LLVM=1 vendor/vermeer-gki_defconfig`
3. `make -j$(nproc) O=out ARCH=arm64 LLVM=1 Image modules`（与 `build.config.aarch64` 的 `MAKE_GOALS="Image modules"` 一致）

工具链：优先使用内核树 `build.config.constants` 中固定的 AOSP 官方预编译 **clang r450784e**；下载失败时自动回退到 Ubuntu 仓库 clang（也可用 Run workflow 输入强制指定）。

- **LTO 模式**：默认 **ThinLTO**（`CONFIG_LTO_CLANG_THIN=y`，内存占用与耗时更低）；官方 `gki_defconfig` 使用 `CONFIG_LTO_CLANG_FULL=y`，如需完全一致可在 Run workflow 时选择 `full`（或 `none`）。
- 构建前会自动清理小米开源树中的**悬空 Kconfig `source` 引用**（如 `drivers/misc/hwid/Kconfig`——对应目录未随源码开源，直接构建会报 `can't open file`）。清理规则只匹配**带引号、不含 `$(VAR)` 变量且目标文件确实缺失**的真实 source 语句，不会误删 `arch/$(SRCARCH)/Kconfig` 这类合法引用或帮助文本。
- 所有 `make` 调用都重定向了 stdin（`< /dev/null`）：该内核树的构建脚本里存在**裸 `bc` 调用**，会阻塞在 stdin 上导致构建假死（曾出现 6 小时零输出）。
- GKI 默认强制 `CONFIG_WERROR=y`（源码里未直接设置，由 GKI Kconfig 强制）；apt 回退工具链 clang 18 比官方 clang r450784e 新，会把树里个别高通旧代码（如 `drivers/soc/qcom/minidump_log.c` 的 implicit-int）升级为错误，因此工作流会**关闭 WERROR**（降级为警告，不中断构建）。

## 断点续编（应对 6 小时任务上限）

GitHub 免费单任务上限 6 小时，完整 `Image + modules` 构建在 4 核 runner 上可能超时。工作流会把 `kernel/out` 构建树缓存到 actions/cache（键 `k70-out-<分支>-<run_id>`，恢复时按前缀取最近一次），构建步骤自带 **270 分钟**超时——超时会先把 `out/` 存入缓存再退出，下一次运行把源码时间戳回拨后自动**断点续编**（已编译对象直接复用）；也可在 Run workflow 时用 `build_targets` 输入手动分轮（先 `Image`，再 `modules`）。

## 产物（Actions Artifacts）

| 文件 | 说明 |
|---|---|
| `boot/Image` | 内核镜像（GKI `Image`，未压缩） |
| `boot/System.map` | 符号表 |
| `Module.symvers` | 模块符号版本（编译外部模块需要） |
| `modules.tar.gz` | 全部内核模块（`modules_install` + depmod） |
| `kernel.config` / `merged-defconfig` | 实际使用的内核配置 |
| `BUILD-INFO.txt` | 源码提交、内核版本、工具链等元信息 |
| `build.log` | 完整构建日志 |

## 使用

- **自动触发**：推送到 `main` 分支即触发构建
- **手动触发**：Actions → *Build Redmi K70 Kernel* → *Run workflow*（可选源码分支、工具链、LTO 模式、构建目标 `build_targets`）

## 说明与注意

- 红米 K70 的**设备树（DTB）不在开源内核树中**（高通将其放在单独的 devicetree 组件中，未随内核开源），因此产物不含 DTB。
- 本仓库用于官方源码的**编译验证与开发研究**：产物的签名密钥、配置与小米官方发布的二进制不同，**不能直接替换刷机**；如需刷入，模块必须与本内核配套，并自行重打包 `vendor_boot` 等镜像。
- 编译 K70 系列 other 型号需改 workflow 中的分支与配置片段：`bsp-manet-u-oss`（K70 Pro，manet）/ `bsp-duchamp-u-oss`（K70E，duchamp）。

## 参考

- [MiCode/Xiaomi_Kernel_OpenSource](https://github.com/MiCode/Xiaomi_Kernel_OpenSource)
- 内核树内官方构建配置：`build.config.msm.vermeer` / `build.config.msm.gki` / `build.config.aarch64`
