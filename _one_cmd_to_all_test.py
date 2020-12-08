import bluepy.btle as ble
from ble_mat_facade import _ble_sync_logger_time
from mat.logger_controller import DEL_FILE_CMD, RUN_CMD, STATUS_CMD, TIME_CMD, STOP_CMD
from mat.logger_controller_ble import LoggerControllerBLE


macs = [
    # '00:1e:c0:4d:bf:c9',
    # '00:1E:C0:6C:75:07',
    # '00:1E:C0:6C:75:0D',
    # '00:1E:C0:6C:74:FD',
    # '00:1E:C0:6C:74:F2',
    # '00:1E:C0:6C:74:F7',
    # '00:1E:C0:6C:76:13'

    # 7 new ones
    '00:1E:C0:6C:76:0F',
    '00:1E:C0:4D:D2:49',
    '00:1E:C0:6C:74:F9',
    '00:1E:C0:4D:C5:72',
    '00:1E:C0:3D:7A:F2',
    '00:1E:C0:3D:7A:C5',
    '00:1E:C0:4D:C0:2F'
]


def delete_one_file(mac, f):
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command(DEL_FILE_CMD, f)
            print('\t\tDEL --> {}'.format(rv))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


def delete_all_lid(mac, _ls):
    with LoggerControllerBLE(mac) as lc:
        _ls = [i.decode() for i in _ls if i[-3:] == b'lid']
        for i in _ls:
            rv = lc.command(DEL_FILE_CMD, i)
            print('\t\tDEL {} --> {}'.format(i, rv))


def run_one_logger(mac):
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command(RUN_CMD)
            print('\t\tRUN --> {}'.format(rv))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


def stop_one_logger(mac):
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command(STOP_CMD)
            print('\t\tSTP --> {}'.format(rv))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


def status_one_logger(mac):
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command(STATUS_CMD)
            print('\t\tSTS --> {}'.format(rv))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


def ls_lid_one_logger(mac):
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.ls_lid()
            print('\t\tDIR lid --> {}'.format(rv))
            return rv
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


def get_time_one_logger(mac):
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command(TIME_CMD)
            print('\t\tGTM --> {}'.format(rv))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


def sync_time_one_logger(mac):
    try:
        with LoggerControllerBLE(mac) as lc:
            _ble_sync_logger_time(lc)
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    for each_mac in macs:
        stop_one_logger(each_mac)
        ls = ls_lid_one_logger(each_mac)
        print(ls)
        delete_all_lid(each_mac, ls)

