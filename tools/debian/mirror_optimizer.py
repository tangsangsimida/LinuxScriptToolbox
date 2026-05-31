import re
from pathlib import Path

from tools.base import Tool
from utils.sudo_utils import write_file, copy_file, need_sudo
from utils.i18n import t
from utils.ui import print_success, print_error, print_info

SOURCES_LIST = Path("/etc/apt/sources.list")
DEB822_SOURCES = Path("/etc/apt/sources.list.d/ubuntu.sources")
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
    description = "Replace APT mirrors with China mirrors"
    distros = ["debian"]

    def _get_sources_path(self) -> Path | None:
        """Return the active sources file, preferring deb822 format."""
        if DEB822_SOURCES.exists():
            return DEB822_SOURCES
        if SOURCES_LIST.exists():
            content = SOURCES_LIST.read_text().strip()
            if content and not content.startswith("# Ubuntu sources have moved"):
                return SOURCES_LIST
        return None

    def backup(self, path: Path) -> bool:
        backup_path = path.with_suffix(path.suffix + BACKUP_SUFFIX)
        if backup_path.exists():
            return False
        copy_file(path, backup_path)
        return True

    # --- deb822 format ---

    def _parse_deb822(self, content: str) -> list[dict[str, str]]:
        """Parse deb822 format into list of stanzas."""
        stanzas = []
        current: dict[str, str] = {}
        for line in content.splitlines():
            if not line.strip():
                if current:
                    stanzas.append(current)
                    current = {}
            elif line.startswith("#"):
                continue
            elif ":" in line:
                key, _, val = line.partition(":")
                current[key.strip()] = val.strip()
        if current:
            stanzas.append(current)
        return stanzas

    def _build_deb822(self, stanzas: list[dict[str, str]]) -> str:
        """Rebuild deb822 content from stanzas."""
        blocks = []
        for s in stanzas:
            lines = [f"{k}: {v}" for k, v in s.items()]
            blocks.append("\n".join(lines))
        return "\n\n".join(blocks) + "\n"

    def optimize_deb822(self, content: str) -> str:
        mirror = f"https://{CHINA_MIRRORS[0]}/ubuntu/"
        stanzas = self._parse_deb822(content)
        for s in stanzas:
            if "URIs" in s:
                s["URIs"] = mirror
        return self._build_deb822(stanzas)

    # --- traditional format ---

    def _detect_repo(self, content: str) -> tuple[str, str, str]:
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

    def optimize_traditional(self, content: str) -> str:
        archive, codename, family = self._detect_repo(content)
        mirror = CHINA_MIRRORS[0]

        if family == "ubuntu":
            comp = "main restricted universe multiverse"
            lines = [
                "# China mirror (fastest for mainland China)",
                f"deb https://{mirror}/{archive} {codename} {comp}",
                f"deb-src https://{mirror}/{archive} {codename} {comp}",
                "",
                f"deb https://{mirror}/{archive} {codename}-updates {comp}",
                f"deb-src https://{mirror}/{archive} {codename}-updates {comp}",
                "",
                f"deb https://{mirror}/{archive} {codename}-backports {comp}",
                f"deb-src https://{mirror}/{archive} {codename}-backports {comp}",
                "",
                f"deb https://{mirror}/{archive} {codename}-security {comp}",
                f"deb-src https://{mirror}/{archive} {codename}-security {comp}",
            ]
        else:
            comp = "main contrib non-free non-free-firmware"
            lines = [
                "# China mirror (fastest for mainland China)",
                f"deb https://{mirror}/{archive} {codename} {comp}",
                f"deb-src https://{mirror}/{archive} {codename} {comp}",
                "",
                f"deb https://{mirror}/{archive} {codename}-updates {comp}",
                f"deb-src https://{mirror}/{archive} {codename}-updates {comp}",
                "",
                f"deb https://{mirror}/{archive}-security {codename}-security {comp}",
                f"deb-src https://{mirror}/{archive}-security {codename}-security {comp}",
            ]
        return "\n".join(lines) + "\n"

    # --- main ---

    def run(self) -> bool | None:
        sources_path = self._get_sources_path()
        if sources_path is None:
            print_error(t("msg.sources_list_not_found"))
            return False

        is_deb822 = sources_path == DEB822_SOURCES
        fmt = "deb822" if is_deb822 else "traditional"
        print_info(t("msg.detected_format", format=fmt, path=str(sources_path)))

        if need_sudo(sources_path):
            print_info(t("msg.root_required"))

        backed_up = self.backup(sources_path)
        if backed_up:
            print_info(t("msg.backup_saved", path=f"{sources_path}{BACKUP_SUFFIX}"))
        else:
            print_info(t("msg.backup_exists"))

        content = sources_path.read_text()
        if is_deb822:
            new_content = self.optimize_deb822(content)
        else:
            new_content = self.optimize_traditional(content)

        write_file(sources_path, new_content)
        print_success(t("msg.sources_list_updated"))
        return True
