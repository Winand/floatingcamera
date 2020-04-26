"""
https://www.pymadethis.com/article/webcam-photobooth-python-qt/

"""
from qtpy import QtMultimediaWidgets as qtmmw
from qtapp import QtForm, QtWidgets, Qt, QtCore
from camera import Cameras

import ctypes
class WINDOWPOS(ctypes.Structure):
    _fields_ = [
        ('hwnd', ctypes.wintypes.HWND),
        ('hwndInsertAfter', ctypes.wintypes.HWND),
        ('x', ctypes.c_int),
        ('y', ctypes.c_int),
        ('cx', ctypes.c_int),
        ('cy', ctypes.c_int),
        ('flags', ctypes.c_ulong)
    ]

WM_WINDOWPOSCHANGING = 0x46  # Sent to a window whose size, position, or place in the Z order is about to change


class Form1(QtWidgets.QDialog):
    _flags_ = Qt.FramelessWindowHint | Qt.Tool
    _ontop_ = True
    _layout_ = QtWidgets.QVBoxLayout

    def __init__(self):
        self.setTopmost(True)  # FIXME: qtapp bug, `_ontop_=True` may fail

        self.disp = self.app.desktop().availableGeometry(self)
        self.stickAt = 10
        self.cam = None

        self.setWindowOpacity(0.85)
        self.setSizeGripEnabled(True)  # allows to resize frameless window

        self.view = qtmmw.QCameraViewfinder(self)
        self.view.show()
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self.view)

        self.cams = Cameras(default_view=self.view)
        self.cams.error.connect(lambda err_str: self.alert(err_str))
        print("Camera list:")
        for i, cam in enumerate(self.cams):
            print(i+1, cam[0],
                  "(default)" if self.cams.default==cam[1] else "")

        self.cams.start_camera(self.cams.default)

        # res = self.cam.supportedViewfinderResolutions()
        # # print(res)
        # settings = qtmm.QCameraViewfinderSettings()
        # # settings.setResolution(res[-3])  # FIXME:
        # self.cam.setViewfinderSettings(settings)
        settings = self.cams.current.viewfinderSettings()
        print(settings.resolution())

        print(self.cams.supported_settings(self.cams.current)[1])

        self.setAttribute(Qt.WA_QuitOnClose)

        self.setup_menu()

    def setup_menu(self):
        "Fill context menu items"
        self.menu = QtWidgets.QMenu(self)

        action = QtWidgets.QWidgetAction(self.menu)
        container = QtWidgets.QWidget()
        QtWidgets.QHBoxLayout(container)
        container.layout().setContentsMargins(0, 2, 0, 2)
        container.layout().addWidget(QtWidgets.QLabel("Opacity:"))
        spnOpacity = QtWidgets.QDoubleSpinBox()
        spnOpacity.setMinimum(0.1)
        spnOpacity.setMaximum(1)
        spnOpacity.setSingleStep(0.05)
        spnOpacity.setValue(self.windowOpacity())
        spnOpacity.valueChanged.connect(lambda d: self.setWindowOpacity(d))
        container.layout().addWidget(spnOpacity)
        action.setDefaultWidget(container)
        self.menu.addAction(action)

        action = QtWidgets.QWidgetAction(self.menu)
        cmbCameras = QtWidgets.QComboBox()
        cmbCameras.addItems([i[0] for i in self.cams])
        cmbCameras.activated.connect(self.cams.start_camera)
        # spnOpacity.valueChanged.connect(lambda d: self.setWindowOpacity(d))
        action.setDefaultWidget(cmbCameras)
        self.menu.addAction(action)

        action = QtWidgets.QWidgetAction(self.menu)
        container = QtWidgets.QWidget()
        self.layout_cam_settings = QtWidgets.QHBoxLayout(container)
        container.layout().setContentsMargins(0, 2, 0, 2)
        action.setDefaultWidget(container)
        self.menu.addAction(action)
        self.update_camera_menu()

        self.menu.addSeparator()
        self.menu.addAction("Quit", self.close)

    def update_camera_menu(self):
        while self.layout_cam_settings.takeAt(0):
            pass  # clear layout

        res_list = self.cams.current.supportedViewfinderResolutions()
        cmb_res = QtWidgets.QComboBox()
        cmb_res.addItems(["%dx%d" % (i.width(), i.height()) for i in res_list])
        for i in enumerate(res_list):
            cmb_res.setItemData(*i)
        cmb_res.activated.connect(self.set_camera_res)
        self.layout_cam_settings.addWidget(cmb_res)

        fps_list = self.cams.current.supportedViewfinderFrameRateRanges()
        cmb_fps = QtWidgets.QComboBox()
        cmb_fps.addItems(["%.1f"%i.minimumFrameRate for i in fps_list])
        # for i in enumerate(fps_list):
        #     cmb_fps.setItemData(*i)
        self.layout_cam_settings.addWidget(cmb_fps)

        self.layout_cam_settings.addWidget(QtWidgets.QLabel("fps"))

        # fmt_list = self.cams.current.supportedViewfinderPixelFormats()
        cmb_fmt = QtWidgets.QComboBox()
        cmb_fmt.addItems(self.cams.supported_pixel_formats())
        # for i in enumerate(fmt_list):
        #     cmb_fmt.setItemData(*i)
        self.layout_cam_settings.addWidget(cmb_fmt)

    def set_camera_res(self, index):
        res = self.sender().itemData(index)
        settings = self.cams.current.viewfinderSettings()
        print(settings.minimumFrameRate())
        settings.setResolution(res)
        self.cams.current.setViewfinderSettings(settings)
        settings = self.cams.current.viewfinderSettings()
        print(settings.minimumFrameRate())

    def start_camera(self, cam_obj):
        """
        Starts camera from `self.cams` list.
        Unloads current camera.
        """
        if self.cam:
            self.cam.unload()
        self.cam = qtmm.QCamera(cam_obj)
        self.cam.setViewfinder(self.view)
        self.cam.setCaptureMode(qtmm.QCamera.CaptureStillImage)
        self.cam.error.connect(lambda: self.alert(self.cam.errorString()))
        self.cam.start()

    def get_supported_settings(self, cam):
        res_d = {}
        preferred = None
        for i in cam.supportedViewfinderSettings():
            res = i.resolution()
            w, h = res.width(), res.height()
            if (w, h) not in res_d:
                res_d[(w, h)] = {}
            fps = round(i.maximumFrameRate(), 1)
            if fps not in res_d[(w, h)]:
                res_d[(w, h)][fps] = []
            # if fps >= 30:
            #     print("%dx%d" % (w, h), fps, i.pixelFormat())
            px_fmt = self.px_fmts[i.pixelFormat()]
            res_d[(w, h)][fps].append(px_fmt)
            if not preferred:
                preferred = [(w, h), fps, px_fmt]
        return res_d, preferred
        # print(res_d)

        # sup = cam.supportedViewfinderSettings()
        # for i in sup:
        #     r = i.resolution()
        #     print("%dx%d" % (r.width(), r.height()),
        #           "%.1f FPS" % i.minimumFrameRate(), i.pixelFormat())

    def contextMenuEvent(self, event):
        self.menu.exec(event.globalPos())

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QtCore.QPoint(event.globalPos() - self.oldPos)
        x, y = self.x() + delta.x(), self.y() + delta.y()
        # print(x)
        # if abs(x - self.disp.left()) <= self.stickAt:
        #     x = self.disp.left()
        self.move(x, y)
        self.oldPos = event.globalPos()

    def mouseDoubleClickEvent(self, event):
        self.close()

    # def moveEvent(self, event):
    #     mon = self.app.desktop().availableGeometry(self)
    #     print(mon)

    def nativeEvent(self, eventType, message):
        message = ctypes.wintypes.MSG.from_address(message.__int__())
        if message.message == WM_WINDOWPOSCHANGING:
            pos = WINDOWPOS.from_address(message.lParam)
            if abs(pos.x - self.disp.left()) <= self.stickAt:
                pos.x = self.disp.left()
            elif abs(pos.x + pos.cx - self.disp.right()) <= self.stickAt:
                pos.x = self.disp.right() - pos.cx
            if abs(pos.y - self.disp.top()) <= self.stickAt:
                pos.y = self.disp.top()
            elif abs(pos.y + pos.cy - self.disp.bottom()) <= self.stickAt:
                pos.y = self.disp.bottom() - pos.cy
        return False, 0




QtForm(Form1, loop=1)


# import cv2
# cv2.namedWindow("preview")
# # vc = cv2.VideoCapture(0)
# # print(vc.isOpened())
# # rval, frame = vc.read()
# # cv2.imshow("preview", frame)
# # while rval:
# #     cv2.imshow("preview", frame)
# #     rval, frame = vc.read()
# #     key = cv2.waitKey(20)
# #     if key == 27: # exit on ESC
# #         break
# cv2.destroyWindow("preview")
