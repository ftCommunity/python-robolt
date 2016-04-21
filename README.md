# Python-robolt

A simple python module to access the [Fischertechnik RoboLT interface])http://www.fischertechnik.de/en/desktopdefault.aspx/tabid-21/39_read-3/usetemplate-2_column_pano/).

## Example usage

```lt.getFw()
>>> from robolt import RoboLT
>>> lt = RoboLT()
# Firmware version
>>> print(lt.getFw())
# Activating the first motor full forward:
>>> lt.setM(1, RoboLT.Left, 100)
# Activating the second motor half speed/force backward:
>>> lt.setM(2, RoboLT.Right, 50)
# Current value of the digital inputs
>>> print(lt.I())
# Current battery voltage
>>> print(lt.getBattery())
```

A complete example for the Fischertechnik TXT controlling a RoboLT can be
found in the [apps repository](https://github.com/ftCommunity/ftcommunity-apps/tree/master/packages/robolttest).

## Non-priviledged access

In order to give non-priviledged users access to the RoboLT a udev rule
may be used. The repository contains a file named `40-robolt.rules`. Putting
this into the appropriate directory (e.g. `/etc/udev/rules.d`) will give
all users access to the RoboLT.

## RoboLT USB documentation

*The following details are for documentation only.* The python-robolt
library is supposed to hide all this from you and give you convenient
access to the underlying functionality.

The RoboLT uses vendor id 146a and product id 000a.

The RoboLT interface uses two interrupt endpoints to set and get the
I/O port state and implements a few vendor specific control requests.

### Vendor specific control requests

These vendor specific control requests use the following parameters:

  * **RequestType**: 0xc0, vendor specific in transfer
  * **Request**: 0xf0
  * **Value**: 1 amd 2 known (perhaps more commands exist)
  * **Index**: 0

The first byte returned in any of these request seems to mirror the 
bit-inverse of the command value. E.g. 254 for value 1. 

### Get firmware version (value 1)

This request gets the 4 byte firmware version from the RoboLT. The total
number of bytes to be requested is 5 as this includes the aforementioned
mirror byte.

Python example:

```
>>> fw = dev.ctrl_transfer(0xc0, 0xf0, 1, 0, 5)
```

The version is return in bytes 1:4.

### Get serial number (value 2)

This request gets 13 bytes of some serial number from the RoboLT. Python
example (again incl the additional mirror byte):

```
>>> fw = dev.ctrl_transfer(0xc0, 0xf0, 2, 0, 14)
```

### Setting outputs/motors

The RoboLTs outputs M1 and M2 each consist 

Motor/Output data is sent via the interrupt out endpoint (ep 1,
`dev[0][(0, 0)][1]`) using a six byte message. The first byte is always
0xf2. Byte 1 contains a bit for each of the 4 outputs to enable the
output driver. Bytes 2 and 3 contain four 3 bit PWM values allowing to
control 8 power levels on each output.

The PWM value for output 1 is stored in bits 0-2 of byte 2. The PWM
value for output 2 is stored in bits 3-5 of byte 2, PWM for output 3
is stored in bits 6 and 7 of byte 2 and bit 0 of byte 3. The PWM value
of output 4 is stored on bits 1-4 of byte 3. Bytes 4 and 5 seem to be
unused and should be set to 0 as depicted below.

```
 Byte0    Byte1    Byte2    Byte3    Byte4    Byte5
11110010 0000EEEE PPPPPPPP 0000PPPP 00000000 00000000
             4321 33222111     4443

```

When dealing with Motors the outputs O1 and O2 are combined to M1
and output O3 and O4 are used for M2. Both PWM values for the both
outputs used for one motor should be set to the same value. The
two enable bits can be used to set the direction of the motor or to
let it run free or stop (brake) it.

Python example setting motor M1 to 50%:

```
dev[0][(0, 0)][1].write([ 0xf2,0x01,0x1b,0,0,0 ])
```

### Reading inputs

Input data is received via the interrupt in endpoint (ep 0,
`dev[0][(0, 0)][0]`) using a six byte message. The first byte
returned contains the digital state of the three inputs I1 - I3
in its LSB's. 

Furthermore three 10 bit analog values A1 - A3 are encoded in the
reply. The lower 8 bits (bits 0-7) of these are returned in bytes 1 -
3. Byte 4 contains bits 8 and 9 of the analog values.

```
 Byte0    Byte1    Byte2    Byte3    Byte4    Byte5
00000DDD AAAAAAAA AAAAAAAA AAAAAAAA 00AAAAAA 00000000
     321 11111111 22222222 33333333   332211
```

A1 represents the analog resistance value on I1. It is 0 of I1
is open and 1023 if I1 is closed. This can be used for resistive
sensors like the temperature sensor.

A2 is the voltage measured on I3 in 0.03V units. E.g. a value of 300
is reported if a voltage of 9V is applied to I3. 

A3 is the voltage mesaured on the power supply in 0.03V units. This
can be useful when running on battery. Again, a value of 300 is returned
if the supplied power is 9V.

Reading the six bytes with Python is done like this:

```
data = dev[0][(0, 0)][0].endpoint_in.read(6)
```
