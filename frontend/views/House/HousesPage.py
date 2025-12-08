import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer
import threading
import requests
import hashlib
from PyQt6.QtGui import QPainter, QColor, QPixmap


# Global cache for downloaded images
image_cache = {}
image_in_progress = set()

class LogoPlaceholder(QWidget):
    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.color = color
        self.setFixedSize(80, 80)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(self.color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, 80, 80, 8, 8)
        painter.setPen(QColor(255, 255, 255))
        font = painter.font()
        font.setPointSize(12)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "LOGO")

class HouseCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, house_name, description, logo_color, parent=None):
        super().__init__(parent)
        self.house_name = house_name
        self.description = description
        self.logo_color = logo_color
        self.setFixedHeight(110)
        self.default_style = """
            QFrame {
                background-color: #ffffff;
                border: none;
                border-radius: 12px;
            }
        """
        self.clicked_style = """
            QFrame {
                background-color: #f0f0f0;
                border: none;
                border-radius: 12px;
            }
        """
        self.setStyleSheet(self.default_style)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 10))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(25)

        # Left logo area (replaces LogoPlaceholder with a QLabel so we can set images)
        self.logo_label = QLabel()
        self.logo_label.setFixedSize(80, 80)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # circular/rounded background color as placeholder
        self.logo_label.setStyleSheet(f"background-color: {self.logo_color}; border-radius: 8px; color: white; font-weight:700;")
        self.logo_label.setText("LOGO")
        layout.addWidget(self.logo_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(8)

        name_label = QLabel(self.house_name)
        name_label.setStyleSheet("""
            font-size: 20px;
            font-weight: 700;
            color: #111827;
        """)
        name_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        desc_label = QLabel(self.description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            font-size: 12px;
            color: #6b7280;
            line-height: 1.5;
        """)
        desc_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        text_layout.addWidget(name_label)
        text_layout.addWidget(desc_label)
        text_layout.addStretch()

        layout.addLayout(text_layout, 1)

        # right-side static CISC image (small emblem)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(script_dir, "../../assets/images/cisc.png")

        image_label = QLabel()
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            image_label.setPixmap(pixmap)
        else:
            image_label.setText("Image\nMissing")
            image_label.setStyleSheet("font-size: 12px; color: #ff0000; text-align: center;")

        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(image_label)

        self.setLayout(layout)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.setStyleSheet(self.clicked_style)
        self.clicked.emit(self.house_name)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.setStyleSheet(self.default_style)

    def enterEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: none;
                border-radius: 12px;
            }
        """)
        super().enterEvent(event)

    def set_image(self, image_bytes: bytes):
        try:
            pix = QPixmap()
            if pix.loadFromData(image_bytes):
                pix = pix.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.logo_label.setPixmap(pix)
                # remove placeholder styling/text
                try:
                    self.logo_label.setStyleSheet("")
                except Exception:
                    pass
        except Exception:
            pass

    def leaveEvent(self, event):
        self.setStyleSheet(self.default_style)
        super().leaveEvent(event)

class HousesPage(QWidget):
    house_clicked = pyqtSignal(str)
    houses_loaded = pyqtSignal(list)
    
    def __init__(self, username, roles, primary_role, token):
        super().__init__()
        self.username = username
        self.roles = roles
        self.primary_role = primary_role
        self.token = token
        self.houses_container = None
        self.init_ui()
        # connect signal
        self.houses_loaded.connect(self.populate_houses)
        # fetch houses from backend
        self.fetch_houses()

    def name_to_color(self, name: str) -> str:
        # deterministically map name to a pleasant color
        h = hashlib.md5(name.encode("utf-8")).hexdigest()
        # use parts of hash for rgb, keep brightness
        r = int(h[0:2], 16)
        g = int(h[2:4], 16)
        b = int(h[4:6], 16)
        # increase brightness for readability
        r = int((r + 200) / 2) if r < 180 else r
        g = int((g + 200) / 2) if g < 180 else g
        b = int((b + 200) / 2) if b < 180 else b
        return f"#{r:02x}{g:02x}{b:02x}"

    def fetch_houses(self):
        def _worker():
            url = "http://127.0.0.1:8000/api/house/houses/"
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            try:
                resp = requests.get(url, headers=headers, timeout=6)
                if resp.status_code == 200:
                    data = resp.json()
                    # DRF returns list; if paginated, adjust
                    if isinstance(data, dict) and "results" in data:
                        items = data["results"]
                    else:
                        items = data
                    self.houses_loaded.emit(items)
                else:
                    self.houses_loaded.emit([])
            except Exception:
                self.houses_loaded.emit([])

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(25)

        title = QLabel("Houses")
        title.setStyleSheet("""
            font-size: 32px;
            font-weight: 300;
            color: #111827;
            margin-bottom: 10px;
        """)
        main_layout.addWidget(title)

        # placeholder loading message - will be replaced by real data
        loading = QLabel("Loading houses...")
        loading.setStyleSheet("font-size:14px; color:#6b7280;")
        main_layout.addWidget(loading)
        self.houses_container = main_layout

        main_layout.addStretch()
        self.setLayout(main_layout)
        self.setStyleSheet("""
            QWidget {
                background-color: #f9fafb;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
        """)

    def populate_houses(self, items: list):
        # clear existing layout widgets in houses_container
        layout = self.houses_container
        # remove all items
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        title = QLabel("Houses")
        title.setStyleSheet("""
            font-size: 32px;
            font-weight: 300;
            color: #111827;
            margin-bottom: 10px;
        """)
        layout.addWidget(title)

        if not items:
            msg = QLabel("No houses available.")
            msg.setStyleSheet("font-size:14px; color:#6b7280;")
            layout.addWidget(msg)
            layout.addStretch()
            return

        for h in items:
            name = h.get("name") or h.get("slug") or "Unnamed"
            desc = h.get("description") or ""
            color = self.name_to_color(name)
            card = HouseCard(name, desc, color)
            card.clicked.connect(self.house_clicked.emit)

            # determine image URL (prefer logo, then banner)
            image_url = None
            if h.get("logo"):
                image_url = h.get("logo")
            elif h.get("banner"):
                image_url = h.get("banner")

            print(f"[DEBUG] House '{name}': url={image_url}")

            if image_url:
                # if relative path, prefix API base
                if image_url.startswith("/"):
                    image_url = f"http://127.0.0.1:8000{image_url}"

                # Check cache first
                cached = image_cache.get(image_url)
                if cached:
                    print(f"[DEBUG]   Using cached image for {name}")
                    card.set_image(cached)
                else:
                    print(f"[DEBUG]   Downloading image for {name}")
                    # Start download in background with card reference
                    if image_url not in image_in_progress:
                        image_in_progress.add(image_url)
                        threading.Thread(
                            target=self._download_and_apply_image,
                            args=(image_url, card),
                            daemon=True
                        ).start()

            layout.addWidget(card)

        layout.addStretch()

    def _download_and_apply_image(self, image_url: str, card):
        """Download image and apply directly to the card."""
        print(f"[DEBUG] _download_and_apply_image: {image_url}")
        try:
            r = requests.get(image_url, timeout=6)
            print(f"[DEBUG]   Response: {r.status_code}")
            if r.status_code == 200:
                data = r.content
                image_cache[image_url] = data
                print(f"[DEBUG]   Cached {len(data)} bytes, applying to card")
                
                # Apply image directly (card is still referenced by layout)
                try:
                    card.set_image(data)
                    print(f"[DEBUG]   Image applied successfully")
                except Exception as e:
                    print(f"[DEBUG]   Error applying image: {e}")
        except Exception as e:
            print(f"[DEBUG]   Download error: {e}")
        finally:
            image_in_progress.discard(image_url)