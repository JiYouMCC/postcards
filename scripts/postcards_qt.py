from __future__ import annotations

import argparse
import ast
import csv
import importlib.util
import json
import locale
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PySide6.QtCore import QDate, QSortFilterProxyModel, Qt, QUrl
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QDesktopServices,
    QFont,
    QFontDatabase,
    QGuiApplication,
    QPixmap,
    QStandardItem,
    QStandardItemModel,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QTableView,
    QTabWidget,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


DISPLAY_COLUMNS = [
    ("id", "ID"),
    ("title", "Title"),
    ("type", "Type"),
    ("platform", "Platform"),
    ("friend_id", "Friend"),
    ("country", "Country"),
    ("region", "Region"),
    ("sent_date", "Sent Date"),
    ("received_date", "Received Date"),
    ("tags", "Tags"),
]

IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]
ROW_FIELDNAMES = [
    "no",
    "id",
    "title",
    "type",
    "platform",
    "friend_id",
    "country",
    "region",
    "sent_date",
    "received_date",
    "tags",
    "url",
    "friend_url",
]
POSTHI_EXCLUDE_LIST = {
    "PHCNGD-0767",
    "PHCNZJ-1410",
    "PHCNFJ-1299",
    "PHCNSH-1876",
    "PHCNSC-0865",
    "PHCNZJ-3796",
    "PHCNJX-0993",
    "PHCNGD-5164",
    "PHCNSX-0251",
    "PHCNSC-0417",
    "PHCNHL-0176",
}


class AppTranslator:
    def __init__(self, mapping: dict[str, str]) -> None:
        self.mapping = mapping

    def tr(self, text: str) -> str:
        if not text:
            return text
        return self.mapping.get(text, text)

    def translate_value(self, key: str, value: str) -> str:
        if not value:
            return value
        if key in {"platform", "country", "region", "type"}:
            return self.tr(value)
        return value


def detect_default_language() -> str:
    system_lang = (locale.getlocale()[0] or "").lower()
    if system_lang.startswith("zh"):
        return "zh"
    return "en"


def load_translation_map(project_root: Path, language: str) -> dict[str, str]:
    i18n_path = project_root / "lg" / f"basic-{language}.json"
    if not i18n_path.exists():
        return {}
    with i18n_path.open("r", encoding="utf-8") as f:
        loaded = json.load(f)
    if not isinstance(loaded, dict):
        return {}
    return {str(k): str(v) for k, v in loaded.items()}


def apply_readable_app_font(app: QApplication, language: str) -> None:
    preferred_families = [
        "Noto Sans CJK SC",
        "Noto Sans SC",
        "Source Han Sans SC",
        "Source Han Sans CN",
        "Sarasa UI SC",
        "WenQuanYi Micro Hei",
        "LXGW WenKai",
    ]
    db = QFontDatabase()
    available = set(db.families())
    chosen_family = next((name for name in preferred_families if name in available), "")

    base_font = app.font()
    if chosen_family:
        app_font = QFont(chosen_family)
    else:
        app_font = QFont(base_font)

    app_font.setPointSize(13)
    app.setFont(app_font)


def center_window(window: QWidget) -> None:
    screen = window.screen() or QGuiApplication.primaryScreen()
    if screen is None:
        return
    frame = window.frameGeometry()
    frame.moveCenter(screen.availableGeometry().center())
    window.move(frame.topLeft())


def load_csv_records(path: Path, direction: str) -> list[dict[str, str]]:
    if not path.exists():
        return []
    records: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            clean = {k: (v or "").strip() for k, v in row.items()}
            clean["direction"] = direction
            records.append(clean)
    return records


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({field: (row.get(field, "") or "").strip() for field in ROW_FIELDNAMES})
    return rows


def write_csv_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ROW_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in ROW_FIELDNAMES})


def find_image_path(root: Path, direction: str, postcard_id: str) -> Path | None:
    if not postcard_id:
        return None
    folder = root / ("received" if direction.lower() == "received" else "sent")
    for ext in IMAGE_EXTENSIONS:
        candidate = folder / f"{postcard_id}{ext}"
        if candidate.exists():
            return candidate
    return None


def normalize_postcard_id_for_dedupe(postcard_id: str) -> str:
    normalized = postcard_id.strip()
    while True:
        match = re.match(r"^(.*)-(\d+)$", normalized)
        if match is None:
            return normalized
        prefix = match.group(1).strip()
        # Only treat trailing -N as manual copy suffix when the prefix still carries numeric id content.
        if not re.search(r"\d", prefix):
            return normalized
        normalized = prefix


def append_rows_with_dedupe(target_file: Path, new_rows: list[list[str]]) -> int:
    with target_file.open("r", encoding="utf-8", newline="") as f:
        existing = list(csv.reader(f))
    existing_dedupe_keys = {
        normalize_postcard_id_for_dedupe(row[1]) for row in existing[1:] if len(row) > 1 and row[1].strip()
    }
    to_write = []
    for row in new_rows:
        if len(row) <= 1 or not row[1].strip():
            continue
        dedupe_key = normalize_postcard_id_for_dedupe(row[1])
        if dedupe_key in existing_dedupe_keys:
            continue
        to_write.append(row)
        existing_dedupe_keys.add(dedupe_key)
    if not to_write:
        return 0
    with target_file.open("a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(to_write)
    return len(to_write)


def run_python_script(project_root: Path, script_name: str) -> tuple[int, str]:
    script_path = project_root / "scripts" / script_name
    if not script_path.exists():
        return (1, f"Script not found: {script_path}")
    completed = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(project_root / "scripts"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = f"{completed.stdout}\n{completed.stderr}".strip()
    return (completed.returncode, output)


def parse_postcrossing_ids(raw: str) -> list[str]:
    pattern = re.compile(r"[A-Z]+-\d+")
    found = [match.group(0).strip().upper() for match in pattern.finditer(raw)]
    return list(dict.fromkeys(found))


def fetch_postcrossing_row(postcard_id: str, mode: str) -> list[str]:
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError as exc:
        raise RuntimeError("Please install requests and beautifulsoup4.") from exc

    response = requests.get(f"https://www.postcrossing.com/postcards/{postcard_id}", timeout=30, verify=False)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")

    sender_box = soup.find("div", class_="details-box sender")
    receiver_box = soup.find("div", class_="details-box receiver right")
    if sender_box is None or receiver_box is None:
        raise RuntimeError(f"Failed to parse postcard page: {postcard_id}")

    if mode == "received":
        target_box = sender_box
    else:
        target_box = receiver_box

    friend_tag = target_box.find("a", attrs={"itemprop": "url"})
    friend_id = friend_tag.text.strip() if friend_tag else ""

    country_tag = target_box.find("a", attrs={"itemprop": "addressCountry"})
    country = country_tag.text.strip() if country_tag else ""
    region = ""
    if country_tag and country_tag.get("title"):
        region = country_tag.get("title").split(",")[0].strip()
    if country == "Taiwan":
        country = "China"
        region = "台湾"

    sent_time_tag = sender_box.find("time")
    recv_time_tag = receiver_box.find("time")
    sent_date = ""
    recv_date = ""
    if sent_time_tag and sent_time_tag.get("title"):
        sent_raw = sent_time_tag.get("title").replace("Sent on ", "").replace(" (UTC)", "")
        sent_date = datetime.strptime(sent_raw, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S %z"
        )
    if recv_time_tag and recv_time_tag.get("title"):
        recv_raw = recv_time_tag.get("title").replace("Received on ", "").replace(" (UTC)", "")
        recv_date = datetime.strptime(recv_raw, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S %z"
        )

    postcard_url = f"https://www.postcrossing.com/postcards/{postcard_id}"
    friend_url = f"https://www.postcrossing.com/user/{friend_id}" if friend_id else ""
    return ["", postcard_id, "", "MATCH", "POSTCROSSING", friend_id, country, region, sent_date, recv_date, "", postcard_url, friend_url]


def load_date_helpers(project_root: Path):
    module_path = project_root / "scripts" / "date_format.py"
    spec = importlib.util.spec_from_file_location("date_format_helper", str(module_path))
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load scripts/date_format.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.parse_date, module.format_date


def parse_icy_entries(raw: str) -> list[list[str]]:
    text = raw.strip()
    entries: list[list[str]] = []
    if not text:
        return entries

    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, (list, tuple)) and len(item) >= 3:
                    entries.append([str(item[0]).strip(), str(item[1]).strip(), str(item[2]).strip()])
            if entries:
                return entries
    except Exception:
        pass

    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        row = next(csv.reader([stripped]))
        if len(row) < 3:
            continue
        entries.append([row[0].strip(), row[1].strip(), row[2].strip()])
    return entries


def normalize_posthi_country(country: str) -> str:
    mapping = {"中国": "China", "日本": "Japan", "马来西亚": "Malaysia"}
    return mapping.get(country, country)


def normalize_posthi_region(region: str) -> str:
    suffixes = [
        "壮族自治区",
        "回族自治区",
        "维吾尔自治区",
        "特别行政区",
        "自治区",
        "省",
        "市",
    ]
    normalized = region
    for suffix in suffixes:
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)]
            break
    return normalized


