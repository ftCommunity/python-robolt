#
# python driver for Fischertechnik RoboLT 
#

import os
import usb.core
import usb.backend.libusb1
import logging

logger = logging.getLogger('robolt')

ID_VENDOR          = 0x146a
ID_PRODUCT         = 0x000a

# limit the visibility to simplify the usage
__all__ = ["scan_for_devices", "RoboLT"]

def scan_for_devices():
    """ Find all available devices """
    devices = []
    try:
        backend = usb.backend.libusb1.get_backend(find_library=lambda x: "/usr/lib/libusb-1.0.so")
        for dev in usb.core.find(find_all=True, idVendor=ID_VENDOR, idProduct=ID_PRODUCT, backend=backend):
            devices.append(dev)
    except usb.core.USBError as e:
        logger.error("Could not find a connected RoboLT device: %s" % str(e))
    return devices

class RoboLT(object):
    # keep state of motor outputs
    enable = [ False, False, False, False ]
    pwm = [ 0,0,0,0 ]

    # constants for motor direction states
    Off = 0
    Left = 1
    Right = 2
    Brake = 3

    """
        Each instance of this class represents a physical RoboLT device.

        Usage :

        >>> from robolt import RoboLT
        >>> lt = RoboLT()
    """

    def __init__(self, device=None):
        """
        If a device is not given, it will attach this instance to the first one found.
        Otherwise you can pass a specific one from the list returned by scan_for_devices.
        """
        self.number = 0
        self.dev = device
        if self.dev is None:
            devices = scan_for_devices()
            if not(devices):
                raise OSError("Could not find a connected RoboLT device")
            self.dev = devices[0]
        self.init_device()

    def init_device(self):
        """
        Reinit device associated with the RoboLT instance
        """
        try:
            self.dev.set_configuration()
            # RoboLT uses two interrupt endpoints
            self.endpoint_in = self.dev[0][(0, 0)][0]
            self.endpoint_out = self.dev[0][(0, 0)][1]
            self.update_out()
        except usb.core.USBError as e:
            logger.error("Could not init device: %s" % str(e))

    def getRawData(self):
        """Read 6 bytes from the RoboLT's endpoint"""
        try:
            return self.endpoint_in.read(6)
        except usb.core.USBError as e:
            logger.exception("Could not read from RoboLT device")
            return None

    def getFw(self):
        """
        Return the RoboLT firmware version
        """
        try:
            ret = self.dev.ctrl_transfer(0xc0, 0xf0, 0x0001, 0, 5)
            return str(ret[1]) + "." + str(ret[2]) + "." + str(ret[3]) + "." + str(ret[4])
        except usb.core.USBError as e:
            logger.exception("Could not send control transfer")
            return None

    def getSerial(self):
        """
        Return the RoboLT serial number
        """
        try:
            ret = self.dev.ctrl_transfer(0xc0, 0xf0, 2, 0, 14)
            return ret[1] + ret[2]*100 + ret[3]*10000 + ret[4]*1000000
        except usb.core.USBError as e:
            logger.exception("Could not send control transfer")
            return None

    def setM(self, id, dir=Off, speed=0):
        """
        sets motor M1 or M2 direction and speed
        """
        if id < 1 or id > 2:
            raise ValueError('Motor id out of range')
        if dir < self.Off or dir > self.Brake:
            raise ValueError('Illegal motor direction value')
        if speed < 0 or speed > 100:
            raise ValueError('Motor speed out of range')

        # map motor values onto the shadow registers
        self.enable[2*id-2] = bool(dir & 1)
        self.enable[2*id-1] = bool(dir & 2)
        self.pwm[2*id-2] = speed
        self.pwm[2*id-1] = speed

        # and force transmission
        self.update_out()

    def setO(self, id, state, pwm=0):
        """
        sets output O1 - O4 state and pwm value
        """
        if id < 1 or id > 4:
            raise ValueError('Output id out of range')
        if state != True and state != False:
            raise ValueError('Illegal output state')
        if pwm < 0 or pwm > 100:
            raise ValueError('Output pwm out of range')

        # map output values onto the shadow registers
        self.enable[id-1] = state
        self.pwm[id-1] = pwm

        # and force transmission
        self.update_out()

    def update_out(self):
        # assemble command sequence from pwm/enable state
        data = [ 0xf2,0,0,0,0,0 ]
        for i in range(4):
            if self.enable[i]: data[1] |= (1<<i)
        data[2] |= int(self.pwm[0]*8/101)
        data[2] |= int(self.pwm[1]*8/101) << 3
        data[2] |= (int(self.pwm[2]*8/101) << 6) & 0xff
        data[3] |= (int(self.pwm[2]*8/101) >> 2)
        data[3] |= (int(self.pwm[3]*8/101) << 1)

        self.endpoint_out.write(data)

    def I(self):
        """
        Returns digital state of inputs I1, I2 and I3
        """
        data = self.getRawData()
        return (bool(data[0] & 1), bool(data[0] & 2), bool(data[0] & 4))

    def A(self):
        """
        Returns analog state of inputs I1 and I3
        """
        data = self.getRawData()
        return ((data[1] + 256 * (data[4]&3)),
                0.03*(data[2] + 256 * ((data[4]>>2)&3)))

    def getBattery(self):
        """
        Returns current supply voltage
        """
        data = self.getRawData()
        return 0.03*(data[3] + 256 * ((data[4]>>4)&3))
