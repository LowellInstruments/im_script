import datetime
import os
import time
from mat.data_converter import default_parameters, DataConverter
from mat.logger_controller import STOP_CMD, RUN_CMD, DEL_FILE_CMD
from mat.logger_controller_ble import LoggerControllerBLE, ble_scan
from mat.utils import PrintColors


# colors enabled
COLORS_ENABLED = 1


def convert_lid_file(lid_file_path):
    # rename file download
    name, _ = lid_file_path.split('.', 1)
    lid_file_ts_path = '{}_{}.lid'.format(name, str(int(time.time())))
    os.rename(lid_file_path, lid_file_ts_path)

    # convert renamed file
    cnv_error_paths = []
    try:
        pars = default_parameters()
        converter = DataConverter(lid_file_ts_path, pars)
        converter.convert()
    except ValueError:
        cnv_error_paths.append(lid_file_ts_path)
        pass

    # calculate csv expected output file names
    name, _ = lid_file_ts_path.split('.', 1)
    out_paths = ['{}_{}.csv'.format(name, 'Temperature'),
                 '{}_{}.csv'.format(name, 'Pressure')]
    cnv_ok_paths = [i for i in out_paths if os.path.exists(i)]
    return cnv_ok_paths, cnv_error_paths


def _print_color(s, color=None):
    if not COLORS_ENABLED or not color:
        print(s)
        return
    pc = PrintColors()
    if color == 'r':
        c = pc.FAIL
    elif color == 'b':
        c = pc.OKBLUE
    elif color == 'g':
        c = pc.OKGREEN
    elif color == 'y':
        c = pc.WARNING
    else:
        c = pc.ENDC
    print(c + s + pc.ENDC)


def print_ble(s, color=None):
    _print_color('BLE thread: {}'.format(s), color)


def print_mas(s, color=None):
    _print_color('MAS thread: {}'.format(s), color)


def _ble_dl_files(lc, ls: dict, dl_folder):
    if not ls:
        return True, []

    # download via xmodem each file inside the logger
    files_dl = []
    print_ble('downloading files... \n{}'.format(ls), 'b')
    for name, size in ls.items():
        rv = lc.get_file(name, dl_folder, size)
        if rv:
            print_ble('got {}, {} bytes'.format(name, size))
            files_dl.append(name)
        else:
            e = 'error get {}, will retry'
            print_ble(e, 'r')
            time.sleep(5)
            break

        # todo: on production, delete file at logger
        # delete the file from inside the logger
        s = 'error deleting file {}'.format(name)
        if _ble_rm_logger_file(lc, name):
            s = 'deleted file {}'.format(name)
        print_ble(s, 'n')

    # OK when ALL files download, also give their names
    return len(files_dl) == len(ls), files_dl


def _ble_stop_logger(lc):
    rv = lc.command(STOP_CMD)
    return rv == [b'STP', b'0200']


def _ble_rm_logger_file(lc, filename):
    rv = lc.command(DEL_FILE_CMD, filename)
    return rv == [b'DEL', b'00']


def _ble_set_logger_fast_mode(lc):
    if not lc.send_btc():
        print_ble('error send_btc, leaving', 'r')
        return False
    return True


def _ble_list_logger_files(lc):
    return lc.ls_lid()


def _ble_run_logger(lc):
    rv = lc.command(RUN_CMD)
    return rv == [b'RUN', b'00']


def _ble_sync_logger_time(lc):
    rv = lc.get_time()
    if not rv or len(str(rv)) != 19:
        return False

    # command: STM only if needed
    d = datetime.datetime.now() - rv
    if abs(d.total_seconds()) > 60:
        rv = lc.sync_time()
        if rv != [b'STM', b'00']:
            return False
    return True


def ble_dl_logger(mac, dl_folder, hci_if):
    with LoggerControllerBLE(mac, hci_if) as lc:
        # ensure logger is stopped
        if not _ble_stop_logger(lc):
            e = 'error stopping logger {}'
            print_ble(e.format(mac), 'r')
            return False, []

        # when logger is new, may use this
        if not _ble_sync_logger_time(lc):
            e = 'error syncing time on logger {}'
            print_ble(e.format(mac), 'r')
            return False, []

        # configure RN4020-based logger for max speed
        if not _ble_set_logger_fast_mode(lc):
            e = 'error setting fast mode on logger {}'
            print_ble(e.format(mac), 'r')
            return False, []

        # list format {'file_1.lid': 12, 'file_2.lid': 45}
        ls = _ble_list_logger_files(lc)

        # download all files in logger
        dl_session_ok, filenames_dl_ok = _ble_dl_files(lc, ls, dl_folder)
        if not dl_session_ok:
            e = 'error downloading some files from logger {}'
            print_ble(e.format(mac), 'r')
            return False, filenames_dl_ok

        # everything went smooth until now
        if not _ble_run_logger(lc):
            e = 'error re-running logger {}'
            print_ble(e.format(mac), 'r')
            return False, filenames_dl_ok

        return True, filenames_dl_ok


def ble_scan_for_loggers(hci: int, timeout):
    # translate bluepy scan results format to an easier one
    sr = ble_scan(hci, timeout)
    friendly_sr = [(i.addr, i.rssi) for i in sr]
    # friendly_sr: lower-case ('28:11...', -88), ('68:6a...', -68),
    return friendly_sr


def mac_filter_by_my_rule(mac):
    """ useful for testing """
    return [(mac, -30)]
