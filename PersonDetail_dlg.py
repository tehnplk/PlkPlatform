from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QFormLayout, QLabel, QVBoxLayout

from Theme_helper import current_theme

DETAIL_KEYS = (
    "pid",
    "hn",
    "cid",
    "full_name",
    "sex",
    "house_no",
    "village_moo",
    "tambon",
)

DISPLAY_LABELS = {
    "full_name": "ชื่อ-สกุล",
    "house_no": "บ้านเลขที่",
    "village_moo": "หมู่ที่",
    "tambon": "ตำบล",
}


def format_detail_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def build_detail_rows(detail: dict[str, Any]) -> list[tuple[str, str]]:
    prename = format_detail_value(detail.get("prename"))
    fname = format_detail_value(detail.get("fname"))
    lname = format_detail_value(detail.get("lname"))
    full_name = " ".join(part for part in [prename, fname, lname] if part).strip()

    enriched_detail = dict(detail)
    enriched_detail["full_name"] = full_name

    rows: list[tuple[str, str]] = []
    for key in DETAIL_KEYS:
        label = DISPLAY_LABELS.get(key, key)
        rows.append((f"{label}:", format_detail_value(enriched_detail.get(key))))
    return rows


class DlgPersonDetail(QDialog):
    def __init__(self, detail: dict, parent=None) -> None:
        super().__init__(parent)
        theme = current_theme()
        self.setWindowTitle("รายละเอียดบุคคล")
        self.setMinimumWidth(460)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(8)
        for label, value in build_detail_rows(detail):
            value_label = QLabel(value)
            value_label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
                | Qt.TextInteractionFlag.TextSelectableByKeyboard
            )
            value_label.setStyleSheet(
                f"background:{theme.surface}; color:{theme.text}; "
                f"border:1px solid {theme.border}; border-radius:8px; padding:6px 8px;"
            )
            form.addRow(label, value_label)

        container = QVBoxLayout(self)
        container.addLayout(form)
        self.setStyleSheet(
            f"""
            QDialog {{
                background: {theme.window};
            }}
            QLabel {{
                color: {theme.text};
                font-size: 13px;
                font-weight: 600;
            }}
            """
        )
