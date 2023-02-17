import numpy as np
from vispy.scene import ArcballCamera, PanZoomCamera

from napari._vispy.utils.quaternion import quaternion2euler


class VispyCamera:
    """Vipsy camera for both 2D and 3D rendering.

    Parameters
    ----------
    view : vispy.scene.widgets.viewbox.ViewBox
        Viewbox for current scene.
    camera : napari.components.Camera
        napari camera model.
    dims : napari.components.Dims
        napari dims model.
    """

    def __init__(self, view, camera, dims):
        self._view = view
        self._camera = camera
        self._dims = dims

        # Create 2D camera
        # aspect=None for non_isotropic zoom - Eitan
        if self._camera.unlock_isotropic:
            aspect = None
        else:
            aspect = 1
        self._2D_camera = PanZoomCamera(aspect=aspect)
        # flip y-axis to have correct alignment
        self._2D_camera.flip = (0, 1, 0)
        self._2D_camera.viewbox_key_event = viewbox_key_event

        # Create 3D camera
        self._3D_camera = ArcballCamera(fov=0)
        self._3D_camera.viewbox_key_event = viewbox_key_event

        self._dims.events.ndisplay.connect(
            self._on_ndisplay_change, position='first'
        )

        self._camera.events.center.connect(self._on_center_change)
        self._camera.events.zoom.connect(self._on_zoom_change)
        self._camera.events.angles.connect(self._on_angles_change)
        self._camera.events.perspective.connect(self._on_perspective_change)

        # added for changing camera aspect ratio and lock_isotropic - Eitan
        self._camera.events.unlock_isotropic.connect(self._on_unlock_isotropic_change)
        self._camera.events.aspect.connect(self._on_zoom_change)

        self._on_ndisplay_change()

    @property
    def angles(self):
        """3-tuple: Euler angles of camera in 3D viewing, in degrees.
        Note that angles might be different than the ones that might have generated the quaternion.
        """

        if self._view.camera == self._3D_camera:
            # Do conversion from quaternion representation to euler angles
            angles = quaternion2euler(
                self._view.camera._quaternion, degrees=True
            )
        else:
            angles = (0, 0, 90)
        return angles

    @angles.setter
    def angles(self, angles):
        if self.angles == tuple(angles):
            return

        # Only update angles if current camera is 3D camera
        if self._view.camera == self._3D_camera:
            # Create and set quaternion
            quat = self._view.camera._quaternion.create_from_euler_angles(
                *angles,
                degrees=True,
            )
            self._view.camera._quaternion = quat
            self._view.camera.view_changed()

    @property
    def center(self):
        """tuple: Center point of camera view for 2D or 3D viewing."""
        if self._view.camera == self._3D_camera:
            center = tuple(self._view.camera.center)
        else:
            # in 2D, we arbitrarily choose 0.0 as the center in z
            center = tuple(self._view.camera.center[:2]) + (0.0,)
        # switch from VisPy xyz ordering to NumPy prc ordering
        center = center[::-1]
        return center

    @center.setter
    def center(self, center):
        if self.center == tuple(center):
            return
        self._view.camera.center = center[::-1]
        self._view.camera.view_changed()

    @property
    def zoom(self):
        """float: Scale from canvas pixels to world pixels."""
        canvas_size = np.array(self._view.canvas.size)
        if self._view.camera == self._3D_camera:
            # For fov = 0.0 normalize scale factor by canvas size to get scale factor.
            # Note that the scaling is stored in the `_projection` property of the
            # camera which is updated in vispy here
            # https://github.com/vispy/vispy/blob/v0.6.5/vispy/scene/cameras/perspective.py#L301-L313
            scale = self._view.camera.scale_factor
        else:
            scale = np.array(
                [self._view.camera.rect.width, self._view.camera.rect.height]
            )
            scale[np.isclose(scale, 0)] = 1  # fix for #2875
        zoom = canvas_size[0] / scale[0] # Eitan: zoom_x
        return zoom

    @zoom.setter
    def zoom(self, zoom):
        if self.zoom == zoom:
            return
        scale = np.array(self._view.canvas.size) / zoom
        scale[1] = scale[1] / self._camera.aspect
        if self._view.camera == self._3D_camera:
            self._view.camera.scale_factor = np.min(scale)
        else:
            # Set view rectangle, as left, right, width, height
            corner = np.subtract(self._view.camera.center[:2], scale / 2)
            self._view.camera.rect = tuple(corner) + tuple(scale)

    @property
    def aspect(self):
        """float: Scale from canvas pixels to world pixels."""
        if not self._camera.unlock_isotropic:
            return 1

        canvas_size = np.array(self._view.canvas.size)
        scale = np.array([self._view.camera.rect.width, self._view.camera.rect.height])
        scale[np.isclose(scale, 0)] = 1  # fix for #2875
        zoom_x = canvas_size[0] / scale[0]
        zoom_y = canvas_size[1] / scale[1]
        return zoom_y / zoom_x

    @aspect.setter
    def aspect(self, aspect):
        if self.aspect == aspect:
            return
        scale = np.array(self._view.canvas.size) / [self.zoom, aspect * self.zoom]
        if self._view.camera == self._3D_camera:
            self._view.camera.scale_factor = np.min(scale)
        else:
            # Set view rectangle, as left, right, width, height
            corner = np.subtract(self._view.camera.center[:2], scale / 2)
            self._view.camera.rect = tuple(corner) + tuple(scale)

    @property
    def perspective(self):
        """Field of view of camera (only visible in 3D mode)."""
        return self._3D_camera.fov

    @perspective.setter
    def perspective(self, perspective):
        if self.perspective == perspective:
            return
        self._3D_camera.fov = perspective
        self._view.camera.view_changed()

    def _on_ndisplay_change(self):
        if self._dims.ndisplay == 3:
            self._view.camera = self._3D_camera
        else:
            self._view.camera = self._2D_camera
        self._on_center_change()
        self._on_zoom_change()
        self._on_angles_change()

    def _on_center_change(self):
        self.center = self._camera.center[-self._dims.ndisplay :]

    def _on_zoom_change(self):
        self.zoom = self._camera.zoom
        self.aspect = self._camera.aspect

    def _on_unlock_isotropic_change(self):
        if self._camera.unlock_isotropic:
            self._2D_camera.aspect = 1
        else:
            self._2D_camera.aspect = None

    def _on_perspective_change(self):
        self.perspective = self._camera.perspective

    def _on_angles_change(self):
        self.angles = self._camera.angles

    def on_draw(self, _event):
        """Called whenever the canvas is drawn.

        Update camera model angles, center, and zoom.
        """
        with self._camera.events.angles.blocker(self._on_angles_change):
            self._camera.angles = self.angles
        with self._camera.events.center.blocker(self._on_center_change):
            self._camera.center = self.center
        with self._camera.events.zoom.blocker(self._on_zoom_change):
            with self._camera.events.aspect.blocker(self._on_zoom_change):
                zoom_y = self._view.canvas.size[1] / self._2D_camera.rect.size[1]
                zoom_x = self._view.canvas.size[0] / self._2D_camera.rect.size[0]
                self._camera.aspect = zoom_y / zoom_x
                self._camera.zoom = zoom_x
                # debug prints:
                # print(f'zoom x, y: {zoom_x,zoom_y}')
                # print(f' data size: {self._2D_camera.rect.size}')
                # print(f'canvas size:{self._view.canvas.size}')
        with self._camera.events.perspective.blocker(
            self._on_perspective_change
        ):
            self._camera.perspective = self.perspective


def viewbox_key_event(event):
    """ViewBox key event handler.

    Parameters
    ----------
    event : vispy.util.event.Event
        The vispy event that triggered this method.
    """
    return
