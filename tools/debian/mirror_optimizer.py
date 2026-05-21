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

    def _detect_repo(self, content: str) -> tuple[str, str, str]:
        """Detect archive, codename, and distro family from existing sources.list.

        Returns (archive, codename, family) where family is 'ubuntu' or 'debian'.
        """
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            match = re.match(r"(?:deb|deb-src)\s+https?://\S+/(\S+)\s+(\S+)", line)
            if match:
                archive = match.group(1)
                codename = match.group(2)
                family = "ubuntu" if "ubuntu" in archive else "debian"
                return archive, codename, family
        return "debian", "bookworm", "debian"

    def build_sources(self, content: str) -> str:
        archive, codename, family = self._detect_repo(content)
        mirror = CHINA_MIRRORS[0]

        if family == "ubuntu":
            components = "main restricted universe multiverse"
            lines = [
                f"# China mirror (fastest for mainland China)",
                f"deb https://{mirror}/{archive} {codename} {components}",
                f"deb-src https://{mirror}/{archive} {codename} {components}",
                "",
                f"deb https://{mirror}/{archive} {codename}-updates {components}",
                f"deb-src https://{mirror}/{archive} {codename}-updates {components}",
                "",
                f"deb https://{mirror}/{archive} {codename}-backports {components}",
                f"deb-src https://{mirror}/{archive} {codename}-backports {components}",
                "",
                f"deb https://{mirror}/{archive} {codename}-security {components}",
                f"deb-src https://{mirror}/{archive} {codename}-security {components}",
            ]
        else:
            components = "main contrib non-free non-free-firmware"
            lines = [
                f"# China mirror (fastest for mainland China)",
                f"deb https://{mirror}/{archive} {codename} {components}",
                f"deb-src https://{mirror}/{archive} {codename} {components}",
                "",
                f"deb https://{mirror}/{archive} {codename}-updates {components}",
                f"deb-src https://{mirror}/{archive} {codename}-updates {components}",
                "",
                f"deb https://{mirror}/{archive}-security {codename}-security {components}",
                f"deb-src https://{mirror}/{archive}-security {codename}-security {components}",
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