def build_posthi_row(row_source: list[str], mode: int, parse_date, format_date) -> list[str] | None:
    # mode: 0=received, 1=sent, 2=expired sent
    if not row_source:
        return None
    card_id = row_source[0].strip()
    if not card_id or card_id in POSTHI_EXCLUDE_LIST:
        return None

    if mode == 2 and (len(row_source) < 2 or row_source[1].strip() != "已过期"):
        return None

    prefix = 1 if mode == 2 else 0

    def cell(idx: int) -> str:
        return row_source[idx].strip() if idx < len(row_source) else ""

    card_type = cell(1 + prefix)
    if card_type == "匹配":
        card_type = "MATCH"
    elif card_type == "社区活动":
        card_type = "GAME"
    elif card_type in ("回寄", "赠送", "寄片"):
        card_type = "GIVE"

    friend_id = cell(5 + prefix)
    friend_url = cell(6 + prefix)
    location = cell(7 + prefix)
    location_parts = location.split(" ", 1) if location else [""]
    country = normalize_posthi_country(location_parts[0].strip())
    region = normalize_posthi_region(location_parts[1].strip()) if len(location_parts) > 1 else ""

    sent_date = ""
    received_date = ""
    if mode == 2:
        raw_sent = cell(15)
        sent_date = format_date(parse_date(raw_sent)) if raw_sent else ""
    else:
        raw_sent = cell(9) if cell(9) else cell(8)
        raw_received = cell(10)
        sent_date = format_date(parse_date(raw_sent)) if raw_sent else ""
        received_date = format_date(parse_date(raw_received)) if raw_received else ""

    return [
        "",
        card_id,
        "",
        card_type,
        "POST-HI",
        friend_id,
        country,
        region,
        sent_date,
        received_date,
        "",
        f"https://www.post-hi.com/card/{card_id}",
        friend_url,
    ]


def collect_posthi_rows(csv_path: Path, mode: int, parse_date, format_date) -> list[list[str]]:
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    result: list[list[str]] = []
    for row in rows[1:]:
        built = build_posthi_row(row, mode, parse_date, format_date)
        if built is not None:
            result.append(built)
    return result


def extract_date_from_string(value: str):
    if not value:
        return None
    match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", value)
    if not match:
        return None
    try:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        return datetime(year, month, day).date()
    except ValueError:
        return None


def split_tags(raw_tags: str) -> set[str]:
    if not raw_tags:
        return set()
    return {part.strip() for part in raw_tags.split() if part.strip()}


def load_pixmap_safely(image_path: Path) -> QPixmap:
    if not image_path.exists():
        return QPixmap()
    if image_path.suffix.lower() == ".png":
        try:
            from PIL import Image
            from PIL.ImageQt import ImageQt

            with Image.open(image_path) as img:
                qimage = ImageQt(img.convert("RGBA"))
            return QPixmap.fromImage(qimage)
        except Exception:
            return QPixmap()
    return QPixmap(str(image_path))


def fetch_icy_row(entry: list[str], mode: int, parse_date, format_date) -> list[str]:
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError as exc:
        raise RuntimeError("Please install requests and beautifulsoup4.") from exc

    card_type_raw, card_path, card_id = entry
    response = requests.get(f"https://icardyou.icu{card_path}", timeout=30, verify=False)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")

    card_type = card_type_raw
    if card_type == "配对":
        card_type = "MATCH"
    elif card_type in ("回寄", "赠送"):
        card_type = "GIVE"
    elif card_type == "活动":
        card_type = "GAME"

    user_links = soup.find_all("a", href=lambda href: href and href.startswith("/userInfo/homePage"))
    friend_id = user_links[mode].get_text(strip=True) if len(user_links) > mode else ""
    friend_url = f"https://icardyou.icu{user_links[mode]['href']}" if len(user_links) > mode else ""

    region_labels = soup.find_all("td", string=lambda s: s and "地区：" in s)
    region = ""
    if len(region_labels) > mode:
        region = region_labels[mode].find_next("td").get_text(strip=True)

    send_time_label = soup.find("td", string=lambda s: s and "发送时间：" in s)
    sent_date = ""
    if send_time_label is not None:
        sent_text = send_time_label.find_next("td").get_text(strip=True)
        sent_date = format_date(parse_date(sent_text))

    recv_time_label = soup.find("td", string=lambda s: s and "到达时间：" in s)
    received_date = ""
    if recv_time_label is not None:
        recv_text = recv_time_label.find_next("td").get_text(strip=True)
        received_date = format_date(parse_date(recv_text))

    return [
        "",
        card_id,
        "",
        card_type,
        "ICARDYOU",
        friend_id,
        "China",
        region,
        sent_date,
        received_date,
        "",
        f"https://icardyou.icu{card_path}",
        friend_url,
    ]


class PostcardFilterProxy(QSortFilterProxyModel):
    def __init__(self, direction: str) -> None:
        super().__init__()
        self.direction = direction
        self.search_text = ""
        self.platform_filter = "All"
        self.country_filter = "All"
        self.type_filter = "All"
        self.region_filter = "All"
        self.friend_filter = ""
        self.tag_filters: set[str] = set()
        self.sent_date_from = None
        self.sent_date_to = None
        self.received_date_from = None
        self.received_date_to = None
        self.expired_filter = "All"

    def refresh_rows_filter(self) -> None:
        self.beginFilterChange()
        self.endFilterChange(QSortFilterProxyModel.Direction.Rows)

    def set_search_text(self, value: str) -> None:
        self.search_text = value.lower().strip()
        self.refresh_rows_filter()

    def set_platform_filter(self, value: str) -> None:
        self.platform_filter = value
        self.refresh_rows_filter()

    def set_country_filter(self, value: str) -> None:
        self.country_filter = value
        self.refresh_rows_filter()

    def set_type_filter(self, value: str) -> None:
        self.type_filter = value
        self.refresh_rows_filter()

    def set_region_filter(self, value: str) -> None:
        self.region_filter = value
        self.refresh_rows_filter()

    def set_friend_filter(self, value: str) -> None:
        self.friend_filter = value.strip().lower()
        self.refresh_rows_filter()

    def set_tag_filters(self, values: set[str]) -> None:
        self.tag_filters = {v.strip() for v in values if v.strip()}
        self.refresh_rows_filter()

    def set_sent_date_from(self, value) -> None:
        self.sent_date_from = value
        self.refresh_rows_filter()

    def set_sent_date_to(self, value) -> None:
        self.sent_date_to = value
        self.refresh_rows_filter()

    def set_received_date_from(self, value) -> None:
        self.received_date_from = value
        self.refresh_rows_filter()

    def set_received_date_to(self, value) -> None:
        self.received_date_to = value
        self.refresh_rows_filter()

    def set_expired_filter(self, value: str) -> None:
        self.expired_filter = value
        self.refresh_rows_filter()

    def filterAcceptsRow(self, source_row: int, source_parent: Any) -> bool:
        model = self.sourceModel()
        if model is None:
            return False

        row_values: dict[str, str] = {}
        for col_idx, (key, _label) in enumerate(DISPLAY_COLUMNS):
            index = model.index(source_row, col_idx, source_parent)
            row_values[key] = str(model.data(index) or "")

        raw_values = row_values
        record_index = model.index(source_row, 0, source_parent)
        record_data = model.data(record_index, Qt.ItemDataRole.UserRole)
        if isinstance(record_data, dict):
            raw_values = {key: str(record_data.get(key, "") or "") for key, _label in DISPLAY_COLUMNS}

        if self.platform_filter != "All" and raw_values["platform"] != self.platform_filter:
            return False
        if self.country_filter != "All" and raw_values["country"] != self.country_filter:
            return False
        if self.type_filter != "All" and raw_values["type"] != self.type_filter:
            return False
        if self.region_filter != "All" and raw_values["region"] != self.region_filter:
            return False
        if self.friend_filter and self.friend_filter not in raw_values.get("friend_id", "").lower():
            return False

        sent_row_date = extract_date_from_string(raw_values.get("sent_date", ""))
        if self.sent_date_from is not None and (sent_row_date is None or sent_row_date < self.sent_date_from):
            return False
        if self.sent_date_to is not None and (sent_row_date is None or sent_row_date > self.sent_date_to):
            return False

        received_raw = raw_values.get("received_date", "")
        received_row_date = extract_date_from_string(received_raw)
        if self.received_date_from is not None and (
            received_row_date is None or received_row_date < self.received_date_from
        ):
            return False
        if self.received_date_to is not None and (received_row_date is None or received_row_date > self.received_date_to):
            return False

        is_expired = not received_raw.strip()
        if self.expired_filter == "Expired" and not is_expired:
            return False
        if self.expired_filter == "Not expired" and is_expired:
            return False

        if self.tag_filters:
            row_tags = split_tags(raw_values.get("tags", ""))
            if not row_tags.intersection(self.tag_filters):
                return False

        if self.search_text:
            haystack = " ".join(list(row_values.values()) + list(raw_values.values())).lower()
            if self.search_text not in haystack:
                return False
        return True


