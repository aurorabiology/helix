from PyQt5.QtWidgets import (
    QPlainTextEdit, QWidget, QHBoxLayout, QTextEdit, QListWidget, QCompleter, QAbstractItemView
)
from PyQt5.QtGui import (
    QColor, QPainter, QTextFormat, QTextCharFormat, QFont, QSyntaxHighlighter, QTextCursor, QFontMetrics
)
from PyQt5.QtCore import Qt, QRect, pyqtSignal, QRegExp, QPoint


class LineNumberArea(QWidget):
    """ Widget to display line numbers on the left gutter """
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)


class HelixLangSyntaxHighlighter(QSyntaxHighlighter):
    """ Syntax highlighter for HelixLang code """
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []
        self._init_highlighting_rules()

    def _init_highlighting_rules(self):
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            "fn", "let", "mut", "if", "else", "while", "for", "return",
            "struct", "enum", "impl", "trait", "use", "mod", "extern",
            "sim", "run", "break", "continue", "match"
        ]
        for word in keywords:
            pattern = QRegExp(r'\b' + word + r'\b')
            self.highlighting_rules.append((pattern, keyword_format))

        # Types
        type_format = QTextCharFormat()
        type_format.setForeground(QColor("#4EC9B0"))
        types = ["Int", "Float", "Bool", "String", "Vec", "Option"]
        for t in types:
            pattern = QRegExp(r'\b' + t + r'\b')
            self.highlighting_rules.append((pattern, type_format))

        # Single-line comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))
        self.highlighting_rules.append((QRegExp(r'//[^\n]*'), comment_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#D69D85"))
        self.highlighting_rules.append((QRegExp(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#B5CEA8"))
        self.highlighting_rules.append((QRegExp(r'\b\d+(\.\d+)?\b'), number_format))

        # Function names (basic)
        function_format = QTextCharFormat()
        function_format.setFontItalic(True)
        function_format.setForeground(QColor("#DCDCAA"))
        self.highlighting_rules.append((QRegExp(r'\b\w+(?=\()'), function_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            index = pattern.indexIn(text, 0)
            while index >= 0:
                length = pattern.matchedLength()
                self.setFormat(index, length, fmt)
                index = pattern.indexIn(text, index + length)
        self.setCurrentBlockState(0)

        # Handle multi-line strings or comments here if needed


class CodeEditor(QPlainTextEdit):
    codeChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFont(QFont("Consolas", 11))
        self.setTabStopDistance(4 * QFontMetrics(self.font()).width(' '))

        # Line number area
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

        # Syntax highlighting
        self.highlighter = HelixLangSyntaxHighlighter(self.document())

        # Autocomplete
        self.completer = None
        self._setup_autocomplete()

        # Error annotations: store line numbers and error messages
        self.error_lines = {}

        # Multi-caret & multi-selection would require deeper customization — this is basic

        # Connect text changed signal
        self.textChanged.connect(self.on_text_changed)

    def _setup_autocomplete(self):
        # List of keywords and functions for autocomplete (expandable)
        keywords = [
            "fn", "let", "mut", "if", "else", "while", "for", "return",
            "struct", "enum", "impl", "trait", "use", "mod", "extern",
            "sim", "run", "break", "continue", "match",
            "Int", "Float", "Bool", "String", "Vec", "Option"
        ]

        self.completer = QCompleter(keywords)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.activated.connect(self.insert_completion)

    def insert_completion(self, completion):
        if self.completer.widget() != self:
            return
        tc = self.textCursor()
        extra = len(completion) - len(self.completer.completionPrefix())
        tc.movePosition(QTextCursor.Left)
        tc.movePosition(QTextCursor.EndOfWord)
        tc.insertText(completion[-extra:])
        self.setTextCursor(tc)

    def textUnderCursor(self):
        tc = self.textCursor()
        tc.select(QTextCursor.WordUnderCursor)
        return tc.selectedText()

    def keyPressEvent(self, event):
        if self.completer and self.completer.popup().isVisible():
            # Let the completer handle navigation keys
            if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
                event.ignore()
                return

        super().keyPressEvent(event)

        ctrl_or_cmd = event.modifiers() & (Qt.ControlModifier | Qt.MetaModifier)
        if ctrl_or_cmd and event.key() == Qt.Key_Space:
            # Trigger autocomplete popup
            completion_prefix = self.textUnderCursor()
            if len(completion_prefix) >= 1:
                self.completer.setCompletionPrefix(completion_prefix)
                cr = self.cursorRect()
                cr.setWidth(self.completer.popup().sizeHintForColumn(0) +
                            self.completer.popup().verticalScrollBar().sizeHint().width())
                self.completer.complete(cr)

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        space = 3 + self.fontMetrics().width('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#2b2b2b"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        font = QFont("Consolas", 10)
        painter.setFont(font)
        painter.setPen(QColor("#8F908A"))

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                if block_number in self.error_lines:
                    painter.setPen(QColor("#FF5555"))  # Red for errors
                else:
                    painter.setPen(QColor("#8F908A"))
                painter.drawText(0, top, self.line_number_area.width() - 5, self.fontMetrics().height(),
                                 Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def highlight_current_line(self):
        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()

            line_color = QColor("#323232")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        # Highlight error lines as well
        for line_num in self.error_lines:
            block = self.document().findBlockByNumber(line_num)
            if block.isValid():
                selection = QTextEdit.ExtraSelection()
                selection.format.setUnderlineColor(QColor("#FF5555"))
                selection.format.setUnderlineStyle(QTextCharFormat.SpellCheckUnderline)
                selection.cursor = QTextCursor(block)
                selection.cursor.clearSelection()
                extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    def annotate_error(self, line_number, message):
        """ Add or update error annotation for a line """
        self.error_lines[line_number] = message
        self.highlight_current_line()

    def clear_error_annotations(self):
        self.error_lines.clear()
        self.highlight_current_line()

    def on_text_changed(self):
        self.codeChanged.emit()
        # Potentially hook to parser to update errors live
        # For example:
        # errors = HelixLangParser.parse(self.toPlainText())
        # self.clear_error_annotations()
        # for err in errors:
        #    self.annotate_error(err.line, err.message)


# Example usage and testing
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    editor = CodeEditor()
    editor.show()
    editor.setPlainText("// Start coding HelixLang here...\nfn main() {\n    let mut x = 10;\n}")

    sys.exit(app.exec_())
