from PyQt6.QtCore import Qt, QRect, QSize, QEvent, QUrl, pyqtSignal
from PyQt6.QtGui import QPainter, QFont, QBrush, QColor, QPen, QDesktopServices
from PyQt6.QtWidgets import QStyledItemDelegate, QStyle, QStyleOptionViewItem, QWidget

class CardDelegate(QStyledItemDelegate):
    accessClicked = pyqtSignal(object)  # QModelIndex

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.radius = 18; self.hpad = 16; self.vpad = 14; self.vgap = 8
        self.card_height = 260
        self.card_bg = QColor("#0f4d2a"); self.card_bg_hover = QColor("#165f35"); self.card_border = QColor("#0c3e22")
        self.title_fg = QColor("#ffffff"); self.blurb_fg = QColor("#d7e3dc"); self.meta_fg = QColor("#bcd3c6")
        self.chip_bg = QColor("#2a6b3b"); self.btn_bg = QColor("#ffb000"); self.btn_text = QColor("#243000"); self.icon_fg = QColor("#d7e3dc")
        self.btn_size = QSize(160, 34); self.icon_size = QSize(18, 18)

    def _content_rect(self, rect: QRect) -> QRect:
        return rect.adjusted(self.hpad, self.vpad, -self.hpad, -self.vpad)

    def _ext_icon_rect(self, rect: QRect) -> QRect:
        m = 10
        return QRect(rect.right()-m-self.icon_size.width(), rect.top()+m, self.icon_size.width(), self.icon_size.height())

    def _button_rect(self, content: QRect) -> QRect:
        x = content.left() + (content.width()-self.btn_size.width())//2
        y = content.bottom() - self.btn_size.height()
        return QRect(x, y, self.btn_size.width(), self.btn_size.height())

    def _layout(self, rect: QRect) -> dict:
        content = self._content_rect(rect)
        chip_h, title_h, url_h, mail_h = 22, 24, 18, 18
        btn = self._button_rect(content)
        meta_w = content.width()
        mail = QRect(content.left(), btn.top()-self.vgap-mail_h, meta_w, mail_h)
        url  = QRect(content.left(), mail.top()-4-url_h, meta_w, url_h)
        chip = QRect(content.left(), content.top(), 110, chip_h)
        title= QRect(content.left(), chip.bottom()+self.vgap, meta_w, title_h)
        blurb_top = title.bottom()+self.vgap; blurb_bot = url.top()-self.vgap
        blurb_h = max(18, blurb_bot - blurb_top)
        blurb = QRect(content.left(), blurb_top, meta_w, blurb_h)
        return {"content":content,"chip":chip,"title":title,"blurb":blurb,"url":url,"mail":mail,"btn":btn,"ext":self._ext_icon_rect(rect)}

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        return QSize(option.rect.width(), self.card_height)

    def paint(self, p: QPainter, opt: QStyleOptionViewItem, idx) -> None:
        p.save()
        cat = idx.data(Qt.ItemDataRole.UserRole+1) or ""
        title = idx.data(Qt.ItemDataRole.UserRole+2) or ""
        blurb = idx.data(Qt.ItemDataRole.UserRole+3) or ""
        url = idx.data(Qt.ItemDataRole.UserRole+4) or ""
        email = idx.data(Qt.ItemDataRole.UserRole+5) or ""
        rect = opt.rect.adjusted(6,6,-6,-6)
        hovered = bool(opt.state & QStyle.StateFlag.State_MouseOver)

        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setBrush(QBrush(self.card_bg_hover if hovered else self.card_bg))
        p.setPen(QPen(self.card_border,1))
        p.drawRoundedRect(rect, self.radius, self.radius)
        R = self._layout(rect)

        p.setBrush(QBrush(self.chip_bg)); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(R["chip"], R["chip"].height()/2, R["chip"].height()/2)
        f = p.font(); f.setPointSize(9); f.setBold(True); p.setFont(f); p.setPen(self.meta_fg)
        p.drawText(R["chip"].adjusted(10,0,-8,0), Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextSingleLine, cat)

        p.setPen(QPen(self.icon_fg)); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(R["ext"],3,3); p.drawText(R["ext"], Qt.AlignmentFlag.AlignCenter, "↗")

        p.setPen(self.title_fg); f=QFont(f); f.setPointSize(13); f.setBold(True); p.setFont(f)
        p.drawText(R["title"], Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextSingleLine, title)

        p.setPen(self.blurb_fg); f=QFont(f); f.setPointSize(10); f.setBold(False); p.setFont(f)
        p.drawText(R["blurb"], int(Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignTop), blurb)

        p.setPen(self.meta_fg); f=QFont(f); f.setPointSize(10); p.setFont(f)
        p.drawText(R["url"],  Qt.TextFlag.TextSingleLine,  f"🔗  {url}")
        p.drawText(R["mail"], Qt.TextFlag.TextSingleLine, f"✉  {email}")

        p.setBrush(QBrush(self.btn_bg)); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(R["btn"],17,17); p.setPen(self.btn_text)
        p.drawText(R["btn"], Qt.AlignmentFlag.AlignCenter, "Access Page  ↗")
        p.restore()

    def editorEvent(self, e, model, opt, idx):
        if e.type()==QEvent.Type.MouseButtonRelease and e.button()==Qt.MouseButton.LeftButton:
            R = self._layout(opt.rect.adjusted(6,6,-6,-6))
            pos = e.position().toPoint()
            url = idx.data(Qt.ItemDataRole.UserRole+4) or ""
            email = idx.data(Qt.ItemDataRole.UserRole+5) or ""
            if R["btn"].contains(pos): self.accessClicked.emit(idx); return True
            if R["ext"].contains(pos) and url: QDesktopServices.openUrl(QUrl(url)); return True
            if R["url"].contains(pos) and url: QDesktopServices.openUrl(QUrl(url)); return True
            if R["mail"].contains(pos) and email: QDesktopServices.openUrl(QUrl(f"mailto:{email}")); return True
        return super().editorEvent(e, model, opt, idx)
