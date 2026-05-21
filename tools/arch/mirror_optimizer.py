import shutil
from pathlib import Path

from utils.sudo_utils import write_file, need_sudo

MIRRORLIST = Path("/etc/pacman.d/mirrorlist")
BACKUP_SUFFIX = ".bak"

CHINA_MIRRORS = [
    "https://mirrors.ustc.edu.cn/archlinux/$repo/os/$arch",
    "https://mirrors.tuna.tsinghua.edu.cn/archlinux/$repo/os/$arch",
    "https://mirrors.sjtug.sjtu.edu.cn/archlinux/$repo/os/$arch",
    "https://mirrors.aliyun.com/archlinux/$repo/os/$arch",
    "https://mirrors.163.com/archlinux/$repo/os/$arch",
    "https://repo.huaweicloud.com/archlinux/$repo/os/$arch",
]


class ArchMirrorOptimizer:
    name = "arch-mirror-optimizer"
    display_name = "Optimize Pacman Mirrors"
    description = "Add China mirrors to the top of /etc/pacman.d/mirrorlist"
    distros = ["arch"]

    def backup(self) -> bool:
        backup_path = MIRRORLIST.with_suffix(MIRRORLIST.suffix + BACKUP_SUFFIX)
        if backup_path.exists():
            return False
        shutil.copy2(MIRRORLIST, backup_path)
        return True

    def restore(self) -> None:
        backup_path = MIRRORLIST.with_suffix(MIRRORLIST.suffix + BACKUP_SUFFIX)
        if not backup_path.exists():
            raise FileNotFoundError("No backup found")
        from utils.sudo_utils import copy_file
        copy_file(backup_path, MIRRORLIST)

    def build_mirrorlist(self) -> str:
        header_lines = [
            "#" * 80,
            "#" + " China mirrors (fastest for mainland China) ".center(78, " ") + "#",
            "#" * 80,
        ]
        mirrors = "\n".join(f"Server = {m}" for m in CHINA_MIRRORS)
        original = MIRRORLIST.read_text() if MIRRORLIST.exists() else ""
        return "\n".join(header_lines) + "\n" + mirrors + "\n\n" + original

    def apply(self, content: str) -> None:
        write_file(MIRRORLIST, content)

    def run(self) -> bool:
        if not MIRRORLIST.exists():
            print("Error: /etc/pacman.d/mirrorlist not found")
            return False

        if need_sudo(MIRRORLIST):
            print("Root privileges required")

        backed_up = self.backup()
        if backed_up:
            print(f"Backup saved to {MIRRORLIST}{BACKUP_SUFFIX}")
        else:
            print("Backup already exists, skipped")

        content = self.build_mirrorlist()
        self.apply(content)
        print("Mirrorlist updated with China mirrors at top")
        return True
