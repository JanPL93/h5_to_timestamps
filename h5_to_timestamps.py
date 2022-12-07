# -*- coding: utf-8 -*-
"""
Created on Mon Dec  5 09:17:12 2022

@author: Jan C. Frankowski Ph.D
jan.frankowski@bruker.com
"""

#%% read metadata from .h5 file

import h5py
import json
import re
import numpy as np
from tkinter import Tk, filedialog, messagebox
import pandas as pd
import os

#%% define input and output folder manually or with tkinter

#path to .lux.h5
#filename = "E:\\janelia\\long_left_2planes\\2022-11-04_090803\\raw\\stack_0_channel_0_obj_left\\Cam_left_00000.lux.h5"

root = Tk()
root.withdraw()
root.attributes('-topmost', True)

#prompt for directory of .h5 files
filename = filedialog.askopenfilename(title="Select .h5  .h5 file.")
print("Selected .h5 file: " + filename)

#%% open .h5 file and read metadata

#open file and navigate to metadata
with h5py.File(filename, "r") as f:
     metadata = json.loads(f["metadata"][()])
     
     #convert to string because the dictionary breaks down to a list at some point
     json_string = str(metadata)

     # define regex
     time_stamps_regex = r'time_stamps.*?\[(.*?)\]'
     
     # search for regex
     time_stamps_match = re.search(time_stamps_regex, json_string)
     if time_stamps_match:
         time_stamps_str = time_stamps_match.group(1)
         
     # split the string
     after_split_strings = time_stamps_str.split(',')

# Close the .h5 file
f.close()


#%% parse timestamps

from dateutil import parser

time_points = []
frame_number = []

for count, value in enumerate(after_split_strings):
    time = parser.parse(value)
    time_points.append(time)
    frame_number.append(count)

latencies = np.diff(time_points).tolist()

#convert to microseconds and milliseconds
latencies_list_us = []
latencies_list_ms = []

for value in latencies:
    us = value.microseconds
    ms = us / 1000
    latencies_list_us.append(us)
    latencies_list_ms.append(ms)
    
# calculate average

avg_ms = np.asarray(latencies_list_ms).mean()
st_dev = np.std(np.asarray(latencies_list_ms))

#%% create dataframe and save csv

#add a spacer to account for no difference in latency at first frame
latencies_list_us.append('na')
latencies_list_ms.append('na')

df = pd.DataFrame(list(zip(after_split_strings, latencies_list_us, latencies_list_ms)), columns=['timestamp', 'delta_us', 'delta_ms'])
df['avg_latency_ms'] = avg_ms
df['SD_latency_ms'] = st_dev

msg_1 = str("Number of frames: " + str(len(frame_number)) + ". \n")
msg_2 = str("Average latency : " + str(avg_ms) +  " ms. \n")
msg_3 = str("SD of latency : " + str(st_dev) +  " ms. \n")
msg_4 = "Average frames per second: " + str(1000 / avg_ms)
final_msg = msg_1 + msg_2 + msg_3 + msg_4
messagebox.showinfo("Summary Data", final_msg)

#save csv
csv_filename = (os.path.split(os.path.abspath(filename))[1] + '_latency.csv')
csv_path = (os.path.split(os.path.abspath(filename))[0])
final_path = os.path.join(csv_path, csv_filename)

try:
    df.to_csv(final_path)
except IOError:
    messagebox.showinfo("Error!", ".CSV already exists!")
    
messagebox.showinfo("CSV save location", final_path)



