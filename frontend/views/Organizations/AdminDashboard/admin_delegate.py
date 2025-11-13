from PyQt6.QtCore import Qt, QRect, QSize, QEvent, pyqtSignal
from PyQt6.QtGui import QPainter, QBrush, QColor, QPen, QFont
from PyQt6.QtWidgets import QStyledItemDelegate, QStyle, QStyleOptionViewItem

class AdminDelegate(QStyledItemDelegate):
    editClicked = pyqtSignal(object)
    deleteClicked = pyqtSignal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.radius = 14
        self.pad = 16
        self.row_h = 188
        self.bg = QColor("#0f4d2a"); self.bg_hover = QColor("#165f35"); self.border = QColor("#0c3e22")
        self.title = QColor("#ffffff"); self.text = QColor("#d7e3dc"); self.meta = QColor("#bcd3c6"); self.link = QColor("#b7e1ff")
        self.chip_bg = QColor("#2a6b3b")
        self.icon_box = QColor("#eef3ef"); self.icon_border = QColor("#b9c9c0")
        self.icon_size = QSize(28, 24); self.icon_gap = 10
        self._pressed_role = None; self._pressed_row = -1

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        return QSize(option.rect.width(), self.row_h)

    def _layout(self, r: QRect) -> dict:
        card = r.adjusted(12, 8, -12, -8)
        content = card.adjusted(self.pad, self.pad, -self.pad, -self.pad)
        chip = QRect(content.left(), content.top(), 120, 22)
        draft = QRect(chip.right()+8, content.top(), 70, 22)

        delete_rect = QRect(content.right()-self.icon_size.width(), content.top(),
                            self.icon_size.width(), self.icon_size.height())
        edit_rect   = QRect(delete_rect.left()-self.icon_gap-self.icon_size.width(), content.top(),
                            self.icon_size.width(), self.icon_size.height())

        title = QRect(content.left(), chip.bottom()+10, content.width()-160, 28)
        blurb = QRect(content.left(), title.bottom()+8, content.width()-40, 44)
        url   = QRect(content.left(), blurb.bottom()+10, content.width()-40, 18)
        email = QRect(content.left(), url.bottom()+4,  content.width()-40, 18)
        return {"card":card,"content":content,"chip":chip,"draft":draft,"title":title,"blurb":blurb,"url":url,"email":email,"edit":edit_rect,"delete":delete_rect}

    def paint(self, p: QPainter, opt: QStyleOptionViewItem, idx) -> None:
        R = self._layout(opt.rect); p.save()
        hovered = bool(opt.state & QStyle.StateFlag.State_MouseOver)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setBrush(QBrush(self.bg_hover if hovered else self.bg)); p.setPen(QPen(self.border, 1))
        p.drawRoundedRect(R["card"], self.radius, self.radius)

        # category chip
        p.setBrush(QBrush(self.chip_bg)); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(R["chip"], 11, 11)
        f = p.font(); f.setPointSize(9); f.setBold(True); p.setFont(f); p.setPen(self.meta)
        p.drawText(R["chip"].adjusted(10,0,-8,0),
                Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextSingleLine,
                idx.data(Qt.ItemDataRole.UserRole+1) or "")

        # draft chip (DraftRole = +6)
        if idx.data(Qt.ItemDataRole.UserRole+6):
            p.setBrush(QBrush(QColor("#e9ecef"))); p.setPen(QPen(QColor("#9aa1a6"),1))
            p.drawRoundedRect(R["draft"], 11, 11)
            df = QFont(f); df.setBold(True); p.setFont(df); p.setPen(QColor("#6b737a"))
            p.drawText(R["draft"], Qt.AlignmentFlag.AlignCenter, "DRAFT")

        # title
        tf = QFont(f); tf.setPointSize(18); tf.setBold(True); p.setFont(tf); p.setPen(self.title)
        p.drawText(R["title"], Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextSingleLine,
                idx.data(Qt.ItemDataRole.UserRole+2) or "")

        # blurb
        bf = QFont(f); bf.setPointSize(10); p.setFont(bf); p.setPen(self.text)
        p.drawText(R["blurb"], int(Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignTop),
                idx.data(Qt.ItemDataRole.UserRole+3) or "")

        # URL + Contact
        p.setPen(self.meta); p.drawText(R["url"], Qt.TextFlag.TextSingleLine, "URL: ")
        uf = QFont(bf); uf.setUnderline(True); p.setFont(uf); p.setPen(self.link)
        p.drawText(R["url"].adjusted(38,0,0,0), Qt.TextFlag.TextSingleLine,
                idx.data(Qt.ItemDataRole.UserRole+4) or "")
        p.setPen(self.meta); nu = QFont(bf); nu.setUnderline(False); p.setFont(nu)
        p.drawText(R["email"], Qt.TextFlag.TextSingleLine, "Contact: ")
        eu = QFont(bf); eu.setUnderline(True); p.setFont(eu); p.setPen(self.link)
        p.drawText(R["email"].adjusted(70,0,0,0), Qt.TextFlag.TextSingleLine,
                idx.data(Qt.ItemDataRole.UserRole+5) or "")

        # action chips
        def chip(rect: QRect, glyph: str, fg: QColor):
            p.setBrush(QBrush(self.icon_box)); p.setPen(QPen(self.icon_border,1))
            p.drawRoundedRect(rect, 6, 6); p.setPen(fg)
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, glyph)
        chip(R["edit"],   "✎", QColor("#0f4d2a"))
        chip(R["delete"], "🗑", QColor("#b61f1f"))
        p.restore()

    def editorEvent(self, e, model, opt, idx):
        R = self._layout(opt.rect); pos = e.position().toPoint()
        hit_edit   = R["edit"].adjusted(-6, -6, 6, 6)
        hit_delete = R["delete"].adjusted(-6, -6, 6, 6)
        if e.type()==QEvent.Type.MouseButtonPress and e.button()==Qt.MouseButton.LeftButton:
            self._pressed_row = idx.row()
            if hit_edit.contains(pos):   self._pressed_role="edit";   return True
            if hit_delete.contains(pos): self._pressed_role="delete"; return True
            self._pressed_role=None; return False
        if e.type()==QEvent.Type.MouseButtonRelease and e.button()==Qt.MouseButton.LeftButton:
            if self._pressed_row==idx.row():
                if self._pressed_role=="edit" and hit_edit.contains(pos):
                    self.editClicked.emit(idx);  self._pressed_role=None; return True
                if self._pressed_role=="delete" and hit_delete.contains(pos):
                    self.deleteClicked.emit(idx); self._pressed_role=None; return True
            self._pressed_role=None; return False
        return False
