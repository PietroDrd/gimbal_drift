import sys
import time
import serial
import signal
import struct
import datetime
import threading
import numpy as np

format_number = 7

def signal_handler(signal, frame):
    global thread
    thread.exit()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Function to generate the output file name
def generate_file_name(format_number):
    now = datetime.datetime.now()
    file_name = now.strftime(f"%Y_%m_%d_%H.%M.%S_format{format_number}.csv")
    return file_name

file_name = generate_file_name(format_number)

s = serial.Serial('/dev/ttyACM0', 115200)
# CHUNKSIZE = 10
# BYTES_FORMAT = '<HIHH'
# CHANNELS = 4
# CHANNELS_TO_PLOT = [0,1,2,3]
CHUNKSIZE_LC = 16
BYTES_FORMAT_LC = '<xxxxIII'
CHANNELS_LC = 3
SEQUENCE_LC = b'\xff\xfc\xff\xfc'
# CHANNELS_TO_PLOT = [0,1,2]
CHUNKSIZE = 16
BYTES_FORMAT = '<HIHII'
CHANNELS = 5
CHANNELS_TO_PLOT = [1,2,3,4]
SAMPLES = 100
CHUNKS = 1
PLOT_GET = 1000
PLOT_BUFFER = 10000
DOWNSAMPLE = 1

