import sys

from kr_event import kr_event
from kr_notice import kr_notice
from kr_update import kr_update
from lab_notice import lab_notice
from lab_update import lab_update

if __name__ == '__main__':
    argv = sys.argv
    del argv[0]
    if len(argv) >= 6:
        kr_notice(argv[0])
        kr_update(argv[1], argv[2])
        kr_event(argv[3])
        lab_notice(argv[4])
        lab_update(argv[5])
