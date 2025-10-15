import numpy as np

csv_data = np.genfromtxt(
    r"c:\Users\lifan\Downloads\LocalState (5)_topf4_test_2\my_Eye_Gaze_Transforms_20250808_012355_9.csv",
    delimiter=",")

ts = csv_data[:, -1]
dts = np.diff(ts)
print(np.where(dts > 1000))
