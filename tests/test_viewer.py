import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace

import vtk
from PyQt5 import QtCore, QtWidgets

from scene import read_scene
from tools import install_tools

ROOT = Path(__file__).resolve().parents[1]


class ImportTest(unittest.TestCase):
    def test_step_round_trip_preserves_bounds(self):
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory) / 'sample box.stp'
            mesh = model.with_suffix('.mesh')
            generate = ('import sys; import convert; '
                        'convert.Part.makeBox(10,20,30).exportStep(sys.argv[1])')
            subprocess.run([sys.executable, '-c', generate, str(model)], cwd=ROOT,
                           capture_output=True, check=True, timeout=45)
            subprocess.run([sys.executable, ROOT / 'import_file.py', model, mesh],
                           check=True, timeout=45)
            part, = read_scene(mesh)
            self.assertEqual(part.actor.GetBounds(), (0, 10, 0, 20, 0, 30))


class ToolHost(QtCore.QObject):
    scene_changed = QtCore.pyqtSignal()


class ToolsTest(unittest.TestCase):
    def test_wireframe_persists_across_model_change(self):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        toolbar = QtWidgets.QToolBar()
        host = ToolHost()
        host.scene = [SimpleNamespace(actor=vtk.vtkActor())]
        host.win = SimpleNamespace(Render=lambda: None)
        install_tools(host, toolbar)
        action, = [a for a in toolbar.actions() if a.text() == '线框']
        action.trigger()
        self.assertEqual(host.scene[0].actor.GetProperty().GetRepresentationAsString(), 'Wireframe')
        host.scene = [SimpleNamespace(actor=vtk.vtkActor())]
        host.scene_changed.emit()
        prop = host.scene[0].actor.GetProperty()
        self.assertEqual(prop.GetRepresentationAsString(), 'Wireframe')
        action.trigger()
        self.assertEqual(prop.GetRepresentationAsString(), 'Surface')
