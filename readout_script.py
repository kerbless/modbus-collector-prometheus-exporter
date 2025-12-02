#!/usr/bin/python3

from os import system
import subprocess

template_command_l = ["/usr/local/bin/modbus",
                    "-s", "4",
                    "-b", "38400",
                    "-P", "e",
                    "-p", "1",
                    "-r", "./registers.modbus",
                    "/dev/ttyUSB0", "\*"]

rs485_device_ids = {"generale":3, "gruppo_frigo":4}

if __name__ == "__main__":
    for el in rs485_device_ids:
        id_device=rs485_device_ids[el]
        template_command = f"modbus -s {id_device} -b 38400 -P e -p 1 -r registers.modbus /dev/ttyUSB0 \*"
        output = subprocess.run(template_command,shell=True,capture_output=True).stdout
        read_vals = output.decode("utf-8").split('\n')[1:] 
        for line in read_vals:
            try:
                lab, val = line.split(":")
                print(f"multimetri-{lab}{{punto_misura=\"{el}\"}} = {float(val):.2f}")
            except:
                pass

