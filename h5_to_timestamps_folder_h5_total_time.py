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
import glob
from natsort import natsorted


intro_message = [' Jan C. Frankowski, Ph.D. - Jan.Frankowski@Bruker.com',
                 '\n'
'This script reads a series of luxdata .h5 files and analyzes the latencies between timestamped frames written by Hamamatsu Orca Flash V4 cameras.',
'\n',
'You will be prompted to navigate to a folder containing raw .h5 files.',
'\n',
'The script wil return three .csv files into the same directory specipied above.'
'\n',
'- "summary_data.csv" contains average ms +- SD for each stack and average FPS.',
'\n',
'- "ms_between_frames.csv" contains the latencies in ms between adjacent frames.',
'\n',
'- "total_time.csv" starts at 0 and writes the total elapsed time (in seconds) for the experiment.',
'\n',
'The script will report the path where the .csv files are saved.']
      
messagebox.showinfo('Timestamp analysis', "\n".join(intro_message))

#%% define input and output folder
root = Tk()
root.withdraw()
root.attributes('-topmost', True)

#prompt for directory of .h5 files
h5_folder = filedialog.askdirectory(title="Select folder containing .h5 files.")
print("Selected directory of .h5 files: " + h5_folder)

#%% parse the filename to get the cam name

h5_file_list = glob.glob(os.path.join(h5_folder, '*.lux.h5'))
#sort in natural order
h5_file_list = natsorted(h5_file_list)

#%% open .h5 file and read metadata

timestamps_per_h5 = []

for filename in h5_file_list:
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
         
         # append to list
         timestamps_per_h5.append(after_split_strings)
    
    # Close the .h5 file
    f.close()


#%% parse timestamps

from dateutil import parser

master_time_points = []
master_frame_numer = []
master_latencies_us = []
master_latencies_ms = []
master_avg_ms = []
master_st_dev = []


for count, timestamps in enumerate(timestamps_per_h5):
    time_points = []
    frame_number = []
    
    for count, value in enumerate(timestamps):
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
        #add a spacer to account for no difference in latency at first frame

    # latencies_list_us.append('na')
    # latencies_list_ms.append('na')
    # calculate average
    
    avg_ms = np.asarray(latencies_list_ms).mean()
    st_dev = np.std(np.asarray(latencies_list_ms))
    
    # append to masters
    master_time_points.append(time_points)
    master_frame_numer.append(frame_number)
    master_latencies_us.append(latencies_list_us)
    master_latencies_ms.append(latencies_list_ms)
    master_avg_ms.append(avg_ms)
    master_st_dev.append(st_dev)
    
#%% add data to dataframe

#create dataframe to store latencies
df_latencies = pd.DataFrame()
df_summary = pd.DataFrame()
df_total_time = pd.DataFrame()

for count, ms in enumerate(master_latencies_ms):
    df_latencies['delta_ms_{}'.format(count)] = ms
    
df_summary['avg_ms_per_stack'] = master_avg_ms
    
df_summary['st_dev_per_stack'] = master_st_dev

fps = []
for ms in master_avg_ms:
    conversion = 1000 / ms
    fps.append(conversion)
df_summary['avg_FPS_per_stack'] = fps


#%% absolute time with first frame as 0

first = master_time_points[0][0]
absolute_latency = []
list_of_latencies = []

for count, timestamps in enumerate(master_time_points):
    differences = [(x - first).total_seconds() for x in timestamps]
    list_of_latencies.append(differences)

for count, value in enumerate(list_of_latencies):
    df_total_time['total_time_s_{}'.format(count)] = value

#%% create dataframe and save csv

#add a spacer to account for no difference in latency at first frame
# latencies_list_us.append('na')
# latencies_list_ms.append('na')

# df = pd.DataFrame(list(zip(after_split_strings, latencies_list_us, latencies_list_ms)), columns=['timestamp', 'delta_us', 'delta_ms'])
# df['avg_latency_ms'] = avg_ms
# df['SD_latency_ms'] = st_dev

# msg_1 = str("Number of frames: " + str(len(frame_number)) + ". \n")
# msg_2 = str("Average latency : " + str(avg_ms) +  " ms. \n")
# msg_3 = str("SD of latency : " + str(st_dev) +  " ms. \n")
# msg_4 = "Average frames per second: " + str(1000 / avg_ms)
# final_msg = msg_1 + msg_2 + msg_3 + msg_4
# messagebox.showinfo("Summary Data", final_msg)

#save csv
csv_filename = ('ms_between_frames.csv')
csv_path = (os.path.split(os.path.abspath(filename))[0])
final_path = os.path.join(csv_path, csv_filename)

csv_filename_2 = ('summary_data.csv')
csv_path_2 = (os.path.split(os.path.abspath(filename))[0])
final_path_2 = os.path.join(csv_path, csv_filename_2)

csv_filename_3 = ('total_time.csv')
csv_path_3 = (os.path.split(os.path.abspath(filename))[0])
final_path_3 = os.path.join(csv_path, csv_filename_3)

try:
    df_latencies.to_csv(final_path)
    df_summary.to_csv(final_path_2)
    df_total_time.to_csv(final_path_3)
except IOError:
    messagebox.showinfo("Error!", ".CSV already exists!")
    
messagebox.showinfo("CSV save location", csv_path)
