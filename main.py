#!/usr/bin/env python3    ¡¡¡ OK !!!
from __future__ import print_function
import matplotlib as mp
import datetime

mp.use('TkAgg')
mp.use('Agg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
from matplotlib.widgets import Cursor
from scipy import fftpack, arange, signal
import numpy as np
from tkinter import *
from pylab import *
import tkinter as Tk
from tkinter import Text
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
import serial
import serial.tools.list_ports
import time
from scipy.signal import hilbert
from scipy.stats import kurtosis
from numpy import linalg as nl

# default settings for radiobuttons (start at 1) and spinboxes (start at 0)
# change these values so you have what you want at startup
defsps = 2
defchans = 3
defsens = 2
defsamplen = 3
defpltype = 1
deffrange = 5
deftwflen = 2
datapath = "C:/Baart/data/"
plotpath = "C:/Baart/plots/"

baud_rate = 525000
num_points = 16384  # Amount of samples to read.
sample_rate = 5000  # Sampling frequency (SPS).
fmax = sample_rate / 2
channels = 3  # number of ADC channels
adc_mVolts = 3300
adc_bits = 12
adc_res = adc_mVolts / (2 ** adc_bits) / 1000  # 3.3V 12 bit ADC.
acc_sens = 300  # 300 mV/g
max_freq = 1000  # Maximum signal frequency, X and Y axis (accelerometer).
fftlen = 8192  # Samples to display FFT
twflen = 2048  # twf data points to display
twopi = 6.28318530717
cf = 1.633  # compensation factor for hann window
gconst = 9806.65
getchans = 3
ptype = 1
scales = (0.00001, 0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 1.5, 2, 2.5, 5, 7.5, 10,
          12.5, 15, 20, 25, 30, 35, 40, 45, 50, 75, 100, 150, 200, 300)
channel_1 = []  # Global channel_1
channel_2 = []  # Global channel_2
channel_3 = []  # Global channel_3
channel_4 = []  # Global channel_4
sequence = []

twf = []
ax = []  # acceleration FFT
vx = []  # velocity FFT
hx = []  # hilbert FFT
hx2 = []
sy = []  # Spectra Y axis points
hy = []  # hilbert Y axis points
ty = []  # Time Y axis points
plot_title = "Channel X"
fl = ""
ts = time.time()
g_date_time = datetime.datetime.fromtimestamp(ts).strftime('%d-%m-%Y %H:%M:%S')
t_timeout = 5  # Timeout time in seconds.

h = 10  # plot height
w = 10  # Plot width
mt = 22  # main title font height
st = 14  # sub title font height
xt = 12  # X axis title font height
yt = 12  # Y axis title font height


class Application:
    def __init__(self, parent):
        self.parent = parent
        self.frames()
        self.f_saved = True  # Sampled data saved
        menubar = Menu(root)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open Data", command=self.open_file)
        filemenu.add_command(label="Save Data", command=self.save_file)
        filemenu.add_command(label="Save Plot", command=self.save_plot)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        helpmenu = Menu(menubar, tearoff=0)
        helpmenu.add_command(label="About...", command=self.about)
        menubar.add_cascade(label="Help", menu=helpmenu)
        root.config(menu=menubar)
        root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        if (self.f_saved == False):
            if messagebox.askyesno("Quit", "Sampled data not saved. Do you still want to quit?"):
                root.destroy()
        else:
            root.destroy()

    def frames(self):
        global scales, h, w, mt, st, xt, yt, defsps, defchans, defsens, defsamplen, defpltype, deffrange, deftwflen
        px = 5
        py = 0
        frame1 = Tk.Frame(root, bd=5, relief='raised', borderwidth=1)
        frame2 = Tk.Frame(root, bd=5, relief='raised')

        self.note = ttk.Notebook(frame2)
        self.tab1 = ttk.Frame(self.note)
        self.tab2 = ttk.Frame(self.note)
        self.note.add(self.tab1, text=" Spectras ")
        self.note.add(self.tab2, text=" Configuration ")
        self.note.pack(side='top', fill='both', padx=5, pady=5)

        frame1.pack(side='left', fill='both', padx=5, pady=5)
        frame2.pack(side='right', fill='both', expand='true')

        tabControl = ttk.Notebook(frame1)  # Create Tab Control
        self.tab6 = ttk.Frame(tabControl)  # Create a tab
        tabControl.add(self.tab6, text='Data')  # Add the tab
        self.tab7 = ttk.Frame(tabControl)  # Add a second tab
        tabControl.add(self.tab7, text='ADC')  # Make second tab visible
        tabControl.pack(expand=1, fill="both")  # Pack to make visible
        data = ttk.Frame(self.tab6)
        data.grid(column=1, row=0, padx=8, pady=4)
        adc = ttk.Frame(self.tab7)
        adc.grid(column=1, row=0, padx=8, pady=4)

        button_scan = Tk.Button(adc, text="Scan ports", command=self.scan_ports, width=10)
        button_read = Tk.Button(adc, text="Read ADC", command=self.read_serial, width=10)
        adc_label1 = Tk.Label(adc, text="Serial Port:")
        adc_label2 = Tk.Label(adc, text="Samples per second:")
        adc_label3 = Tk.Label(adc, text="Data Sample Length:")
        adc_label4 = Tk.Label(adc, text="Accelerometer Sensitivity:")
        adc_label5 = Tk.Label(adc, text="Data Channels:")
        self.sel_port = ttk.Combobox(adc, textvariable='', state="readonly", width=8)
        portnames = self.scan_serial()
        self.sel_port['values'] = portnames
        if (portnames != []):
            self.sel_port.current(0)
        self.read_sps = ttk.Combobox(adc, textvariable='', state="readonly", width=8)
        self.read_sps['values'] = ('1000', '2000', '5000', '10000', '15000', '20000')
        self.read_sps.current(defsps)
        self.read_sens = ttk.Combobox(adc, textvariable='', state="readonly", width=8)
        self.read_sens['values'] = ('100 mV/g', '200 mV/g', '300 mV/g', '500 mV/g')
        self.read_sens.current(defsens)
        self.read_len = ttk.Combobox(adc, textvariable='', state="readonly", width=8)
        self.read_len['values'] = ('1024', '2048', '4096', '8192', '16384', '32768', '65536')
        self.read_len.current(defsamplen)
        self.adc_message = Text(adc, height=7, width=18)

        self.cget_var = Tk.IntVar()
        self.cget_var.set(defchans)
        self.cget_button1 = Tk.Radiobutton(adc, text="1 only",
                                           variable=self.cget_var, value=1, command=self.cget_sel)
        self.cget_button2 = Tk.Radiobutton(adc, text="1 & 2",
                                           variable=self.cget_var, value=2, command=self.cget_sel)
        self.cget_button3 = Tk.Radiobutton(adc, text="1, 2 & 3",
                                           variable=self.cget_var, value=3, command=self.cget_sel)
        self.cget_button4 = Tk.Radiobutton(adc, text="ALL 4",
                                           variable=self.cget_var, value=4, command=self.cget_sel)

        data_label1 = Tk.Label(data, text="Statistics:")
        data_label2 = Tk.Label(data, text="Plot Type:")
        data_label3 = Tk.Label(data, text="Plot Channel:")
        data_label4 = Tk.Label(data, text="Frequency Range:")
        data_label5 = Tk.Label(data, text="TWF Length:")
        self.data_message = Text(data, height=4, width=18)

        self.ptget_var = Tk.IntVar()
        self.ptget_var.set(defpltype)
        self.ptget_button1 = Tk.Radiobutton(data, text="Time Waveform",
                                           variable=self.ptget_var, value=1, command=self.ptget_sel)
        self.ptget_button2 = Tk.Radiobutton(data, text="Acceleration",
                                           variable=self.ptget_var, value=2, command=self.ptget_sel)
        self.ptget_button3 = Tk.Radiobutton(data, text="Velocity",
                                           variable=self.ptget_var, value=3, command=self.ptget_sel)
        self.ptget_button4 = Tk.Radiobutton(data, text="Demodulated",
                                           variable=self.ptget_var, value=4, command=self.ptget_sel)

        self.fmax_var = Tk.IntVar()
        self.fmax_var.set(deffrange)
        self.fmax_button1 = Tk.Radiobutton(data, text="0 - 25  Hz", variable=self.fmax_var, value=1,
                                           command=self.fmax_sel)
        self.fmax_button2 = Tk.Radiobutton(data, text="0 - 50  Hz", variable=self.fmax_var, value=2,
                                           command=self.fmax_sel)
        self.fmax_button3 = Tk.Radiobutton(data, text="0 - 100  Hz", variable=self.fmax_var, value=3,
                                           command=self.fmax_sel)
        self.fmax_button4 = Tk.Radiobutton(data, text="0 - 250  Hz", variable=self.fmax_var, value=4,
                                           command=self.fmax_sel)
        self.fmax_button5 = Tk.Radiobutton(data, text="0 - 500 Hz", variable=self.fmax_var, value=5,
                                           command=self.fmax_sel)
        self.fmax_button6 = Tk.Radiobutton(data, text="0 - 1000 Hz", variable=self.fmax_var, value=6,
                                           command=self.fmax_sel)
        self.fmax_button7 = Tk.Radiobutton(data, text="0 - 2500 Hz", variable=self.fmax_var, value=7,
                                           command=self.fmax_sel)
        self.fmax_button8 = Tk.Radiobutton(data, text="0 - 5000 Hz", variable=self.fmax_var, value=8,
                                           command=self.fmax_sel)
        self.fmax_button9 = Tk.Radiobutton(data, text="0 - 10000 Hz", variable=self.fmax_var, value=9,
                                           command=self.fmax_sel)
        self.twf_var = Tk.IntVar()
        self.twf_var.set(deftwflen)
        self.twf_button1 = Tk.Radiobutton(data, text="1024", variable=self.twf_var, value=1,
                                          command=self.twf_sel)
        self.twf_button2 = Tk.Radiobutton(data, text="2048", variable=self.twf_var, value=2,
                                          command=self.twf_sel)
        self.twf_button3 = Tk.Radiobutton(data, text="4096", variable=self.twf_var, value=3,
                                          command=self.twf_sel)
        self.twf_button4 = Tk.Radiobutton(data, text="8192", variable=self.twf_var, value=4,
                                          command=self.twf_sel)
        self.twf_button5 = Tk.Radiobutton(data, text="16384", variable=self.twf_var, value=5,
                                          command=self.twf_sel)
        self.chan_var = Tk.IntVar()
        self.chan_var.set(1)
        self.chan_button1 = Tk.Radiobutton(data, text="Channel 1",
                                           variable=self.chan_var, value=1, command=self.chan_sel)
        self.chan_button2 = Tk.Radiobutton(data, text="Channel 2",
                                           variable=self.chan_var, value=2, command=self.chan_sel)
        self.chan_button3 = Tk.Radiobutton(data, text="Channel 3",
                                           variable=self.chan_var, value=3, command=self.chan_sel)
        self.chan_button4 = Tk.Radiobutton(data, text="Channel 4",
                                           variable=self.chan_var, value=4, command=self.chan_sel)

        # ADC tab Grid
        button_scan.grid(row=0, column=0, padx=5, pady=25)
        adc_label1.grid(row=1, column=0, padx=5, pady=5)
        self.sel_port.grid(row=2, column=0, padx=5, pady=5)
        adc_label2.grid(row=3, column=0, padx=5, pady=5)
        self.read_sps.grid(row=4, column=0, padx=5, pady=5)
        adc_label3.grid(row=5, column=0, padx=5, pady=5)
        self.read_len.grid(row=6, column=0, padx=5, pady=5)
        adc_label4.grid(row=7, column=0, padx=5, pady=5)
        self.read_sens.grid(row=8, column=0, padx=5, pady=5)
        adc_label5.grid(row=9, column=0, padx=15, pady=15)

        self.cget_button1.grid(row=10, column=0, sticky="W", padx=px, pady=py)
        self.cget_button2.grid(row=11, column=0, sticky="W", padx=px, pady=py)
        self.cget_button3.grid(row=12, column=0, sticky="W", padx=px, pady=py)
        self.cget_button4.grid(row=13, column=0, sticky="W", padx=px, pady=py)
        self.adc_message.grid(row=14, column=0, padx=5, pady=25)
        button_read.grid(row=15, column=0, padx=5, pady=5)

        # Data tab Grid
        data_label1.grid(row=0, column=0, padx=5, pady=5)
        self.data_message.grid(row=1, column=0, padx=5, pady=5)
        data_label2.grid(row=2, column=0, padx=5, pady=5)
        self.ptget_button1.grid(row=3, column=0, sticky="W", padx=px, pady=py)
        self.ptget_button2.grid(row=4, column=0, sticky="W", padx=px, pady=py)
        self.ptget_button3.grid(row=5, column=0, sticky="W", padx=px, pady=py)
        self.ptget_button4.grid(row=6, column=0, sticky="W", padx=px, pady=py)


        data_label3.grid(row=9, column=0, padx=5, pady=5)
        self.chan_button1.grid(row=10, column=0, sticky="W", padx=px, pady=py)
        self.chan_button2.grid(row=11, column=0, sticky="W", padx=px, pady=py)
        self.chan_button3.grid(row=12, column=0, sticky="W", padx=px, pady=py)
        self.chan_button4.grid(row=13, column=0, sticky="W", padx=px, pady=py)
        data_label4.grid(row=15, column=0, padx=5, pady=5)
        self.fmax_button1.grid(row=16, column=0, sticky="W", padx=px, pady=py)
        self.fmax_button2.grid(row=17, column=0, sticky="W", padx=px, pady=py)
        self.fmax_button3.grid(row=18, column=0, sticky="W", padx=px, pady=py)
        self.fmax_button4.grid(row=19, column=0, sticky="W", padx=px, pady=py)
        self.fmax_button5.grid(row=20, column=0, sticky="W", padx=px, pady=py)
        self.fmax_button6.grid(row=21, column=0, sticky="W", padx=px, pady=py)
        self.fmax_button7.grid(row=22, column=0, sticky="W", padx=px, pady=py)
        self.fmax_button8.grid(row=23, column=0, sticky="W", padx=px, pady=py)
        self.fmax_button9.grid(row=24, column=0, sticky="W", padx=px, pady=py)
        data_label5.grid(row=25, column=0, padx=5, pady=5)
        self.twf_button1.grid(row=26, column=0, sticky="W", padx=px, pady=py)
        self.twf_button2.grid(row=27, column=0, sticky="W", padx=px, pady=py)
        self.twf_button3.grid(row=28, column=0, sticky="W", padx=px, pady=py)
        self.twf_button4.grid(row=29, column=0, sticky="W", padx=px, pady=py)
        self.twf_button5.grid(row=30, column=0, sticky="W", padx=px, pady=py)

        # Add Figures
        fig1 = Figure(figsize=(w, h))
        fig1.suptitle('Vibration Analysis', fontsize=mt)
        ax = fig1.add_subplot(1, 1, 1)
        ax.grid()  # Shows grid.
        self.canvas1 = FigureCanvasTkAgg(fig1, master=self.tab1)
        self.canvas1.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
        self.canvas1._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
        

    def read_serial(self):
        global sample_rate, fstep, twf, message, acc_sens, baud_rate, adc_bits, adc_mVolts, getchans, adc_res
        acc_sens = 300  # 300 mV/g
        adc_mVolts = 3300
        adc_bits = 12
        adc_res = adc_mVolts / (2 ** adc_bits) / 1000

        port = self.sel_port.get()

        message = "Port: {0} \n".format(port)
        self.show_message(self.adc_message, message)

        state_serial = False
        try:
            serial_avr = serial.Serial(port=port, baudrate=baud_rate,
                                       bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                                       stopbits=serial.STOPBITS_ONE, timeout=0)

            time.sleep(2)  # waiting the initialization...
            message = "Initializing... \n"
            self.show_message(self.adc_message, message)

            if (serial_avr.isOpen() == True):
                state_serial = True
            else:
                state_serial = False
        except (serial.SerialException, ValueError) as ex:
            messagebox.showerror("Result", "Can't open serial port: " + str(ex))

        if (state_serial == True):
            global num_points, channel_1, channel_2, channel_3, channel_4, max_freq, twflen, sequence, channels

            channel_1 = []
            channel_2 = []
            channel_3 = []
            channel_4 = []
            sequence = []
            buffer = []
            serial_avr.flushInput()
            serial_avr.flushOutput()

            values_received = []
            num_points = int(self.read_len.get())
            sen = self.read_sens.get()
            acc_sens = ((int)(sen[:3]))

            data_rxd = 0  # Received samples counter.
            sps = self.read_sps.get()

            if sps == '1000':
                sample_rate = 1000
                duration = num_points / sample_rate
                message = "Sampling time:\n{0:.2f} Seconds\nSending ENQ ...\n".format(duration)
                self.show_message(self.adc_message, message)
                serial_avr.write(b'ENQ1')
            elif sps == '2000':
                sample_rate = 2000
                duration = num_points / sample_rate
                message = "Sampling time:\n{0:.2f} Seconds\nSending ENQ ...\n".format(duration)
                self.show_message(self.adc_message, message)
                serial_avr.write(b'ENQ2')
            elif sps == '5000':
                sample_rate = 5000
                duration = num_points / sample_rate
                message = "Sampling time:\n{0:.2f} Seconds\nSending ENQ ...\n".format(duration)
                self.show_message(self.adc_message, message)
                serial_avr.write(b'ENQ3')
            elif sps == '10000':
                sample_rate = 10000
                duration = num_points / sample_rate
                message = "Sampling time:\n{0:.2f} Seconds\nSending ENQ ...\n".format(duration)
                self.show_message(self.adc_message, message)
                serial_avr.write(b'ENQ4')
            elif sps == '15000':
                sample_rate = 15000
                duration = num_points / sample_rate
                message = "Sampling time:\n{0:.2f} Seconds\nSending ENQ ...\n".format(duration)
                self.show_message(self.adc_message, message)
                serial_avr.write(b'ENQ5')
            else:
                sample_rate = 20000
                duration = num_points / sample_rate
                message = "Sampling time:\n{0:.2f} Seconds\nSending ENQ ...\n".format(duration)
                self.show_message(self.adc_message, message)
                serial_avr.write(b'ENQ6')

            serial_avr.write(b"\x7E")  # End of packet.

            global t_timeout
            timeout_state = False
            t0 = time.time()  # Start loop time stamp.
            tic = time.clock()
            while ((data_rxd < num_points) and (timeout_state == False)):
                if serial_avr.inWaiting():
                    lectura = serial_avr.read(serial_avr.inWaiting())
                    buffer += lectura

                if len(buffer) > 15:
                    try:
                        i = buffer.index(0x7E)
                    except (ValueError):
                        i = -1
                    if i >= 0:
                        packet = buffer[:i]
                        buffer = buffer[i + 1:]
                        values = [i for i in packet]

                        x = 0
                        while x < len(values):
                            if values[x] == 0x7D:
                                values_received.append(values[x + 1] ^ 0x20)
                                x = x + 1
                            else:
                                values_received.append(values[x])
                            x = x + 1

                        channel1 = (values_received[0] * 256) + values_received[1]
                        channel2 = (values_received[2] * 256) + values_received[3]
                        channel3 = (values_received[4] * 256) + values_received[5]
                        channel4 = (values_received[6] * 256) + values_received[7]
                        seq = (values_received[8] - 32)

                        channel_1.append(channel1)
                        channel_2.append(channel2)
                        channel_3.append(channel3)
                        channel_4.append(channel4)
                        sequence.append(seq)

                        values_received = []
                        t0 = time.time()
                        data_rxd += 1;

                # Check if t_timeout seconds have elapsed since time stamp t0
                if time.time() - t0 > t_timeout:
                    timeout_state = True

            if timeout_state == False:
                toc = time.clock()
                print(toc - tic)
                self.adc_message.config(state=Tk.NORMAL)  # Enable to modify
                self.adc_message.insert(Tk.END, "Sending EOT \n")
                root.update_idletasks()  # Needed to make message visible

                serial_avr.write(b'EOT')  # Stop data sampling.
                serial_avr.write(b"\x7E")  # End of packet.

                serial_avr.close()  # Close serial port.

                twf = channel_1[:]
                l = len(twf)
                self.f_saved = False  # Sampled data not saved
                ts = time.time()

                if getchans > 1:
                    channels = 2
                else:
                    channels = 1

                if getchans > 2:
                    channels = 3
                else:
                    channels = 2

                if getchans > 3:
                    channels = 4
                else:
                    channels = 3

                global g_date_time, fl, plot_title
                g_date_time = datetime.datetime.fromtimestamp(ts).strftime('%d-%m-%Y %H:%M:%S')
                fl = "ADC"
                self.chan_var.set(1)
                if l != 0:  # Apply only if data available
                    plot_title = "ADC - Channel 1"
                    message = "Success ...."
                    self.show_message(self.adc_message, message)
                    message = ""
                    self.chan_var.set(1)
                    self.fmax_var.set(5)
                    self.twf_var.set(2)
                    max_freq = 1000
                    twflen = 2048
                    fmax = sample_rate / 2
                    l = len(twf)
                    fstep = fmax / l / 2
                    self.set_button_states()
                    self.do_fft(chan_no=1)
                    self.prep_data()
                    self.plot()
            else:
                serial_avr.write(b'EOT')  # Stop data sampling.
                serial_avr.write(b"\x7E")  # End of packet.
                serial_avr.close()  # Close serial port.
                message = "Serial timeout\n"
                self.show_message(self.adc_message, message)

    def show_message(self, data_message, message):
        data_message.config(state=Tk.NORMAL)  # Enable to modify
        data_message.insert(Tk.END, message)
        data_message.config(state=Tk.DISABLED)  # Disable - Read only
        data_message.see("end")  # Show the "end" of text
        root.update_idletasks()  # Needed to make message visible

    def scan_ports(self):
        portnames = self.scan_serial()
        self.sel_port['values'] = portnames
        if portnames != []:
            self.sel_port.current(0)

    def do_fft(self, chan_no):

        global twf, ax, vx, hx, sy, ty, hy, plot_title, l, fstep, tmp, message, cf, sample_rate, adc_mVolts, \
            adc_res, adc_bits, acc_sens, h2, sy, fmax

        tl = len(twf)
        fstep = fmax / (tl / 2)
        tmp = [0] * tl
        bias = np.mean(twf)

        for i in range(tl):
            twf[i] = (twf[i] - bias) * adc_res * (1000 / acc_sens)
            tmp[i] = twf[i] * twf[i]

        k = kurtosis(twf) + 3  # kurtosis (add 3 for pearsons)
        r = np.sqrt(np.mean(tmp))  # rms value
        p = np.sqrt(np.amax(tmp))  # peak value (may be pos or neg hence sqr then sqrt
        c = p / r  # crest factor

        message += " Kurtosis: {0:.3f}\n".format(k)
        message += " RMS     : {0:.3f}\n".format(r)
        message += " Peak    : {0:.3f}\n".format(p)
        message += " Crest   : {0:.3f}\n".format(c)

        self.data_message.delete('1.0', END)
        self.data_message.insert(END, message)

        m = int(tl / 2)
        t = 1.0 / sample_rate
        w = signal.hann(tl, sym=False)  # Hann (Hanning) window

        ty = np.linspace(0, tl / 5, tl)
        sy = np.linspace(0.0, 1.0 / (2.0 * t), m)
        hy = np.linspace(0.0, 1.0 / (2.0 * t), m - 2)
        lhy = len(hy)

        ax = np.abs(fftpack.rfft(twf * w) * (2 / tl) * cf)
        ax = ax[:int(tl / 2)]
        for i in range(0, 5):
            ax[i] = 0

        vx = [0] * m
        for i in range(5, m):
            vx[i] = ((ax[i] * gconst) / (twopi * sy[i]))  # calculate velocity

        nt = len(twf)
        hilt = hilbert(twf[::])
        y = np.abs(hilt) ** 2
        y = y - np.mean(y)
        y = np.abs(np.fft.rfft(y)) / nt
        hx[:] = 2 * y[1:lhy + 1]

        analy = signal.hilbert(twf[::])
        y = abs(analy[0:m])
        sig_f = abs(np.abs(fftpack.rfft(y)))
        h2 = np.zeros(len(sig_f))  # new line
        h2 = sig_f / (nl.norm(sig_f))
        h2[0] = 0

    def prep_data(self):

        global twf, ax, vx, hx, sy, ty, hy, plot_title, max_freq, twflen, fstep,\
            tmp, h, w, mt, st, xt, yt, h2, sy, ptype, ymin, yscale, px, py, ylab, xlab, pxmax

        fft_pts = (int)(max_freq / fstep)
        tim = 0

        if ptype == 1:
            px = ty[0:twflen]
            py = twf[0:twflen]
            ylab = "Acceleration - g's"
            xlab = "Time - milliseconds"
            pxmax = (1 / 5 * twflen)
            tim = 1

        elif ptype == 2:
            px = sy[0:fft_pts]
            py = ax[0:fft_pts]
            ylab = "Acceleration - g's"
            xlab = "Frequency - Hz"
            pxmax = max_freq

        elif ptype == 3:
            px = sy[0:fft_pts]
            py = vx[0:fft_pts]
            ylab = "Velocity - mm/s"
            xlab = "Frequency - Hz"
            pxmax = max_freq

        elif ptype == 4:
            px = hy[0:fft_pts]
            py = hx[0:fft_pts]
            ylab = "Acceleration - g's"
            xlab = "Frequency - Hz"
            pxmax = max_freq

        yscale = 300
        ymax = 0
        ymin = 0
        pts = (len(py))
        for i in range(pts):
            if py[i] > ymax:
                ymax = py[i]
            if py[i] < ymin:
                ymin = py[i]

        if 0 - ymin > ymax:
            ymax = 0 - ymin

        for i in range(29):
            if ymax < scales[i]:
                break

        yscale = scales[i]

        if tim == 1:
            ymin = 0 - yscale
        else:
            ymin = 0

    def plot(self):
        global ymin, yscale, px, py, ylab, xlab, pxmax
        ax, = self.canvas1.figure.get_axes()
        ax.clear()
        ax.set_ylim(ymin, yscale)
        #cursor = SnaptoCursor(ax, px, py) #these two lines should connect the plot to an interractive cursor
        #self.canvas1.mpl_connect('motion_notify_event', cursor.mouse_move) # as of yet, I cant get them to work.
        ax.plot(px, py, linewidth=0.5, color='r')
        ax.grid()
        ax.set_title(plot_title, fontsize=st)
        ax.set_ylabel(ylab, fontsize=yt)
        ax.set_xlabel(xlab, fontsize=xt)
        ax.set_xlim(xmin=0, xmax=pxmax)
        self.canvas1.draw()


    def ptget_sel(self):
        global ptype
        ptype = self.ptget_var.get()
        self.prep_data()
        self.plot()

    def cget_sel(self):
        global getchans
        getchans = self.cget_var.get()

    def chan_sel(self):
        global twf, channel_1, channel_2, channel_3, channel_4, plot_title, message
        chan_no = self.chan_var.get()

        if chan_no == 1:
            twf = channel_1[:]
            plot_title = fl + " - Channel 1"
            message = ""
        elif chan_no == 2:
            twf = channel_2[:]
            plot_title = fl + " - Channel 2"
            message = ""
        else:
            twf = channel_3[:]
            plot_title = fl + " - Channel 3"
            message = ""

        self.do_fft(chan_no)
        self.prep_data()
        self.plot()

    def twf_sel(self):
        global twflen, l
        twfval = self.twf_var.get()

        if twfval == 1:
            twflen = 1024
        elif twfval == 2:
            twflen = 2048
        elif twfval == 3:
            twflen = 4096
        elif twfval == 4:
            twflen = 8192
        else:
            twflen = 16384

        if (len(twf) != 0):  # Apply only if data available
            self.prep_data()
            self.plot()

    def fmax_sel(self):
        global max_freq
        adc = self.fmax_var.get()

        if adc == 1:
            max_freq = 25
        elif adc == 2:
            max_freq = 50
        elif adc == 3:
            max_freq = 100
        elif adc == 4:
            max_freq = 250
        elif adc == 5:
            max_freq = 500
        elif adc == 6:
            max_freq = 1000
        elif adc == 7:
            max_freq = 2500
        elif adc == 8:
            max_freq = 5000
        else:
            max_freq = 10000

        if (len(twf) != 0):  # Apply only if data available
            self.prep_data()
            self.plot()

    def open_file(self):

        global fl
        yup = 0

        ftypes = [('TWF files', '*.twf'), ('DAT files', '*.dat')]
        fl = filedialog.askopenfilename(initialdir=datapath,
                                        title="Open", filetypes=ftypes)

        if fl.find('.twf') > 0:
            self.open_twf(fl)
        elif fl.find('.TWF') > 0:
            self.open_twf(fl)
        elif fl.find('.dat') > 0:
            self.open_dat(fl)
        elif fl.find('.DAT') > 0:
            self.open_dat(fl)

    def clear(self):
        ax, = self.canvas1.figure.get_axes()
        ax.clear()
        ax, = self.canvas2.figure.get_axes()
        ax.clear()
        ax, = self.canvas3.figure.get_axes()
        ax.clear()
        ax, = self.canvas4.figure.get_axes()
        ax.clear()

    def open_dat(self, filnam):

        global sample_rate, channel_1, channel_2, channel_3, channel_4, fmax, fstep, plot_title, message, \
            fl, max_freq, twflen, twf, acc_sens, channels, adc_mVolts, adc_bits, adc_res

        sample_rate = 52734
        acc_sens = 100
        channels = 1
        adc_mVolts = 3300
        adc_bits = 24
        adc_res = adc_mVolts / (2 ** adc_bits) / 1000
        bias = 1.65

        tic = time.clock()
        if filnam != '':

            sample_array = np.genfromtxt(fl, delimiter="\t")

            temp = sample_array[:, 0]
            channel_1 = [(i + bias) / adc_res for i in temp]

            temp = sample_array[:, 1]
            channel_2 = [(i + bias) / adc_res for i in temp]
            if (channel_2[0] > 0):
                self.chan_button2.configure(state=NORMAL)
                channels += 1
            else:
                self.chan_button2.configure(state=DISABLED)

            temp = sample_array[:, 2]
            channel_3 = [(i + bias) / adc_res for i in temp]
            if (channel_2[0] > 0):
                self.chan_button3.configure(state=NORMAL)
                channels += 1
            else:
                self.chan_button3.configure(state=DISABLED)

            temp = sample_array[:, 3]
            channel_4 = [(i + bias) / adc_res for i in temp]
            if (channel_4[0] > 0):
                self.chan_button4.configure(state=NORMAL)
                channels += 1
            else:
                self.chan_button4.configure(state=DISABLED)

            fmax = sample_rate / 2
            twf = channel_1[:]
            plot_title = fl + " - Channel 1"
            message = ""
            self.set_button_states()
            self.chan_var.set(1)
            self.fmax_var.set(6)
            self.twf_var.set(2)
            max_freq = 1000
            twflen = 2048
            self.do_fft(chan_no=1)
            self.prep_data()
            self.plot()
            toc = time.clock()
            #print(toc - tic)

    def open_twf(self, filnam):
        global sample_rate, channel_1, channel_2, channel_3, channel_4, l, twf, fstep, message, plot_title, \
            fl, fmax, acc_sens, channels, num_points, max_freq, twflen, adc_res, adc_bits, adc_mVolts
        tic = time.clock()
        if filnam != '':
            arch = open(filnam, "r")
            data_arch = arch.read()
            chan = self.extract_by_tag(data_arch, 'nc')
            channels = int(chan[0])
            num_samples = self.extract_by_tag(data_arch, 'nd')
            num_points = int(num_samples[0])
            samp_rate = self.extract_by_tag(data_arch, 'sr')
            samp_rate = self.extract_by_tag(data_arch, 'sr')
            sample_rate = int(samp_rate[0])
            sens = self.extract_by_tag(data_arch, 'as')
            acc_sens = int(sens[0])
            volts = self.extract_by_tag(data_arch, 'av')
            adc_mVolts = int(volts[0])
            bits = self.extract_by_tag(data_arch, 'ab')
            adc_bits = int(bits[0])
            adc_res = adc_mVolts / (2 ** adc_bits) / 1000  # 3.3V 12 bit ADC.

            channel_1 = self.extract_by_tag(data_arch, 'L1')
            if channels > 1:
                channel_2 = self.extract_by_tag(data_arch, 'L2')
                self.chan_button2.configure(state=NORMAL)
            else:
                self.chan_button2.configure(state=DISABLED)

            if channels > 2:
                channel_3 = self.extract_by_tag(data_arch, 'L3')
                self.chan_button3.configure(state=NORMAL)
            else:
                self.chan_button3.configure(state=DISABLED)

            if channels > 3:
                channel_4 = self.extract_by_tag(data_arch, 'L4')
                self.chan_button4.configure(state=NORMAL)
            else:
                self.chan_button4.configure(state=DISABLED)

            self.set_button_states()
            sample_rate = int(samp_rate[0])
            fmax = sample_rate / 2
            twf = channel_1[:]
            plot_title = fl + " - Channel 1"
            message = ""
            self.chan_var.set(1)
            self.fmax_var.set(6)
            self.twf_var.set(2)
            max_freq = 1000
            twflen = 2048
            self.do_fft(chan_no=1)
            self.prep_data()
            self.plot()
            toc = time.clock()
            #print(toc - tic)

    def save_file(self):
        ftypes = [('TWF files', '*.twf')]
        savefile = filedialog.asksaveasfilename(initialdir=datapath,
                                                title="Save As", filetypes=ftypes)

        if savefile != '':
            if savefile.find('.twf') < 1:
                savefile += '.twf'
            global channel_1, channel_2, channel_3, channel_4
            if len(channel_1) > 0:
                self.record(channel_1, channel_2, channel_3, channel_4, savefile)
                self.f_saved = True  # Sampled data saved
            else:
                message = "No sampled data to save\n"
                self.show_message(self.data_message, message)

    def set_button_states(self):
        global sample_rate, num_points

        maxf = sample_rate / 2

        if maxf > 500:
            self.fmax_button5.configure(state=NORMAL)
        else:
            self.fmax_button5.configure(state=DISABLED)
        if maxf > 1000:
            self.fmax_button6.configure(state=NORMAL)
        else:
            self.fmax_button6.configure(state=DISABLED)
        if maxf > 2500:
            self.fmax_button7.configure(state=NORMAL)
        else:
            self.fmax_button7.configure(state=DISABLED)
        if maxf > 5000:
            self.fmax_button8.configure(state=NORMAL)
        else:
            self.fmax_button8.configure(state=DISABLED)
        if maxf > 10000:
            self.fmax_button9.configure(state=NORMAL)
        else:
            self.fmax_button9.configure(state=DISABLED)

        if num_points > 1024:
            self.twf_button2.configure(state=NORMAL)
        else:
            self.twf_button2.configure(state=DISABLED)
        if num_points > 2048:
            self.twf_button3.configure(state=NORMAL)
        else:
            self.twf_button3.configure(state=DISABLED)
        if num_points > 4096:
            self.twf_button4.configure(state=NORMAL)
        else:
            self.twf_button4.configure(state=DISABLED)
        if num_points > 8192:
            self.twf_button5.configure(state=NORMAL)
        else:
            self.twf_button5.configure(state=DISABLED)

    def save_plot(self):
        ftypes = [('Portable Network Graphics', '*.png')]

        savefile = filedialog.asksaveasfilename(initialdir=plotpath,
                                                title="Save As", filetypes=ftypes)

        if savefile.find('.png') < 1:
            savefile += '.png'

        plt = self.canvas1.figure
        plt.savefig(savefile)

    def zoom_plot(self):

        curtab = self.note.index(self.note.select())


    def scan_serial(self):
        portnames = []
        ports = (list(serial.tools.list_ports.comports()))
        for index in range(len(ports)):
            portnames.append(ports[index][0])
        return portnames

    def simpleParse(self, mainString, beginString, endString):
        posBeginString = mainString.find(beginString) + len(beginString)
        posEndString = mainString.find(endString)
        result = mainString[posBeginString:posEndString]
        return result

    def extract_by_tag(self, data_arch, tag):
        beginString = '<' + tag + '>'
        endString = '</' + tag + '>'
        str_parse = self.simpleParse(data_arch, beginString, endString)
        str_channel = str_parse.split(',')
        channel = []
        n = len(str_channel)
        for i in range(n):
            channel.append(int(str_channel[i]))
        return channel

    def conv_str_tag(self, channel, tag):
        n = len(channel)
        s_channel = '<' + tag + '>'
        for i in range(n - 1):
            s_channel = s_channel + str(channel[i]) + ','
        s_channel = s_channel + str(channel[n - 1]) + '</' + tag + '>'
        return s_channel

    def record(self, chan_1, chan_2, chan_3, chan_4, f_name):
        global channels, num_points, sample_rate, g_date_time, acc_sens, adc_mVolts, adc_bits

        str_channel = ''
        str_channel += self.conv_str_tag(chan_1, 'L1') + '\n'
        if channels > 1:
            str_channel += self.conv_str_tag(chan_2, 'L2') + '\n'
        if channels > 2:
            str_channel += self.conv_str_tag(chan_3, 'L3') + '\n'
        if channels > 3:
            str_channel += self.conv_str_tag(chan_4, 'L4') + '\n'

        str_aux = ''
        str_aux += '<nc>{0}</nc>'.format(channels) + '\n'
        str_aux += '<nd>' + str(num_points) + '</nd>' + '\n'
        str_aux += '<sr>' + str(sample_rate) + '</sr>' + '\n'
        str_aux += '<ts>' + str(g_date_time) + '</ts>' + '\n'
        str_aux += '<as>{0}</as>'.format(acc_sens) + '\n'
        str_aux += '<av>{0}</av>'.format(adc_mVolts) + '\n'
        str_aux += '<ab>{0}</ab>'.format(adc_bits) + '\n'

        ext = f_name[-4:]
        if ext != ".twf" or ext != ".TWF":
            f_name += ".twf"

        arch = open(f_name, "w")
        arch.write(str_aux)
        arch.write(str_channel)
        arch.close()

    def about(self):
        filewin = Toplevel(root)

class SnaptoCursor:
    def __init__(self, a, x, y):
        self.ax = a
        self.lx = a.axhline(color='g')  # the horiz line
        self.ly = a.axvline(color='g')  # the vert line
        self.x = x
        self.y = y
        self.txt = a.text( 0.7, 0.9, '', transform=a.transAxes)

    def mouse_move(self, event):
        if not event.inaxes:
            print("N")
            return
        print("Y")
        x, y = event.xdata, event.ydata
        indx = searchsorted(self.x, [x])[0]
        x = self.x[indx]
        y = self.y[indx]
        self.lx.set_ydata(y )
        self.ly.set_xdata(x )
        self.txt.set_text( '%1.2fmm/sec  @  %1.2f Hz.'%(y,x) )
        print ('x=%1.2f, y=%1.2f'%(x,y))
        draw()

if __name__ == '__main__':
    root = Tk.Tk()
    root.wm_state('zoomed')
    root.title('Baart FFT spectrum analyser  -  Steve Ferry 2018')
    root.iconbitmap(r'baart.ico')
    app = Application(root)
    root.mainloop()

