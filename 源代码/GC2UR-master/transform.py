import math

robot_base = "p[0.0, 0.0, 0.0, 0.0, 0.0, 0.0]"
#zero_point = None
x_axis_point = "p[0.03, 0.03, 0.0, 0.0, 0.0, 0.0]"
y_axis_point = "p[0.01, 0.03, 0.0, 0.0, 0.0, 0.0]"

angle = 0.0                                                     #以弧度为单位，逆时针方向
angle_deviation = 0.25                                          #角度“zero_point - x_axis_point”和“zero_point - y_axis_point”的百分比分布
zero_x = 0.0
zero_y = 0.0

def get_angle(x0, y0, x1, y1):             #返回新 X 轴相对于参考坐标系的 X 轴的旋转，如果点不合适，则返回 -1

    if x1 > x0 and y1 > y0:     #上弦
        theta1 = math.atan((y1 - y0) / (x1 - x0))
        return theta1

    elif x1 < x0 and y1 > y0:   #第二季度
        theta1 = -math.atan((x1 - x0) / (y1 - y0))
        return theta1 + math.radians(90)

    elif x1 < x0 and y1 < y0:   #第三季度
        theta1 = math.atan((y1 - y0) / (x1 - x0))
        return theta1 + math.radians(180)

    elif x1 > x0 and y1 < y0:   #第四季度
        theta1 = -math.atan((x1 - x0) / (y1 - y0))
        return theta1 + math.radians(270)

    elif x1 == x0 and y1 > y0:
        return math.radians(90)

    elif x1 == x0 and y1 < y0:
        return math.radians(270)

    elif y1 == y0 and x1 > x0:
        return 0

    elif y1 == y0 and x1 < x0:
        return math.radians(180)

    else:
        return 0

def get_distance(x0, y0, x1, y1):

    distance = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5

    return distance

def set_axis(zero_point):

    global zero_x, zero_y, angle

    zero_x, zero_y = parse_point(zero_point)

    if angle != None:
        return

    x0, y0 = parse_point(zero_point)
    x1, y1 = parse_point(x_axis_point)
    x2, y2 = parse_point(y_axis_point)

    angle1 = get_angle(x0, y0, x1, y1)
    angle2 = get_angle(x0, y0, x2, y2) - math.pi / 2

    if abs(angle1 / angle2 - 1) < angle_deviation * 0.01:

        angle = (angle1 + angle2) / 2

    else:

        angle = -1

def transform_point(x, y, x0 = None, y0 = None, x_base = 0, y_base = 0):

    global zero_x, zero_y

    #if x == 0 and y == 0:
        #return zero_x, zero_y

    if x0 == None and y0 == None:
        x0 = zero_x
        y0 = zero_y

    point_angle = get_angle(x_base, y_base, x, y)
    distance = get_distance(x_base, y_base, x, y)

    target_angle = point_angle + angle

    if 0 < target_angle <= math.radians(90):
        target_x = x0 + distance * math.cos(target_angle)
        target_y = y0 + distance * math.sin(target_angle)

    elif math.radians(90) < target_angle <= math.radians(180):
        target_x = x0 + distance * math.cos(target_angle)
        target_y = y0 + distance * math.sin(target_angle)

    elif math.radians(180) < target_angle <= math.radians(270):
        target_x = x0 + distance * math.cos(target_angle)
        target_y = y0 + distance * math.sin(target_angle)

    else:
        target_x = x0 + distance * math.cos(target_angle)
        target_y = y0 + distance * math.sin(target_angle)

    return target_x, target_y

def parse_point(point):
    point = point.replace("p[", "")
    point = point.replace("]", "")
    point = point.split(", ")
    x = float(point[0])
    y = float(point[1])

    return x, y

def set_params(anchor, rotation):
    global angle, zero_point

    angle = rotation
    zero_point = anchor