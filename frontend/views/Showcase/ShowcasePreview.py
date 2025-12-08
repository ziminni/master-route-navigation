from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Optional

from PyQt6.QtCore import Qt, QPoint, QRectF
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QPainterPath, QColor, QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QLabel,
    QTextBrowser, QWidget, QSizePolicy
)

# DB helpers
try:
    from .db.ShowcaseDBHelper import (
        get_project,
        competition_exists,
        get_competition_with_relations,
    )
except Exception:
    from db.ShowcaseDBHelper import (
        get_project,
        competition_exists,
        get_competition_with_relations,
    )

GREEN   = "#146c43"
TEXT    = "#1f2937"
MUTED   = "#6b7280"
BG      = "#f3f4f6"
BORDER  = "#e5e7eb"


# ---------- helpers: assets ----------

def _find_dir(name: str) -> Path:
    here = Path(__file__).resolve()
    for up in range(0, 7):
        base = here.parents[up] if up else here.parent
        cand = base / "assets" / name
        if cand.is_dir():
            return cand
    return Path.cwd() / "assets" / name


ICON_DIR = _find_dir("icons")
IMG_DIR  = _find_dir("images")


def _icon(name: str) -> QIcon:
    p = ICON_DIR / name
    return QIcon(str(p)) if p.exists() else QIcon()


def _placeholder(w: int, h: int, label: str = "image") -> QPixmap:
    w = max(w, 1)
    h = max(h, 1)
    pm = QPixmap(w, h)
    pm.fill(QColor("#d1d5db"))
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(QColor("#9ca3af"))
    p.setBrush(QColor("#e5e7eb"))
    p.drawRoundedRect(0, 0, w, h, 18, 18)
    f = QFont()
    f.setPointSize(12)
    f.setBold(True)
    p.setFont(f)
    p.setPen(QColor("#6b7280"))
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, label.upper())
    p.end()
    return pm


def _load_image(fname: str | None) -> QPixmap:
    if fname:
        p = Path(fname)
        if not p.exists():
            p = IMG_DIR / fname
        if p.exists():
            pm = QPixmap(str(p))
            if not pm.isNull():
                return pm
    return _placeholder(900, 400)


# ---------- rounded image widget (aspect-ratio aware, capped height) ----------

class RoundedImage(QWidget):
    def __init__(self, radius: int = 18, parent: QWidget | None = None):
        super().__init__(parent)
        self.radius = radius
        self._pm = QPixmap()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(220)

    def _update_min_height(self) -> None:
        if self._pm.isNull():
            return
        w = self._pm.width()
        h = self._pm.height()
        if w <= 0:
            return
        aspect = h / float(w)
        base_width = max(min(self.width(), 900), 600)
        target = int(base_width * aspect)
        target = max(200, min(target, 360))
        self.setMinimumHeight(target)

    def setPixmap(self, pm: QPixmap):
        self._pm = pm
        self._update_min_height()
        self.update()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._update_min_height()

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(r, self.radius, self.radius)
        p.setClipPath(path)

        if not self._pm.isNull():
            scaled = self._pm.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            p.drawPixmap(x, y, scaled)
        else:
            p.fillRect(r, QColor("#d1d5db"))

        p.setClipping(False)
        p.setPen(QColor(BORDER))
        p.drawRoundedRect(r, self.radius, self.radius)
        p.end()


# ---------- main dialog ----------

