'''
Copyright (C) 2015-2018 Team C All Rights Reserved

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

bl_info = {
    'name': 'RootMotion',
    'description': 'RootMotion for Game making',
    'author': 'CELPEC.COM,Vinson(epth on Github)',
    'email':'celpecgame@gmail.com',
    'version': (1, 0, 0, 0),
    'blender': (2, 80, 0),
    'location': 'View3D',
    'category': '3D View'}

from . import root_motion


def register():
    root_motion.register()


def unregister():
    root_motion.unregister()
