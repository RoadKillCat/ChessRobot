import serial, os.path

"""
==Joe's Serial Protocol==
  Runs at a baud rate of 115200 pulses per second.
  The number of bytes in the message is sent first.
  The next byte represents the message type.
  The following number of enclosed bytes (NEBs) is dependent on the message type.
  First byte  | Message (type)  | NEBs | Enclosed bytes meaning
  0           | home            | 0    | N/A
  1           | motor state     | 1    | (0/1 => disable/enable)
  2           | set grabber     | 1    | (0/1 => grab off/grab on
  3           | move position   | 6    | (x: [0¬335, y: [100¬450], z: [0¬200])
                                          ^          ^             ^
       these uint16s (actually casted to signed) are sent *little-endian* (see INT_FROM_BYTES)

  Arduino will reply with a one byte code after every message.
  Value       | Meaning
  0           | Task completed as expected
  1           | x_pos has reached x_target - useful for timings
  2           | Invalid request structure (wrong NEBs)
  3           | Task failed due to invalid input ranges
  4           | Unkown request type

"""



LIMITS = {'x': (0, 335),
          'y': (100, 450),
          'z': (0, 200)}

class Arm():
    '''This class implements the necessary methods to communicate over serial
    with an Arduino that is running the corresponding "Joe's Serial Protocol"
    C++ code on.'''
    def __init__(self, port):
        '''Initialises an arm instance.
            - port <= serial port string'''
        self.port = port
        self._connect_to_arduino()
        self.serial.flushInput()
    def home(self):
        '''Moves the arm to its home position which is
        defined on the Arduino's side.'''
        self._write_and_check_success([1, 0])
    def set_motors(self, state):
        '''Enables or disables the stepper and servo motors on the arm.
            - state <= boolean: True=enable; False=disable'''
        self._write_and_check_success([2, 1, state])
    def set_grabber(self, state):
        '''Sets the state of the grabber on the arm's effector.
            - state <= boolean: True=grab on; False=grab off'''
        self._write_and_check_success([2, 2, state])
    def move_to(self, x, y, z):
        '''Moves the arm to the specified coordinate; given in millimeters.'''
        if not (LIMITS['x'][0] <= x <= LIMITS['x'][1] and \
                LIMITS['y'][0] <= y <= LIMITS['y'][1] and \
                LIMITS['z'][0] <= z <= LIMITS['z'][1]):
            raise ValueError('Position '+str([x,y,z])+' out of limits.')
        if not (type(x) == type(y) == type(z) == int):
            raise TypeError('Parameters: x,y,z must be integers!')
        self._write_and_check_success([7, 3,
                                       *self._bytes_from_int(x),
                                       *self._bytes_from_int(y),
                                       *self._bytes_from_int(z)])
    def block_till_reach_target(self):
        '''Waits till x_pos reaches next x_target. Blocking.'''
        r = self.serial.read()[0]
        if r != 1:
            raise Exception('Arduino return code != 1: '+ str(r))
    def _write_and_check_success(self, message):
        self.serial.flushInput()
        self.serial.write(message)
        r = self.serial.read()[0]
        if r != 0:
            raise Exception('Arduino code non-zero when sending: '+str(message)+ \
                            ', it replied with: '+str(r))
    def _connect_to_arduino(self):
        try:
            self.serial = serial.Serial(self.port, 115200);
        except serial.serialutil.SerialException:
            raise Exception('Could not open ['+self.port+'].')
    def _bytes_from_int(self, i):
        return (i >> 8, i & 0xff)