class ShowcasePreviewDialog(QDialog):
    """
    items: list of dicts from list_showcase_cards(...)
    Each item may be a project or a competition card.
    """

    def __init__(self, items: List[Dict], start_index: int = 0, parent=None):
        super().__init__(parent)
        self.items = items
        self.idx = start_index
        self.img_idx = 0
        self.drag_pos = QPoint()

        # caches
        self._kind_cache: dict[int, bool] = {}
        self._comp_cache: dict[int, Dict] = {}
        self._proj_cache: dict[int, Optional[Dict]] = {}

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)
        self.resize(1024, 700)
        self.setStyleSheet(f"""
            QDialog {{
                background:{BG};
                border:1px solid {BORDER};
                border-radius:12px;
            }}
            QPushButton[kind="tool"] {{
                background:{GREEN};
                color:white;
                border:none;
                border-radius:12px;
                padding:6px;
                min-width:28px;
                min-height:28px;
            }}
            QPushButton[kind="tool"]:hover {{
                background:#158f4f;
            }}
            QLabel.title {{
                color:{GREEN};
                font-size:18px;
                font-weight:700;
            }}
            QLabel.meta {{
                color:{MUTED};
                font-size:12px;
            }}
            QLabel.chip {{
                background:#ecfdf5;
                color:{GREEN};
                border:1px solid #c7f0df;
                border-radius:10px;
                padding:2px 8px;
                font-size:11px;
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        # ----- IMAGE AREA (top) -----
        self.img_wrap = QFrame(self)
        iv = QVBoxLayout(self.img_wrap)
        iv.setContentsMargins(0, 0, 0, 0)
        iv.setSpacing(0)

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(8, 8, 8, 8)
        top_bar.setSpacing(6)

        self.drag_btn = QPushButton()
        self.drag_btn.setProperty("kind", "tool")
        self.drag_btn.setIcon(_icon("icon_menu.png"))
        self.drag_btn.setCursor(Qt.CursorShape.SizeAllCursor)
        top_bar.addWidget(self.drag_btn, 0, Qt.AlignmentFlag.AlignLeft)
        top_bar.addStretch(1)

        self.counter_lbl = QLabel("")
        self.counter_lbl.setObjectName("counter")
        self.counter_lbl.setStyleSheet(
            "QLabel#counter{color:white; background:rgba(0,0,0,.45);"
            "padding:2px 8px; border-radius:9px; font-size:11px;}"
        )
        top_bar.addWidget(self.counter_lbl, 0, Qt.AlignmentFlag.AlignRight)

        self.close_btn = QPushButton()
        self.close_btn.setProperty("kind", "tool")
        self.close_btn.setIcon(_icon("icon_close.png"))
        self.close_btn.clicked.connect(self.reject)
        top_bar.addWidget(self.close_btn, 0, Qt.AlignmentFlag.AlignRight)
        iv.addLayout(top_bar)

        self.rounded = RoundedImage(18, self.img_wrap)
        iv.addWidget(self.rounded, 1)

        nav_row = QHBoxLayout()
        nav_row.setContentsMargins(0, 6, 0, 0)
        nav_row.setSpacing(0)

        self.prev_btn = QPushButton()
        self.prev_btn.setProperty("kind", "tool")
        self.prev_btn.setIcon(_icon("icon_chevron_left.png"))
        self.next_btn = QPushButton()
        self.next_btn.setProperty("kind", "tool")
        self.next_btn.setIcon(_icon("icon_chevron_right.png"))
        self.prev_btn.clicked.connect(self._prev_image)
        self.next_btn.clicked.connect(self._next_image)

        nav_row.addWidget(self.prev_btn, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        nav_row.addStretch(1)
        nav_row.addWidget(self.next_btn, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        iv.addLayout(nav_row)

        root.addWidget(self.img_wrap, 0)

        # ----- TEXT AREA (bottom) -----
        text_frame = QFrame(self)
        text_frame.setStyleSheet(
            f"QFrame{{background:white; border-radius:12px; border:1px solid {BORDER};}}"
        )
        tb = QVBoxLayout(text_frame)
        tb.setContentsMargins(12, 10, 12, 10)
        tb.setSpacing(6)

        head_row = QHBoxLayout()
        head_row.setSpacing(8)

        self.title_lbl = QLabel("Title")
        self.title_lbl.setObjectName("title")
        self.title_lbl.setProperty("class", "title")

        self.status_chip = QLabel("")
        self.status_chip.setProperty("class", "chip")

        head_row.addWidget(self.title_lbl, 1)
        head_row.addWidget(self.status_chip, 0, Qt.AlignmentFlag.AlignRight)
        tb.addLayout(head_row)

        self.meta_lbl = QLabel("")
        self.meta_lbl.setProperty("class", "meta")
        tb.addWidget(self.meta_lbl)

        # rich info (project / event details)
        self.info_lbl = QLabel("")
        self.info_lbl.setWordWrap(True)
        self.info_lbl.setStyleSheet(f"color:{MUTED}; font-size:12px;")
        self.info_lbl.setTextFormat(Qt.TextFormat.RichText)
        self.info_lbl.setOpenExternalLinks(True)
        tb.addWidget(self.info_lbl)

        self.desc = QTextBrowser()
        self.desc.setOpenExternalLinks(True)
        self.desc.setStyleSheet(
            f"QTextBrowser{{border:1px solid {BORDER}; background:white;"
            "border-radius:10px; padding:8px; font-size:13px;}}"
        )
        self.desc.setMinimumHeight(260)
        self.desc.setMaximumHeight(420)
        self.desc.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb.addWidget(self.desc, 1)

        root.addWidget(text_frame, 1)

        # more height to text than image
        root.setStretch(0, 3)
        root.setStretch(1, 7)

        self._refresh()

    # ---------- utility ----------

    def _images_for_current(self) -> List[str]:
        item = self.items[self.idx]
        imgs = item.get("images") or ([item.get("image")] if item.get("image") else [])
        if not imgs:
            imgs = ["1.jpg"]
        return imgs

    def _meta_text_project(self, it: Dict, proj: Optional[Dict] = None) -> str:
        parts: List[str] = []
        pid = it.get("id")
        if pid is not None:
            parts.append(f"Project ID #{pid}")
        author = (it.get("author_display") or (proj or {}).get("author_display"))
        if author:
            parts.append(f"by {author}")
        posted = (proj or {}).get("posted_ago") or it.get("posted_ago")
        if posted:
            parts.append(posted)
        nimg = it.get("images_count")
        if isinstance(nimg, int):
            parts.append(f"{nimg} image{'s' if nimg != 1 else ''}")
        return " • ".join(parts)

    def _is_competition_item(self, it: Dict) -> bool:
        """
        Decide if the current card refers to a competition.
        Prefer explicit 'kind', otherwise fall back to DB existence check.
        """
        if it.get("kind") == "competition":
            return True
        if it.get("kind") == "project":
            return False

        cid = it.get("id")
        if cid is None:
            return False

        if cid in self._kind_cache:
            return self._kind_cache[cid]

        try:
            flag = competition_exists(int(cid))
        except Exception:
            flag = False

        self._kind_cache[cid] = flag
        return flag

    def _load_competition_details(self, competition_id: int) -> Optional[Dict]:
        if competition_id in self._comp_cache:
            return self._comp_cache[competition_id]
        comp = get_competition_with_relations(competition_id)
        self._comp_cache[competition_id] = comp
        return comp

    def _load_project_details(self, project_id: int) -> Optional[Dict]:
        if project_id in self._proj_cache:
            return self._proj_cache[project_id]
        try:
            proj = get_project(project_id)
        except Exception:
            proj = None
        self._proj_cache[project_id] = proj
        return proj

    # ---------- refresh ----------

    def _refresh(self):
        it = self.items[self.idx]
        imgs = self._images_for_current()

        is_comp = self._is_competition_item(it)
        comp = self._load_competition_details(it["id"]) if is_comp else None
        proj = None if is_comp else self._load_project_details(it["id"])

        # title + status
        self.title_lbl.setText(it.get("title", ""))
        st = it.get("status") or ""
        self.status_chip.setText(st)
        self.status_chip.setVisible(bool(st))

        # meta
        if is_comp and comp:
            parts: List[str] = []
            cid = comp.get("competition_id") or it.get("id")
            if cid is not None:
                parts.append(f"Competition ID #{cid}")
            if comp.get("organizer"):
                parts.append(comp["organizer"])
            if it.get("posted_ago"):
                parts.append(it["posted_ago"])
            self.meta_lbl.setText(" • ".join(parts))
        else:
            self.meta_lbl.setText(self._meta_text_project(it, proj))

        # summary info (rich label)
        img_count = it.get("images_count") or len(imgs)
        if is_comp and comp:
            event_type = comp.get("event_type") or it.get("category") or "Not specified"
            start = comp.get("start_date") or ""
            end = comp.get("end_date") or ""
            if start and end and start != end:
                sched = f"{start} – {end}"
            else:
                sched = start or end or "Not specified"

            cid = comp.get("competition_id") or it.get("id")
            vis = "Public" if comp.get("is_public") else "Private"
            rel_evt = comp.get("related_event_id")

            lines: List[str] = []
            if cid is not None:
                lines.append(f"<b>Competition ID:</b> #{cid}")
            lines.append(f"<b>Event type:</b> {event_type}")
            lines.append(f"<b>Schedule:</b> {sched}")
            lines.append(f"<b>Images:</b> {img_count}")
            lines.append(f"<b>Visibility:</b> {vis}")
            if rel_evt:
                lines.append(f"<b>Related Event ID:</b> {rel_evt}")

            url_info = comp.get("external_url") or it.get("external_url")
            if url_info:
                lines.append(f"<b>Event link:</b> <a href='{url_info}'>{url_info}</a>")

            self.info_lbl.setText("<br>".join(lines))
        else:
            # project
            pid = it.get("id")
            category = (proj or {}).get("category") or it.get("category") or "Not specified"
            context = (proj or {}).get("context") or it.get("context") or "Not specified"
            course = (proj or {}).get("course_id")
            org = (proj or {}).get("organization_id")
            is_public = (proj or {}).get("is_public")
            tags = (proj or {}).get("tags") or it.get("tags") or []
            tag_txt = ", ".join(
                t["name"] if isinstance(t, dict) else str(t) for t in tags
            ) if tags else "None"
            visibility = "Public" if is_public else "Private"

            url_info = (proj or {}).get("external_url") or it.get("external_url")

            lines: List[str] = []
            if pid is not None:
                lines.append(f"<b>Project ID:</b> #{pid}")
            lines.append(f"<b>Category:</b> {category}")
            lines.append(f"<b>Context:</b> {context}")
            if course is not None or org is not None:
                course_txt = course if course not in (None, "") else "None"
                org_txt = org if org not in (None, "") else "None"
                lines.append(
                    f"<b>Course ID:</b> {course_txt} &nbsp;&nbsp; "
                    f"<b>Organization ID:</b> {org_txt}"
                )
            lines.append(f"<b>Visibility:</b> {visibility}")
            lines.append(f"<b>Tags:</b> {tag_txt}")
            if url_info:
                lines.append(f"<b>Online link:</b> <a href='{url_info}'>{url_info}</a>")

            self.info_lbl.setText("<br>".join(lines))

        # long text (description + team/achievements + link)
        body = (it.get("long_text") or it.get("blurb") or "").strip()
        html_parts: List[str] = []
        if body:
            html_parts.append(body.replace("\n", "<br>"))

        url_for_footer: Optional[str] = None

        if is_comp and comp:
            achs = comp.get("achievements") or []
            if achs:
                html_parts.append("<hr><b>Achievements</b><ul>")
                for ach in achs:
                    line = f"<b>{ach.get('achievement_title','Achievement')}</b>"
                    res = ach.get("result_recognition") or ""
                    awd = ach.get("specific_awards") or ""
                    extras = [s for s in (res, awd) if s]
                    if extras:
                        line += " – " + " / ".join(extras)
                    if ach.get("awarded_at"):
                        line += f" (Awarded: {ach['awarded_at']})"
                    notes = (ach.get("notes") or "").strip()
                    if notes:
                        line += f"<br>&nbsp;&nbsp;{notes}"

                    projs = ach.get("projects") or []
                    if projs:
                        ptxt = ", ".join(
                            f"#{p.get('projects_id')} – {p.get('title') or 'Untitled project'}"
                            for p in projs
                        )
                        line += f"<br>&nbsp;&nbsp;<i>Related projects:</i> {ptxt}"

                    users = ach.get("users") or []
                    if users:
                        names: List[str] = []
                        for u in users:
                            username = u.get("username") or f"user#{u.get('auth_user_id')}"
                            role = u.get("role")
                            if role:
                                names.append(f"{username} ({role})")
                            else:
                                names.append(username)
                        utxt = ", ".join(names)
                        line += f"<br>&nbsp;&nbsp;<i>Participants:</i> {utxt}"

                    html_parts.append(f"<li>{line}</li>")
                html_parts.append("</ul>")

            url_for_footer = comp.get("external_url") or it.get("external_url")
        else:
            # project team & members
            if proj:
                members = proj.get("members") or []
                if members:
                    html_parts.append("<hr><b>Team &amp; Group Members</b><ul>")
                    for m in members:
                        username = m.get("username") or "Member"
                        role = (m.get("role") or "").strip()
                        contrib = (m.get("contributions") or "").strip()
                        extras: List[str] = []
                        if role:
                            extras.append(role)
                        if contrib:
                            extras.append(contrib)
                        if extras:
                            line = f"<b>{username}</b> – " + " · ".join(extras)
                        else:
                            line = f"<b>{username}</b>"
                        html_parts.append(f"<li>{line}</li>")
                    html_parts.append("</ul>")

            url_for_footer = (proj or {}).get("external_url") or it.get("external_url")

        if url_for_footer:
            html_parts.append(f"<br><a href='{url_for_footer}'>Open link</a>")

        html = "<p style='color:{0};line-height:1.5'>{1}</p>".format(
            TEXT, "<br>".join(html_parts) if html_parts else ""
        )
        self.desc.setHtml(html)

        # image
        self.img_idx = self.img_idx % len(imgs)
        pm = _load_image(imgs[self.img_idx])
        self.rounded.setPixmap(pm)
        self.counter_lbl.setText(f"{self.img_idx+1}/{len(imgs)}")

    # ---------- events ----------

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.rounded.update()

    def _prev_image(self):
        imgs = self._images_for_current()
        self.img_idx = (self.img_idx - 1) % len(imgs)
        self._refresh()

    def _next_image(self):
        imgs = self._images_for_current()
        self.img_idx = (self.img_idx + 1) % len(imgs)
        self._refresh()

    # dragging frameless dialog
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self.drag_pos)
        super().mouseMoveEvent(e)

    # keyboard navigation
    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_Left, Qt.Key.Key_A):
            self._prev_image()
        elif e.key() in (Qt.Key.Key_Right, Qt.Key.Key_D):
            self._next_image()
        elif e.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(e)
