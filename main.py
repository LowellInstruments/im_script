import argparse
import datetime
import lzma
import os
from signal import signal, SIGINT
import queue
import sys
import time
import yaml
from ble_mat_facade import print_mas
from th_ble import ReadBLELCMessagesForever


def _sigint_handler(_s, _f):
    # Handle any cleanup here
    print('CTRL-C detected, exit all threads')
    os._exit(0)


def _sleep_align_wallclock(interval):
    # align with interval, sleep more or less
    interval = int(interval)
    t = datetime.datetime.utcnow()
    diff = interval - (t.second + t.microsecond / 1000000.0)
    time.sleep(diff)


def _banner_dirs(cd, sd, od):
    print('currentdir cd: {}'.format(cd))
    print('stagindir  sd: cd + {}'.format(sd))
    print('outputdir  od: cd + {}'.format(od))


def main():
    # to manage ctrl + C
    signal(SIGINT, _sigint_handler)

    # build argument parser and collect argument values
    desc = 'Integrated Monitoring BLE Logger Collector'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-d', '--datadir', required=True,
                        help='Output directory for data files')
    parser.add_argument('-s', '--source', required=True, type=int,
                        help='The X in BLE interface input hciX')
    parser.add_argument('-i', '--interval', required=True, type=int,
                        help='Interval to re-query a logger')
    parser.add_argument('-w', '--whitelist', required=True,
                        help='mac whitelist file path')
    _args = vars(parser.parse_args())
    _ad, _as = _args['datadir'], _args['source']
    _awl, _ai = _args['whitelist'], _args['interval']

    # build intermediate, or staging, and completed files location
    currentdir = os.getcwd()
    stagingdir = os.path.join(_ad, 'staging', 'blelc', str(_as))
    outputdir = os.path.join(_ad, 'queue', '1', 'blelc', str(_as))
    os.makedirs(stagingdir, exist_ok=True)
    os.makedirs(outputdir, exist_ok=True)
    _banner_dirs(currentdir, stagingdir, outputdir)

    # thread: BLE reader, see th_ble.py
    source_queue = queue.Queue()
    with open(_awl, 'r') as fy:
        loggers_wl_case = yaml.load(fy, Loader=yaml.FullLoader)
        loggers_wl = {k.lower(): v for k, v in loggers_wl_case.items()}

    reader = ReadBLELCMessagesForever(source_queue, stagingdir, _as, loggers_wl, _ai)
    reader.start()

    # thread: master, dequeues reader msgs not atomically
    # sleep(1) ensures unique timestamped names, do not remove
    while True:
        _sleep_align_wallclock(_ai)
        while source_queue.qsize():
            msg = source_queue.get_nowait()
            time.sleep(1)

            # build staging_file containing zipped BLE data
            now = datetime.datetime.utcnow()
            ts = now.strftime('%Y%m%dT%H%M%SZ.xz')
            staging_file = os.path.join(stagingdir, ts)
            with lzma.open(staging_file, 'wb') as zipped:
                with open(msg, 'rb') as ble_data:
                    zipped.write(ble_data.read())

            # rename staging_file to queue_file
            queue_file = os.path.join(outputdir, ts)
            os.rename(staging_file, queue_file)
            s = 'dequeued {} -> {}'.format(msg, queue_file)
            print_mas(s, 'y')
            sys.stdout.flush()


if __name__ == '__main__':
    # for dev, Pycharm run configuration passes main() args
    main()

    # for production
    # while True:
    #     try:
    #         try:
    #             main()
    #             sys.exit()
    #         except KeyboardInterrupt:
    #             sys.exit()
    #     except Exception as ex:
    #         print('Error during BLE main loop')
    #         traceback.print_exc(file=sys.stdout)
    #         sys.stdout.flush()
    #         time.sleep(5)





