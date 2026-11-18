import json, sys, struct, pathlib, resource, re
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as F, Part, MeshPart, numpy as np

def stl_geometry(source):
    from vtkmodules.vtkIOGeometry import vtkSTLReader
    from vtkmodules.util.numpy_support import vtk_to_numpy
    reader = vtkSTLReader()
    reader.SetFileName(str(source))
    reader.Update()
    poly = reader.GetOutput()
    if reader.GetErrorCode() or not poly.GetNumberOfPolys():
        raise ValueError('STL 不包含可读取的三角面')
    return vtk_to_numpy(poly.GetPoints().GetData()), vtk_to_numpy(poly.GetPolys().GetConnectivityArray()).reshape(-1, 3)

def step_geometry(shape):
    mesh = MeshPart.meshFromShape(Shape=shape,LinearDeflection=.16,AngularDeflection=.46,Relative=False)
    vertices, triangles = mesh.Topology
    return [(p.x,p.y,p.z) for p in vertices], triangles

def convert(source,output,demo=False):
    if source.suffix.lower() == '.stl':
        # STL already contains triangles; keep its coordinates and topology.
        meshes = [(source.stem, stl_geometry(source))]
    else:
        if demo:
            doc=F.openDocument(str(source.resolve()))
            items=[(o.Label,o.Shape) for o in doc.Objects if hasattr(o,'Shape')]
        else:
            shape=Part.read(str(source)); pieces=shape.childShapes() if shape.ShapeType in ('Compound','CompSolid') else [shape]
            items=[(f'零件 {i+1:02d}',p) for i,p in enumerate(pieces)]
        meshes = ((name, step_geometry(shape)) for name, shape in items)
    arrays=[]; rows=[]; offset=0
    for title,(vertices,triangles) in meshes:
        if not len(triangles):continue
        row={'name':title};rows.append(row)
        for key,arr in [('p',np.asarray(vertices,dtype='<f4')),('i',np.asarray(triangles,dtype='<u4'))]:
            b=arr.tobytes();arrays.append(b);row[key]=[offset,arr.size];offset+=len(b)
    if not rows:raise ValueError('模型不包含可显示的曲面')
    head=json.dumps(rows,ensure_ascii=False).encode();head+=b' '*(-len(head)%4)
    with output.open('wb') as f:
        f.write(struct.pack('<I',len(head)));f.write(head);f.writelines(arrays)

if __name__=='__main__':convert(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),len(sys.argv)>3)
