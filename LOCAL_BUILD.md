# 本地编译指南（Local Build）

本分支已包含**完整内核源码**（补丁已预应用），clone 即可编译。

> ⚠️ **必须在大小写敏感的文件系统上操作**：Linux 原生、WSL2 的 ext4  home 目录（不要用 /mnt/c）、或 macOS 的大小写敏感 APFS 卷。内核树含有仅靠大小写区分的文件（如 `xt_CONNMARK.h`/`xt_connmark.h`），Windows NTFS 默认配置下无法 checkout。

## 环境准备（Ubuntu 22.04/24.04）

```bash
sudo apt-get update
sudo apt-get install -y build-essential bc bison flex cpio zip unzip curl wget git rsync \
  libssl-dev libelf-dev libncurses-dev zstd lz4 lzop u-boot-tools kmod dwarves \
  python3 python-is-python3 clang lld llvm
```

## 编译

### main / sukisu-susfs（5.15.78，官方源码 [+ SukiSU/SUSFS]）

```bash
git clone -b <分支名> https://github.com/yangyang8002/Redmi-K70-Kernel.git kernel
cd kernel
# 生成 .config（GKI 官方流程：gki_defconfig + vermeer vendor fragment）
make O=out ARCH=arm64 LLVM=1 gki_defconfig
cp out/.config .config
./scripts/kconfig/merge_config.sh -m .config arch/arm64/configs/vendor/vermeer_GKI.config
mv .config out/.config
make O=out ARCH=arm64 LLVM=1 olddefconfig
# ThinLTO（与 CI 默认一致）
./scripts/config --file out/.config -d WERROR -d LTO_NONE -e LTO_CLANG_THIN
make -j"$(nproc)" O=out ARCH=arm64 LLVM=1 \
     KCFLAGS='-Wno-error=implicit-int -Wno-error=implicit-function-declaration -Wno-error=strict-prototypes -Wno-error=return-type -Wno-error=date-time -Wno-error=incompatible-pointer-types' \
     Image modules < /dev/null
```

### linux-6.6 / linux-6.6-port（GKI 6.6.143 [+ vermeer 驱动移植]）

```bash
git clone -b <分支名> https://github.com/yangyang8002/Redmi-K70-Kernel.git kernel
cd kernel
make O=out ARCH=arm64 LLVM=1 gki_defconfig
cp out/.config .config
./scripts/kconfig/merge_config.sh -m .config arch/arm64/configs/vendor/vermeer_GKI.config
mv .config out/.config
make O=out ARCH=arm64 LLVM=1 olddefconfig
./scripts/config --file out/.config -d WERROR -d LTO_NONE   # 6.6-port 默认不开 LTO
make -j"$(nproc)" O=out ARCH=arm64 LLVM=1 \
     KCFLAGS='-Wno-error=implicit-int -Wno-error=implicit-function-declaration -Wno-error=strict-prototypes -Wno-error=int-conversion' \
     Image modules < /dev/null
# linux-6.6-port 另含相机测试 DTB：
make O=out ARCH=arm64 LLVM=1 qcom/sm8550-vermeer-camss-test.dtb
```

## 产物

- 内核：`out/arch/arm64/boot/Image`
- 模块：`find out -name '*.ko'`
- 配置：`out/.config`

## 参考

- 打包 boot/init_boot/vendor_boot 镜像：见 README.md「Boot / Init Boot / Vendor Boot 打包说明」
- 相机移植细节：`port-6.6/CAMERA_NOTES.md`（linux-6.6-port 分支）
