import json, sys, struct, pathlib, resource, re
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
sys.path.append('/usr/lib/freecad/lib')
import FreeCAD as F, Part, MeshPart, numpy as np

def convert(source,output,demo=False):
    if demo:
        doc=F.openDocument(str(source.resolve()))
        items=[(o.Label,o.Shape) for o in doc.Objects if hasattr(o,'Shape')]
    else:
        shape=Part.read(str(source)); pieces=shape.childShapes() if shape.ShapeType in ('Compound','CompSolid') else [shape]
        items=[(f'零件 {i+1:02d}',p) for i,p in enumerate(pieces)]
    arrays=[]; rows=[]; offset=0
    for title,shape in items:
        mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.16,AngularDeflection=.46,Relative=False)
        vertices, triangles=mesh.Topology
        if not triangles:continue
        row={'name':title};rows.append(row)
        for key,arr in [('p',np.asarray([(p.x,p.y,p.z) for p in vertices],dtype='<f4')),('i',np.asarray(triangles,dtype='<u4'))]:
            b=arr.tobytes();arrays.append(b);row[key]=[offset,arr.size];offset+=len(b)
    if not rows:raise ValueError('模型不包含可显示的曲面')
    head=json.dumps(rows,ensure_ascii=False).encode();head+=b' '*(-len(head)%4)
    with output.open('wb') as f:
        f.write(struct.pack('<I',len(head)));f.write(head);f.writelines(arrays)

if __name__=='__main__':convert(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),len(sys.argv)>3)
