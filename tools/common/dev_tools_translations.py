"""Dev tools setup translations / 开发工具安装翻译."""

from utils.i18n import register_translations

register_translations("en", {
    "msg.devtool_all": "All Toolchains",
    "msg.devtool_all_desc": "Install all available toolchains",
    "msg.devtool_already_installed": "{toolchain} is already installed.",
    "msg.devtool_arm_gcc": "ARM GCC Toolchain",
    "msg.devtool_arm_gcc_desc": "Install arm-none-eabi-gcc for ARM Cortex-R/M embedded development",
    "msg.devtool_install_failed": "Failed to install toolchain.",
    "msg.devtool_install_success": "{toolchain} installed successfully.",
    "msg.devtool_installing": "Installing: {packages}...",
    "msg.devtool_riscv_gcc": "RISC-V GCC Toolchain",
    "msg.devtool_riscv_gcc_desc": "Install riscv64-elf-gcc for RISC-V embedded development",
    "msg.devtool_select": "Select toolchain to install:",
    "tool.dev-tools.description": "Quick install embedded toolchains (ARM GCC, RISC-V GCC)",
    "tool.dev-tools.display_name": "Dev Tools Setup",
})

register_translations("zh", {
    "msg.devtool_all": "全部工具链",
    "msg.devtool_all_desc": "安装所有可用工具链",
    "msg.devtool_already_installed": "{toolchain} 已安装。",
    "msg.devtool_arm_gcc": "ARM GCC 工具链",
    "msg.devtool_arm_gcc_desc": "安装 arm-none-eabi-gcc 用于 ARM Cortex-R/M 嵌入式开发",
    "msg.devtool_install_failed": "工具链安装失败。",
    "msg.devtool_install_success": "{toolchain} 安装成功。",
    "msg.devtool_installing": "正在安装：{packages}...",
    "msg.devtool_riscv_gcc": "RISC-V GCC 工具链",
    "msg.devtool_riscv_gcc_desc": "安装 riscv64-elf-gcc 用于 RISC-V 嵌入式开发",
    "msg.devtool_select": "选择要安装的工具链：",
    "tool.dev-tools.description": "快速安装嵌入式工具链（ARM GCC、RISC-V GCC）",
    "tool.dev-tools.display_name": "开发工具安装",
})
