# vermeer (Redmi K70) 相机硬件事实档案

数据来源：官方 HyperOS 3.0.307（Android 16）线刷包
- `dtbo.img` entry[53] = "8550 vermeer" overlay（381KB，小米官方相机 DT）
- `super.img` → odm_a 分区 lib64/camera/（camx 传感器模块）
- `super.img` → vendor_dlkm_a 分区 camera.ko（7MB，未 strip）

## 相机阵列（全部双供应商冗余设计）

| 角色 | 传感器 | 模组厂 | CCI | CSIPHY | TLMM GPIO | xclk |
|---|---|---|---|---|---|---|
| 主摄 wide | **OV50E (OVX8000)** | ofilm / AAC | 0 | **5** | 102, 118 | 19.2 MHz |
| 超广 ultra | **IMX355**（索尼） | ofilm | **1** | 2 | — | 19.2 MHz |
| 前摄 front | **OV16A1Q / GC16B3** | AAC | 0 | 4 | 100, 120 | 19.2 MHz |
| 微距 macro | **GC02M1**（格科微） | ofilm | 0 | 3 | 103, 119 | 19.2 MHz |

- 对焦马达：GT9764（AAC），I2C 挂 CCI0
- EEPROM：GT24P64E / P24C128E / P24C64F（各摄独立）
- 主摄安装方向：yaw 180°、roll 90°（图像需旋转校正）

## 电源轨（主摄）

| 轨 | 电压 | 用途 |
|---|---|---|
| cam_vana | 2.8V | 模拟 |
| cam_vio | 1.8V | IO |
| cam_vdig | **1.104V** | 数字核心 |
| cam_v_custom1 | 3.1V | OIS/辅助 |
| cam_vaf | （VCM 轨） | 对焦马达 |

前摄 vdig = 1.2V；微距仅 vana + vio。

## OV50E 传感器级参数

- 7-bit I2C 地址：**0x10**（write id 0x20）；EEPROM：0x50
- Chip ID：**0x5045**（寄存器 0x300b/0x300c）
- MIPI：**C-PHY 3-trio**（2200 Msps/trio，摩托罗拉表）
- 曝光：0x3500[19:16]/0x3501[15:8]/0x3502[7:0]（20-bit）
- 模拟增益：0x3508[9:8]/0x3509[7:0]（reg = gain × 16）
- 帧长：0x3840-0x3842（20-bit VTS）
- 模式（像素时钟 600MHz）：
  - 8192x6144@20（全分辨率）：HTS 4400 / VTS 6816
  - 4096x3072@30（4-cell bin）：HTS 4400 / VTS 4544
  - 2048x1536@120 / 1920x1080@240（慢动作）：HTS 2496 / VTS 2002
- 寄存器表来源：MotorolaMobilityLLC/kernel-mtk（GPL-2.0，
  mot_aion_ov50e_mipi_raw/setting/），已由脚本转换进 ov50e.c

## stock 系统相机 DT 的藏身之处（考古结论）

- vendor_boot.img DTB（8 FDT）：**无相机节点**（小米剥离）
- boot.img kernel：无内嵌 DTB（GKI 规范）
- **dtbo.img：57 个 overlay 条目**，覆盖小米 8550 全家族
  （babylon/fuxi/ishtar/nuwa/sheng/socrates/vermeer + QCOM 参考板）
  ——bootloader 按 codename 选中 vermeer 条目叠加到主 DTB
- 这就是"MiCode 源码没有相机 dtsi 但手机相机能用"的答案

## 6.6 移植用到的兼容事实

- CCI 驱动：6.6 `i2c-qcom-cci.c` 无 sm8550 compatible，DT 用
  `"qcom,sm8550-cci", "qcom,msm8996-cci"`（v2 硬件兼容 fallback）
- CCI 引脚：cci0=gpio110/111+112/113，cci1=gpio114/115（cci2=gpio74/75
  存在于硬件但 vermeer overlay 未挂传感器）
- camss 平台节点（寄存器/中断/时钟名）= SM8550 平台常量，直接取自
  上游 sm8550.dtsi（与 stock reserved-memory camera_region@9b300000 一致）
