import subprocess
import pkg_resources
import platform
import os
import evdev


def notebooks_dir():
    return pkg_resources.resource_filename('jetbot', 'notebooks')


def platform_notebooks_dir():
    if 'aarch64' in platform.machine():
        return os.path.join(notebooks_dir(), 'robot')
    else:
        return os.path.join(notebooks_dir(), 'host')


def platform_model_str():
    with open('/proc/device-tree/model', 'r') as f:
        return str(f.read()[:-1])


def platform_is_nano():
    return 'jetson-nano' in platform_model_str()


def get_ip_address(interface):
    try:
        if get_network_interface_state(interface) == 'down':
            return None
        cmd = "ifconfig %s | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'" % interface
        return subprocess.check_output(cmd, shell=True).decode('ascii')[:-1]
    except:
        return None


def get_network_interface_state(interface):
    return subprocess.check_output('cat /sys/class/net/%s/operstate' % interface, shell=True).decode('ascii')[:-1]

def get_wifi_ssid():
    return subprocess.check_output('iwgetid -r', shell=True).decode('ascii')[:-1]

def get_dualshock4():
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        dn = device.name.lower().strip()
        if dn == "wireless controller":
            return device

def get_dualshock4_mac():
    d = get_dualshock4()
    if d != None:
        return d.phys
    else:
        return None
