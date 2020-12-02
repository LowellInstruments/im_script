import _gdbm
import os
import queue
import threading
import time
import yaml
import shelve
import bluepy.btle as ble
from ble_mat_facade import (ble_dl_logger,
                            ble_scan_for_loggers,
                            print_ble,
                            convert_lid_file,
                            mac_filter_by_my_rule)


def _th_rerun_countdown(s):
    for i in reversed(range(5)):
        e = 'died, exc -> {} re-run in {} ...'.format(str(s), i)
        print_ble(e, 'r')
        time.sleep(1)


def _th_run_banner(th):
    s = 'boot with hci{}'
    print_ble(s.format(th.hci), 'b')
    s = 'boot with whitelist {}'
    print_ble(s.format(list(th.mac_wl)), 'b')
    s = 'boot with now {}'
    print_ble(s.format(int(time.time())), 'b')


def _mac_filter_by_not_recent(friendly_sr):
    """ ensure we did not recently already queried this logger """
    _r = shelve.open('.recent.db')
    macs = [i for i in friendly_sr if i[0] not in _r.keys()]
    _r.close()
    return macs


def _recent_update(mac, went_ok, ok_interval: int):
    # todo: on production, remove this shelving fixture
    # went_ok = False

    # _r : {mac_1: [time, error], ...}
    _next = time.time()
    _next += ok_interval if went_ok else 60
    _r = shelve.open('.recent.db')
    _up = _r.get(mac, [_next, 0])[1]
    _r[mac] = [_next, _up + 1]
    _r.close()

    if not went_ok:
        s = '{} put in ignore list for 60 seconds'
        print_ble(s.format(mac), 'r')


def _recent_prune():
    # _r : {mac_1: [time, error], ...}
    now = time.time()
    _r = shelve.open('.recent.db')
    _exp = [i for i in list(_r.keys()) if _r[i][0] < now]
    for each_expired in _exp:
        print_ble('{} un-ignored'.format(each_expired), 'y')
        del _r[each_expired]
    _r.close()


class ReadBLELCMessagesForever(threading.Thread):
    """ Read BLE loggers forever into queue from hciX """
    def __init__(self, _queue, dl_folder, hci: int, logger_wl, ok_interval: int):
        threading.Thread.__init__(self)
        self.queue = _queue
        self.hci = hci
        self.logger_wl = logger_wl
        self.mac_wl = self.logger_wl.keys()
        self.dl_folder = dl_folder
        self.ok_interval = ok_interval

    def _mac_filter_by_whitelist(self, friendly_sr):
        """ ensure is a loggers in our whitelist """
        return [i for i in friendly_sr if i[0] in self.mac_wl]

    def run(self):
        # todo: force-test this exception by manually disconnecting
        while 1:
            try:
                self._run()
            except ble.BTLEException as ex:
                # ble exception
                _th_rerun_countdown(ex)
            except AttributeError as ae:
                # None has no attribute ex: send_btc
                _th_rerun_countdown(ae)
            except _gdbm.error as ge:
                # shelve error
                _th_rerun_countdown(ge)

    def _run(self):
        """ enqueue file names downloaded from loggers """
        _th_run_banner(self)

        # this thread scans forever
        while True:
            _recent_prune()
            scan_results = ble_scan_for_loggers(self.hci, 5.0)
            scan_results = self._mac_filter_by_whitelist(scan_results)
            scan_results = _mac_filter_by_not_recent(scan_results)
            # scan_results = mac_filter_by_my_rule('00:1e:c0:6c:76:13')

            # download each logger which did not get filtered
            for each_sr in scan_results:
                mac = each_sr[0]
                print_ble('--- logger {} start ---'.format(mac), 'b')
                dl_logger_ok, names_dl = ble_dl_logger(mac, self.dl_folder, self.hci)

                for each_dl in names_dl:
                    path = os.path.join(self.dl_folder, each_dl)
                    csv_names, err_names = convert_lid_file(path)
                    for each_csv in csv_names:
                        print_ble('enqueuing {}'.format(each_csv), 'g')
                        self.queue.put_nowait(each_csv)
                    for each_err in err_names:
                        print_ble('error convert {}'.format(each_err), 'r')

                # display result
                s = 'OK' if dl_logger_ok else 'error'
                print_ble('--- logger {} {} ---'.format(mac, s), 'b')

                # how often re-query a logger upon OK / upon error
                _recent_update(mac, dl_logger_ok, self.ok_interval)


# to test this class separately
if __name__ == '__main__':
    # grab whitelisted macs file
    with open('loggers.yaml', 'r') as f:
        mac_wl = yaml.load(f, Loader=yaml.FullLoader)

    # show current folder
    fol = os.path.join(os.getcwd(), 'dl_files')
    print('current data folder is {}'.format(fol))

    # set hci interface, internal 0 external 1
    my_hci = 0

    # run thread
    dummy_q = queue.Queue()
    reader = ReadBLELCMessagesForever(dummy_q, fol, my_hci, mac_wl)
    reader.run()



