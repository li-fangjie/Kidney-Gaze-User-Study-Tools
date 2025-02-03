#include "opencv2/opencv.hpp"
#include <iostream>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <fstream>
 
using namespace std;
using namespace cv;

uint64_t timeSinceEpochMillisec() {
  using namespace std::chrono;
  return duration_cast<milliseconds>(system_clock::now().time_since_epoch()).count();
}

int main(int argc, char* argv[]){
 
  // Create a VideoCapture object and use camera to capture the video
  VideoCapture cap(1); 
  int fps = atoi(argv[1]); 
  cout << "FPS Selected:" << fps <<endl;
  // Check if camera opened successfully
  if(!cap.isOpened()){
    cout << "Error opening video stream" << endl;
        return -1;
  }
  bool record = false;
  // Default resolutions of the frame are obtained.The default resolutions are system dependent.
  int frame_width = cap.get(cv::CAP_PROP_FRAME_WIDTH);
  int frame_height = cap.get(cv::CAP_PROP_FRAME_HEIGHT);
  int frame_no = 0;
  ofstream myfile;
  myfile.open(string(argv[2])+".csv");
  int oldtime = 0;
  int newtime = 0;
  float fps_counter = 0;
  // Define the codec and create VideoWriter object.The output is stored in 'outcpp.avi' file.
  VideoWriter video(string(argv[2]) + ".avi", cv::VideoWriter::fourcc('M','J','P','G'), fps, Size(frame_width,frame_height));
 
  while(1){
 
    Mat frame;
    
    // Capture frame-by-frame
    cap >> frame;
  
    // If the frame is empty, break immediately
    if (frame.empty())
      break;
    newtime = timeSinceEpochMillisec();
    fps_counter = 1.0/float(newtime-oldtime) * 1000;
    oldtime = newtime;
    if (record == true){
    // Write the frame into the file 'outcpp.avi'
        video.write(frame);
    myfile << frame_no << ',' << timeSinceEpochMillisec() << "\n";
    cout << "Recording FPS: " << fps_counter << endl;
    frame_no = frame_no+1;}
    else cout << "FPS: " << fps_counter << endl;
    
    // Display the resulting frame    
    imshow( "Frame", frame );
  
    // Press  ESC on keyboard to  exit
    char c = (char)waitKey(1);
    if( c == 27 ) 
      break;
    if (c == 32)
      {record = true;
      cout << "Recording started" << endl;}
  }
 
  // When everything done, release the video capture and write object
  cap.release();
  video.release();
 
  // Closes all the frames
  destroyAllWindows();
  return 0;
}