# KIDNEY-GAZE-USER-STUDY-TOOLS
This is the repository for the python scripts used during user study experiments for the kidney gaze project.

The repository consists of 3 components:
1. `Experiment Controller`: This is used for controlling HoloLens display and data recording settings remotely through a laptop.
2. `Data Logger`: This is used for video recording through a laptop. It is exclusively used for phantom trials, whereas 

## Installation
### `Experiment Controller`
The dependencies of the scripts are outlined in the `environment.yml` as a conda environment. Run `conda env create -f environment.yml` to create the virtual environment `EyeGazeStudy`.

### `Data Logger`
The dependencies for the video logger is as follows:
- OpenCV
- Numpy

You can create your own virtual enviornment with these dependencies.

## Running an Experiment
### `Experiment Controller`
- Setup a WiFi hot spot on the computer running the script. 
- Within the hot spot network, set the local ip of the computer to be static, `192.168.0.10`, with subnet mask `225.255.255.0`. (This should only happen once)
- Connect the HoloLenses to the hotspot.
- Start the HoloLens App.
- Activate the virtual environment `EyeGazeStudy`
- Start the controller: `python "./Experiment Controller/server.py"`

### `Data Logger`
- Connect the ureteroscope video output to a video capture card.
- Connect the video capture card usb output to the laptop, so that the capture card acts as a webcam.
- Open OBS studio, and set the video capture card output as the input source. Make sure the output/scene size is correct.
- Start a virtual camera.
- Enable the virtual environment for data logger (if you have one), or just make sure the dependencies are met.
- Start Data Logger: `python "./Data Logger/main.py [fps] [output_filename]`, where `[fps]` is the fps of the output file, and `[output_filename]` is the file name of the output video.
- With the focus on the Data Logger video window (e.g. by clicking on it), press **space** to start recording. Press **esc** to stop recording.