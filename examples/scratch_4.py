from ome_zarr.io import parse_url
from ome_zarr.reader import Reader
import dask.array as da
import napari
from pyramid.pyramid import Pyramid
from typing import Optional, Tuple, List
from napari.utils.status_messages import status_format
import numpy as np
from napari_pz_pyramid._vispy.gridlines import PzGridLines
from napari_pz_pyramid._vispy.graph_axis import PzAxis
# url = "https://uk1s3.embassy.ebi.ac.uk/idr/zarr/v0.4/idr0062A/6001240.zarr"
url = r'C:\t\testzq'
#url = r'G:\Shared drives\PowerBI\pyramids\2023_span'

p = Pyramid(url)
dask_data = p.reduced_pyramid()
dask_data = dask_data[:3]
dask_data[0] = da.broadcast_to(dask_data[0], (dask_data[1].shape[0], *dask_data[0].shape[1:]))
# We can view this in napari
# NB: image axes are CZYX: split channels by C axis=0
viewer = napari.Viewer()
g = PzGridLines(viewer.window.qt_viewer.view)

viewer.add_image([d for d in dask_data])#dask_data[0,:,:,:])

pz_axes_x = PzAxis(pyramid=p, viewer=viewer, format_time=True,
                        orientation='bottom',
                        axis_label='Time',
                        axis_font_size=12,
                        axis_label_margin=30,
                        tick_label_margin=15)
pz_axes_y = PzAxis(pyramid=p, viewer=viewer, format_time=False,
                        orientation='left',
                        axis_label='Pos',
                        axis_font_size=12,
                        axis_label_margin=50,
                        tick_label_margin=5)
pz_axes_x.height_max = 80
pz_axes_y.width_max = 150
viewer.window.qt_viewer.grid.add_widget(pz_axes_x, row=1, col=1)
viewer.window.qt_viewer.grid.add_widget(pz_axes_y, row=0, col=0)

pz_axes_y.link_view(viewer.window.qt_viewer.view)
pz_axes_x.link_view(viewer.window.qt_viewer.view)

viewer.camera.events.zoom.connect(pz_axes_x.on_resize)
viewer.camera.events.center.connect(pz_axes_x.on_resize)

from napari_pz_pyramid.pz_utils import get_status
get_status_p = get_status(p, image=viewer.layers[0])
viewer.layers[0].get_status = get_status_p





if __name__ == '__main__':
    napari.run()
