from ome_zarr.io import parse_url
from ome_zarr.reader import Reader
import napari

# url = "https://uk1s3.embassy.ebi.ac.uk/idr/zarr/v0.4/idr0062A/6001240.zarr"
url = r'C:\t\testzn'
# read the image data
store = parse_url(url, mode="r").store

reader = Reader(parse_url(url))
# nodes may include images, labels etc
nodes = list(reader())
# first node will be the image pixel data
image_node = nodes[0]

dask_data = image_node.data

# We can view this in napari
# NB: image axes are CZYX: split channels by C axis=0
viewer = napari.Viewer()
viewer.add_image([d for d in dask_data])#dask_data[0,:,:,:])
if __name__ == '__main__':
    napari.run()