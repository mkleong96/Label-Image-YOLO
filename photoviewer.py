from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class PhotoViewer(QGraphicsView):
    rectClicked = pyqtSignal(bool) #### Signal to send selected rectangle number to labelling

    def __init__(self, parent):
        super(PhotoViewer, self).__init__(parent)
        self._zoom = 0
        self.number = 0
        self._empty = True
        self._scene = QGraphicsScene(self)
        self._photo = QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setBackgroundBrush(QBrush(QColor(30, 30, 30)))
        self.setFrameShape(QFrame.NoFrame)
        #### Initialize needed dictionary and list
        PhotoViewer.index_dict = {}
        PhotoViewer.color_dictionary = {}
        self.rect_list = []
        PhotoViewer.selected_rectangle_list = []
        PhotoViewer.selected_rectangle_index_list = []
        
    def hasPhoto(self):
        return not self._empty

    #### Get selected rectangle name from labelling to set color when changed class
    def selected_rectangle(self, selected_rectangle):
        #### Assign variable to use in another class
        PhotoViewer.selected_rectangle_list = selected_rectangle

    #### Get selected rectangle label index from labelling to set color when changed class
    def selected_rectangle_index(self, label_index):
        #### Assign variable to use in another class
        PhotoViewer.selected_rectangle_index_list = label_index

    #### Get data from labelling to set rectangle color when starting
    def color_dict(self, color_dictionary):
        #### Assign variable to use in another class
        PhotoViewer.color_dictionary = color_dictionary

    #### Set size of image 
    def fitInView(self, scale=True):
        rect = QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasPhoto():
                unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.scale(factor, factor)
            self._zoom = 0

    #### Get pixmap from labelling to set image on graphics view
    def setPhoto(self, pixmap=None):
        self._zoom = 0
        self.pixmap = pixmap
        if pixmap and not pixmap.isNull(): #### If has photo
            self._empty = False
            self.setDragMode(QGraphicsView.ScrollHandDrag) #### Set image can be dragged
            self._photo.setPixmap(pixmap) #### Show image on graphics view
        else: #### If has no photo
            self._empty = True
            self.setDragMode(QGraphicsView.NoDrag)
            self._photo.setPixmap(QPixmap())
        self.fitInView()
 
    #### Get image width and height from labelling 
    def image_size(self, width, height):
        #### Assign variables to use in another class
        PhotoViewer.w = width
        PhotoViewer.h = height

    #### Set image can be zoomed and scrolled using wheel of mouse
    def wheelEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        if self.hasPhoto():
            #### If user holding 'Ctrl' and scrolling up, zoom in image
            if event.angleDelta().y() > 0 and modifiers == Qt.ControlModifier:
                factor = 1.25
                self._zoom += 1
                if self._zoom > 0:
                    self.scale(factor, factor)
                elif self._zoom == 0:
                    self.fitInView()
                else:
                    self._zoom = 0
            #### If user holding 'Ctrl' and scrolling down, zoom out image
            if event.angleDelta().y() < 0 and modifiers == Qt.ControlModifier:
                factor = 0.8
                self._zoom -= 1
                if self._zoom > 0:
                    self.scale(factor, factor)
                elif self._zoom == 0:
                    self.fitInView()
                else:
                    self._zoom = 0
            #### If user scrolling up, scroll up image
            if event.angleDelta().y() < 0:
                self.verticalScrollBar().setSliderPosition(int(self.verticalScrollBar().sliderPosition()*1.25))
            #### If user scrolling down, scroll down image
            if event.angleDelta().y() > 0:
                self.verticalScrollBar().setSliderPosition(int(self.verticalScrollBar().sliderPosition() * 0.8))

    #### Set drag mode
    def toggleDragMode(self):
        if self.dragMode() == QGraphicsView.ScrollHandDrag:
            self.setDragMode(QGraphicsView.NoDrag)
        elif not self._photo.pixmap().isNull():
            self.setDragMode(QGraphicsView.ScrollHandDrag)

    #### Send selected rectangle number when clicked on rectangle
    def mousePressEvent(self, event):
        super(PhotoViewer, self).mousePressEvent(event)
        #### Find the number of rectangle 
        for i in range(0, (len(self.rect_list))):
            if self.rect_list[i].isSelected():
                self.number = i
        self.rectClicked.emit(True) #### Send signal to labelling to connect function in labelling

    #### Draw rectangles on graphics view
    def add_rect(self, x, y, width, height): #### Get data from labelling to draw rectangles
        self._current_rect_item = GraphicsRectItem(x, y, width, height) #### Draw rectangles according to data 
        self._scene.addItem(self._current_rect_item) #### Add rectangles on graphics view
        self.rect_list.append(self._current_rect_item) #### Add rectangles name to list

    #### Delete rectangles from graphics view
    def delete_rec(self, item):
        self._scene.removeItem(item) #### Remove rectangles from graphics scene
        self.rect_list.clear() #### Clear rectangle list


