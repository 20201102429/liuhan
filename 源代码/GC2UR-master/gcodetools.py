import math
import datetime
import transform

transformation = False
base_point, angle = None, None

movel_radius = 0
movel_speed = 0.25
movel_acc = 1.2
movec_radius = 0
movec_speed = 0.25
movec_acc = 1.2

min_radius = 0.00001   # 最小圆弧半径

analogAffector = False  # 如果为 True，则将模拟输出设置为 analogOutValue
analogOutNumber = 0  # 模拟输出编号
analogOutValue = 1.05  # 在伏特
digitalOutNumber = 0  # 数字输出编号
delay_before_spindle_start = 0
delay_after_spindle_start = 0
delay_before_spindle_stop = 0
delay_after_spindle_stop = 0

f = 0.001  # 这是如果 gcode 以毫米为单位

last_x, last_y, last_z = 0, 0, 0
rx, ry, rz = 0, 0, 0


def parse_gcode_string(gcommand):

    """
    解析收到的 gcode 字符串，如果该字符串有效，则将其传递给 process_gcode_string
    """

    if gcommand:

        gcommand = gcommand.split()  # 用空格分隔字符串中的参数

        if "N" in gcommand[0]:  # 如果字符串以“N**”开头，则切断此参数，这是行号
            gcommand.remove(gcommand[0])

        if gcommand:
            return(process_gcode_string(gcommand))

def process_gcode_string(gcommand):

    """
    分析输入字符串中的命令
    """

    global last_z, last_y, last_x, rx, ry, rz, movel_speed, movec_speed

    if "F" in gcommand[0]:  # 如果是行驶速度设置
        speed = int(gcommand[0].replace("F", ""))
        return(setSpeed(speed))

    if "M" in gcommand[0]:  # 如果是 M 队，那么
        if gcommand[0] == "M3" or gcommand[0] == "M03" or gcommand[0] == "M4" or gcommand[0] == "M04":
            return spindleOn()
        elif gcommand[0] == "M5" or gcommand[0] == "M05":
            return spindleOff()
        else:
            pass

    if gcommand[0] == "G0" or gcommand[0] == "G1":  # 如果是直线运动命令

        x, y, z, speed = getLinearMove(gcommand)

        return(movel(x, y, z, rx, ry, rz, movel_acc, speed, movel_radius))

    elif gcommand[0] == "G2" or gcommand[0] == "G3":  # 如果是弧形移动命令

        x0, y0, z0, x1, y1, z1, x2, y2, z2, R = getCircularMove(gcommand)

        if x0 != None and y0 != None and z0 != None and x1 != None and y1 != None and z1 != None and x2 != None and y2 != None and z2 != None and R != None:

            if R < min_radius:
                first_line = movel(x1, y1, z1, rx, ry, rz, a=1.2, v=0.25, r=0, t=0)
                second_line = movel(x2, y2, z2, rx, ry, rz, a=1.2, v=0.25, r=0, t=0)
                last_x = x2
                last_y = y2
                last_z = z2
                return first_line + "\n" + second_line
            else:
                return movec(x1, y1, z1, rx, ry, rz, x2, y2, z2, rx, ry, rz)
        else:
            return None

def movel(x, y, z, rx, ry, rz, a=1.2, v=0.25, r=0, t=0):
    """
    创建直线运动命令
    """

    x = float("{0:.6f}".format(x))
    y = float("{0:.6f}".format(y))
    z = float("{0:.6f}".format(z))
    rx = float("{0:.6f}".format(rx))
    ry = float("{0:.6f}".format(ry))
    rz = float("{0:.6f}".format(rz))

    return f"movel(p[{x}, {y}, {z}, {rx}, {ry}, {rz}], {a}, {v}, {t}, {r})"

def movec(x1, y1, z1, rx1, ry1, rz1, x2, y2, z2, rx2, ry2, rz2, a=1.2, v=0.25, r=0, mode=0):
    """
    创建循环命令
    """
    x1 = float("{0:.6f}".format(x1))
    y1 = float("{0:.6f}".format(y1))
    z1 = float("{0:.6f}".format(z1))
    rx1 = float("{0:.6f}".format(rx1))
    ry1 = float("{0:.6f}".format(ry1))
    rz1 = float("{0:.6f}".format(rz1))
    x2 = float("{0:.6f}".format(x2))
    y2 = float("{0:.6f}".format(y2))
    z2 = float("{0:.6f}".format(z2))
    rx2 = float("{0:.6f}".format(rx2))
    ry2 = float("{0:.6f}".format(ry2))
    rz2 = float("{0:.6f}".format(rz2))

    return f"movec(p[{x1}, {y1}, {z1}, {rx1}, {ry1}, {rz1}], p[{x2}, {y2}, {z2}, {rx2}, {ry2}, {rz2}], {a}, {v}, {r}, {mode})"

