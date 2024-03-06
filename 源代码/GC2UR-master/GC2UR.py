import gcodetools as ur
import visualisation as vis

base_point = "p[0.0, 0.0, 0.0, 0.0, 0.0, 0.0]"  # 机器人坐标系中与 GCode 零点相对应的坐标
angle = 0                                  # 旋转

gcode_filename = 'new.jpg.stroke.nc'
urscript_filename = 'script.urscript'


ur.set_transform(base_point, angle)
ur.convert(gcode_filename, urscript_filename)
vis.draw_all(urscript_filename)
