#!/usr/bin/python3
import gc
import sys
import tempfile
from pathlib import Path

import vtk
from scene import read_scene
from tools import install_tools
from PyQt5 import QtCore as C, QtGui as G, QtWidgets as W
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / 'assets'
APP = 'STEP / STL 模型查看器'
MODEL_SUFFIXES = {'.step', '.stp', '.stl'}
VIEWS = {'等轴测': ((1, 1.45, .95), (0, 0, 1)), '正视': ((0, -1, 0), (0, 0, 1)),
         '俯视': ((0, 0, 1), (0, 1, 0)), '右视': ((1, 0, 0), (0, 0, 1))}


def icon(name):
    return G.QIcon(str(ASSETS / (name + '.svg')))


class Viewer(W.QMainWindow):
    scene_changed = C.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP); self.setWindowIcon(icon('app')); self.resize(1220, 790)
        self.setAcceptDrops(True)
        self.scene = []; self.proc = None; self.tmp = None; self.file = None
        self.settings = C.QSettings('LocalCAD', 'StepViewer')
        bar = self.addToolBar('模型工具'); bar.setMovable(False); bar.setIconSize(C.QSize(20, 20))
        bar.setToolButtonStyle(C.Qt.ToolButtonTextBesideIcon)
        self.open_action = bar.addAction(icon('folder-open'), '打开模型', self.browse)
        self.open_action.setShortcut(G.QKeySequence.Open); bar.addSeparator()
        self.fit_action = bar.addAction(icon('focus'), '适合窗口', self.fit); self.fit_action.setShortcut('F')
        bar.addSeparator(); bar.addAction(icon('axis-3d'), '视角').setEnabled(False)
        self.views = W.QComboBox(); self.views.addItems(VIEWS); self.views.activated[str].connect(self.orient)
        bar.addWidget(self.views); bar.addSeparator()
        install_tools(self, bar)
        self.cancel_action = bar.addAction('取消导入', self.cancel); self.cancel_action.setVisible(False)
        split = W.QSplitter(); self.setCentralWidget(split)
        panel = W.QWidget(); layout = W.QVBoxLayout(panel); layout.setContentsMargins(14, 19, 14, 12)
        title = W.QLabel('模型结构'); title.setStyleSheet('font-size:16px;font-weight:600'); layout.addWidget(title)
        self.label = W.QLabel('未打开模型'); self.label.setWordWrap(True); self.label.setStyleSheet('color:#566876'); layout.addWidget(self.label)
        self.parts = W.QListWidget(); self.parts.setAlternatingRowColors(True); layout.addWidget(self.parts, 1)
        self.parts.itemChanged.connect(self.toggle)
        self.parts.setContextMenuPolicy(C.Qt.CustomContextMenu); self.parts.customContextMenuRequested.connect(self.part_menu)
        self.all_btn = W.QPushButton(icon('eye'), '显示全部'); self.all_btn.clicked.connect(lambda: self.show_parts(None)); layout.addWidget(self.all_btn)
        split.addWidget(panel); self.canvas = QVTKRenderWindowInteractor(split); split.addWidget(self.canvas)
        split.setStretchFactor(1, 1); split.setSizes([250, 970]); self.canvas.setFocusPolicy(C.Qt.StrongFocus)
        self.r = vtk.vtkRenderer(); self.r.SetBackground(.91, .93, .94)
        self.win = self.canvas.GetRenderWindow(); self.win.SetMultiSamples(4); self.win.AddRenderer(self.r)
        self.ia = self.win.GetInteractor(); self.style = vtk.vtkInteractorStyleTrackballCamera(); self.ia.SetInteractorStyle(self.style)
        self.r.GetActiveCamera().ParallelProjectionOn()
        self.axes = vtk.vtkOrientationMarkerWidget(); self.axes.SetOrientationMarker(vtk.vtkAxesActor()); self.axes.SetInteractor(self.ia)
        self.axes.SetViewport(0, 0, .16, .16); self.axes.SetEnabled(1); self.axes.InteractiveOff()
        self.count = W.QLabel(); self.statusBar().addPermanentWidget(self.count); self.statusBar().showMessage('就绪')
        self.setStyleSheet('QToolBar{background:#fafbfc;padding:6px;spacing:5px;border-bottom:1px solid #ced6da}'
                           'QListWidget{border:1px solid #d5dce0;alternate-background-color:#f5f7f8}'
                           'QListWidget::item{padding:5px 1px} QStatusBar{color:#415461}')

    def browse(self):
        path, _ = W.QFileDialog.getOpenFileName(self, '打开模型', self.settings.value('directory', str(Path.home())),
            '三维模型 (*.[sS][tT][eE][pP] *.[sS][tT][pP] *.[sS][tT][lL]);;'
            'STL 网格 (*.[sS][tT][lL]);;STEP 模型 (*.[sS][tT][eE][pP] *.[sS][tT][pP]);;所有文件 (*)')
        if path: self.open_file(Path(path))

    def open_file(self, path):
        path = Path(path).absolute()
        if path.suffix.lower() not in MODEL_SUFFIXES or not path.is_file():
            self.statusBar().showMessage('无法打开：请选择存在的 STEP、STP 或 STL 文件'); return
        self.cancel(); self.tmp = tempfile.TemporaryDirectory(prefix='step-viewer-')
        mesh = Path(self.tmp.name) / 'display.mesh'; p = C.QProcess(self); self.proc = p
        self.cancel_action.setVisible(True); self.statusBar().showMessage('正在读取：' + path.name)
        p.setProcessChannelMode(C.QProcess.MergedChannels)
        p.finished.connect(lambda code, status: self.finished(p, code, mesh, path))
        p.errorOccurred.connect(lambda err: self.finished(p, -1, mesh, path) if err == C.QProcess.FailedToStart else None)
        p.start(sys.executable, [str(ROOT / 'import_file.py'), str(path), str(mesh)])

    def finished(self, process, code, mesh, path):
        if self.proc is not process: return
        try:
            output = bytes(process.readAllStandardOutput()).decode(errors='replace')
            if code != 0: raise ValueError('文件损坏、格式不受支持，或导入器未能读取几何')
            scene = read_scene(mesh)
            self.apply_scene(scene, path.name); self.file = path
            self.settings.setValue('directory', str(path.parent))
            msg = '已打开：' + path.name
            if 'F330_COMPANION' in output: msg += '（同版 FCStd 显示缓存）'
            self.statusBar().showMessage(msg)
        except Exception as exc:
            self.statusBar().showMessage(f'打开失败：{path.name} · {exc}')
        finally:
            self.proc = None; process.deleteLater(); self.tmp.cleanup(); self.tmp = None; self.cancel_action.setVisible(False)

    def cancel(self):
        if self.proc:
            p, self.proc = self.proc, None; p.kill(); p.waitForFinished(); p.deleteLater()
            self.tmp.cleanup(); self.tmp = None; self.cancel_action.setVisible(False); self.statusBar().showMessage('已取消导入')

    def apply_scene(self, scene, name):
        for _, actor, _, _ in self.scene: self.r.RemoveActor(actor)
        self.scene = scene; self.parts.blockSignals(True); self.parts.clear()
        for text, actor, color, _ in scene:
            self.r.AddActor(actor); item = W.QListWidgetItem(text, self.parts); item.setToolTip(text)
            swatch = G.QPixmap(10, 10); swatch.fill(color); item.setIcon(G.QIcon(swatch)); item.setCheckState(C.Qt.Checked)
        self.parts.blockSignals(False); self.label.setText(name); self.setWindowTitle(f'{name} · {APP}')
        self.scene_changed.emit()
        self.update_count(); self.views.setCurrentIndex(0); self.orient('等轴测')

    def orient(self, name):
        direction, up = VIEWS[name]; cam = self.r.GetActiveCamera(); focal = cam.GetFocalPoint()
        cam.SetPosition(*(v+d for v, d in zip(focal, direction))); cam.SetViewUp(up); self.fit()

    def fit(self):
        if any(row[1].GetVisibility() for row in self.scene):
            self.r.ResetCamera(); self.r.ResetCameraClippingRange()
        self.win.Render()

    def update_count(self):
        visible = sum(a.GetVisibility() for _, a, _, _ in self.scene)
        self.count.setText(f'{visible} / {len(self.scene)} 个部件可见  ')

    def toggle(self, item):
        self.scene[self.parts.row(item)][1].SetVisibility(item.checkState() == C.Qt.Checked)
        self.update_count(); self.r.ResetCameraClippingRange(); self.win.Render()

    def show_parts(self, only):
        self.parts.blockSignals(True)
        for i, (_, actor, _, _) in enumerate(self.scene):
            on = only is None or i == only; actor.SetVisibility(on); self.parts.item(i).setCheckState(C.Qt.Checked if on else C.Qt.Unchecked)
        self.parts.blockSignals(False); self.update_count(); self.fit()

    def part_menu(self, pos):
        item = self.parts.itemAt(pos)
        if item:
            menu = W.QMenu(self); solo = menu.addAction('只看这个部件'); restore = menu.addAction('显示全部')
            choice = menu.exec_(self.parts.mapToGlobal(pos))
            if choice == solo: self.show_parts(self.parts.row(item))
            elif choice == restore: self.show_parts(None)

    def dragged_file(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile() and Path(url.toLocalFile()).suffix.lower() in MODEL_SUFFIXES: return Path(url.toLocalFile())

    def dragEnterEvent(self, event):
        if self.dragged_file(event): event.acceptProposedAction()

    def dropEvent(self, event):
        path = self.dragged_file(event)
        if path: event.acceptProposedAction(); self.open_file(path)

    def closeEvent(self, event):
        self.cancel(); self.axes.SetEnabled(0); self.canvas.Finalize(); super().closeEvent(event)


if __name__ == '__main__':
    W.QApplication.setAttribute(C.Qt.AA_EnableHighDpiScaling)
    app = W.QApplication(sys.argv); app.setApplicationName(APP); app.setDesktopFileName('local-step-viewer')
    w = Viewer(); w.show(); w.ia.Initialize()
    if len(sys.argv) > 1: C.QTimer.singleShot(0, lambda: w.open_file(Path(sys.argv[1])))
    else:
        w.apply_scene(read_scene(ASSETS / 'f330.mesh'), 'F330 总装示例'); w.statusBar().showMessage('示例：F330 总装')
    exit_code = app.exec_()
    # Destroy VTK/Qt widgets while the Qt application and X display still exist.
    del w
    gc.collect()
    del app
    sys.exit(exit_code)