def setSpeed(speed):
    """
    设置移动速度
    """
    global movel_speed, movec_speed
    movel_speed = speed * 0.001
    movec_speed = speed * 0.001
    return "#set speed to {} mm/s".format(speed)

def spindleOn():
    """
    包括执行器
    """
    global analogOutValue, delay_before_spindle_start, delay_after_spindle_start
    response = ""

    if delay_before_spindle_start:
        response += f"sleep({delay_before_spindle_start})\n"

    if analogAffector:
        analogOutValue = "%.2f" % (analogOutValue * 0.1)
        response += f"set_analog_out({analogOutNumber}, {analogOutValue})"
    else:
        response += f"set_digital_out({digitalOutNumber}, True)"

    if delay_after_spindle_start:
        response += f"\nsleep({delay_after_spindle_start})"

    return response

def spindleOff():
    """
    关闭执行器
    """
    global delay_before_spindle_stop, delay_after_spindle_stop
    response = ""

    if delay_before_spindle_stop:
        response += f"sleep({delay_before_spindle_stop})\n"

    if analogAffector:
        response += f"set_analog_out({analogOutNumber}, 0)"
    else:
        response += f"set_digital_out({digitalOutNumber}, False)"

    if delay_after_spindle_stop:
        response += f"\nsleep({delay_after_spindle_stop})"

    return response

def getLinearMove(gcommand):
    """
   生成直线运动命令参数
    """

    gcommand.remove(gcommand[0])
    global last_z, last_y, last_x
    x, y, z, speed = None, None, None, None

    for k in range(len(gcommand)):

        if "X" in gcommand[k]:
            gcommand[k] = gcommand[k].replace('X', '')
            if gcommand[k]:
                x = float(gcommand[k]) * f
            else:
                x = float(gcommand[k + 1]) * f
            last_x = x

        if "Y" in gcommand[k]:
            gcommand[k] = gcommand[k].replace('Y', '')
            if gcommand[k]:
                y = float(gcommand[k]) * f
            else:
                y = float(gcommand[k + 1]) * f
            last_y = y

        if "Z" in gcommand[k]:
            gcommand[k] = gcommand[k].replace('Z', '')
            if gcommand[k]:
                z = float(gcommand[k]) * f
            else:
                z = float(gcommand[k + 1]) * f
            last_z = z

        if "F" in gcommand[k]:
            speed = int(gcommand[k].replace("F", ""))

    if x != None and y != None and transformation == True:
        x, y = transform.transform_point(x, y)
        last_x, last_y = transform.transform_point(last_x, last_y)

    if x == None:
        x = last_x
    if y == None:
        y = last_y
    if z == None:
        z = last_z
    if speed == None:
        speed = movel_speed



    return x, y, z, speed

