"""Build VTK display actors from the import worker's mesh format."""
import json
import struct
from typing import NamedTuple

import numpy as np
import vtk
from PyQt5.QtGui import QColor
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray

COLORS = ['#8093a4', '#d5a351', '#527d9d', '#4a967c', '#d7764f', '#c99766',
          '#c99766', '#c99766', '#c99766', '#bec6ce']


class PartView(NamedTuple):
    name: str
    actor: vtk.vtkActor
    color: QColor
    triangle_count: int


def read_scene(path):
    data = path.read_bytes()
    length, = struct.unpack_from('<I', data)
    rows = json.loads(data[4:4+length])
    result = []
    for n, row in enumerate(rows):
        def array(key, dtype):
            offset, count = row[key]
            return np.frombuffer(data, dtype=dtype, count=count, offset=4+length+offset)

        xyz = array('p', '<f4').reshape(-1, 3)
        tris = array('i', '<u4')
        if not len(tris) or len(tris) % 3 or tris.max() >= len(xyz) or not np.isfinite(xyz).all():
            raise ValueError('无效的显示网格')
        points = vtk.vtkPoints()
        points.SetData(numpy_to_vtk(xyz, deep=True))
        cells = vtk.vtkCellArray()
        offsets = np.arange(0, len(tris)+1, 3, dtype=np.int64)
        cells.SetData(numpy_to_vtkIdTypeArray(offsets, deep=True),
                      numpy_to_vtkIdTypeArray(tris.astype(np.int64), deep=True))
        poly = vtk.vtkPolyData()
        poly.SetPoints(points)
        poly.SetPolys(cells)
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputData(poly)
        normals.SetFeatureAngle(35)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(normals.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        color = QColor(COLORS[n % len(COLORS)])
        prop = actor.GetProperty()
        prop.SetColor(*color.getRgbF()[:3])
        prop.SetAmbient(.23)
        prop.SetSpecular(.15)
        result.append(PartView(row['name'], actor, color, len(tris)//3))
    if not result:
        raise ValueError('没有可显示的曲面')
    return result
