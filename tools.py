"""Register native toolbar extensions here."""
from pathlib import Path

from PyQt5.QtGui import QIcon


def install_tools(viewer, toolbar):
    icon = QIcon(str(Path(__file__).resolve().parent / 'assets' / 'box.svg'))
    wireframe = toolbar.addAction(icon, '线框')
    wireframe.setCheckable(True)
    wireframe.setToolTip('以三角网格线框显示部件')

    def apply_wireframe():
        for part in viewer.scene:
            prop = part.actor.GetProperty()
            if wireframe.isChecked():
                prop.SetRepresentationToWireframe()
            else:
                prop.SetRepresentationToSurface()

    def toggle_wireframe():
        apply_wireframe()
        viewer.win.Render()

    wireframe.toggled.connect(toggle_wireframe)
    viewer.scene_changed.connect(apply_wireframe)