#### Class to draw rectangles on graphics view
class GraphicsRectItem(QGraphicsRectItem):

    #### Initialize handles of rectangle
    handleTopLeft = 1
    handleTopMiddle = 2
    handleTopRight = 3
    handleMiddleLeft = 4
    handleMiddleRight = 5
    handleBottomLeft = 6
    handleBottomMiddle = 7
    handleBottomRight = 8

    #### Initialize handles size
    handleSize = + 20.0
    handleSpace = -10.0
    
    #### Initialize handles cursor
    handleCursors = {
        handleTopLeft: Qt.SizeFDiagCursor,
        handleTopMiddle: Qt.SizeVerCursor,
        handleTopRight: Qt.SizeBDiagCursor,
        handleMiddleLeft: Qt.SizeHorCursor,
        handleMiddleRight: Qt.SizeHorCursor,
        handleBottomLeft: Qt.SizeBDiagCursor,
        handleBottomMiddle: Qt.SizeVerCursor,
        handleBottomRight: Qt.SizeFDiagCursor,
    }

    def __init__(self, *args):
        """
        Initialize the shape.
        """
        super().__init__(*args)
        self.handles = {}
        self.handleSelected = None
        self.mousePressPos = None
        self.mousePressRect = None
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True) #### Set rectangle movable
        self.setFlag(QGraphicsItem.ItemIsSelectable, True) #### Set rectangle selectable
        self.setFlag(QGraphicsItem.ItemIsFocusable, True) #### Set rectangle focusable
        self.updateHandlesPos()

    def handleAt(self, point):
        """
        Returns the resize handle below the given point.
        """
        for k, v, in self.handles.items():
            if v.contains(point):
                return k
        return None

    #### When cursor move to handle of rectangle, change cursor pattern
    def hoverMoveEvent(self, moveEvent):
        """
        Executed when the mouse moves over the shape (NOT PRESSED).
        """
        super().hoverMoveEvent(moveEvent)
        handle = self.handleAt(moveEvent.pos())
        cursor = Qt.ArrowCursor if handle is None else self.handleCursors[handle]
        self.setCursor(cursor)

    #### When cursor move from handle of rectangle, change cursor pattern
    def hoverLeaveEvent(self, moveEvent):
        """
        Executed when the mouse leaves the shape (NOT PRESSED).
        """
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(moveEvent)

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the item.
        """
        self.handleSelected = self.handleAt(mouseEvent.pos())
        if self.handleSelected:
            self.mousePressPos = mouseEvent.pos()
            self.mousePressRect = self.boundingRect()
        super().mousePressEvent(mouseEvent)

    #### Maintain rectangle only can be moved within image
    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse is being moved over the item while being pressed.
        """
        if self.handleSelected is not None:
            self.interactiveResize(mouseEvent.pos())
        else:
            super().mouseMoveEvent(mouseEvent)
            #### Get rectangle geometry to check
            if self.sceneBoundingRect().x() + 10 < 0: #### Set cannot move out of left
                self.setPos(self.pos().x() - self.sceneBoundingRect().x() - 10, self.sceneBoundingRect().y() + (self.pos().y() - self.sceneBoundingRect().y()))
            if self.sceneBoundingRect().y() + 10 < 0: #### Set cannot move out of top
                self.setPos(self.sceneBoundingRect().x() + (self.pos().x() - self.sceneBoundingRect().x()), self.pos().y() - self.sceneBoundingRect().y() - 10)
            if self.sceneBoundingRect().bottomRight().x() - 10 > PhotoViewer.w: #### Set cannot move out of right
                self.setPos(PhotoViewer.w - self.sceneBoundingRect().width() + (self.pos().x() - self.sceneBoundingRect().x()) + 10, self.sceneBoundingRect().y() + (self.pos().y() - self.sceneBoundingRect().y()))
            if self.sceneBoundingRect().bottomRight().y() - 10 > PhotoViewer.h: #### Set cannot move out of bottom
                self.setPos(self.sceneBoundingRect().x() + (self.pos().x() - self.sceneBoundingRect().x()), PhotoViewer.h - self.sceneBoundingRect().height() + (self.pos().y() - self.sceneBoundingRect().y())+10)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the item.
        """
        super().mouseReleaseEvent(mouseEvent)
        self.handleSelected = None
        self.mousePressPos = None
        self.mousePressRect = None
        self.update()

    def boundingRect(self):
        """
        Returns the bounding rect of the shape (including the resize handles).
        """
        o = self.handleSize + self.handleSpace
        return self.rect().adjusted(-o, -o, o, o)

    def updateHandlesPos(self):
        """
        Update current resize handles according to the shape size and position.
        """
        s = self.handleSize
        b = self.boundingRect()
        self.handles[self.handleTopLeft] = QRectF(b.left(), b.top(), s, s)
        self.handles[self.handleTopMiddle] = QRectF(b.center().x() - s / 2, b.top(), s, s)
        self.handles[self.handleTopRight] = QRectF(b.right() - s, b.top(), s, s)
        self.handles[self.handleMiddleLeft] = QRectF(b.left(), b.center().y() - s / 2, s, s)
        self.handles[self.handleMiddleRight] = QRectF(b.right() - s, b.center().y() - s / 2, s, s)
        self.handles[self.handleBottomLeft] = QRectF(b.left(), b.bottom() - s, s, s)
        self.handles[self.handleBottomMiddle] = QRectF(b.center().x() - s / 2, b.bottom() - s, s, s)
        self.handles[self.handleBottomRight] = QRectF(b.right() - s, b.bottom() - s, s, s)

    def interactiveResize(self, mousePos):
        """
        Perform shape interactive resize.
        """
        offset = self.handleSize + self.handleSpace
        boundingRect = self.boundingRect()
        rect = self.rect()
        diff = QPointF(0, 0)

        self.prepareGeometryChange()

        #### Set can only resize within image
        #### Top left handle
        if self.handleSelected == self.handleTopLeft:
            #### Deselect handle if resize out of image
            if self.sceneBoundingRect().topLeft().x() < -10 or self.sceneBoundingRect().topLeft().y() < -10:
                self.handleSelected = None

            fromX = self.mousePressRect.left()
            fromY = self.mousePressRect.top()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setLeft(toX)
            boundingRect.setTop(toY)
            rect.setLeft(boundingRect.left() + offset)
            rect.setTop(boundingRect.top() + offset)
            self.setRect(rect)

        #### Top middle handle
        elif self.handleSelected == self.handleTopMiddle:
            #### Deselect handle if resize out of image
            if self.sceneBoundingRect().top() < -10:
                self.handleSelected = None

            fromY = self.mousePressRect.top()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setY(toY - fromY)
            boundingRect.setTop(toY)
            rect.setTop(boundingRect.top() + offset)
            self.setRect(rect)

        #### Top right handle
        elif self.handleSelected == self.handleTopRight:
            #### Deselect handle if resize out of image
            if self.sceneBoundingRect().topRight().x() > PhotoViewer.w + 10 or self.sceneBoundingRect().y() < -10:
                self.handleSelected = None

            fromX = self.mousePressRect.right()
            fromY = self.mousePressRect.top()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setRight(toX)
            boundingRect.setTop(toY)
            rect.setRight(boundingRect.right() - offset)
            rect.setTop(boundingRect.top() + offset)
            self.setRect(rect)

        #### Middle left handle
        elif self.handleSelected == self.handleMiddleLeft:
            #### Deselect handle if resize out of image
            if self.sceneBoundingRect().left() < -10:
                self.handleSelected = None

            fromX = self.mousePressRect.left()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            diff.setX(toX - fromX)
            boundingRect.setLeft(toX)
            rect.setLeft(boundingRect.left() + offset)
            self.setRect(rect)

        #### Middle right handle
        elif self.handleSelected == self.handleMiddleRight:
            #### Deselect handle if resize out of image
            if self.sceneBoundingRect().right() > PhotoViewer.w + 10:
                self.handleSelected = None

            fromX = self.mousePressRect.right()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            diff.setX(toX - fromX)
            boundingRect.setRight(toX)
            rect.setRight(boundingRect.right() - offset)
            self.setRect(rect)

        #### Bottom left handle
        elif self.handleSelected == self.handleBottomLeft:
            #### Deselect handle if resize out of image
            if self.sceneBoundingRect().bottomLeft().x() < -10 or self.sceneBoundingRect().bottomLeft().y() > PhotoViewer.h + 10:
                self.handleSelected = None

            fromX = self.mousePressRect.left()
            fromY = self.mousePressRect.bottom()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setLeft(toX)
            boundingRect.setBottom(toY)
            rect.setLeft(boundingRect.left() + offset)
            rect.setBottom(boundingRect.bottom() - offset)
            self.setRect(rect)

        #### Botton middle handle
        elif self.handleSelected == self.handleBottomMiddle:
            #### Deselect handle if resize out of image
            if self.sceneBoundingRect().bottom() > PhotoViewer.h + 10:
                self.handleSelected = None

            fromY = self.mousePressRect.bottom()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setY(toY - fromY)
            boundingRect.setBottom(toY)
            rect.setBottom(boundingRect.bottom() - offset)
            self.setRect(rect)

        #### Bottom right handle
        elif self.handleSelected == self.handleBottomRight:
            #### Deselect handle if resize out of image
            if self.sceneBoundingRect().bottomRight().x() > PhotoViewer.w + 10 or self.sceneBoundingRect().bottomRight().y() > PhotoViewer.h + 10:
                self.handleSelected = None

            fromX = self.mousePressRect.right()
            fromY = self.mousePressRect.bottom()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setRight(toX)
            boundingRect.setBottom(toY)
            rect.setRight(boundingRect.right() - offset)
            rect.setBottom(boundingRect.bottom() - offset)
            self.setRect(rect)

        self.updateHandlesPos()

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        """
        path = QPainterPath()
        path.addRect(self.rect())
        if self.isSelected():
            for shape in self.handles.values():
                path.addEllipse(shape)
        return path

    #### Fill up color of rectangle
    def paint(self, painter, option, widget=None):
        """
        Paint the node in the graphic view.
        """
        #### Color list
        CLASS_COLORS = [QColor(52, 152, 219, 200), QColor(243, 156, 18, 200), QColor(0, 255, 0, 200),
                        QColor(175, 122, 197, 200), QColor(46, 204, 113, 200), QColor(255, 0, 0, 200),
                        QColor(103, 186, 190, 200), QColor(160, 160, 160, 200), QColor(255, 255, 0, 200), 
                        QColor(0, 0, 255, 200), QColor(137, 34, 244, 200), QColor(100, 100, 100, 200), 
                        QColor(109, 122, 19, 200), QColor(239, 136, 233, 200), QColor(4, 211, 151, 200),
                        QColor(111, 140, 152, 200), QColor(59, 189, 197, 200), QColor(137, 74, 55, 200),
                        QColor(63, 185, 159, 200), QColor(11, 122, 115, 200)]
        
        #### Set white color when creating new rectangle
        painter.setBrush(QBrush(QColor(255, 255, 255, 0))) #### Rectangle color
        painter.setPen(QPen(QColor(255, 255, 255, 150), 5.0, Qt.SolidLine)) #### Rectangle boundary color
        painter.drawRect(self.rect())

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(255, 255, 255, 150))) #### Handle color
        painter.setPen(QPen(QColor(255, 255, 255, 150), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)) #### Handle boundary color
        for handle, rect in self.handles.items():
            if self.handleSelected is None or handle == self.handleSelected:
                painter.drawEllipse(rect)

        #### Change rectangle color when it is selected
        if self.isSelected():
            painter.setBrush(QBrush(QColor(255, 255, 255, 50)))
            painter.drawRect(self.rect())

        #### Change rectangle color according to classes when starting labelling program
        for x in range(len(PhotoViewer.color_dictionary)):
            for y in range(len(PhotoViewer.color_dictionary[f'{x}'])):
                if self == PhotoViewer.color_dictionary[f'{x}'][y]:
                    #### Set transparent to rectangle and change only boundary color
                    painter.setBrush(QBrush(QColor(255, 255, 255, 0)))
                    painter.setPen(QPen(QColor(CLASS_COLORS[x]), 5.0, Qt.SolidLine))
                    painter.drawRect(self.rect())
                    painter.setRenderHint(QPainter.Antialiasing)
                    #### Change handle color
                    painter.setBrush(QBrush(QColor(CLASS_COLORS[x])))
                    painter.setPen(QPen(QColor(CLASS_COLORS[x]), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                    for handle, rect in self.handles.items():
                        if self.handleSelected is None or handle == self.handleSelected:
                            painter.drawEllipse(rect)

        #### Change rectangle boundary color when changing classes
        if PhotoViewer.selected_rectangle_index_list != [] and PhotoViewer.selected_rectangle_list != []:
            for h in range(len(PhotoViewer.selected_rectangle_list)):
                for i in range(len(PhotoViewer.color_dictionary)):
                    if PhotoViewer.selected_rectangle_index_list[h] == i:
                        if self == PhotoViewer.selected_rectangle_list[h]:
                            #### Set to transparent before changing color
                            #### change color according to selected classes
                            painter.setBrush(QBrush(QColor(255, 255, 255, 0)))
                            painter.setPen(QPen(QColor(255, 255, 255, 255), 5.0, Qt.SolidLine))
                            painter.setPen(QPen(QColor(CLASS_COLORS[i]), 5.0, Qt.SolidLine))
                            painter.drawRect(self.rect())
                            painter.setRenderHint(QPainter.Antialiasing)
                            painter.setBrush(QBrush(QColor(CLASS_COLORS[i])))
                            painter.setPen(QPen(QColor(CLASS_COLORS[i]), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                            for handle, rect in self.handles.items():
                                if self.handleSelected is None or handle == self.handleSelected:
                                    painter.drawEllipse(rect)
