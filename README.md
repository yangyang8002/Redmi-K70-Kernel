# 红米 K70（vermeer）官方内核 · GitHub Actions 自动编译

[![Build Redmi K70 Kernel](https://github.com/yangyang8002/redmi-k70-kernel/actions/workflows/build-kernel.yml/badge.svg)](https://github.com/yangyang8002/redmi-k70-kernel/actions/workflows/build-kernel.yml)

> ## ⚠️ 实验性 linux-6.6 分支（`linux-6.6`）
>
> **[<img src="https://github.com/yangyang8002/redmi-k70-kernel/actions/workflows/build-kernel-6.6.yml/badge.svg?branch=linux-6.6" alt="Build 6.6" height="20">](https://github.com/yangyang8002/redmi-k70-kernel/actions/workflows/build-kernel-6.6.yml)**（[工作流](.github/workflows/build-kernel-6.6.yml)）
>
> ### ⛔ 不可用于日用 / 不要刷入真机
>
> 此分支将内核从 5.15 迁移到 **Linux 6.6**，但这是一个**纯实验性构建**：
>
> - **基线**：AOSP GKI [`android15-6.6`](https://android.googlesource.com/kernel/common/+/refs/heads/android15-6.6) 分支（当前 **6.6.143**，GKI 2.0 / Android 15 基线）+ 小米 MiCode 5.15 树的 [`vermeer_GKI.config`](https://github.com/MiCode/Xiaomi_Kernel_OpenSource/blob/bsp-vermeer-t-oss/arch/arm64/configs/vendor/vermeer_GKI.config) 配置片段合并（高通官方 fragment 流程）。
> - **为什么无法日用**：vermeer 的设备驱动（显示 / 相机 / 基带 / 传感器 / 触控等）只存在于 5.15 vendor 树；6.6 GKI 树中**没有这些驱动**（配置项在 `olddefconfig` 时被丢弃）。同时原厂 vendor_boot / vendor_dlkm 里的模块是按 **android13-5.15 KMI** 编译的，与 6.6 内核 vermagic 不兼容。刷入后**无法启动或硬件全部失效**。
> - **Root 方案**：与 `sukisu-susfs` 分支相同 —— SukiSU-Ultra（`builtin` 分支）+ SUSFS（[`gki-android15-6.6`](https://gitlab.com/simonpunk/susfs4ksu/-/tree/gki-android15-6.6) 补丁，0 rejects），全部 `CONFIG_KSU_SUSFS_*` 选项开启。
> - **vermagic**：`6.6.143-android15-6.6`（对齐官方 GKI release 格式；禁用 `LOCALVERSION_AUTO` 去掉 `-g<sha>` 后缀）。
> - **vendor_boot**：实验性打包 —— GKI 6.6 树自产的模块（flat 布局）；GKI 树没有 vermeer 的 vendor 模块清单（`gki_system_dlkm_modules` / `modules.list.msm.vermeer` 是 5.15 树文件）。
> - **结论**：满足"尝试迁移到 6.6"的构建可行性验证 —— 6.6 GKI 基线 + vermeer 配置可完整编译出 Image / 模块 / boot.img / vendor_boot.img；但要做出**可日用的 6.6**，需要小米官方放出 6.6 vendor 源码（OSS 分支），或整个 vendor 驱动栈的社区移植（数月工作量）。
>
> 调研结论（2026-10）：MiCode 无任何 6.6 分支（266 个分支全查）；LineageOS / Everest / 一加等同 SoC（SM8550）社区树全部停留在 5.15 —— **不存在现成的 vermeer 6.6 基线**。

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
- OSS 树整个剥离了 `drivers/misc/hwid/`，但 `drivers/usb/repeater/repeater-qti-pmic-eusb2.c` 仍包含 `../../misc/hwid/hwid.h` 并调用 `get_hw_version_platform()`/`get_hw_country_version()`。工作流会生成一个 **stub 头文件**（返回值不匹配任何真实项目/国家），使 eUSB2 驱动走标准 `qcom,param-override-seq` 调参路径（ms scheme 关闭）；真实设备上小米的国别/硬件特调不会生效。
- 所有 `make` 调用都重定向了 stdin（`< /dev/null`）：该内核树的构建脚本里存在**裸 `bc` 调用**，会阻塞在 stdin 上导致构建假死（曾出现 6 小时零输出）。
- GKI 默认强制 `CONFIG_WERROR=y`（源码里未直接设置，由 GKI Kconfig 强制）；apt 回退工具链 clang 18 比官方 clang r450784e 新，会把树里个别高通旧代码（如 `drivers/soc/qcom/minidump_log.c` 的 implicit-int）升级为错误，因此工作流会**关闭 WERROR**（降级为警告，不中断构建）。另外该树顶层 `Makefile` 还**硬编码**了 `-Werror=implicit-int` 和 `-Werror=implicit-function-declaration`（与 CONFIG_WERROR 无关），工作流通过 `KCFLAGS` 把 GKI 顶层 Makefile 硬编码的、clang 认识的 `-Werror=` 类别（implicit-int、implicit-function-declaration、strict-prototypes、return-type、date-time、incompatible-pointer-types）统一降级为警告（KCFLAGS 在 KBUILD_CFLAGS 之后追加，优先级更高；警告仍会打印）。注意不能加入 clang 不认识的类别（如 GCC 专有的 designated-init），否则会让 `cc-option` 探测保留该旗标导致编译失败。

## 断点续编（应对 6 小时任务上限）

GitHub 免费单任务上限 6 小时，完整 `Image + modules` 构建在 4 核 runner 上可能超时。工作流会把 `kernel/out` 构建树缓存到 actions/cache（键 `k70-out-<分支>-<run_id>`，恢复时按前缀取最近一次），构建步骤自带 **270 分钟**超时——超时会先把 `out/` 存入缓存再退出，下一次运行把源码时间戳回拨后自动**断点续编**（已编译对象直接复用）；也可在 Run workflow 时用 `build_targets` 输入手动分轮（先 `Image`，再 `modules`）。

## 产物（Actions Artifacts）

| 文件 | 说明 |
|---|---|
| `boot.img` | **Boot 镜像**（boot image header v4，官方参数，未签名） |
| `vendor_boot.img` | **Vendor Boot 镜像**（v4，官方 cmdline + 官方模块清单；见下方打包说明） |
| `init_boot.img` | **Init Boot 镜像**（提供 `stock/init_boot.img` 时原样附带；见下方说明） |
| `vendor_ramdisk.cpio.gz` | vendor_boot 的 vendor ramdisk 原始 cpio（供自定义重打包） |
| `vendor_boot.modules.load` / `vendor_dlkm-modules.tar.gz` | 第一阶段模块清单 / vendor_dlkm 分区模块集（镜像外模块） |
| `boot/Image` | 内核镜像（GKI `Image`，未压缩，`boot.img` 的 kernel 段同物） |
| `boot/System.map` | 符号表 |
| `Module.symvers` | 模块符号版本（编译外部模块需要） |
| `modules.tar.gz` | 全部内核模块（`modules_install` + depmod） |
| `kernel.config` / `merged-defconfig` | 实际使用的内核配置 |
| `BUILD-INFO.txt` | 源码提交、内核版本、工具链等元信息 |
| `build.log` | 完整构建日志 |

## Boot / Init Boot / Vendor Boot 打包说明

官方打包参数全部取自内核树自带的 `build.config.msm.vermeer` / `build.config.msm.common`：

- `boot.img`：`mkbootimg --header_version 4 --kernel Image --cmdline "" --base 0x80000000 --pagesize 4096`（`BOOT_IMAGE_HEADER_VERSION=4`、`BASE_ADDRESS`、`PAGE_SIZE` 均官方值）。GKI boot v4 的 cmdline 为空，引导参数在 vendor_boot 的 `vendor_cmdline` 里。**未签名**（GKI `boot_signature` 需 Google 认证密钥，无法生成）。
- `vendor_boot.img`：`vendor_cmdline` 为官方 gki 变体值（`console=ttyMSM0,115200n8 earlycon=qcom_geni,0x00a9C000 qcom_geni_serial.con_enabled=1 nosoftlockup bootconfig`）；vendor ramdisk 按官方规则构造——`android/gki_system_dlkm_modules` + `modules.list.msm.vermeer` 两个官方清单内的模块（过滤掉 OSS 树剥离后无法编译的，如 `hwid.ko`）+ `modules.load` + 官方 blocklist + depmod 元数据；其余模块按官方 `prepare_vendor_dlkm` 逻辑归入 `vendor_dlkm-modules.tar.gz`。
- `init_boot.img`：其 generic ramdisk 是 **AOSP 用户态**（`/init` 二进制、linker 等），不属于内核源码，内核树无法构建。本构建通过提交树内修复消除 `-dirty` 后缀，release 字符串（`5.15.78`）与官方从此 OSS 树干净构建的产物一致；若你手上官方 init_boot 内模块的 vermagic 与 `5.15.78` 不一致（小米出厂固件可能由内部树构建、带不同后缀），则不能直通——需用本仓库的模块重打 ramdisk。把官方 `init_boot.img` 放进仓库 `stock/` 目录重新触发构建，它会被原样打进 artifacts。

### 如何补齐 DTB 与官方镜像参数（`stock/` 目录）

内核树不包含设备树（`DTB_DIR=vendor/qcom` 的 DTS 被 OSS 剥离），因此默认打包的 `vendor_boot.img` **不含 DTB**。补齐方法：

1. 用 [payload-dumper-go](https://github.com/ssut/payload-dumper-go) 从红米 K70 官方完整卡刷包（`.zip` 内 `payload.bin`）提取 `boot.img`、`init_boot.img`、`vendor_boot.img`、`vbmeta.img`；
2. 在本仓库建 `stock/` 目录，放入 `vendor_boot.img`（必需，用于提取真实设备 DTB + bootconfig）和 `init_boot.img`（用于附带），提交推送或手动触发构建；
3. 构建会自动从 `stock/vendor_boot.img` 解包提取 DTB 与 bootconfig，用官方参数重打 `vendor_boot.img`，并把 `stock/init_boot.img` 原样附进 artifacts。

### 刷机（自行承担风险）

- 前提：Bootloader 已解锁；产物未签名，需关闭 AVB 校验：
  `fastboot flash vbmeta --disable-verity --disable-verification vbmeta.img`（vbmeta 用官方卡刷包提取的那份）
- 刷入三件：`fastboot flash boot boot.img` → `fastboot flash vendor_boot vendor_boot.img` →（如提供了 stock）`fastboot flash init_boot init_boot.img`
- `vendor_dlkm-modules.tar.gz` 中的模块对应真机 `vendor_dlkm` 分区；如需刷入需自行重打包 ext4/EROFS 镜像（超出本仓库范围）。
- 首次刷自定义内核建议先 `fastboot boot boot.img` 临时引导测试（无 dtb 的 vendor_boot 在真机上无法引导时，必须先补齐 `stock/vendor_boot.img`）。

## 使用

- **自动触发**：推送到 `main` 分支即触发构建
- **手动触发**：Actions → *Build Redmi K70 Kernel* → *Run workflow*（可选源码分支、工具链、LTO 模式、构建目标 `build_targets`）

## 实验性分支：linux-6.6-port（6.6 + 厂商驱动移植）

`linux-6.6-port` 分支在 AOSP GKI android15-6.6（6.6.143）之上移植了 MiCode vermeer 5.15 开源厂商驱动栈，CI 全绿（build-kernel-6.6-port.yml）。

> **诚实声明：编译通过 ≠ 可以开机**。SM8550（8 Gen 3）整机厂驱动栈迁到 6.6 属无先例操作；运行时正确性（能否开机、各外设是否工作）**只能在真机上验证**，CI 无法保证。刷入风险自负，务必备份 boot/init_boot/vendor_boot 原厂镜像。

**移植架构**：msm DRM/摄像头媒体栈整目录替换；soc/clk/pinctrl/interconnect 等以 5.15 版覆盖 6.6 同名文件（仅当 6.6 无同名文件时）；Kconfig/Makefile 自动合并 5.15 定义块；编译期 API 漂移逐个适配（class_create、ww_mutex、iommu domain ops、qcom_icc_node、android_debug_symbol 等约 40 处）。

**官方模块清单覆盖：45/108**（另有 ufs_qcom 等以 6.6 上游横线文件名构建，名单按 basename 严格匹配会误判为 missing）。已构建的关键栈：

- **FBE 全盘加密链**：hwkm.ko + crypto-qti-hwkm.ko + crypto-qti-common.ko + tmecom-intf.ko + qcom-scm.ko（含 qtee_shmbridge + 移植的 qcom_scm ES v2 调用）——userdata 加密挂载所需
- **存储**：ufs-qcom.ko + qcom_ice.ko + phy-qcom-ufs-qmp-v4-kalama.ko + sdhci-msm.ko + cqhci.ko
- **SoC 基础**：pinctrl-kalama、pinctrl-msm、clk-rpmh、icc-rpmh、qcom_rpmh、smem、socinfo、cmd-db、qcom_ipcc、qcom_aoss、qcom-pdc
- **调试/可靠性**：minidump.ko（core）、debug_symbol、qcom_logbuf_vh、dcc_v2、iommu-logger、arm_smmu
- **上游替代 5.15 私有驱动**：gcc/dispcc/videocc/gpucc-sm8550（时钟）、interconnect-qcom-sm8550（总线）、qcom-tsens（温度）、qcom-wdt（看门狗）

**已知接受的损失**（官方清单内但放弃移植）：

- 显示/相机/GPU(kgsl)/WiFi 闭源相关约 40 个：OSS 源码被小米剥离，5.15 时代就编不出，与 6.6 无关
- `sched-walt`：WALT 调度器深度依赖 5.15 的 cfs_rq 内部结构，6.6 调度器重构后无法缝合（退回上游 EAS）
- `qcom_iommu_util`：5.15 fast-pgtable IOMMU 加速器，移植需整体替换 6.6 IOMMU 核心且会破坏已可用的 arm-smmu
- `mem-hooks`/`mem-offline`/`minidump_log`/`QCOM_MINIDUMP_PANIC_DUMP`：依赖 6.6 已移除的 mm/kallsyms 内部接口
- `clk-dummy` 等 kalama 私有时钟：由上游 sm8550 时钟驱动替代（功能等价）

## 说明与注意

- 红米 K70 的**设备树（DTB）不在开源内核树中**（`DTB_DIR=vendor/qcom` 的 DTS 被 OSS 剥离）；默认 `vendor_boot.img` 不含 DTB，按上方 `stock/` 目录方法补齐后即为完整可引导配置。
- 产物的签名密钥与小米官方发布的不同（**未签名**，无 GKI boot_signature），官方线刷/卡刷包校验不会通过；解锁 Bootloader 并关闭 AVB 校验后可 `fastboot` 刷入（见上方刷机节）。模块已与本内核配套重打包进 `vendor_boot.img`。
- `vendor_boot.img` 内不含 `hwid.ko`、`mi_power.ko` 等小米闭源模块（OSS 树剥离了其源码，无法编译）；官方清单内其余模块齐全。
- 编译 K70 系列 other 型号需改 workflow 中的分支与配置片段：`bsp-manet-u-oss`（K70 Pro，manet）/ `bsp-duchamp-u-oss`（K70E，duchamp）。

## 参考

- [MiCode/Xiaomi_Kernel_OpenSource](https://github.com/MiCode/Xiaomi_Kernel_OpenSource)
- 内核树内官方构建配置：`build.config.msm.vermeer` / `build.config.msm.gki` / `build.config.aarch64`
