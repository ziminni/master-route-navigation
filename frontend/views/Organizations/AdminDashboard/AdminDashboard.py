from pathlib import Path
import json, shutil
from uuid import uuid4

from PyQt6.QtCore import Qt, QSortFilterProxyModel
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QLabel, QListView,
    QPushButton, QStackedWidget, QFormLayout, QTextEdit, QMessageBox, QAbstractItemView,
    QGroupBox, QGridLayout, QListWidget, QListWidgetItem, QFileDialog, QFrame, QSizePolicy, QSpacerItem
)
from .admin_models import Service, ServiceStore, AdminServiceModel
from .admin_delegate import AdminDelegate

_DEF_CATS = ["Organization", "Dorm", "Health", "Office"]

class _Proxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._q = ""
        self._cat = "All"
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

    def setQuery(self, t):
        self._q = t or ""
        self.invalidateFilter()

    def setCategory(self, c):
        self._cat = c or "All"
        self.invalidateFilter()

    def filterAcceptsRow(self, row, parent) -> bool:
        m = self.sourceModel()
        idx = m.index(row, 0, parent)
        title = (m.data(idx, m.TitleRole) or "").lower()
        blurb = (m.data(idx, m.BlurbRole) or "").lower()
        cat   = (m.data(idx, m.CategoryRole) or "").lower()
        if self._cat != "All" and cat != self._cat.lower():
            return False
        q = self._q.strip().lower()
        return not q or q in title or q in blurb

