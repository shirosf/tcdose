#!/usr/bin/python
import serial
import sys
import time
import getopt

STX=0x02
ETX=0x03
ACK=0x06

class tc300_serial(object):
    def __init__(self, spdev):
        self.srp=serial.Serial(spdev, 115200, timeout=1)

    def send_data(self, data):
        parity=0
        self.srp.write(chr(STX))
        for i in data:
            self.srp.write(i)
            parity^=ord(i)
        self.srp.write(chr(ETX))
        ps="%02X" % parity
        for i in ps:
            self.srp.write(i)

    def close(self):
        self.srp.close()

    def rec_data_tout(self):
        res=[]
        while True:
            x=self.srp.read()
            if len(x)==0: break
            res.append(x)
        if ord(res[0])!=STX: return NULL
        rss=''
        for i in res[1:]:
            if ord(i)==ETX: break
            rss+=i
        parity=0
        for i in rss:
            parity^=ord(i)
        if parity!=int(''.join(res[len(res)-2:]), base=16): return None
        return rss

    def send_wait_ack(self, data):
        self.send_data(data)
        x=self.srp.read()
        if len(x)==0: return 1
        if x!=ACK: return -1
        return 0

    def print_dose_rate(self, data):
        if data[0:2]!='01':
            print data
            return
        x=int(data[2:], base=16)
        print 0.001 * x

    def print_spectrum(self, data):
        if data[0:2]!='08':
            print data[0:2]
            return
        reso=3.0/512.0
        for i in range((len(data)-2)/4):
            sd=int(data[2+i*4:6+i*4], base=16)
            print "%5.3f, %d" % (reso*i, sd)

def doserate(tsrp, measure_time, rtimes, interval=3):
    tsrp.send_wait_ack('8B0')

    if measure_time==30:
        tsrp.send_wait_ack('802')
    elif measure_time==10:
        tsrp.send_wait_ack('801')
    elif measure_time==3:
        tsrp.send_wait_ack('800')
    else:
        print "not supported"
        return -1

    for count in range(rtimes):
        tsrp.send_data('01')
        rd=tsrp.rec_data_tout()
        tsrp.print_dose_rate(rd)
        tsrp.send_data('02')
        time.sleep(interval)

    return 0

def spectrum(tsrp, rtimes, interval=3, clear=False):
    tsrp.send_wait_ack('8B1')
    if clear:
        tsrp.send_wait_ack('88')
    for count in range(rtimes):
        tsrp.send_data('08')
        rd=tsrp.rec_data_tout()
        tsrp.print_spectrum(rd)
        print
        time.sleep(interval)

def usage():
    print "tcdose.py [options] doserate|spectrum"
    print "options"
    print "  -t|--times value: set measurement times, default=1"
    print "  -i|--interval value: set interval seconds, default=3"
    print "  -w|--mwindow [3|10|30]: set dose measurement time-window, default=30(seconds)"
    print "  -c|--clear: clear spectrum date at the start"
    print "  -d|--device serial_device: set serial port device, default=/dev/ttyACM0"
    print "  -h|--help: print this help"

if __name__ == "__main__":

    try:
        opts, args = getopt.getopt(sys.argv[1:], "ht:i:cw:d:",
	      ["help","times=","interval=","mwindow=","clear","device="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    init_clear=False
    interval_sec=3
    measure_times=1
    measure_window=30
    serial_device='/dev/ttyACM0'

    for o, a in opts:
    	if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-c", "--clear"):
            init_clear=True
        if o in ("-i", "--interval"):
            interval_sec=int(a)
        if o in ("-t", "--times"):
            measure_times=int(a)
        if o in ("-w", "--mwindow"):
            measure_window=int(a)
        if o in ("-d", "--device"):
            serial_device=a

    if len(args)==0:
        usage()
        sys.exit(2)


    tsrp=tc300_serial(serial_device)
    
    if args[0]=='spectrum':
        spectrum(tsrp, measure_times, interval_sec, clear=init_clear)
    elif args[0]=='doserate':
        doserate(tsrp, measure_window, measure_times, interval_sec)
    else:
        usage()
        sys.exit(2)

    tsrp.close()
    sys.exit(0)


