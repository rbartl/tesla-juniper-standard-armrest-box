"""Offscreen STL renderer (VTK) -> PNG with real lighting/shadows.
Usage: render.py IN.stl OUT.png [az el] """
import sys
import vtk

inp, outp = sys.argv[1], sys.argv[2]
az = float(sys.argv[3]) if len(sys.argv) > 3 else 35
el = float(sys.argv[4]) if len(sys.argv) > 4 else 32

reader = vtk.vtkSTLReader()
reader.SetFileName(inp)
reader.Update()

normals = vtk.vtkPolyDataNormals()
normals.SetInputConnection(reader.GetOutputPort())
normals.SetFeatureAngle(45)
normals.ConsistencyOn()
normals.AutoOrientNormalsOn()
normals.NonManifoldTraversalOff()
normals.Update()

mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(normals.GetOutputPort())

actor = vtk.vtkActor()
actor.SetMapper(mapper)
p = actor.GetProperty()
p.SetColor(0.42, 0.60, 0.72)
p.SetOpacity(1.0)
p.SetSpecular(0.10); p.SetSpecularPower(12); p.SetDiffuse(0.88); p.SetAmbient(0.32)
p.SetInterpolationToPhong()
p.BackfaceCullingOff()
p.FrontfaceCullingOff()
p.EdgeVisibilityOff()

ren = vtk.vtkRenderer()
ren.SetBackground(0.96, 0.96, 0.96)
ren.AddActor(actor)
ren.SetUseShadows(1)

# lights
for pos, inten in [((-1, -0.6, 1.4), 1.0), ((1.2, -1, 0.6), 0.5), ((0.2, 1, 0.5), 0.35)]:
    l = vtk.vtkLight()
    l.SetPosition(*pos); l.SetFocalPoint(0, 0, 0); l.SetIntensity(inten)
    l.SetPositional(False)
    ren.AddLight(l)

rw = vtk.vtkRenderWindow()
rw.SetOffScreenRendering(1)
rw.AddRenderer(ren)
rw.SetSize(1600, 1150)

ren.ResetCamera()
cam = ren.GetActiveCamera()
cam.Azimuth(az)
cam.Elevation(el)
cam.OrthogonalizeViewUp()
ren.ResetCamera()
ren.ResetCameraClippingRange()

bounds = normals.GetOutput().GetBounds()
dx = bounds[1] - bounds[0]
dy = bounds[3] - bounds[2]
dz = bounds[5] - bounds[4]
txt = vtk.vtkTextActor()
txt.SetInput(f"{dx:.1f} x {dy:.1f} x {dz:.1f} mm  (X x Y x Z)")
txt.GetTextProperty().SetFontSize(28)
txt.GetTextProperty().SetColor(0.1, 0.1, 0.1)
txt.SetPosition(20, 20)
ren.AddActor2D(txt)

rw.Render()

w2i = vtk.vtkWindowToImageFilter()
w2i.SetInput(rw)
w2i.Update()
w = vtk.vtkPNGWriter()
w.SetFileName(outp)
w.SetInputConnection(w2i.GetOutputPort())
w.Write()
print("wrote", outp)
