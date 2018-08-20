import math, serial, time, atexit

ser = serial.Serial('/dev/ttyUSB0', 9600)

#GENERAL
home_pos = (0,20,10)
cur_pos = home_pos
grabbed = 0

#TUNING
cm_p_sec = 30   #cm per second
stp_p_cm = 0.1    #steps per cm
settle_time = 3 #time for mechanical wobble to stabilise

#ROBOT ARM CONFIG
servo_grab_on   = 154
servo_grab_off  = 140
servo_grab_time = 1   #time to grab
arm_lengths = 20
gripper_length = 4
#servo offsets
servo_offset_front  = -16
servo_offset_back   = -8
servo_offset_bottom = -25

#CHESS BOARD CONFIG
x_sides = 13.5
y_close = 9
y_far   = 38
z_piece = 2
z_above = 10


def test_piece_movement():
    move_piece((0,0),(7,0))
    move_piece((7,0),(0,0))

def calibrate():
    home()
    slide_to(*piece_coordinate(0,0),z_piece)
    time.sleep(settle_time)
    home()
    slide_to(*piece_coordinate(7,0),z_piece)
    time.sleep(settle_time)
    home()
    slide_to(*piece_coordinate(7,7),z_piece)
    time.sleep(settle_time)
    home()
    slide_to(*piece_coordinate(0,7),z_piece)
    time.sleep(settle_time)
    home()

def piece_coordinate(x, y):
    #returns the x,y coord in the robot's coordinate system from
    #the board's 8x8 sysyem ((0,0) in bottom left; y going away)
    return (-x_sides if not x else lerp(x/7,-x_sides,x_sides),
             y_close if not y else lerp(y/7,y_close,y_far))

def move_piece(c1, c2):
    c1, c2 = (piece_coordinate(*c) for c in (c1, c2))
    home()
    set_grabber(0)
    print('aligning with c1...')
    slide_to(*c1, z_above)
    time.sleep(settle_time)
    print('poised\npositioning for grab...')
    slide_to(*c1, z_piece)
    print('ready to grab\ngrabbing...')
    set_grabber(1)
    print('grabbed\nescaping...')
    slide_to(*c1, z_above)
    print('escaped\ngoing home...')
    home()
    print('home\naligning with c2...')
    slide_to(*c2, z_above)
    time.sleep(settle_time)
    print('poised\npositioning for release...')
    slide_to(*c2, z_piece)
    print('ready to release\nreleasing...')
    set_grabber(0)
    print('released\nescaping...')
    slide_to(*c2, z_above)
    print('escpaed\ngoing home...')
    home()
    print('move complete')

def lerp(i, x1, x2):
    return x1 + i * (x2-x1)

def lerp3d(i, c1, c2):
    return [lerp(i, c1[c], c2[c]) for c in range(3)]

def dist3d(c1, c2):
    return ((c2[0]-c1[0])**2+(c2[1]-c1[1])**2+(c2[2]-c1[2])**2)**0.5

def slide_to(x, y, z):
    global cur_pos
    dist = dist3d(cur_pos, (x,y,z))
    if dist == 0:
        #assert we are actually there (needed for initial home)
        move_to(*cur_pos)
        return
    time_ = dist / cm_p_sec
    #n = time.time()
    steps = math.ceil(dist * stp_p_cm)
    for i in range(steps+1):
        if move_to(*lerp3d(i/steps, cur_pos, (x, y, z))):
            cur_pos = (x, y, z)
            return 1
        time.sleep(time_ / steps)
    cur_pos = (x, y, z)
    #print(time_, time.time() -n )

def set_grabber(state):
    global grabbed
    ser.write([servo_grab_on if state else servo_grab_off, 10])
    time.sleep(servo_grab_time)
    grabbed = state

def move_to(x, y, z):
    try:
        d = math.sqrt(x**2+y**2) - gripper_length
        A = math.acos((d**2+z**2) / (2*arm_lengths*(d**2+z**2)**0.5))
        Z = math.atan2(z,d)
        R = math.atan2(x,y)
        print(math.degrees(R))

        servo_front  = math.degrees(A+Z)
        servo_back   = math.degrees(A-Z)
        servo_bottom = math.degrees(R)+90

        #grabber, back servo, front servo, rotate, end signal
        payload = [servo_grab_on if grabbed else servo_grab_off,
                   180 - int(servo_back)   + servo_offset_back,
                   180 - int(servo_front)  + servo_offset_front,
                   180 - int(servo_bottom) + servo_offset_bottom,
                   10]

        ser.write(payload)
    except ValueError:
        print('ERR: {},{},{}'.format(x,y,z))
        return 1
    return 0

def home():
    slide_to(*home_pos)

atexit.register(home)