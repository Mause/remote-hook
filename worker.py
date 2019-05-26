import time

import schedule

from main import REDIS


def keepalive():
    print('thump-thump')
    REDIS.publish("watch-keepalive", 'thump-thump')


def main():
    schedule.every(30).seconds.do(keepalive)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