def getCircularMove(gcommand):
    """
    生成循环命令参数
    """

    if gcommand[0] == "G2":
        direction = "CW"  # дуга по часовой стрелке
    else:
        direction = "CCW"  # дуга против часовой стрелки

    gcommand.remove(gcommand[0])

    global last_z, last_y, last_x

    x0 = last_x
    y0 = last_y
    z0 = last_z
    z2, speed = None, None

    for k in range(len(gcommand)):

        if "X" in gcommand[k]:
            gcommand[k] = gcommand[k].replace('X', '')
            if gcommand[k]:
                x2 = float(gcommand[k]) * f
            else:
                x2 = float(gcommand[k + 1]) * f
            last_x = x2

        if "Y" in gcommand[k]:
            gcommand[k] = gcommand[k].replace('Y', '')
            if gcommand[k]:
                y2 = float(gcommand[k]) * f
            else:
                y2 = float(gcommand[k + 1]) * f
            last_y = y2

        if "Z" in gcommand[k]:
            gcommand[k] = gcommand[k].replace('Z', '')
            if gcommand[k]:
                z = float(gcommand[k]) * f
            else:
                z = float(gcommand[k + 1]) * f
            last_z = z2

        if "I" in gcommand[k]:  #X 轴上的中心偏移
            gcommand[k] = gcommand[k].replace('I', '')
            if gcommand[k]:
                i = float(gcommand[k]) * f
            else:
                i = float(gcommand[k + 1]) * f

        if "J" in gcommand[k]:  # Y 轴中心偏移
            gcommand[k] = gcommand[k].replace('J', '')
            if gcommand[k]:
                j = float(gcommand[k]) * f
            else:
                j = float(gcommand[k + 1]) * f

        if "F" in gcommand[k]:
            speed = int(gcommand[k].replace("F", ""))

    if speed == None:
        speed = movec_speed
    if z2 == None:
        z2 = last_z

    if transformation == True:
        x2, y2 = transform.transform_point(x2, y2)
        last_x, last_y = transform.transform_point(last_x, last_y)
        i, j = transform.transform_point(i, j, 0, 0, 0, 0)

    x_center = x0 + i
    y_center = y0 + j
    z1 = (z0 + z2) / 2

    quad = calcQuad(x0, x2, y0, y2, direction)

    x1, y1, R = arcCenter(x0, y0, x2, y2, x_center, y_center, direction, quad)

    if x1 != None and y1 != None and R != None:

        return x0, y0, z0, x1, y1, z1, x2, y2, z2, R

    else:

        return None, None, None, None, None, None, None, None, None, None

def arcCenter(x0, y0, x2, y2, x_r, y_r, direction, quad):  # 圆弧起点、圆弧终点、圆弧中心点
    """
  定义圆弧的中点
    """

    #让我们找到和弦长度：
    l = ((x2 - x0) ** 2 + (y2 - y0) ** 2) ** 0.5

    if l != 0.0:    # 如果弦长不为零

        # 让我们找到和弦中间的坐标：
        x1 = (x0 + x2) / 2
        y1 = (y0 + y2) / 2
        # 让我们找出从和弦中间到弧中心的距离：
        l_1 = ((x1 - x_r) ** 2 + (y1 - y_r) ** 2) ** 0.5

        # 让我们找到弧的半径：
        R = (((x0 - x_r) ** 2 + (y0 - y_r) ** 2) ** 0.5 + ((x2 - x_r) ** 2 + (y2 - y_r) ** 2) ** 0.5) / 2

        # 让我们找到从弧线中间点到弦的中间线段：
        l_2 = R - l_1
        # 让我们找到弧的角度：
        angle = calcAngle(x0, x1, x2, y0, y1, y2, x_r, y_r, quad, l, R, direction)

        if angle == None:
            return None, None, None

        if angle < 179.95:

            dx = (x1 - x_r) * R / l_1
            dy = (y1 - y_r) * R / l_1

            x = x_r + dx
            y = y_r + dy

            return x, y, R

        elif angle > 180.05:

            dx = (x1 - x_r) * R / l_1
            dy = (y1 - y_r) * R / l_1

            x = x_r - dx
            y = y_r - dy

            return x, y, R

        else:

            return (halfCicle(x0, x1, x2, y0, y1, y2, l, R, quad))

    else:
        x = (x0 + x2) / 2
        y = (y0 + y2) / 2
        R = 0.0

        return x, y, R

def halfCicle(x0, x1, x2, y0, y1, y2, l, R, quad):
    """
    如果圆弧是半圆，则指定圆弧中间的点
    """

    if quad == 12:  # 如果我们的半圆同时位于两个正方形中
        x = (x0 + x2) / 2
        y = y0 + abs((x2 - x0) / 2)
        return x, y, R
    elif quad == 14:
        y = (y0 + y2) / 2
        x = x0 + abs((y2 - y0) / 2)
        return x, y, R
    elif quad == 23:
        y = (y0 + y2) / 2
        x = x0 - abs((y2 - y0) / 2)
        return x, y, R
    elif quad == 34:
        x = (x0 + x2) / 2
        y = y0 - abs((x2 - x0) / 2)
        return x, y, R
    elif quad == 1:
        sin_a = abs(y2 - y0) / l
        cos_a = abs(x2 - x0) / l
        y = y1 + R * sin_a
        x = x1 + R * cos_a
        return x, y, R
    elif quad == 2:
        sin_a = abs(y2 - y0) / l
        cos_a = abs(x2 - x0) / l
        y = y1 + R * sin_a
        x = x1 - R * cos_a
        return x, y, R
    elif quad == 3:
        sin_a = abs(y2 - y0) / l
        cos_a = abs(x2 - x0) / l
        y = y1 - R * sin_a
        x = x1 - R * cos_a
        return x, y, R
    elif quad == 4:
        sin_a = abs(y2 - y0) / l
        cos_a = abs(x2 - x0) / l
        y = y1 - R * sin_a
        x = x1 + R * cos_a
        return x, y, R

