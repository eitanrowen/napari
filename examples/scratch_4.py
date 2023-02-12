from ome_zarr.io import parse_url
from ome_zarr.reader import Reader
import dask.array as da
import napari
from pyramid.pyramid import Pyramid
from typing import Optional, Tuple, List
from napari.utils.status_messages import status_format
import numpy as np

# url = "https://uk1s3.embassy.ebi.ac.uk/idr/zarr/v0.4/idr0062A/6001240.zarr"
url = r'C:\t\testzq'

p = Pyramid(url)
dask_data = p.reduced_pyramid()
dask_data[0]=da.broadcast_to(dask_data[0], (dask_data[1].shape[0], *dask_data[0].shape[1:]))
dask_data = dask_data[:3]
# We can view this in napari
# NB: image axes are CZYX: split channels by C axis=0
viewer = napari.Viewer()
viewer.add_image([d for d in dask_data])#dask_data[0,:,:,:])
def generate_layer_coords_status(position, value):
    if position is not None:
        full_coord = list(map(str, np.round(position).astype(int)))
        full_coord[3] = str(p.ind_to_datetime(value[0],position[3]))
        msg = f" [{' '.join(full_coord)}]"
    else:
        msg = ""

    if value is not None:
        if isinstance(value, tuple) and value != (None, None):
            # it's a multiscale -> value = (data_level, value)
            msg += f': {status_format(value[0])}'
            if value[1] is not None:
                msg += f', {status_format(value[1])}'
        else:
            # it's either a grayscale or rgb image (scalar or list)
            msg += f': {status_format(value)}'
    return msg


def get_status(
        position: Optional[Tuple[float, ...]] = None,
        *,
        view_direction: Optional[np.ndarray] = None,
        dims_displayed: Optional[List[int]] = None,
        world=False,
):
    """
    Status message information of the data at a coordinate position.

    Parameters
    ----------
    position : tuple of float
        Position in either data or world coordinates.
    view_direction : Optional[np.ndarray]
        A unit vector giving the direction of the ray in nD world coordinates.
        The default value is None.
    dims_displayed : Optional[List[int]]
        A list of the dimensions currently being displayed in the viewer.
        The default value is None.
    world : bool
        If True the position is taken to be in world coordinates
        and converted into data coordinates. False by default.

    Returns
    -------
    source_info : dict
        Dictionary containing a information that can be used as a status update.
    """
    if position is not None:
        value = viewer.layers[0].get_value(
            position,
            view_direction=view_direction,
            dims_displayed=dims_displayed,
            world=world,
        )
    else:
        value = None

    source_info = viewer.layers[0]._get_source_info()
    source_info['coordinates'] = generate_layer_coords_status(
        position[-viewer.layers[0].ndim:], value
    )
    return source_info

viewer.layers[0].get_status = get_status





if __name__ == '__main__':
    napari.run()