class TagQuickEditDialog(QDialog):
    def __init__(self, parent: QWidget, translator: AppTranslator, current_tags: str, known_tags: list[str]) -> None:
        super().__init__(parent)
        self.translator = translator
        self.setWindowTitle(self.translator.tr("Edit tags"))
        self.resize(720, 460)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.translator.tr("Tags (space-separated):")))
        self.tags_input = QLineEdit(current_tags)
        layout.addWidget(self.tags_input)
        layout.addWidget(QLabel(self.translator.tr("Quick add tags:")))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        button_container = QWidget()
        button_grid = QGridLayout(button_container)
        button_grid.setContentsMargins(0, 0, 0, 0)

        if known_tags:
            columns = 6
            for idx, tag in enumerate(known_tags):
                button = QPushButton(tag)
                button.clicked.connect(lambda _checked=False, t=tag: self.append_tag(t))
                button_grid.addWidget(button, idx // columns, idx % columns)
        else:
            button_grid.addWidget(QLabel(self.translator.tr("No existing tags yet.")), 0, 0)

        scroll.setWidget(button_container)
        layout.addWidget(scroll, 1)

        actions = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        actions.accepted.connect(self.accept)
        actions.rejected.connect(self.reject)
        layout.addWidget(actions)

    def append_tag(self, tag: str) -> None:
        current = self.tags_input.text().strip()
        tokens = [t for t in current.split() if t]
        if tag not in tokens:
            tokens.append(tag)
            self.tags_input.setText(" ".join(tokens))

    def normalized_tags(self) -> str:
        return " ".join(self.tags_input.text().split())


class PostcardsPanel(QWidget):
    def __init__(
        self, project_root: Path, direction: str, records: list[dict[str, str]], translator: AppTranslator
    ) -> None:
        super().__init__()
        self.project_root = project_root
        self.direction = direction
        self.records = records
        self.translator = translator
        self.all_filter_value = "All"
        self.all_filter_label = self.translator.tr("All")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.translator.tr("Title, ID, tag"))
        self.search_input.setMinimumWidth(280)
        self.friend_input = QLineEdit()
        friend_label_key = "Sender Name" if self.direction.lower() == "received" else "Receiver Name"
        self.friend_input.setPlaceholderText(self.translator.tr(friend_label_key))
        self.friend_input.setMinimumWidth(280)

        self.platform_combo = QComboBox()
        self.platform_combo.addItem(self.all_filter_label, self.all_filter_value)
        self.country_combo = QComboBox()
        self.country_combo.addItem(self.all_filter_label, self.all_filter_value)
        self.type_combo = QComboBox()
        self.type_combo.addItem(self.all_filter_label, self.all_filter_value)
        self.region_combo = QComboBox()
        self.region_combo.addItem(self.all_filter_label, self.all_filter_value)
        self.expired_combo = QComboBox()
        self.expired_combo.addItem(self.all_filter_label, self.all_filter_value)
        self.expired_combo.addItem(self.translator.tr("Expired"), "Expired")
        self.expired_combo.addItem(self.translator.tr("Not expired"), "Not expired")
        self.reset_filters_btn = QPushButton(self.translator.tr("Reset"))
        self.tags_toggle_btn = QToolButton()
        self.tags_toggle_btn.setText(self.translator.tr("Tags"))
        self.tags_toggle_btn.setCheckable(True)
        self.tags_toggle_btn.setChecked(False)

        self.tags_filter_container = QWidget()
        self.tags_filter_layout = QVBoxLayout(self.tags_filter_container)
        self.tags_filter_layout.setContentsMargins(0, 0, 0, 0)
        self.tags_filter_layout.addWidget(QLabel(f"{self.translator.tr('Tags')}:"))
        self.tags_filter_list = QListWidget()
        self.tags_filter_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.tags_filter_layout.addWidget(self.tags_filter_list)
        self.tags_filter_container.setVisible(False)

        self.sent_date_from_check = QCheckBox(self.translator.tr("from"))
        self.sent_date_to_check = QCheckBox(self.translator.tr("to"))
        self.sent_date_from_edit = QDateEdit()
        self.sent_date_to_edit = QDateEdit()
        self.sent_date_from_edit.setCalendarPopup(True)
        self.sent_date_to_edit.setCalendarPopup(True)
        self.sent_date_from_edit.setDisplayFormat("yyyy-MM-dd")
        self.sent_date_to_edit.setDisplayFormat("yyyy-MM-dd")
        self.sent_date_from_edit.setDate(QDate.currentDate().addYears(-1))
        self.sent_date_to_edit.setDate(QDate.currentDate())
        self.sent_date_from_edit.setEnabled(False)
        self.sent_date_to_edit.setEnabled(False)

        self.received_date_from_check = QCheckBox(self.translator.tr("from"))
        self.received_date_to_check = QCheckBox(self.translator.tr("to"))
        self.received_date_from_edit = QDateEdit()
        self.received_date_to_edit = QDateEdit()
        self.received_date_from_edit.setCalendarPopup(True)
        self.received_date_to_edit.setCalendarPopup(True)
        self.received_date_from_edit.setDisplayFormat("yyyy-MM-dd")
        self.received_date_to_edit.setDisplayFormat("yyyy-MM-dd")
        self.received_date_from_edit.setDate(QDate.currentDate().addYears(-1))
        self.received_date_to_edit.setDate(QDate.currentDate())
        self.received_date_from_edit.setEnabled(False)
        self.received_date_to_edit.setEnabled(False)

        self.model = QStandardItemModel(0, len(DISPLAY_COLUMNS))
        self.model.setHorizontalHeaderLabels([self.translator.tr(label) for _key, label in DISPLAY_COLUMNS])
        self.proxy_model = PostcardFilterProxy(direction)
        self.proxy_model.setSourceModel(self.model)

        self.table = QTableView()
        self.table.setModel(self.proxy_model)
        self.table.setSortingEnabled(True)
        self.table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)

        self.value_labels: dict[str, QLabel] = {}
        form = QFormLayout()
        detail_fields = [
            ("id", "ID"),
            ("title", "Title"),
            ("platform", "Platform"),
            ("friend_id", "Friend"),
            ("country", "Country"),
            ("region", "Region/City"),
            ("sent_date", "Sent Date"),
            ("received_date", "Received Date"),
            ("tags", "Tags"),
        ]
        for key, label_text in detail_fields:
            label = QLabel("-")
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            label.setWordWrap(True)
            form.addRow(f"{self.translator.tr(label_text)}:", label)
            self.value_labels[key] = label

        self.image_label = QLabel("No image")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(420, 300)
        self.image_label.setStyleSheet("QLabel { background: #f0f0f0; border: 1px solid #d0d0d0; }")

        self.open_card_button = QPushButton("Open postcard link")
        self.open_friend_button = QPushButton("Open friend link")
        self.edit_title_button = QPushButton("Edit title")
        self.edit_tags_button = QPushButton("Edit tags")
        self.edit_country_button = QPushButton("Edit country")
        self.edit_region_button = QPushButton("Edit region/city")
        self.edit_id_button = QPushButton("Edit ID")
        self.duplicate_row_button = QPushButton("Duplicate row")
        self.open_card_button.clicked.connect(self.open_card_link)
        self.open_friend_button.clicked.connect(self.open_friend_link)
        self.edit_title_button.clicked.connect(self.edit_selected_title)
        self.edit_tags_button.clicked.connect(self.edit_selected_tags)
        self.edit_country_button.clicked.connect(self.edit_selected_country)
        self.edit_region_button.clicked.connect(self.edit_selected_region)
        self.edit_id_button.clicked.connect(self.edit_selected_id)
        self.duplicate_row_button.clicked.connect(self.duplicate_selected_row)

        self.status_label = QLabel("Showing 0 of 0 postcards")

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.addLayout(form)
        right_layout.addWidget(self.image_label, 1)
        right_layout.addWidget(self.open_card_button)
        right_layout.addWidget(self.open_friend_button)
        right_layout.addWidget(self.edit_title_button)
        right_layout.addWidget(self.edit_tags_button)
        right_layout.addWidget(self.edit_country_button)
        right_layout.addWidget(self.edit_region_button)
        right_layout.addWidget(self.edit_id_button)
        right_layout.addWidget(self.duplicate_row_button)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        primary_filter_row = QHBoxLayout()
        primary_filter_row.addWidget(QLabel(f"{self.translator.tr('Search')}:"))
        primary_filter_row.addWidget(self.search_input, 3)
        primary_filter_row.addWidget(QLabel(f"{self.translator.tr('Country')}:"))
        primary_filter_row.addWidget(self.country_combo)
        primary_filter_row.addWidget(QLabel(f"{self.translator.tr('Region/City')}:"))
        primary_filter_row.addWidget(self.region_combo)
        primary_filter_row.addStretch(1)

        secondary_filter_row = QHBoxLayout()
        secondary_filter_row.addWidget(QLabel(f"{self.translator.tr(friend_label_key)}:"))
        secondary_filter_row.addWidget(self.friend_input, 3)
        secondary_filter_row.addWidget(QLabel(f"{self.translator.tr('Type')}:"))
        secondary_filter_row.addWidget(self.type_combo)
        secondary_filter_row.addWidget(QLabel(f"{self.translator.tr('Platform')}:"))
        secondary_filter_row.addWidget(self.platform_combo)
        secondary_filter_row.addWidget(self.tags_toggle_btn)
        secondary_filter_row.addStretch(1)

        tertiary_filter_row = QHBoxLayout()
        tertiary_filter_row.addWidget(QLabel(f"{self.translator.tr('Sent Date')}:"))
        tertiary_filter_row.addWidget(self.sent_date_from_check)
        tertiary_filter_row.addWidget(self.sent_date_from_edit)
        tertiary_filter_row.addWidget(self.sent_date_to_check)
        tertiary_filter_row.addWidget(self.sent_date_to_edit)
        tertiary_filter_row.addWidget(QLabel(f"{self.translator.tr('Received Date')}:"))
        tertiary_filter_row.addWidget(self.received_date_from_check)
        tertiary_filter_row.addWidget(self.received_date_from_edit)
        tertiary_filter_row.addWidget(self.received_date_to_check)
        tertiary_filter_row.addWidget(self.received_date_to_edit)
        tertiary_filter_row.addStretch(1)

        quaternary_filter_row = QHBoxLayout()
        quaternary_filter_row.addWidget(self.tags_toggle_btn)
        quaternary_filter_row.addWidget(QLabel(f"{self.translator.tr('Expired')}:"))
        quaternary_filter_row.addWidget(self.expired_combo)
        quaternary_filter_row.addWidget(self.reset_filters_btn)
        quaternary_filter_row.addStretch(1)

        left_layout.addLayout(primary_filter_row)
        left_layout.addLayout(secondary_filter_row)
        left_layout.addLayout(tertiary_filter_row)
        left_layout.addLayout(quaternary_filter_row)
        left_layout.addWidget(self.tags_filter_container)
        left_layout.addWidget(self.table, 1)
        left_layout.addWidget(self.status_label)

        splitter = QSplitter()
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([860, 460])

        layout = QVBoxLayout(self)
        layout.addWidget(splitter)

        self.search_input.textChanged.connect(self.proxy_model.set_search_text)
        self.friend_input.textChanged.connect(self.on_filter_controls_changed)
        self.platform_combo.currentTextChanged.connect(self.on_filter_controls_changed)
        self.country_combo.currentTextChanged.connect(self.on_filter_controls_changed)
        self.type_combo.currentTextChanged.connect(self.on_filter_controls_changed)
        self.region_combo.currentTextChanged.connect(self.on_filter_controls_changed)
        self.expired_combo.currentTextChanged.connect(self.on_filter_controls_changed)
        self.tags_filter_list.itemSelectionChanged.connect(self.on_filter_controls_changed)
        self.tags_toggle_btn.toggled.connect(self.on_tags_toggled)
        self.sent_date_from_check.toggled.connect(self.on_sent_date_from_toggled)
        self.sent_date_to_check.toggled.connect(self.on_sent_date_to_toggled)
        self.sent_date_from_edit.dateChanged.connect(self.on_filter_controls_changed)
        self.sent_date_to_edit.dateChanged.connect(self.on_filter_controls_changed)
        self.received_date_from_check.toggled.connect(self.on_received_date_from_toggled)
        self.received_date_to_check.toggled.connect(self.on_received_date_to_toggled)
        self.received_date_from_edit.dateChanged.connect(self.on_filter_controls_changed)
        self.received_date_to_edit.dateChanged.connect(self.on_filter_controls_changed)
        self.reset_filters_btn.clicked.connect(self.reset_filters)
        self.search_input.textChanged.connect(self.update_status)
        self.friend_input.textChanged.connect(self.update_status)
        self.platform_combo.currentTextChanged.connect(self.update_status)
        self.country_combo.currentTextChanged.connect(self.update_status)
        self.type_combo.currentTextChanged.connect(self.update_status)
        self.region_combo.currentTextChanged.connect(self.update_status)
        self.expired_combo.currentTextChanged.connect(self.update_status)
        self.tags_filter_list.itemSelectionChanged.connect(self.update_status)
        self.sent_date_from_check.toggled.connect(self.update_status)
        self.sent_date_to_check.toggled.connect(self.update_status)
        self.sent_date_from_edit.dateChanged.connect(self.update_status)
        self.sent_date_to_edit.dateChanged.connect(self.update_status)
        self.received_date_from_check.toggled.connect(self.update_status)
        self.received_date_to_check.toggled.connect(self.update_status)
        self.received_date_from_edit.dateChanged.connect(self.update_status)
        self.received_date_to_edit.dateChanged.connect(self.update_status)
        self.table.selectionModel().selectionChanged.connect(self.on_row_selected)

        self.load_data(records)
        self.update_status()

    def load_data(self, records: list[dict[str, str]]) -> None:
        sort_key = "received_date" if self.direction.lower() == "received" else "sent_date"
        self.records = sorted(records, key=lambda r: r.get(sort_key, ""), reverse=True)
        self.model.setRowCount(0)
        for record in self.records:
            row_items: list[QStandardItem] = []
            for key, _label in DISPLAY_COLUMNS:
                value = self.translator.translate_value(key, record.get(key, ""))
                item = QStandardItem(value)
                row_items.append(item)
            row_items[0].setData(record, Qt.ItemDataRole.UserRole)
            self.model.appendRow(row_items)

        sort_col = 8 if self.direction.lower() == "received" else 7
        self.table.sortByColumn(sort_col, Qt.SortOrder.DescendingOrder)

        self.refresh_linked_filter_options()
        self.apply_filter_values_to_proxy()

        if self.proxy_model.rowCount() > 0:
            self.table.selectRow(0)
        else:
            self.clear_detail()
        self.update_status()

    def record_matches_for_options(self, record: dict[str, str], ignore_key: str) -> bool:
        platform_value = self.current_combo_raw(self.platform_combo)
        country_value = self.current_combo_raw(self.country_combo)
        type_value = self.current_combo_raw(self.type_combo)
        region_value = self.current_combo_raw(self.region_combo)
        friend_value = self.friend_input.text().strip().lower()
        selected_tags = self.selected_tag_filters()
        expired_value = self.current_combo_raw(self.expired_combo)
        sent_date_from, sent_date_to = self.get_date_filter_bounds(
            self.sent_date_from_check,
            self.sent_date_from_edit,
            self.sent_date_to_check,
            self.sent_date_to_edit,
        )
        received_date_from, received_date_to = self.get_date_filter_bounds(
            self.received_date_from_check,
            self.received_date_from_edit,
            self.received_date_to_check,
            self.received_date_to_edit,
        )

        if (
            ignore_key != "platform"
            and platform_value != self.all_filter_value
            and record.get("platform", "") != platform_value
        ):
            return False
        if ignore_key != "country" and country_value != self.all_filter_value and record.get("country", "") != country_value:
            return False
        if ignore_key != "type" and type_value != self.all_filter_value and record.get("type", "") != type_value:
            return False
        if ignore_key != "region" and region_value != self.all_filter_value and record.get("region", "") != region_value:
            return False
        if ignore_key != "friend" and friend_value and friend_value not in record.get("friend_id", "").lower():
            return False

        sent_row_date = extract_date_from_string(record.get("sent_date", ""))
        if sent_date_from is not None and (sent_row_date is None or sent_row_date < sent_date_from):
            return False
        if sent_date_to is not None and (sent_row_date is None or sent_row_date > sent_date_to):
            return False

        received_raw = record.get("received_date", "")
        received_row_date = extract_date_from_string(received_raw)
        if received_date_from is not None and (received_row_date is None or received_row_date < received_date_from):
            return False
        if received_date_to is not None and (received_row_date is None or received_row_date > received_date_to):
            return False

        is_expired = not received_raw.strip()
        if ignore_key != "expired" and expired_value == "Expired" and not is_expired:
            return False
        if ignore_key != "expired" and expired_value == "Not expired" and is_expired:
            return False
        if ignore_key != "tags" and selected_tags:
            row_tags = split_tags(record.get("tags", ""))
            if not row_tags.intersection(selected_tags):
                return False
        return True

    def get_date_filter_bounds(
        self,
        from_check: QCheckBox,
        from_edit: QDateEdit,
        to_check: QCheckBox,
        to_edit: QDateEdit,
    ):
        date_from = None
        date_to = None
        if from_check.isChecked():
            qd = from_edit.date()
            date_from = datetime(qd.year(), qd.month(), qd.day()).date()
        if to_check.isChecked():
            qd = to_edit.date()
            date_to = datetime(qd.year(), qd.month(), qd.day()).date()
        return date_from, date_to

    def refill_combo_with_values(self, combo: QComboBox, values: list[str], selected_value: str) -> None:
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(self.all_filter_label, self.all_filter_value)
        for value in values:
            combo.addItem(self.translator.tr(value), value)
        selected_idx = combo.findData(selected_value, Qt.ItemDataRole.UserRole)
        if selected_idx >= 0:
            combo.setCurrentIndex(selected_idx)
        else:
            combo.setCurrentIndex(0)
        combo.blockSignals(False)

    def current_combo_raw(self, combo: QComboBox) -> str:
        value = combo.currentData(Qt.ItemDataRole.UserRole)
        if isinstance(value, str) and value:
            return value
        return self.all_filter_value

    def selected_tag_filters(self) -> set[str]:
        return {
            item.data(Qt.ItemDataRole.UserRole)
            for item in self.tags_filter_list.selectedItems()
            if isinstance(item.data(Qt.ItemDataRole.UserRole), str) and item.data(Qt.ItemDataRole.UserRole).strip()
        }

    def known_tags(self) -> list[str]:
        return sorted({tag for record in self.records for tag in split_tags(record.get("tags", ""))})

    def on_tags_toggled(self, checked: bool) -> None:
        self.tags_filter_container.setVisible(checked)

    def refresh_linked_filter_options(self) -> None:
        selected_platform = self.current_combo_raw(self.platform_combo)
        selected_country = self.current_combo_raw(self.country_combo)
        selected_type = self.current_combo_raw(self.type_combo)
        selected_region = self.current_combo_raw(self.region_combo)
        selected_expired = self.current_combo_raw(self.expired_combo)
        selected_tags = self.selected_tag_filters()

        platforms = sorted(
            {
                r.get("platform", "")
                for r in self.records
                if r.get("platform", "") and self.record_matches_for_options(r, "platform")
            }
        )
        countries = sorted(
            {
                r.get("country", "")
                for r in self.records
                if r.get("country", "") and self.record_matches_for_options(r, "country")
            }
        )
        types = sorted(
            {
                r.get("type", "")
                for r in self.records
                if r.get("type", "") and self.record_matches_for_options(r, "type")
            }
        )
        regions = sorted(
            {
                r.get("region", "")
                for r in self.records
                if r.get("region", "") and self.record_matches_for_options(r, "region")
            }
        )
        tags = sorted(
            {
                tag
                for r in self.records
                if self.record_matches_for_options(r, "tags")
                for tag in split_tags(r.get("tags", ""))
            }
        )

        self.refill_combo_with_values(self.platform_combo, platforms, selected_platform)
        self.refill_combo_with_values(self.country_combo, countries, selected_country)
        self.refill_combo_with_values(self.type_combo, types, selected_type)
        self.refill_combo_with_values(self.region_combo, regions, selected_region)
        selected_expired_idx = self.expired_combo.findData(selected_expired, Qt.ItemDataRole.UserRole)
        if selected_expired_idx >= 0:
            self.expired_combo.setCurrentIndex(selected_expired_idx)

        self.tags_filter_list.blockSignals(True)
        self.tags_filter_list.clear()
        for tag in tags:
            item = QListWidgetItem(self.translator.tr(tag))
            item.setData(Qt.ItemDataRole.UserRole, tag)
            self.tags_filter_list.addItem(item)
            if tag in selected_tags:
                item.setSelected(True)
        self.tags_filter_list.blockSignals(False)

    def apply_filter_values_to_proxy(self) -> None:
        self.proxy_model.set_platform_filter(self.current_combo_raw(self.platform_combo))
        self.proxy_model.set_country_filter(self.current_combo_raw(self.country_combo))
        self.proxy_model.set_type_filter(self.current_combo_raw(self.type_combo))
        self.proxy_model.set_region_filter(self.current_combo_raw(self.region_combo))
        self.proxy_model.set_friend_filter(self.friend_input.text())
        self.proxy_model.set_tag_filters(self.selected_tag_filters())
        sent_date_from, sent_date_to = self.get_date_filter_bounds(
            self.sent_date_from_check,
            self.sent_date_from_edit,
            self.sent_date_to_check,
            self.sent_date_to_edit,
        )
        self.proxy_model.set_sent_date_from(sent_date_from)
        self.proxy_model.set_sent_date_to(sent_date_to)
        received_date_from, received_date_to = self.get_date_filter_bounds(
            self.received_date_from_check,
            self.received_date_from_edit,
            self.received_date_to_check,
            self.received_date_to_edit,
        )
        self.proxy_model.set_received_date_from(received_date_from)
        self.proxy_model.set_received_date_to(received_date_to)
        self.proxy_model.set_expired_filter(self.current_combo_raw(self.expired_combo))

    def on_filter_controls_changed(self, *_args) -> None:
        self.refresh_linked_filter_options()
        self.apply_filter_values_to_proxy()

    def on_sent_date_from_toggled(self, checked: bool) -> None:
        self.sent_date_from_edit.setEnabled(checked)
        self.on_filter_controls_changed()

    def on_sent_date_to_toggled(self, checked: bool) -> None:
        self.sent_date_to_edit.setEnabled(checked)
        self.on_filter_controls_changed()

    def on_received_date_from_toggled(self, checked: bool) -> None:
        self.received_date_from_edit.setEnabled(checked)
        self.on_filter_controls_changed()

    def on_received_date_to_toggled(self, checked: bool) -> None:
        self.received_date_to_edit.setEnabled(checked)
        self.on_filter_controls_changed()

    def reset_filters(self) -> None:
        current_date = QDate.currentDate()
        defaults = [
            self.platform_combo,
            self.country_combo,
            self.type_combo,
            self.region_combo,
            self.expired_combo,
        ]
        for combo in defaults:
            combo.blockSignals(True)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)
        self.search_input.blockSignals(True)
        self.search_input.clear()
        self.search_input.blockSignals(False)
        self.friend_input.blockSignals(True)
        self.friend_input.clear()
        self.friend_input.blockSignals(False)
        self.tags_filter_list.blockSignals(True)
        self.tags_filter_list.clearSelection()
        self.tags_filter_list.blockSignals(False)
        self.tags_toggle_btn.setChecked(False)

        toggles = [
            self.sent_date_from_check,
            self.sent_date_to_check,
            self.received_date_from_check,
            self.received_date_to_check,
        ]
        for check in toggles:
            check.blockSignals(True)
            check.setChecked(False)
            check.blockSignals(False)

        self.sent_date_from_edit.setEnabled(False)
        self.sent_date_to_edit.setEnabled(False)
        self.received_date_from_edit.setEnabled(False)
        self.received_date_to_edit.setEnabled(False)
        self.sent_date_from_edit.setDate(current_date.addYears(-1))
        self.sent_date_to_edit.setDate(current_date)
        self.received_date_from_edit.setDate(current_date.addYears(-1))
        self.received_date_to_edit.setDate(current_date)
        self.proxy_model.set_search_text("")
        self.on_filter_controls_changed()
        self.update_status()

    def clear_detail(self) -> None:
        for label in self.value_labels.values():
            label.setText("-")
        self.image_label.setText("No image")
        self.image_label.setPixmap(QPixmap())

    def csv_path(self) -> Path:
        file_name = "received.csv" if self.direction.lower() == "received" else "sent.csv"
        return self.project_root / "_data" / file_name

    def record_signature(self, record: dict[str, str]) -> tuple[str, ...]:
        return tuple((record.get(field, "") or "").strip() for field in ROW_FIELDNAMES)

    def refresh_after_csv_write(self, preferred_id: str) -> None:
        latest = load_csv_records(self.csv_path(), self.direction)
        self.load_data(latest)
        for row_idx in range(self.proxy_model.rowCount()):
            source_index = self.proxy_model.mapToSource(self.proxy_model.index(row_idx, 0))
            record = self.model.item(source_index.row(), 0).data(Qt.ItemDataRole.UserRole)
            if isinstance(record, dict) and record.get("id", "") == preferred_id:
                self.table.selectRow(row_idx)
                self.on_row_selected()
                break

    def update_selected_row(self, changes: dict[str, str], preferred_id: str | None = None) -> bool:
        record = self.current_record()
        if record is None:
            QMessageBox.information(self, "No selection", "Please select one row first.")
            return False
        csv_path = self.csv_path()
        rows = load_csv_rows(csv_path)
        old_signature = self.record_signature(record)
        target_idx = next(
            (idx for idx, row in enumerate(rows) if self.record_signature(row) == old_signature),
            None,
        )
        if target_idx is None:
            QMessageBox.warning(self, "Update failed", "Could not locate the selected row in CSV.")
            return False
        updated = rows[target_idx].copy()
        updated.update(changes)
        updated = {field: (updated.get(field, "") or "").strip() for field in ROW_FIELDNAMES}
        if "id" in changes:
            new_id = updated.get("id", "")
            if not new_id:
                QMessageBox.warning(self, "Invalid ID", "ID cannot be empty.")
                return False
            duplicate_exists = any(idx != target_idx and row.get("id", "") == new_id for idx, row in enumerate(rows))
            if duplicate_exists:
                QMessageBox.warning(self, "Duplicate ID", f"ID already exists: {new_id}")
                return False
        rows[target_idx] = updated
        write_csv_rows(csv_path, rows)
        self.refresh_after_csv_write(preferred_id or updated.get("id", ""))
        return True

    def edit_selected_title(self) -> None:
        record = self.current_record()
        if record is None:
            QMessageBox.information(self, "No selection", "Please select one row first.")
            return
        value, ok = QInputDialog.getText(self, "Edit title", "Title:", text=record.get("title", ""))
        if not ok:
            return
        self.update_selected_row({"title": value.strip()})

    def edit_selected_tags(self) -> None:
        record = self.current_record()
        if record is None:
            QMessageBox.information(self, "No selection", "Please select one row first.")
            return
        dialog = TagQuickEditDialog(self, self.translator, record.get("tags", ""), self.known_tags())
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self.update_selected_row({"tags": dialog.normalized_tags()})

    def edit_selected_country(self) -> None:
        record = self.current_record()
        if record is None:
            QMessageBox.information(self, "No selection", "Please select one row first.")
            return
        value, ok = QInputDialog.getText(self, "Edit country", "Country:", text=record.get("country", ""))
        if not ok:
            return
        self.update_selected_row({"country": value.strip()})

    def edit_selected_region(self) -> None:
        record = self.current_record()
        if record is None:
            QMessageBox.information(self, "No selection", "Please select one row first.")
            return
        value, ok = QInputDialog.getText(self, "Edit region/city", "Region/City:", text=record.get("region", ""))
        if not ok:
            return
        self.update_selected_row({"region": value.strip()})

    def edit_selected_id(self) -> None:
        record = self.current_record()
        if record is None:
            QMessageBox.information(self, "No selection", "Please select one row first.")
            return
        current_id = record.get("id", "")
        value, ok = QInputDialog.getText(self, "Edit ID", "ID:", text=current_id)
        if not ok:
            return
        new_id = value.strip()
        if not new_id or new_id == current_id:
            return
        self.update_selected_row({"id": new_id}, preferred_id=new_id)

    def duplicate_selected_row(self) -> None:
        record = self.current_record()
        if record is None:
            QMessageBox.information(self, "No selection", "Please select one row first.")
            return
        source_id = record.get("id", "").strip()
        if not source_id:
            QMessageBox.warning(self, "Duplicate failed", "Selected row has empty ID.")
            return
        csv_path = self.csv_path()
        rows = load_csv_rows(csv_path)
        old_signature = self.record_signature(record)
        target_idx = next(
            (idx for idx, row in enumerate(rows) if self.record_signature(row) == old_signature),
            None,
        )
        if target_idx is None:
            QMessageBox.warning(self, "Duplicate failed", "Could not locate the selected row in CSV.")
            return
        existing_ids = {row.get("id", "").strip() for row in rows}
        suffix = 1
        duplicated_id = f"{source_id}-{suffix}"
        while duplicated_id in existing_ids:
            suffix += 1
            duplicated_id = f"{source_id}-{suffix}"
        duplicated = rows[target_idx].copy()
        duplicated["id"] = duplicated_id
        rows.insert(target_idx + 1, duplicated)
        write_csv_rows(csv_path, rows)
        self.refresh_after_csv_write(duplicated_id)

    def current_record(self) -> dict[str, str] | None:
        index = self.table.currentIndex()
        if not index.isValid():
            return None
        source = self.proxy_model.mapToSource(index)
        record = self.model.item(source.row(), 0).data(Qt.ItemDataRole.UserRole)
        return record if isinstance(record, dict) else None

    def on_row_selected(self) -> None:
        record = self.current_record()
        if not record:
            self.clear_detail()
            return

        for key, label in self.value_labels.items():
            label.setText(self.translator.translate_value(key, record.get(key, "")) or "-")

        image_path = find_image_path(self.project_root, self.direction, record.get("id", ""))
        if image_path and image_path.exists():
            pixmap = load_pixmap_safely(image_path)
            if not pixmap.isNull():
                self.image_label.setPixmap(
                    pixmap.scaled(
                        self.image_label.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
                return
        self.image_label.setText("No image")
        self.image_label.setPixmap(QPixmap())

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        if self.current_record():
            self.on_row_selected()

    def open_url(self, raw_url: str) -> None:
        url = raw_url.strip()
        if not url:
            QMessageBox.information(self, "No URL", "This record does not have a URL.")
            return
        QDesktopServices.openUrl(QUrl(url))

    def open_card_link(self) -> None:
        record = self.current_record()
        if record:
            self.open_url(record.get("url", ""))

    def open_friend_link(self) -> None:
        record = self.current_record()
        if record:
            self.open_url(record.get("friend_url", ""))

    def update_status(self) -> None:
        self.status_label.setText(
            f"Showing {self.proxy_model.rowCount()} of {self.model.rowCount()} {self.direction.lower()} postcards"
        )


class ImportDialog(QDialog):
    def __init__(self, project_root: Path, on_data_changed, translator: AppTranslator) -> None:
        super().__init__()
        self.project_root = project_root
        self.on_data_changed = on_data_changed
        self.translator = translator
        self.image_selected_files: list[Path] = []
        self.image_assignments: dict[str, Path] = {}
        self._centered_once = False
        self.setWindowTitle(self.translator.tr("Import New Postcards"))
        self.resize(1000, 760)
        self.setMaximumSize(1024, 768)

        self.tabs = QTabWidget()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.run_postprocess_btn = QPushButton("Run sort.py + grouped.py")
        self.run_postprocess_btn.clicked.connect(self.run_postprocess_scripts)

        self.tabs.addTab(self.build_posthi_tab(), "Post-Hi")
        self.tabs.addTab(self.build_postcrossing_tab(), "Postcrossing")
        self.tabs.addTab(self.build_icy_tab(), "iCardYou")
        self.tabs.addTab(self.build_image_tab(), "Images")

        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs, 1)

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        if not self._centered_once:
            center_window(self)
            self._centered_once = True

    def log(self, message: str) -> None:
        self.log_output.append(message)

    def build_posthi_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Select 3 Post-Hi CSV files from any path, then import."))

        self.posthi_received_path_input = QLineEdit()
        self.posthi_sent_path_input = QLineEdit()
        self.posthi_expired_sent_path_input = QLineEdit()
        self.posthi_received_path_input.setReadOnly(True)
        self.posthi_sent_path_input.setReadOnly(True)
        self.posthi_expired_sent_path_input.setReadOnly(True)

        def add_picker_row(label: str, line_edit: QLineEdit, on_click) -> None:
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            row.addWidget(line_edit, 1)
            btn = QPushButton("Browse...")
            btn.clicked.connect(on_click)
            row.addWidget(btn)
            layout.addLayout(row)

        add_picker_row(
            "Received CSV:",
            self.posthi_received_path_input,
            lambda: self.select_posthi_file(self.posthi_received_path_input, "Select Post-Hi received CSV"),
        )
        add_picker_row(
            "Sent CSV:",
            self.posthi_sent_path_input,
            lambda: self.select_posthi_file(self.posthi_sent_path_input, "Select Post-Hi sent CSV"),
        )
        add_picker_row(
            "Expired Sent CSV:",
            self.posthi_expired_sent_path_input,
            lambda: self.select_posthi_file(self.posthi_expired_sent_path_input, "Select Post-Hi expired sent CSV"),
        )

        run_btn = QPushButton("Import selected Post-Hi CSV files")
        run_btn.clicked.connect(self.run_posthi_import)
        layout.addWidget(run_btn)
        layout.addStretch(1)
        return widget

    def select_posthi_file(self, target_input: QLineEdit, title: str) -> None:
        selected_file, _ = QFileDialog.getOpenFileName(
            self,
            title,
            str(self.project_root),
            "CSV files (*.csv)",
        )
        if selected_file:
            target_input.setText(selected_file)

    def build_postcrossing_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Paste Received IDs (e.g. US-123, DE-456):"))
        self.pc_received_input = QTextEdit()
        layout.addWidget(self.pc_received_input, 1)
        layout.addWidget(QLabel("Paste Sent IDs:"))
        self.pc_sent_input = QTextEdit()
        layout.addWidget(self.pc_sent_input, 1)
        run_btn = QPushButton("Import Postcrossing IDs")
        run_btn.clicked.connect(self.run_postcrossing_import)
        layout.addWidget(run_btn)
        return widget

    def build_icy_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(
            QLabel(
                "Paste iCardYou RECEIVED entries.\n"
                "Supported formats:\n"
                "- JavaScript/Python list: [[\"配对\",\"/sendpostcard/postcardDetail/1336317\",\"CNSH44625\"], ...]\n"
                "- One-per-line CSV: 配对,/sendpostcard/postcardDetail/1336317,CNSH44625"
            )
        )
        self.icy_received_input = QTextEdit()
        self.icy_received_input.setPlaceholderText(
            "[[\"配对\",\"/sendpostcard/postcardDetail/1336317\",\"CNSH44625\"],"
            "[\"配对\",\"/sendpostcard/postcardDetail/1336316\",\"CNSH44624\"]]"
        )
        layout.addWidget(self.icy_received_input, 1)
        layout.addWidget(QLabel("Paste iCardYou SENT entries (same format as above):"))
        self.icy_sent_input = QTextEdit()
        self.icy_sent_input.setPlaceholderText(
            "[[\"配对\",\"/sendpostcard/postcardDetail/1335001\",\"CNSH44500\"],"
            "[\"配对\",\"/sendpostcard/postcardDetail/1334999\",\"CNSH44499\"]]"
        )
        layout.addWidget(self.icy_sent_input, 1)
        run_btn = QPushButton("Import iCardYou entries")
        run_btn.clicked.connect(self.run_icy_import)
        layout.addWidget(run_btn)
        return widget

    def build_image_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(
            QLabel(
                "Workflow:\n"
                "1) Refresh missing-image candidates\n"
                "2) Choose source images and preview them\n"
                "3) Assign selected image to selected candidate ID\n"
                "4) Click Execute import"
            )
        )

        row = QHBoxLayout()
        row.addWidget(QLabel("Direction:"))
        self.image_direction_combo = QComboBox()
        self.image_direction_combo.addItems(["Received", "Sent"])
        row.addWidget(self.image_direction_combo)
        row.addWidget(QLabel("Scope:"))
        self.image_scope_combo = QComboBox()
        self.image_scope_combo.addItems(["Missing only", "All cards (allow update)"])
        row.addWidget(self.image_scope_combo)
        refresh_btn = QPushButton("Refresh candidates")
        refresh_btn.clicked.connect(self.refresh_missing_image_candidates)
        row.addWidget(refresh_btn)
        row.addStretch(1)
        layout.addLayout(row)

        content = QHBoxLayout()

        candidate_col = QVBoxLayout()
        candidate_col.addWidget(QLabel("Candidate postcards"))
        self.image_candidate_list = QListWidget()
        candidate_col.addWidget(self.image_candidate_list, 1)
        content.addLayout(candidate_col, 1)

        right_col = QVBoxLayout()

        image_col = QVBoxLayout()
        image_col.addWidget(QLabel("Selected source images"))
        self.image_file_list = QListWidget()
        self.image_file_list.currentTextChanged.connect(self.preview_selected_image)
        image_col.addWidget(self.image_file_list, 1)
        choose_btn = QPushButton("Choose source images...")
        choose_btn.clicked.connect(self.choose_source_images)
        image_col.addWidget(choose_btn)
        right_col.addLayout(image_col, 1)

        mapping_col = QVBoxLayout()
        preview_row = QHBoxLayout()
        preview_col = QVBoxLayout()
        existing_col = QVBoxLayout()

        preview_col.addWidget(QLabel("Preview"))
        self.image_preview_label = QLabel("No image selected")
        self.image_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview_label.setMinimumSize(320, 240)
        self.image_preview_label.setStyleSheet("QLabel { background: #f0f0f0; border: 1px solid #d0d0d0; }")
        preview_col.addWidget(self.image_preview_label, 1)

        existing_col.addWidget(QLabel("Existing uploaded image (selected card)"))
        self.image_existing_preview_label = QLabel("No existing image")
        self.image_existing_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_existing_preview_label.setMinimumSize(320, 240)
        self.image_existing_preview_label.setStyleSheet("QLabel { background: #f0f0f0; border: 1px solid #d0d0d0; }")
        existing_col.addWidget(self.image_existing_preview_label, 1)

        preview_row.addLayout(preview_col, 1)
        preview_row.addLayout(existing_col, 1)
        mapping_col.addLayout(preview_row, 1)

        assign_btn = QPushButton("Assign selected image -> selected candidate")
        assign_btn.clicked.connect(self.assign_image_to_candidate)
        mapping_col.addWidget(assign_btn)

        mapping_col.addWidget(QLabel("Selected card URL"))
        self.image_selected_url_input = QLineEdit()
        self.image_selected_url_input.setReadOnly(True)
        mapping_col.addWidget(self.image_selected_url_input)
        open_url_btn = QPushButton("Open selected card URL")
        open_url_btn.clicked.connect(self.open_selected_candidate_url)
        mapping_col.addWidget(open_url_btn)

        self.image_assignment_list = QListWidget()
        mapping_col.addWidget(QLabel("Current assignments"))
        mapping_col.addWidget(self.image_assignment_list, 1)

        clear_btn = QPushButton("Clear selected assignment")
        clear_btn.clicked.connect(self.clear_selected_assignment)
        mapping_col.addWidget(clear_btn)

        execute_btn = QPushButton("Execute import (resize + rename + move)")
        execute_btn.clicked.connect(self.run_image_import)
        mapping_col.addWidget(execute_btn)

        right_col.addLayout(mapping_col, 2)
        right_col.addWidget(self.run_postprocess_btn)
        right_col.addWidget(QLabel("Logs:"))
        right_col.addWidget(self.log_output, 1)
        content.addLayout(right_col, 2)

        layout.addLayout(content, 1)
        self.image_direction_combo.currentTextChanged.connect(self.refresh_missing_image_candidates)
        self.image_scope_combo.currentTextChanged.connect(self.refresh_missing_image_candidates)
        self.image_candidate_list.currentItemChanged.connect(self.on_candidate_selection_changed)
        self.refresh_missing_image_candidates()
        return widget

    def refresh_missing_image_candidates(self) -> None:
        direction = self.image_direction_combo.currentText().strip()
        scope = self.image_scope_combo.currentText().strip()
        csv_path = self.project_root / "_data" / ("received.csv" if direction == "Received" else "sent.csv")
        records = load_csv_records(csv_path, direction)
        candidates: list[dict[str, Any]] = []
        seen: set[str] = set()
        for record in records:
            postcard_id = record.get("id", "").strip()
            if not postcard_id or postcard_id in seen:
                continue
            image_path = find_image_path(self.project_root, direction, postcard_id)
            has_image = image_path is not None
            if scope == "Missing only" and has_image:
                seen.add(postcard_id)
                continue
            candidates.append(
                {
                    "id": postcard_id,
                    "url": record.get("url", "").strip(),
                    "has_image": has_image,
                    "image_path": str(image_path) if image_path else "",
                }
            )
            seen.add(postcard_id)
        self.image_candidate_list.clear()
        for candidate in candidates:
            status = "Has image" if candidate["has_image"] else "Missing image"
            item = QListWidgetItem(f"{candidate['id']} [{status}]")
            item.setData(Qt.ItemDataRole.UserRole, candidate)
            self.image_candidate_list.addItem(item)
        candidate_ids = {candidate["id"] for candidate in candidates}
        self.image_assignments = {k: v for k, v in self.image_assignments.items() if k in candidate_ids}
        self.refresh_assignment_list()
        self.image_selected_url_input.clear()
        self.image_existing_preview_label.setText("No existing image")
        self.image_existing_preview_label.setPixmap(QPixmap())
        if self.image_candidate_list.count() > 0:
            self.image_candidate_list.setCurrentRow(0)

    def on_candidate_selection_changed(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is None:
            self.image_selected_url_input.clear()
            self.image_existing_preview_label.setText("No existing image")
            self.image_existing_preview_label.setPixmap(QPixmap())
            return
        candidate = current.data(Qt.ItemDataRole.UserRole)
        if isinstance(candidate, dict):
            self.image_selected_url_input.setText(candidate.get("url", ""))
            existing_path = Path(candidate.get("image_path", "")) if candidate.get("image_path", "") else None
            if existing_path and existing_path.exists():
                pixmap = load_pixmap_safely(existing_path)
                if not pixmap.isNull():
                    self.image_existing_preview_label.setPixmap(
                        pixmap.scaled(
                            self.image_existing_preview_label.size(),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                    )
                else:
                    self.image_existing_preview_label.setText("Existing image preview failed")
                    self.image_existing_preview_label.setPixmap(QPixmap())
            else:
                self.image_existing_preview_label.setText("No existing image")
                self.image_existing_preview_label.setPixmap(QPixmap())
        else:
            self.image_selected_url_input.clear()
            self.image_existing_preview_label.setText("No existing image")
            self.image_existing_preview_label.setPixmap(QPixmap())

    def open_selected_candidate_url(self) -> None:
        url = self.image_selected_url_input.text().strip()
        if not url:
            QMessageBox.information(self, "No URL", "Selected candidate has no card URL.")
            return
        QDesktopServices.openUrl(QUrl(url))

    def choose_source_images(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select source postcard images",
            str(self.project_root),
            "Images (*.jpg *.jpeg *.png *.webp *.gif)",
        )
        if not files:
            return
        self.image_selected_files = [Path(p) for p in files]
        self.image_file_list.clear()
        self.image_file_list.addItems([str(p) for p in self.image_selected_files])
        if self.image_selected_files:
            self.image_file_list.setCurrentRow(0)

    def preview_selected_image(self, path_text: str) -> None:
        path = Path(path_text) if path_text else None
        if path is None or not path.exists():
            self.image_preview_label.setText("No image selected")
            self.image_preview_label.setPixmap(QPixmap())
            return
        pixmap = load_pixmap_safely(path)
        if pixmap.isNull():
            self.image_preview_label.setText("Preview failed")
            self.image_preview_label.setPixmap(QPixmap())
            return
        self.image_preview_label.setPixmap(
            pixmap.scaled(
                self.image_preview_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def assign_image_to_candidate(self) -> None:
        candidate_item = self.image_candidate_list.currentItem()
        image_item = self.image_file_list.currentItem()
        if candidate_item is None or image_item is None:
            QMessageBox.warning(self, "Selection required", "Please select one candidate and one image first.")
            return
        candidate_data = candidate_item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(candidate_data, dict):
            QMessageBox.warning(self, "Invalid candidate", "Candidate data is invalid. Please refresh candidates.")
            return
        postcard_id = str(candidate_data.get("id", "")).strip()
        if not postcard_id:
            QMessageBox.warning(self, "Invalid candidate", "Candidate ID is empty.")
            return
        image_path = Path(image_item.text())
        if not image_path.exists():
            QMessageBox.warning(self, "Missing image", f"Image not found: {image_path}")
            return
        self.image_assignments[postcard_id] = image_path
        self.refresh_assignment_list()

    def refresh_assignment_list(self) -> None:
        self.image_assignment_list.clear()
        for postcard_id in sorted(self.image_assignments.keys()):
            self.image_assignment_list.addItem(f"{postcard_id} <= {self.image_assignments[postcard_id]}")

    def clear_selected_assignment(self) -> None:
        item = self.image_assignment_list.currentItem()
        if item is None:
            return
        text = item.text()
        postcard_id = text.split(" <=", 1)[0].strip()
        if postcard_id in self.image_assignments:
            del self.image_assignments[postcard_id]
        self.refresh_assignment_list()

    def run_posthi_import(self) -> None:
        received_path = Path(self.posthi_received_path_input.text().strip())
        sent_path = Path(self.posthi_sent_path_input.text().strip())
        expired_path = Path(self.posthi_expired_sent_path_input.text().strip())
        if not received_path.exists() or not sent_path.exists() or not expired_path.exists():
            QMessageBox.warning(self, "Missing files", "Please select all three Post-Hi CSV files first.")
            return

        try:
            parse_date, format_date = load_date_helpers(self.project_root)
            recv_rows = collect_posthi_rows(received_path, 0, parse_date, format_date)
            sent_rows = collect_posthi_rows(sent_path, 1, parse_date, format_date)
            expired_rows = collect_posthi_rows(expired_path, 2, parse_date, format_date)
            recv_added = append_rows_with_dedupe(self.project_root / "_data" / "received.csv", recv_rows)
            sent_added = append_rows_with_dedupe(self.project_root / "_data" / "sent.csv", sent_rows + expired_rows)
        except Exception as exc:
            QMessageBox.warning(self, "Import failed", str(exc))
            return

        self.log(f"Post-Hi imported from selected files: received +{recv_added}, sent +{sent_added}")
        self.on_data_changed()
        QMessageBox.information(self, "Done", f"Imported received +{recv_added}, sent +{sent_added}.")

    def run_postcrossing_import(self) -> None:
        try:
            import urllib3

            urllib3.disable_warnings()
            recv_ids = parse_postcrossing_ids(self.pc_received_input.toPlainText())
            sent_ids = parse_postcrossing_ids(self.pc_sent_input.toPlainText())
            recv_rows = [fetch_postcrossing_row(card_id, "received") for card_id in recv_ids]
            sent_rows = [fetch_postcrossing_row(card_id, "sent") for card_id in sent_ids]
            recv_added = append_rows_with_dedupe(self.project_root / "_data" / "received.csv", recv_rows)
            sent_added = append_rows_with_dedupe(self.project_root / "_data" / "sent.csv", sent_rows)
        except Exception as exc:
            QMessageBox.warning(self, "Import failed", str(exc))
            return

        self.log(f"Postcrossing imported: received +{recv_added}, sent +{sent_added}")
        self.on_data_changed()
        QMessageBox.information(self, "Done", f"Imported received +{recv_added}, sent +{sent_added}.")

    def run_icy_import(self) -> None:
        try:
            import urllib3

            urllib3.disable_warnings()
            parse_date, format_date = load_date_helpers(self.project_root)
            recv_entries = parse_icy_entries(self.icy_received_input.toPlainText())
            sent_entries = parse_icy_entries(self.icy_sent_input.toPlainText())
            recv_rows = [fetch_icy_row(entry, 0, parse_date, format_date) for entry in recv_entries]
            sent_rows = [fetch_icy_row(entry, 1, parse_date, format_date) for entry in sent_entries]
            recv_added = append_rows_with_dedupe(self.project_root / "_data" / "received.csv", recv_rows)
            sent_added = append_rows_with_dedupe(self.project_root / "_data" / "sent.csv", sent_rows)
        except Exception as exc:
            QMessageBox.warning(self, "Import failed", str(exc))
            return

        self.log(f"iCardYou imported: received +{recv_added}, sent +{sent_added}")
        self.on_data_changed()
        QMessageBox.information(self, "Done", f"Imported received +{recv_added}, sent +{sent_added}.")

    def run_postprocess_scripts(self) -> None:
        code_sort, out_sort = run_python_script(self.project_root, "sort.py")
        code_group, out_group = run_python_script(self.project_root, "grouped.py")
        self.log(out_sort or "sort.py finished.")
        self.log(out_group or "grouped.py finished.")
        if code_sort != 0 or code_group != 0:
            QMessageBox.warning(self, "Post-process failed", "sort.py or grouped.py failed. See logs.")
            return
        self.on_data_changed()
        QMessageBox.information(self, "Done", "sort.py + grouped.py finished.")

    def run_image_import(self) -> None:
        try:
            from PIL import Image
        except ImportError:
            QMessageBox.warning(self, "Missing dependency", "Please install Pillow.")
            return

        if not self.image_assignments:
            QMessageBox.warning(self, "No assignments", "Please assign at least one image to a candidate ID.")
            return

        direction = self.image_direction_combo.currentText().lower()
        target_dir = self.project_root / ("received" if direction == "received" else "sent")
        target_dir.mkdir(parents=True, exist_ok=True)

        imported = 0
        updated = 0
        for postcard_id, source in self.image_assignments.items():
            if not source.exists():
                self.log(f"Skipped missing source image: {source}")
                continue
            output_path = target_dir / f"{postcard_id}.jpg"
            existed_before = output_path.exists()
            with Image.open(source) as img:
                width, height = img.size
                if width > height:
                    target_width = 600
                    target_height = int(height / width * 600)
                else:
                    target_height = 600
                    target_width = int(width / height * 600)
                resized = img.resize((target_width, target_height))
                resized = resized.convert("RGB")
                resized.save(output_path, format="JPEG")
            if existed_before:
                updated += 1
            else:
                imported += 1

        self.log(f"Imported images to {target_dir}: new +{imported}, updated +{updated}")
        self.on_data_changed()
        self.refresh_missing_image_candidates()
        self.image_assignments.clear()
        self.refresh_assignment_list()
        QMessageBox.information(self, "Done", f"Imported new {imported}, updated {updated} images.")


class MainWindow(QMainWindow):
    def __init__(self, project_root: Path, translator: AppTranslator, current_lang: str) -> None:
        super().__init__()
        self.project_root = project_root
        self.translator = translator
        self.current_lang = current_lang
        self._centered_once = False
        self.received_records: list[dict[str, str]] = []
        self.sent_records: list[dict[str, str]] = []

        self.setWindowTitle(self.translator.tr("JiYou's Postcard Collection"))
        self.resize(1024, 768)
        self.setMaximumSize(1024, 768)

        self.stacked = QStackedWidget()
        self.received_panel = PostcardsPanel(project_root, "Received", [], self.translator)
        self.sent_panel = PostcardsPanel(project_root, "Sent", [], self.translator)
        self.stacked.addWidget(self.received_panel)
        self.stacked.addWidget(self.sent_panel)
        self.setCentralWidget(self.stacked)

        self.setup_menu()
        self.reload_data()
        self.show_received()

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        if not self._centered_once:
            center_window(self)
            self._centered_once = True

    def setup_menu(self) -> None:
        menu_bar = self.menuBar()

        view_menu = menu_bar.addMenu(self.translator.tr("Collection"))
        self.received_action = QAction(self.translator.tr("Show Received"), self, checkable=True)
        self.sent_action = QAction(self.translator.tr("Show Sent"), self, checkable=True)
        action_group = QActionGroup(self)
        action_group.setExclusive(True)
        action_group.addAction(self.received_action)
        action_group.addAction(self.sent_action)
        self.received_action.triggered.connect(self.show_received)
        self.sent_action.triggered.connect(self.show_sent)
        view_menu.addAction(self.received_action)
        view_menu.addAction(self.sent_action)

        tools_menu = menu_bar.addMenu("Tools")
        import_action = QAction(self.translator.tr("Import new postcards..."), self)
        import_action.triggered.connect(self.open_import_dialog)
        tools_menu.addAction(import_action)

        reload_action = QAction("Reload data", self)
        reload_action.triggered.connect(self.reload_data)
        tools_menu.addAction(reload_action)

        language_menu = menu_bar.addMenu(self.translator.tr("Language"))
        self.language_action_group = QActionGroup(self)
        self.language_action_group.setExclusive(True)
        self.lang_zh_action = QAction(self.translator.tr("中文"), self, checkable=True)
        self.lang_en_action = QAction(self.translator.tr("English"), self, checkable=True)
        self.language_action_group.addAction(self.lang_zh_action)
        self.language_action_group.addAction(self.lang_en_action)
        self.lang_zh_action.setChecked(self.current_lang == "zh")
        self.lang_en_action.setChecked(self.current_lang == "en")
        self.lang_zh_action.triggered.connect(lambda checked: self.on_language_selected("zh", checked))
        self.lang_en_action.triggered.connect(lambda checked: self.on_language_selected("en", checked))
        language_menu.addAction(self.lang_zh_action)
        language_menu.addAction(self.lang_en_action)

    def reload_data(self) -> None:
        data_dir = self.project_root / "_data"
        self.received_records = load_csv_records(data_dir / "received.csv", "Received")
        self.sent_records = load_csv_records(data_dir / "sent.csv", "Sent")
        self.received_panel.load_data(self.received_records)
        self.sent_panel.load_data(self.sent_records)
        self.update_main_status()

    def update_main_status(self) -> None:
        panel = self.current_panel()
        direction = "Received" if panel is self.received_panel else "Sent"
        self.statusBar().showMessage(
            f"{direction}: {panel.proxy_model.rowCount()} / {panel.model.rowCount()} postcards"
        )

    def current_panel(self) -> PostcardsPanel:
        return self.received_panel if self.stacked.currentWidget() is self.received_panel else self.sent_panel

    def show_received(self) -> None:
        self.stacked.setCurrentWidget(self.received_panel)
        self.received_action.setChecked(True)
        self.update_main_status()

    def show_sent(self) -> None:
        self.stacked.setCurrentWidget(self.sent_panel)
        self.sent_action.setChecked(True)
        self.update_main_status()

    def open_import_dialog(self) -> None:
        dialog = ImportDialog(self.project_root, self.reload_data, self.translator)
        dialog.exec()

    def on_language_selected(self, lang: str, checked: bool) -> None:
        if not checked:
            return
        if lang == self.current_lang:
            return
        script_path = Path(__file__).resolve()
        try:
            subprocess.Popen(
                [sys.executable, str(script_path), "--root", str(self.project_root), "--lang", lang],
                cwd=str(script_path.parent),
            )
        except Exception as exc:
            QMessageBox.warning(self, "Language switch failed", str(exc))
            if self.current_lang == "zh":
                self.lang_zh_action.setChecked(True)
            else:
                self.lang_en_action.setChecked(True)
            return
        QApplication.instance().quit()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Desktop viewer and importer for postcards project data.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Project root containing _data, received, and sent directories.",
    )
    parser.add_argument(
        "--lang",
        choices=["zh", "en"],
        default=detect_default_language(),
        help="UI language for desktop app. Defaults to system language (zh/en).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    required = [root / "_data", root / "received", root / "sent"]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        print("Missing required paths:")
        for p in missing:
            print(f"  - {p}")
        return 2

    app = QApplication(sys.argv)
    apply_readable_app_font(app, args.lang)
    translator = AppTranslator(load_translation_map(root, args.lang))
    window = MainWindow(root, translator, args.lang)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
