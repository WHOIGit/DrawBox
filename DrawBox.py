import math
import json
import os

from PyQt5 import QtCore, QtGui, QtWidgets


class Window(QtWidgets.QMainWindow):
    def __init__(self, args):
        super().__init__()
        self.args = args

        self.files = args.files
        self.filei = 0

        self.rects = [[] for _ in range(len(args.files))]
        self.recti = -1

        # Try to restore saved state
        self.unmatched = {}
        if os.path.exists(args.output):
            namemap = \
                { os.path.basename(fn): i for i, fn in enumerate(self.files) }
            with open(args.output, 'r') as f:
                restored = json.load(f)
            for name, rects in restored.items():
                if name in namemap:
                    for x, y, w, h in rects:
                        rect = QtCore.QRect(x, y, w, h)
                        self.rects[namemap[name]].append(rect)
                else:
                    # Don't lose any boxes
                    self.unmatched[name] = rects

        self.canvas = Canvas()
        self.canvas.rectDrawn.connect(self.handle_rect_drawn)
        self.canvas.rectResized.connect(self.handle_rect_resized)
        self.canvas.rectSelected.connect(self.handle_rect_selected)
        self.setCentralWidget(self.canvas)

        self.load_image()

    def save_output(self):
        rectmap = {}
        for fn, rects in zip(self.files, self.rects):
            trects = []
            for r in rects:
                x, y = r.topLeft().x(), r.topLeft().y()
                w, h = r.width(), r.height()
                trects.append((x, y, w, h))
            rectmap[os.path.basename(fn)] = trects

        rectmap.update(self.unmatched)

        with open(args.output, 'w') as f:
            json.dump(rectmap, f)

    def handle_rect_drawn(self, rect):
        self.rects[self.filei].append(rect)
        self.recti = len(self.rects[self.filei]) - 1
        self.update_rects()
    
    def handle_rect_resized(self, recti, rect):
        self.rects[self.filei][self.recti] = rect
        self.update_rects()

    def handle_rect_selected(self, recti):
        self.recti = recti
        self.update_rects()

    def load_image(self):
        image = QtGui.QImage(self.files[self.filei])
        self.canvas.image = image
        
        self.recti = -1
        self.update_rects()

        self.resize(image.width(), image.height())
        self.canvas.update()
    
    def update_rects(self):
        self.canvas.rects = self.rects[self.filei]
        self.canvas.recti = self.recti
        self.canvas.update()
        self.save_output()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Q:
            QtCore.QCoreApplication.quit() 
        elif event.key() == QtCore.Qt.Key_Left:
            if self.filei > 0:
                self.filei -= 1
                self.load_image()
        elif event.key() == QtCore.Qt.Key_Right:
            if self.filei < len(self.files) - 1:
                self.filei += 1
                self.load_image()
        elif event.key() == QtCore.Qt.Key_Tab:
            if len(self.rects[self.filei]) > 0:
                self.recti = (self.recti + 1) % len(self.rects[self.filei])
                self.update_rects()
        elif event.key() == QtCore.Qt.Key_Backtab:
            if len(self.rects[self.filei]) > 0:
                self.recti = (self.recti - 1) % len(self.rects[self.filei])
                self.update_rects()
        elif event.key() == QtCore.Qt.Key_Backspace:
            if self.recti >= 0:
                del self.rects[self.filei][self.recti]
                self.recti -= 1
                self.update_rects()


class Canvas(QtWidgets.QWidget):
    rectDrawn = QtCore.pyqtSignal(QtCore.QRect)
    rectResized = QtCore.pyqtSignal(int, QtCore.QRect)
    rectSelected = QtCore.pyqtSignal(int)

    handleSize = 4

    def __init__(self):
        super().__init__()

        self.image = None
        self.rects = []
        self.recti = -1

        self.dragBegin = None
        self.dragEnd = None

        self.isDrawing = False

        self.isResizing = False

        self.show()

    def paintEvent(self, event):
        qp = QtGui.QPainter(self)
        if self.image:
            qp.drawImage(0, 0, self.image)
        
        # Draw any existing rectangles
        for i, rect in enumerate(self.rects):
            if i == self.recti:
                qp.setBrush(QtGui.QBrush(QtGui.QColor(100, 255, 255, 50)))
            else:
                qp.setBrush(QtGui.QBrush(QtGui.QColor(255, 255, 100, 50)))
            qp.drawRect(rect)
        
        # Draw grabbers for the current rectangle
        if self.recti >= 0:
            qp.setBrush(QtGui.QBrush(QtGui.QColor(255, 255, 255, 255)))
            qp.drawEllipse(self.rects[self.recti].topLeft(),
                           self.handleSize, self.handleSize)
            qp.drawEllipse(self.rects[self.recti].topRight(),
                           self.handleSize, self.handleSize)
            qp.drawEllipse(self.rects[self.recti].bottomLeft(),
                           self.handleSize, self.handleSize)
            qp.drawEllipse(self.rects[self.recti].bottomRight(),
                           self.handleSize, self.handleSize)

        # Draw the currently drawn rectangle
        if self.isDrawing:
            qp.setBrush(QtGui.QBrush(QtGui.QColor(100, 255, 255, 50)))
            qp.drawRect(QtCore.QRect(self.dragBegin, self.dragEnd))

    def mousePressEvent(self, event):
        self.dragBegin = event.pos()
        self.dragEnd = event.pos()

        if self.recti >= 0:
            dist = \
                lambda a, b: math.sqrt((a.x() - b.x())**2 + (a.y() - b.y())**2)
            corners = {
                'tl': self.rects[self.recti].topLeft(),
                'tr': self.rects[self.recti].topRight(),
                'bl': self.rects[self.recti].bottomLeft(),
                'br': self.rects[self.recti].bottomRight(),
            }
            opposites = {
                'tl': self.rects[self.recti].bottomRight(),
                'tr': self.rects[self.recti].bottomLeft(),
                'bl': self.rects[self.recti].topRight(),
                'br': self.rects[self.recti].topLeft(),
            }
            for abbr, corner in corners.items():
                if dist(corner, self.dragBegin) < self.handleSize:
                    self.isResizing = True
                    self.dragEnd = corner
                    self.dragBegin = opposites[abbr]
                    break

        self.isDrawing = not self.isResizing
        self.update()

    def mouseMoveEvent(self, event):
        self.dragEnd = event.pos()

        if self.isResizing:
            # Emit that we resized the rect
            rect = QtCore.QRect(self.dragBegin, self.dragEnd).normalized()
            self.rectResized.emit(self.recti, rect)

        self.update()

    def mouseReleaseEvent(self, event):
        self.dragEnd = event.pos()

        # We did not move very, interpret it as a click
        distance = (self.dragEnd - self.dragBegin).manhattanLength()
        if not self.isResizing and distance < 4:
            for i, rect in reversed(list(enumerate(self.rects))):
                if rect.contains(self.dragEnd):
                    self.rectSelected.emit(i)
                    break 
        elif self.isDrawing:
            # Emit that something was drawn
            rect = QtCore.QRect(self.dragBegin, self.dragEnd).normalized()
            self.rectDrawn.emit(rect)

        self.isDrawing = self.isResizing = False
        self.update()


if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', required=True)
    parser.add_argument('files', nargs='+')
    args = parser.parse_args()

    basenames = set()
    for f in args.files:
        basename = os.path.basename(f)
        if basename in basenames:
            raise argparse.ArgumentError('All files must have unique names')
        basenames.add(basename)

    app = QtWidgets.QApplication(sys.argv)
    window = Window(args)
    window.show()
    sys.exit(app.exec_())