def calcQuad(x0, x2, y0, y2, direction):
    """
    计算弧所在的四分之一
    """

    if direction == "CW" and x2 == x0 and y2 < y0:
        quad = 14
    elif direction == "CW" and x2 == x0 and y2 > y0:
        quad = 23
    elif direction == "CW" and y2 == y0 and x2 > x0:
        quad = 12
    elif direction == "CW" and y2 == y0 and x2 < x0:
        quad = 34
    elif direction == "CCW" and x2 == x0 and y2 > y0:
        quad = 14
    elif direction == "CCW" and x2 == x0 and y2 < y0:
        quad = 23
    elif direction == "CCW" and y2 == y0 and x2 < x0:
        quad = 12
    elif direction == "CCW" and y2 == y0 and x2 > x0:
        quad = 23
    elif direction == "CW" and x2 > x0 and y2 < y0:
        quad = 1
    elif direction == "CW" and x2 > x0 and y2 > y0:
        quad = 2
    elif direction == "CW" and x2 < x0 and y2 > y0:
        quad = 3
    elif direction == "CW" and x2 < x0 and y2 < y0:
        quad = 4
    elif direction == "CCW" and x2 < x0 and y2 > y0:
        quad = 1
    elif direction == "CCW" and x2 < x0 and y2 < y0:
        quad = 2
    elif direction == "CCW" and x2 > x0 and y2 < y0:
        quad = 3
    elif direction == "CCW" and x2 > x0 and y2 > y0:
        quad = 4
    else:
        quad = 0

    return quad

def calcAngle(x0, x1, x2, y0, y1, y2, x_r, y_r, quad, l, R, direction):
    """
    计算圆弧的角度
    """

    angle = 2 * math.asin(0.5 * l / R)
    angle = math.degrees(angle)

    if quad == 1:
        if x_r < x1 and y_r < y1:
            return angle
        else:
            return 360 - angle

    if quad == 12:
        if y_r < y1:
            return angle
        else:
            return 360 - angle

    if quad == 14:
        if x_r < x1:
            return angle
        else:
            return 360 - angle

    if quad == 2:
        if x_r > x1 and y_r < y1:
            return angle
        else:
            return 360 - angle

    if quad == 23:
        if x_r > x1:
            return angle
        else:
            return 360 - angle

    if quad == 3:
        if x_r > x1 and y_r > y1:
            return angle
        else:
            return 360 - angle

    if quad == 34:
        if y_r > y1:
            return angle
        else:
            return 360 - angle

    if quad == 4:
        if x_r < x1 and y_r > y1:
            return angle
        else:
            return 360 - angle

def print_header():
    now = datetime.datetime.now()

    if transformation == True:
        return ("# This URScript file was generated by GC2UR tool coded by M.Kalugin at %s. Have fun!" % str(now) + '\n' "# Target gcode was moved, zero point of gcode now is %s" % base_point + ", rotation angle is %.2f" %math.degrees(angle) + " degrees" + '\n' + '\n')

    return("# This URScript file was generated by GC2UR tool coded by M.Kalugin at %s. Have fun!" % str(now) + '\n' + '\n' + '\n')

def convert(gcode_filename, urscript_filename):

    gcode = open(gcode_filename, 'r')
    urscript = open(urscript_filename, 'w')
    urscript.write(print_header())

    for line in gcode:
        script_line = parse_gcode_string(line)
        if script_line:
            print(script_line)
            urscript.write(script_line + '\n')

    urscript.close()

def set_transform(anchor, rotation):
    global transformation, base_point, angle

    if rotation != 0 or anchor != "p[0.0, 0.0, 0.0, 0.0, 0.0, 0.0]":
        transformation = True
    else:
        transformation = False
    base_point = anchor
    angle = math.radians(rotation)

    transform.set_params(base_point, angle)

    if transformation == True:
        transform.set_axis(base_point)