class SerialReader(threading.Thread):
    """ Defines a thread for reading and buffering serial data.
    By default, about 5MSamples are stored in the buffer.
    Data can be retrieved from the buffer by calling get(N)"""
    def __init__(self, port, chunkSize=10, chunks=100):
        threading.Thread.__init__(self)
        # circular buffer for storing serial data until it is
        # fetched by the GUI
        self.buffer = np.empty((0, CHANNELS), dtype=np.uint32)
       
        self.channels = CHANNELS    # number of data channels to read
        self.channelsLC = CHANNELS_LC    # number of data channels to read
        self.channels_to_plot = CHANNELS_TO_PLOT    # numbers of data channels to process
        self.nc = len(self.channels_to_plot)
        self.dt = None              # dt of a single sample
        self.chunks = chunks        # number of chunks to store in the buffer
        self.chunkSize = chunkSize  # size of a single chunk (items, not bytes)
        self.chunkSizeTH = chunkSize  # size of a single chunk (items, not bytes)
        self.chunkSizeLC = CHUNKSIZE_LC  # size of a single chunk (items, not bytes) in LOAD CELL mode
        self.bytesFmt = BYTES_FORMAT
        self.bytesFmtTH = BYTES_FORMAT
        self.bytesFmtLC = BYTES_FORMAT_LC
        self.ptr = 0                # pointer to most (recently collected buffer index) + 1
        self.port = port            # serial port handle
        self.sps = 0.0              # holds the average sample acquisition rate
        self.loadcellFlag = False   # are we in LOAD CELL mode?
        self.exitFlag = False
        self.exitMutex = threading.Lock()
        self.dataMutex = threading.Lock()
        self.loadcellMutex = threading.Lock()

    def run(self):
        exitMutex = self.exitMutex
        dataMutex = self.dataMutex
        # buffer = self.buffer
        port = self.port
        count = 0
        sps = None
        lastUpdate = time.perf_counter()
       
        with open(file_name, 'ab') as file:
            while True:
                # see whether an exit was requested
                with exitMutex:
                    if self.exitFlag:
                        # self.port.close()
                        break
            
                # read one full chunk from the serial port
                # resp = s.readlines(self.chunkSize)
                # resp = s.readlines(self.chunks)
                # resp2 = np.array([r.decode('ascii').rstrip().split(',') for r in resp], dtype=np.uint32)
                # ----
                with self.loadcellMutex:
                    if self.loadcellFlag == True:
                        self.chunksize = self.chunkSizeLC
                        self.bytesFmt = self.bytesFmtLC
                    else:
                        self.chunksize = self.chunkSizeTH
                        self.bytesFmt = self.bytesFmtTH
                    # print("Got the lock", self.chunkSize, self.bytesFmt)
                in_waiting = s.in_waiting
                if in_waiting == self.chunkSize:
                    resp = s.read(size=self.chunkSize)
                    # print(f"Read {self.chunksize}")
                    # print(resp)
                    if self.match_bytes(resp[0:4]):
                        self.handle_messages(resp)
                        with self.loadcellMutex:
                            if self.loadcellFlag == False:
                                continue
                        # handle_messages(int.from_bytes(resp, 'big'))
                    # else:
                    if resp[0:4] == SEQUENCE_LC:
                        resp2 = [struct.unpack(self.bytesFmtLC, resp)]
                    else:
                        resp2 = [struct.unpack(self.bytesFmtTH, resp)]
                    # resp2 = [struct.unpack(self.bytesFmt, resp)]
                    resp2 = np.array(resp2, dtype=np.uint32)
                    np.savetxt(file, resp2, delimiter=',', fmt='%d')
                    # print("r2", resp2)
                elif in_waiting < self.chunkSize * self.chunks:
                # if in_waiting < self.chunkSize:
                    continue
                elif in_waiting % self.chunkSize * self.chunks == 0:
                # elif in_waiting % self.chunkSize == 0:
                    resp = s.read(size=in_waiting)
                    # print(resp)
                    resp2 = []
                    for i in range(0, in_waiting // self.chunkSize):
                        r = resp[i*self.chunkSize : (i+1)*self.chunkSize]
                        # if match_bytes(int.from_bytes(r[0:3], 'little')):
                        # print(r)
                        if self.match_bytes(r[0:4]):
                            self.handle_messages(r)
                            with self.loadcellMutex:
                                if self.loadcellFlag == False:
                                    continue
                            # handle_messages(int.from_bytes(r, 'big'))
                            # continue
                        # else:
                        if resp[0:4] == SEQUENCE_LC:
                            resp2.append(struct.unpack(self.bytesFmtLC, r))
                        else:
                            resp2.append(struct.unpack(self.bytesFmtTH, r))
                        # resp2.append(struct.unpack(self.bytesFmt, r))
                    # resp2 = [struct.unpack(BYTES_FORMAT, resp[i*self.chunkSize : (i+1)*self.chunkSize]) for i in range(0, in_waiting // self.chunkSize)]
                    # resp2 = [struct.unpack('<HIHH', resp[i*self.chunkSize : (i+1)*self.chunkSize]) for i in range(0, in_waiting // self.chunkSize)]
                    resp2 = np.array(resp2, dtype=np.uint32)
                    np.savetxt(file, resp2, delimiter=',', fmt='%d')
                    # print("r2", resp2)
                else:
                # elif in_waiting > self.chunkSize * self.chunks:
                    print(f"Skipping {in_waiting} bytes")
                    s.reset_input_buffer()
                    continue
                # ----
                # keep track of the acquisition rate in bytes-per-second
                # count += self.chunkSize * self.chunks
                # now = time.perf_counter()
                # dt = now-lastUpdate
                # if dt > 1.0:
                #     # sps is an exponential average of the running sample rate measurement
                #     if sps is None:
                #         sps = count / dt
                #     else:
                #         sps = sps * 0.9 + (count / dt) * 0.1
                #     count = 0
                #     lastUpdate = now
            
                # # write the new chunk into the circular buffer
                # # and update the buffer pointer
                # with dataMutex:
                #     # print("Got dataMutex run")
                #     # self.buffer = np.vstack((self.buffer, resp2))
                #     if sps is not None:
                #         self.sps = sps
                #         if self.sps > 0:
                #             self.dt = 1/self.sps

    def match_bytes(self, sequence):
        # print("match", sequence)
        if sequence == b'\xff\xff\x00\x00':
            return True
        return False

    def handle_messages(self, sequence):
        # print("match", sequence)
        if sequence[0:4] != b'\xff\xff\x00\x00':
            raise ValueError(f"Sequence '{sequence}' doesn't start with 0xffff, how did we get here?")
        # elif sequence == 0xffff0000f0ff0000f0ff0000ffff0000:
        elif sequence == b'\xff\xff\x00\x00\xf0\xff\x00\x00\xf0\xff\x00\x00\xff\xff\x00\x00':
            print("Sending STOP command")
            with self.loadcellMutex:
                self.loadcellFlag = False
        # elif sequence == 0xffff0000f1ff0000f1ff0000ffff0000:
        elif sequence == b'\xff\xff\x00\x00\xf1\xff\x00\x00\xf1\xff\x00\x00\xff\xff\x00\x00':
            print("Sending ARM command")
            with self.loadcellMutex:
                self.loadcellFlag = False
        # elif sequence == 0xffff0000fcff0000fcff0000ffff0000:
        elif sequence == b'\xff\xff\x00\x00\xfc\xff\x00\x00\xfc\xff\x00\x00\xff\xff\x00\x00':
            print("Reading LOAD CELL")
            with self.loadcellMutex:
                self.loadcellFlag = True
                # print("Got the lock")
        # elif sequence == 0xffff0000f2ff0000f2ff0000ffff0000:
        elif sequence[0:6] == b'\xff\xff\x00\x00\xf2\xff' and sequence[8:10] == b'\xf2\xff' and sequence[12:16] == b'\xff\xff\x00\x00':
            thr_set = int.from_bytes(sequence[6:8], 'little')
            print("Set throttle to", thr_set)
            with self.loadcellMutex:
                self.loadcellFlag = False
        else:
            print("sequence", sequence)
    
    def exit(self):
        """ Instruct the serial thread to exit."""
        with self.exitMutex:
            self.exitFlag = True

# Create thread to read and buffer serial data.
thread = SerialReader(s, chunkSize=CHUNKSIZE, chunks=CHUNKS)
thread.start()
