# Copyright (C) 2015-2021: The University of Edinburgh
#                 Authors: Craig Warren, Antonis Giannopoulos, and John Hartley
#
# This file is part of gprMax.
#
# gprMax is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# gprMax is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with gprMax.  If not, see <http://www.gnu.org/licenses/>.

import logging

import numpy as np

from ..fractals import FractalSurface
from ..utilities.utilities import round_value
from .cmds_geometry import UserObjectGeometry, rotate_2point_object

logger = logging.getLogger(__name__)


class AddSurfaceRoughness(UserObjectGeometry):
    """Allows you to add grass with roots to a :class:`gprMax.cmds_geometry.fractal_box.FractalBox` in the model.

    :param p1: The lower left (x,y,z) coordinates of a surface on a :class:`gprMax.cmds_geometry.fractal_box.FractalBox`
    :type p1: list, non-optional
    :param p2: The lower left (x,y,z) coordinates of a surface on a :class:`gprMax.cmds_geometry.fractal_box.FractalBox`
    :type p2: list, non-optional
    :param frac_dim: is the fractal dimension which, for an orthogonal parallelepiped, should take values between zero and three.
    :type frac_dim: float, non-optional
    :param weighting: Weightings in the first and second direction of the surface.
    :type weighting: list, non-optional
    :param limits: Define lower and upper limits for a range over which the roughness can vary.
    :type limits: list, non-optional
    :param fractal_box_id:  An identifier for the :class:`gprMax.cmds_geometry.fractal_box.FractalBox` that the roughness should be applied to
    :type fractal_box_id: list, non-optional
    :param seed:  Is an optional parameter which controls the seeding of the random number generator used to create the fractals.
    :type seed: int, optional
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.hash = '#add_surface_roughness'

    def rotate(self, axis, angle, origin=None):
        """Set parameters for rotation."""
        self.axis = axis
        self.angle = angle
        self.origin = origin
        self.dorotate = True

    def __dorotate(self):
        """Perform rotation."""
        pts = np.array([self.kwargs['p1'], self.kwargs['p2']])
        rot_pts = rotate_2point_object(pts, self.axis, self.angle, self.origin)
        self.kwargs['p1'] = tuple(rot_pts[0, :])
        self.kwargs['p2'] = tuple(rot_pts[1, :])
        
    def create(self, grid, uip):

        try:
            p1 = self.kwargs['p1']
            p2 = self.kwargs['p2']
            frac_dim = self.kwargs['frac_dim']
            weighting = np.array(self.kwargs['weighting'], dtype=np.float64)
            limits = np.array(self.kwargs['limits'])
            fractal_box_id = self.kwargs['fractal_box_id']
        except KeyError:
            logger.exception(self.__str__() + ' incorrect parameters')
            raise

        try:
            seed = self.kwargs['seed']
        except KeyError:
            seed = None

        if self.dorotate:
            self.__dorotate()

        # Get the correct fractal volume
        volumes = [volume for volume in grid.fractalvolumes if volume.ID == fractal_box_id]
        if volumes:
            volume = volumes[0]
        else:
            logger.exception(self.__str__() + f' cannot find FractalBox {fractal_box_id}')
            raise ValueError

        p1, p2 = uip.check_box_points(p1, p2, self.__str__())
        xs, ys, zs = p1
        xf, yf, zf = p2

        if frac_dim < 0:
            logger.exception(self.__str__() + ' requires a positive value for the fractal dimension')
            raise ValueError
        if weighting[0] < 0:
            logger.exception(self.__str__() + ' requires a positive value for the fractal weighting in the first direction of the surface')
            raise ValueError
        if weighting[1] < 0:
            logger.exception(self.__str__() + ' requires a positive value for the fractal weighting in the second direction of the surface')
            raise ValueError

        # Check for valid orientations
        if xs == xf:
            if ys == yf or zs == zf:
                logger.exception(self.__str__() + ' dimensions are not specified correctly')
                raise ValueError
            if xs != volume.xs and xs != volume.xf:
                logger.exception(self.__str__() + ' can only be used on the external surfaces of a fractal box')
                raise ValueError
            fractalrange = (round_value(limits[0] / grid.dx), round_value(limits[1] / grid.dx))
            # xminus surface
            if xs == volume.xs:
                if fractalrange[0] < 0 or fractalrange[1] > volume.xf:
                    logger.exception(self.__str__() + ' cannot apply fractal surface to fractal box as it would exceed either the upper coordinates of the fractal box or the domain in the x direction')
                    raise ValueError
                requestedsurface = 'xminus'
            # xplus surface
            elif xf == volume.xf:
                if fractalrange[0] < volume.xs or fractalrange[1] > grid.nx:
                    logger.exception(self.__str__() + ' cannot apply fractal surface to fractal box as it would exceed either the lower coordinates of the fractal box or the domain in the x direction')
                    raise ValueError
                requestedsurface = 'xplus'

        elif ys == yf:
            if xs == xf or zs == zf:
                logger.exception(self.__str__() + ' dimensions are not specified correctly')
                raise ValueError
            if ys != volume.ys and ys != volume.yf:
                logger.exception(self.__str__() + ' can only be used on the external surfaces of a fractal box')
                raise ValueError
            fractalrange = (round_value(limits[0] / grid.dy), round_value(limits[1] / grid.dy))
            # yminus surface
            if ys == volume.ys:
                if fractalrange[0] < 0 or fractalrange[1] > volume.yf:
                    logger.exception(self.__str__() + ' cannot apply fractal surface to fractal box as it would exceed either the upper coordinates of the fractal box or the domain in the y direction')
                    raise ValueError
                requestedsurface = 'yminus'
            # yplus surface
            elif yf == volume.yf:
                if fractalrange[0] < volume.ys or fractalrange[1] > grid.ny:
                    logger.exception(self.__str__() + ' cannot apply fractal surface to fractal box as it would exceed either the lower coordinates of the fractal box or the domain in the y direction')
                    raise ValueError
                requestedsurface = 'yplus'

        elif zs == zf:
            if xs == xf or ys == yf:
                logger.exception(self.__str__() + ' dimensions are not specified correctly')
                raise ValueError
            if zs != volume.zs and zs != volume.zf:
                logger.exception(self.__str__() + ' can only be used on the external surfaces of a fractal box')
                raise ValueError
            fractalrange = (round_value(limits[0] / grid.dz), round_value(limits[1] / grid.dz))
            # zminus surface
            if zs == volume.zs:
                if fractalrange[0] < 0 or fractalrange[1] > volume.zf:
                    logger.exception(self.__str__() + ' cannot apply fractal surface to fractal box as it would exceed either the upper coordinates of the fractal box or the domain in the x direction')
                    raise ValueError
                requestedsurface = 'zminus'
            # zplus surface
            elif zf == volume.zf:
                if fractalrange[0] < volume.zs or fractalrange[1] > grid.nz:
                    logger.exception(self.__str__() + ' cannot apply fractal surface to fractal box as it would exceed either the lower coordinates of the fractal box or the domain in the z direction')
                    raise ValueError
                requestedsurface = 'zplus'

        else:
            logger.exception(self.__str__() + ' dimensions are not specified correctly')
            raise ValueError

        surface = FractalSurface(xs, xf, ys, yf, zs, zf, frac_dim)
        surface.surfaceID = requestedsurface
        surface.fractalrange = fractalrange
        surface.operatingonID = volume.ID
        if seed is not None:
            surface.seed = int(seed)
        else:
            surface.seed = seed
        surface.weighting = weighting

        # List of existing surfaces IDs
        existingsurfaceIDs = [x.surfaceID for x in volume.fractalsurfaces]
        if surface.surfaceID in existingsurfaceIDs:
            logger.exception(self.__str__() + f' has already been used on the {surface.surfaceID} surface')
            raise ValueError

        surface.generate_fractal_surface(grid)
        volume.fractalsurfaces.append(surface)

        logger.info(self.grid_name(grid) + f'Fractal surface from {xs * grid.dx:g}m, {ys * grid.dy:g}m, {zs * grid.dz:g}m, to {xf * grid.dx:g}m, {yf * grid.dy:g}m, {zf * grid.dz:g}m with fractal dimension {surface.dimension:g}, fractal weightings {surface.weighting[0]:g}, {surface.weighting[1]:g}, fractal seeding {surface.seed}, and range {limits[0]:g}m to {limits[1]:g}m, added to {surface.operatingonID}.')
