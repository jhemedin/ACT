"""
act.plotting.GeoDisplay
-----------------------

Stores the class for GeographicPlotDisplay.

"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .plot import Display
try:
    import cartopy.crs as ccrs
    from cartopy.io.img_tiles import Stamen
    import cartopy.feature as cfeature
    CARTOPY_AVAILABLE = True
except ImportError:
    CARTOPY_AVAILABLE = False


class GeographicPlotDisplay(Display):
    """
    A class for making geographic tracer plot of aircraft, ship or other moving
    platform plot..

    This is inherited from the :func:`act.plotting.Display`
    class and has therefore has the same attributes as that class.
    See :func:`act.plotting.Display`
    for more information. There are no additional attributes or parameters
    to this class.

    In order to create geographic plots, ACT needs the Cartopy package to be
    installed on your system. More information about
    Cartopy go here:https://scitools.org.uk/cartopy/docs/latest/ .

    Examples
    --------

    """
    def __init__(self, obj, ds_name=None, **kwargs):
        if not CARTOPY_AVAILABLE:
            raise ImportError("Cartopy needs to be installed on your "
                              "system to make geographic display plots.")
        super().__init__(obj, ds_name, **kwargs)
        if self.fig is None:
            self.fig = plt.figure(**kwargs)

    def geoplot(self, data_field=None, lat_field='lat',
                lon_field='lon', dsname=None, cbar_label=None, title=None,
                projection=ccrs.PlateCarree(), plot_buffer=0.08,
                stamen='terrain-background', tile=8, cartopy_feature=None,
                cmap='rainbow', text=None, gridlines=True, resolution='110m',
                size=6, color='gray', **kwargs):
        """
        Creates a latttude and longitude plot of a time series data set with
        data values indicated by color and described with a colorbar.
        Latitude values must be in degree north (-90 to 90) and
        longitude must be in degree east (-180 to 180).

        Parameters
        ----------
        data_field: str
            Name of data filed in object to plot.
        lat_field: str
            Name of latitude field in object to use.
        lon_field: str
            Name of longitude field in object to use.
        dsname: str or None
            The name of the datastream to plot. Set to None to make ACT
            attempt to automatically determine this.
        cbar_label: str
            Label to use with colorbar. If set to None will attempt
            to create label from long_name and units.
        title: str
            Plot title.
        projection: str
            Project to use on plot.
        plot_buffer: float
            Buffer to add around data on plot in lat and lon dimension
        stamen: str
            Dataset to use for background image. Set to None to not use
            background image.
        tile: int
            Tile zoom to use with background image. Higer number indicates
            more resolution. A value of 8 is typical for a normal sonde plot.
        cartopy_feature: list of str or str
            Cartopy feature to add to plot.
        cmap: str
            Color map to use for colorbar.
        text: dictionary
            Dictionary of {text:[lon,lat]} to add to plot. Can have more
            than one set of text to add.
        gridlines: boolean
            Use latitude and longitude gridlines.
        resolution: str
            Resolution of NaturalEarthFeatures to use. See cartopy
            documentation for details.
        size: int
            Size of the axes text labels.
        color: str
            Matplotlib color to used to color axes label text.
        **kwargs: keyword arguments
            Any other keyword arguments that will be passed
            into :func:`matplotlib.pyplot.scatter` when the figure
            is made. See the matplotlib
            documentation for further details on what keyword
            arguments are available.

        """
        # Get current plotting figure
        # del self.axes
        # if self.fig is None:
        #     self.fig = plt.figure()

        if dsname is None and len(self._arm.keys()) > 1:
            raise ValueError(("You must choose a datastream when there are 2 "
                              "or more datasets in the GeographicPlotDisplay "
                              "object."))
        elif dsname is None:
            dsname = list(self._arm.keys())[0]

        if data_field is None:
            raise ValueError(("You must enter the name of the data "
                              "to be plotted."))

        # Extract data from object
        try:
            lat = self._arm[dsname][lat_field].values
        except KeyError:
            raise ValueError(("You will need to provide the name of the "
                              "field if not '{}' to use for latitued "
                              "data.").format(lat_field))
        try:
            lon = self._arm[dsname][lon_field].values
        except KeyError:
            raise ValueError(("You will need to provide the name of the "
                              "field if not '{}' to use for longitude "
                              "data.").format(lon_field))

        # Set up metadata information for display on plot
        if cbar_label is None:
            try:
                cbar_label = (
                    self._arm[dsname][data_field].attrs['long_name'] +
                    ' (' + self._arm[dsname][data_field].attrs['units'] + ')')
            except KeyError:
                cbar_label = data_field

        lat_limits = [np.nanmin(lat), np.nanmax(lat)]
        lon_limits = [np.nanmin(lon), np.nanmax(lon)]
        box_size = np.max([np.abs(np.diff(lat_limits)),
                           np.abs(np.diff(lon_limits))])
        bx_buf = box_size * plot_buffer

        lat_center = np.sum(lat_limits) / 2.
        lon_center = np.sum(lon_limits) / 2.

        lat_limits = [lat_center - box_size / 2. - bx_buf,
                      lat_center + box_size / 2. + bx_buf]
        lon_limits = [lon_center - box_size / 2. - bx_buf,
                      lon_center + box_size / 2. + bx_buf]

        data = self._arm[dsname][data_field].values

        # Create base plot projection
        ax = plt.axes(projection=projection)
        plt.subplots_adjust(left=0.01, right=0.99, bottom=0.05, top=0.93)
        ax.set_extent([lon_limits[0], lon_limits[1], lat_limits[0],
                       lat_limits[1]], crs=ccrs.PlateCarree())

        if title is None:
            try:
                dim = list(self._arm[dsname][data_field].dims)
                ts = pd.to_datetime(str(self._arm[dsname][dim[0]].values[0]))
                date = ts.strftime('%Y-%m-%d')
                time_str = ts.strftime('%H:%M:%S')
                plt.title(' '.join([dsname, 'at', date, time_str]))
            except NameError:
                plt.title(dsname)
        else:
            plt.title(title)

        if stamen:
            tiler = Stamen(stamen)
            ax.add_image(tiler, tile)

        colorbar_map = None
        if cmap is not None:
            colorbar_map = plt.cm.get_cmap(cmap)
        sc = ax.scatter(lon, lat, c=data, cmap=colorbar_map, **kwargs)
        cbar = plt.colorbar(sc)
        cbar.ax.set_ylabel(cbar_label)
        if cartopy_feature is not None:
            if isinstance(cartopy_feature, str):
                cartopy_feature = [cartopy_feature]
            cartopy_feature = [ii.upper() for ii in cartopy_feature]
            if 'STATES' in cartopy_feature:
                ax.add_feature(cfeature.STATES.with_scale(resolution))
            if 'LAND' in cartopy_feature:
                ax.add_feature(cfeature.LAND.with_scale(resolution))
            if 'OCEAN' in cartopy_feature:
                ax.add_feature(cfeature.OCEAN.with_scale(resolution))
            if 'COASTLINE' in cartopy_feature:
                ax.add_feature(cfeature.COASTLINE.with_scale(resolution))
            if 'BORDERS' in cartopy_feature:
                ax.add_feature(cfeature.BORDERS.with_scale(resolution),
                               linestyle=':')
            if 'LAKES' in cartopy_feature:
                ax.add_feature(cfeature.LAKES.with_scale(resolution),
                               alpha=0.5)
            if 'RIVERS' in cartopy_feature:
                ax.add_feature(cfeature.RIVERS.with_scale(resolution))
        if text is not None:
            for label, location in text.items():
                ax.plot(location[0], location[1], marker='*', color='black')
                ax.text(location[0], location[1], label, color='black')

        if gridlines:
            gl = ax.gridlines(draw_labels=True,
                              linewidth=1, color=color, alpha=0.5,
                              linestyle=':')
            gl.xlabels_top = False
            gl.ylabels_left = True
            gl.xlabels_bottom = True
            gl.ylabels_right = False
            gl.xlabel_style = {'size': size, 'color': color}
            gl.ylabel_style = {'size': size, 'color': color}

        return ax