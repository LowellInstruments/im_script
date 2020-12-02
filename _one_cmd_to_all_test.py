import bluepy.btle as ble
from ble_mat_facade import _ble_sync_logger_time
from mat.logger_controller import DEL_FILE_CMD, RUN_CMD, STATUS_CMD
from mat.logger_controller_ble import LoggerControllerBLE


macs = [
    # '00:1e:c0:4d:bf:c9',
    '00:1E:C0:6C:75:07',
    '00:1E:C0:6C:75:0D',
    '00:1E:C0:6C:74:FD',
    '00:1E:C0:6C:74:F2',
    '00:1E:C0:6C:74:F7',
    '00:1E:C0:6C:76:13'
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
        _ls = [i.decode() for i in _ls if i.endswith(b'lid')]
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


def status_one_logger(mac):
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command(STATUS_CMD)
            print('\t\tSTS --> {}'.format(rv))
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
        status_one_logger(each_mac)

    # for each_mac in macs:
        # it will connect twice but, meh
        # ls = ls_lid_rn4020(each_mac)
        # delete_all_lid(each_mac, ls)
