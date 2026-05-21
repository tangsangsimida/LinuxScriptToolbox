import re
import shutil
from pathlib import Path

from tools.base import Tool
from utils.sudo_utils import write_file, copy_file, need_sudo
from utils.i18n import t

SOURCES_LIST = Path("/etc/apt/sources.list")
BACKUP_SUFFIX = ".bak"

CHINA_MIRRORS = [
    "mirrors.ustc.edu.cn",
    "mirrors.tuna.tsinghua.edu.cn",
    "mirrors.aliyun.com",
    "mirrors.163.com",
    "repo.huaweicloud.com",
]


class DebianMirrorOptimizer(Tool):
    name = "debian-mirror-optimizer"
    display_name = "Optimize APT Mirrors"
    description = "Replace mirrors in /etc/apt/sources.list with China mirrors"
    distros = ["debian"]

    def backup(self) -> bool:
        backup_path = SOURCES_LIST.with_suffix(SOURCES_LIST.suffix + BACKUP_SUFFIX)
        if backup_path.exists():
            return False
        copy_file(SOURCES_LIST, backup_path)
        return True

    def _detect_repo(self, content: str) -> tuple[str, str]:
        """Detect distro codename and archive type from existing sources.list."""
        codename = "bookworm"
        archive = "debian"
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            match = re.search(r"(deb|deb-src)\s+https?://\S+\s+(\w+)", line)
            if match:
                codename = match.group(2)
                if codename in ("stable", "testing", "unstable", "oldstable"):
                    break
                break
        if "ubuntu" in content.lower():
            archive = "ubuntu"
            for line in content.splitlines():
                match = re.search(r"https?://\S+\s+(\w+)-", line)
                if match:
                    codename = match.group(1)
                    break
        return archive, codename

    def build_sources(self, content: str) -> str:
        archive, codename = self._detect_repo(content)
        mirror = CHINA_MIRRORS[0]
        lines = [
            f"# China mirror (fastest for mainland China)",
            f"deb https://{mirror}/{archive} {codename} main contrib non-free non-free-firmware",
            f"deb-src https://{mirror}/{archive} {codename} main contrib non-free non-free-firmware",
            f"",
            f"deb https://{mirror}/{archive} {codename}-updates main contrib non-free non-free-firmware",
            f"deb-src https://{mirror}/{archive} {codename}-updates main contrib non-free non-free-firmware",
            f"",
            f"deb https://{mirror}/{archive}-security {codename}-security main contrib non-free non-free-firmware",
            f"deb-src https://{mirror}/{archive}-security {codename}-security main contrib non-free non-free-firmware",
        ]
        return "\n".join(lines) + "\n"

    def run(self) -> bool:
        if not SOURCES_LIST.exists():
            print(t("msg.sources_list_not_found"))
            return False

        if need_sudo(SOURCES_LIST):
            print(t("msg.root_required"))

        backed_up = self.backup()
        if backed_up:
            print(t("msg.backup_saved", path=f"{SOURCES_LIST}{BACKUP_SUFFIX}"))
        else:
            print(t("msg.backup_exists"))

        content = SOURCES_LIST.read_text()
        new_content = self.build_sources(content)
        write_file(SOURCES_LIST, new_content)
        print(t("msg.sources_list_updated"))
        return True