class AdminDashboard(QWidget):
    def __init__(self, **kwargs):
        super().__init__()

        base = Path(__file__).resolve().parent
        data_path = base / "services.json"
        if not data_path.exists():
            data_path.write_text(json.dumps({"items": []}, ensure_ascii=False, indent=2), encoding="utf-8")

        self.store = ServiceStore(data_path)
        self.model = AdminServiceModel(self.store)

        self.stack = QStackedWidget(self)
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.addWidget(self.stack)

        # ========== LIST PAGE ==========
        self.page_list = QWidget()
        self.stack.addWidget(self.page_list)
        pv = QVBoxLayout(self.page_list)
        pv.setSpacing(10)

        # styles for toolbar and inputs
        self.page_list.setStyleSheet("""
        QLabel#title { font-size:22px; font-weight:800; color:#0f4d2a; }
        QPushButton#add { background:#ffb000; color:#1f2d18; padding:8px 14px; border-radius:8px; font-weight:600; }
        QFrame#searchbar { border:1px solid #d7dadf; border-radius:8px; }
        QLineEdit#search { border:0; padding:8px 10px; }
        QComboBox#cat { padding:8px 10px; border:1px solid #d7dadf; border-radius:8px; min-width:120px; }
        QLabel#section { color:#2d3a34; font-weight:700; }
        """)

        # header: title + add button
        header = QHBoxLayout()
        pv.addLayout(header)
        title = QLabel("Admin Dashboard")
        title.setObjectName("title")
        self.btn_add = QPushButton("＋  Add Department")
        self.btn_add.setObjectName("add")
        header.addWidget(title, 1)
        header.addWidget(self.btn_add, 0)

        # search + category row
        bar = QHBoxLayout()
        sb = QFrame()
        sb.setObjectName("searchbar")
        sb.setLayout(bar)
        bar.setContentsMargins(8, 0, 8, 0)
        self.search = QLineEdit(placeholderText="Search here…")
        self.search.setObjectName("search")
        self.search.setClearButtonEnabled(True)
        bar.addWidget(self.search, 1)

        row = QHBoxLayout()
        pv.addWidget(sb)
        pv.addLayout(row)
        row.addWidget(QLabel("Manage Departments", objectName="section"), 1)

        # right-aligned category filter
        self.category = QComboBox(objectName="cat")
        self.category.addItem("All")
        self.store.load()
        for c in sorted({(it.category or "Uncategorized") for it in self.store.items}):
            self.category.addItem(c)
        row.addWidget(self.category, 0)

        # cards list
        self.view = QListView()
        self.view.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        pv.addWidget(self.view, 1)

        self.proxy = _Proxy(self)
        self.proxy.setSourceModel(self.model)
        self.view.setModel(self.proxy)
        self.delegate = AdminDelegate(self.view)
        self.view.setItemDelegate(self.delegate)

        self.count = QLabel("")
        pv.addWidget(self.count)

        self.search.textChanged.connect(self.proxy.setQuery)
        self.category.currentTextChanged.connect(self.proxy.setCategory)
        self.btn_add.clicked.connect(lambda: self._add_new())

        if hasattr(self.model, "changed"):
            self.model.changed.connect(self._on_model_changed)
        self.delegate.editClicked.connect(self._edit_row)
        self.delegate.deleteClicked.connect(self._delete_row)

        # ========== EDITOR PAGE ==========
        self.page_edit = QWidget()
        self.stack.addWidget(self.page_edit)
        pe = QVBoxLayout(self.page_edit)
        pe.setContentsMargins(6, 6, 6, 6)
        pe.setSpacing(10)
        self.page_edit.setStyleSheet("""
        QGroupBox { border:1px solid #d7dadf; border-radius:8px; margin-top:16px; padding:10px; }
        QGroupBox::title { subcontrol-origin: margin; left: 12px; top: 6px; padding: 0 6px; color:#0f4d2a; font-weight:700; }
        QLineEdit, QTextEdit, QComboBox { padding:6px; }
        QPushButton#primary { background:#0f4d2a; color:white; padding:8px 18px; border-radius:8px; }
        QPushButton#danger  { background:#e0e0e0; color:#0f4d2a; padding:8px 18px; border-radius:8px; }
        QPushButton#ghost   { background:#eceeef; color:#333; padding:8px 18px; }
        """)

        top = QHBoxLayout()
        pe.addLayout(top)

        gb_basic = QGroupBox("Basic Information")
        top.addWidget(gb_basic, 1)
        g1 = QGridLayout(gb_basic)
        g1.setHorizontalSpacing(12)
        g1.setVerticalSpacing(10)

        self.e_title = QLineEdit()
        self.e_title.setPlaceholderText("e.g. Student Supreme Student")
        self.e_category = QComboBox()
        self.e_category.addItems([""] + _DEF_CATS)
        self.e_blurb = QTextEdit()
        self.e_blurb.setPlaceholderText("Provide a description of the department")
        self.e_location = QLineEdit()
        self.e_location.setPlaceholderText("e.g. Admin, window 3")
        self.e_image = QLineEdit()
        self.e_image.setReadOnly(True)
        self.btn_browse = QPushButton("Browse")
        self.btn_browse.clicked.connect(self._browse_image)

        r = 0
        g1.addWidget(QLabel("Department*"), r, 0); g1.addWidget(self.e_title, r, 1); r += 1
        g1.addWidget(QLabel("Category*"),   r, 0); g1.addWidget(self.e_category, r, 1); r += 1
        g1.addWidget(QLabel("Department Description*"), r, 0); g1.addWidget(self.e_blurb, r, 1); r += 1
        g1.addWidget(QLabel("Physical location*"), r, 0); g1.addWidget(self.e_location, r, 1); r += 1
        g1.addWidget(QLabel("Image*"), r, 0)
        w_img = QWidget()
        row_img = QHBoxLayout(w_img)
        row_img.setContentsMargins(0, 0, 0, 0)
        row_img.addWidget(self.e_image, 1)
        row_img.addWidget(self.btn_browse, 0)
        g1.addWidget(w_img, r, 1); r += 1

        gb_services = QGroupBox("Services")
        top.addWidget(gb_services, 1)
        g2 = QGridLayout(gb_services)
        self.service_list = QListWidget()
        self.service_list.setMinimumHeight(160)
        g2.addWidget(QLabel("Service list*"), 0, 0, 1, 2)
        g2.addWidget(self.service_list, 1, 0, 1, 2)
        g2.addWidget(QLabel("Add a service*"), 2, 0, 1, 2)
        self.e_srv_name = QLineEdit()
        self.e_srv_name.setPlaceholderText("e.g. Blood Donation")
        self.e_srv_desc = QTextEdit()
        self.e_srv_desc.setPlaceholderText("Description of the service")
        btn_add_srv = QPushButton("Add service")
        btn_add_srv.clicked.connect(self._add_service)
        g2.addWidget(QLabel("Name*"), 3, 0); g2.addWidget(self.e_srv_name, 3, 1)
        g2.addWidget(QLabel("Description*"), 4, 0); g2.addWidget(self.e_srv_desc, 4, 1)
        g2.addItem(QSpacerItem(0, 8, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum), 5, 0, 1, 2)
        g2.addWidget(btn_add_srv, 6, 1)

        gb_contacts = QGroupBox("URL and Contact Information")
        pe.addWidget(gb_contacts)
        g3 = QGridLayout(gb_contacts)
        self.e_url = QLineEdit();  self.e_url.setPlaceholderText("https://example.com")
        self.e_email = QLineEdit(); self.e_email.setPlaceholderText("e.g. dept@example.edu.ph")
        self.e_contact = QLineEdit(); self.e_contact.setPlaceholderText("09000000000")
        g3.addWidget(QLabel("Service URL *"), 0, 0); g3.addWidget(self.e_url, 0, 1)
        g3.addWidget(QLabel("Email *"),       1, 0); g3.addWidget(self.e_email, 1, 1)
        g3.addWidget(QLabel("Contact number"),2, 0); g3.addWidget(self.e_contact, 2, 1)

        row_btns = QHBoxLayout()
        pe.addLayout(row_btns)
        self.btn_draft  = QPushButton("Draft");  self.btn_draft.setObjectName("ghost")
        self.btn_save   = QPushButton("Create"); self.btn_save.setObjectName("primary")
        self.btn_cancel = QPushButton("Cancel"); self.btn_cancel.setObjectName("danger")
        row_btns.addWidget(self.btn_draft, 0); row_btns.addStretch(1)
        row_btns.addWidget(self.btn_save, 0); row_btns.addWidget(self.btn_cancel, 0)

        # hooks
        self._editing_row = -1
        self._draft = False
        self.btn_draft.clicked.connect(self._toggle_draft)
        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(lambda: self.stack.setCurrentWidget(self.page_list))

        # init
        self.stack.setCurrentWidget(self.page_list)
        self._refresh_categories()
        self._update_count()

    # ==== list helpers ====
    def _on_model_changed(self):
        self._refresh_categories()
        self._update_count()

    def _refresh_categories(self):
        cats = {"All"}
        for r in range(self.model.rowCount()):
            idx = self.model.index(r, 0)
            c = (self.model.data(idx, getattr(self.model, "CategoryRole", -1)) or "").strip() or "Uncategorized"
            cats.add(c)
        cur = self.category.currentText() or "All"
        self.category.blockSignals(True)
        self.category.clear()
        self.category.addItems(["All"] + sorted([c for c in cats if c != "All"]))
        if cur in cats:
            self.category.setCurrentText(cur)
        self.category.blockSignals(False)

    def _update_count(self):
        self.count.setText(f"{self.proxy.rowCount()} items")

    def _row_from_proxy(self, pidx) -> int:
        if not pidx.isValid():
            return -1
        return self.proxy.mapToSource(pidx).row()

    # ==== list actions ====
    def _add_new(self):
        self._editing_row = -1
        self._draft = False
        self._fill_editor(Service(category="", title="", blurb="", url="", email="",
                                  location="", contact="", image="", services=[]))
        self.btn_save.setText("Create")
        self.stack.setCurrentWidget(self.page_edit)

    def _edit_row(self, pidx):
        r = self._row_from_proxy(pidx)
        if r < 0 or r >= self.model.rowCount():
            return
        s = self._item_at(r)
        self._editing_row = r
        self._draft = getattr(s, "draft", False)
        self._fill_editor(s)
        self.btn_save.setText("Save")
        self.stack.setCurrentWidget(self.page_edit)

    def _delete_row(self, pidx):
        r = self._row_from_proxy(pidx)
        if r < 0 or r >= self.model.rowCount():
            return
        if QMessageBox.question(self, "Confirm", "Delete this service?") == QMessageBox.StandardButton.Yes:
            self.model.remove(r)

    # ==== editor helpers ====
    def _browse_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select image", "", "Images (*.png *.jpg *.jpeg *.webp *.bmp);;All files (*)"
        )
        if path:
            self.e_image.setText(path)

    # ==== file upload helpers ====
    def _uploads_dir(self) -> Path:
        # frontend/views/Organizations/AdminDashboard/… -> frontend/assets/uploads
        return Path(__file__).resolve().parents[3] / "assets" / "uploads"

    def _ensure_uploads(self) -> Path:
        d = self._uploads_dir()
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _is_in_uploads(self, p: Path) -> bool:
        try:
            return self._uploads_dir().resolve() in p.resolve().parents
        except Exception:
            return False

    def _copy_image_to_uploads(self, src: str) -> str:
        if not src:
            return ""
        src_path = Path(src)
        if not src_path.exists():
            return src
        if self._is_in_uploads(src_path):
            rel = src_path.relative_to(self._uploads_dir())
            return f"assets/uploads/{rel.as_posix()}"
        self._ensure_uploads()
        ext = src_path.suffix.lower() or ".jpg"
        dst_name = f"{uuid4().hex}{ext}"
        dst_path = self._uploads_dir() / dst_name
        shutil.copy2(src_path, dst_path)
        return f"assets/uploads/{dst_name}"

    def _add_service(self):
        name = self.e_srv_name.text().strip()
        desc = self.e_srv_desc.toPlainText().strip()
        if not name:
            return
        it = QListWidgetItem(f"{name} — {desc[:60]}")
        it.setData(Qt.ItemDataRole.UserRole, {"name": name, "desc": desc})
        self.service_list.addItem(it)
        self.e_srv_name.clear()
        self.e_srv_desc.clear()

    def _services_from_ui(self):
        out = []
        for i in range(self.service_list.count()):
            it = self.service_list.item(i)
            out.append(it.data(Qt.ItemDataRole.UserRole) or {})
        return out

    def _toggle_draft(self):
        self._draft = not self._draft
        self.btn_draft.setText("Draft" + (" ✓" if self._draft else ""))

    def _item_at(self, row: int) -> Service:
        if hasattr(self.model, "item"):
            return self.model.item(row)
        idx = self.model.index(row, 0)
        g = lambda role, d="": self.model.data(idx, role) or d
        return Service(
            category=g(getattr(self.model, "CategoryRole", -1)),
            title=g(getattr(self.model, "TitleRole", -1)),
            blurb=g(getattr(self.model, "BlurbRole", -1)),
            url=g(getattr(self.model, "UrlRole", -1)),
            email=g(getattr(self.model, "EmailRole", -1)),
            location=g(getattr(self.model, "LocationRole", -1)),
            contact=g(getattr(self.model, "ContactRole", -1)),
            image=g(getattr(self.model, "ImageRole", -1)),
            services=g(getattr(self.model, "ServicesRole", -1)) or [],
            draft=bool(g(getattr(self.model, "DraftRole", -1), False)),
        )

    def _fill_editor(self, s: Service):
        if s.category and s.category in _DEF_CATS:
            self.e_category.setCurrentText(s.category)
        else:
            self.e_category.setCurrentIndex(0)
        self.e_title.setText(getattr(s, "title", ""))
        self.e_blurb.setPlainText(getattr(s, "blurb", ""))
        self.e_location.setText(getattr(s, "location", ""))
        self.e_image.setText(getattr(s, "image", ""))
        self.service_list.clear()
        for it in getattr(s, "services", []) or []:
            item = QListWidgetItem(f"{it.get('name','')} — {it.get('desc','')[:60]}")
            item.setData(Qt.ItemDataRole.UserRole, {"name": it.get("name", ""), "desc": it.get("desc", "")})
            self.service_list.addItem(item)
        self.e_url.setText(getattr(s, "url", ""))
        self.e_email.setText(getattr(s, "email", ""))
        self.e_contact.setText(getattr(s, "contact", ""))

    def _save(self):
        cat = self.e_category.currentText().strip()
        img_rel = self._copy_image_to_uploads(self.e_image.text().strip())
        s = Service(
            category=cat,
            title=self.e_title.text().strip(),
            blurb=self.e_blurb.toPlainText().strip(),
            url=self.e_url.text().strip(),
            email=self.e_email.text().strip(),
            location=self.e_location.text().strip(),
            contact=self.e_contact.text().strip(),
            image=img_rel,
            services=self._services_from_ui(),
            draft=self._draft,
        )
        if self._editing_row == -1:
            self.model.add(s)
        else:
            self.model.update(self._editing_row, s)

        self._editing_row = -1
        self.stack.setCurrentWidget(self.page_list)
        self.proxy.invalidateFilter()
