
from qtpy import QtMultimedia as qtmm
from qtapp import QtCore

class Cameras(QtCore.QObject):
    """
    Collection of cameras in the system
    `cameras` - list of cameras
    `default` - system default camera
    `current` - currently used camera
    """
    error = QtCore.Signal(qtmm.QCamera.Error)
    px_fmts = {4: "RGB24", 11: "BGR24", 18: "YUV422P", 30: "JPG"}

    def __init__(self, default_view=None):
        super().__init__()
        # bijection map
        self.px_fmts.update({v: k for k, v in self.px_fmts.items()})
        self.current = None
        self.default = qtmm.QCameraInfo.defaultCamera()
        self.cameras = qtmm.QCameraInfo.availableCameras()
        self.default_view = default_view

    def _find_by_name(self, name):
        for desc, obj in self:
            if name == desc:
                return obj
        return None

    def start_camera(self, camera_id, view=None):
        """
        Start camera specified in `camera_id` in a `view`.
        `camera_id` can be camera description, index or QCameraInfo object.
        If `view` is not specified `default_view` is used.
        Unloads `current` camera beforehand.
        """
        if isinstance(camera_id, str):
            cam_obj = self._find_by_name(camera_id)
        elif isinstance(camera_id, int):
            cam_obj = self.cameras[camera_id]
        else:
            cam_obj = camera_id
        view = view or self.default_view
        if self.current:
            self.current.unload()
        self.current = qtmm.QCamera(cam_obj)
        self.current.setViewfinder(view)
        self.current.setCaptureMode(qtmm.QCamera.CaptureStillImage)
        self.current.error.connect(self.error)
        self.current.start()

    def __iter__(self):
        for i in self.cameras:
            yield i.description(), i

    def supported_pixel_formats(self, camera=None):
        """
        Returns a list of supported viewfinder pixel formats.
        If `camera` is not specified `current` is used.
        """
        camera = camera or self.current
        return [self.px_fmts[i] for i in
                camera.supportedViewfinderPixelFormats()]

    def supported_settings(self, camera=None):
        """
        Returns a list of supported viewfinder settings:
        {(w, h): {fps: [fmt, ...], ...}, ...}
        If `camera` is not specified `current` is used.
        """
        res_d = {}
        preferred = None
        camera = camera or self.current
        for i in camera.supportedViewfinderSettings():
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
