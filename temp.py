import numpy as np

csv_file = np.genfromtxt(r"c:\Users\super\Downloads\my_Eye_Gaze_Transforms_20250728_143443_2.csv", delimiter=",")
print(csv_file)
ts = csv_file[:, -1]
dts = np.diff(ts)
print(np.where(dts > 1000))

