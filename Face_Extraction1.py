# import required libraries
import cv2    
from keras.preprocessing import image   
import os

# name of movie
movie_name = "Alone"
# location of movie
video_uri = "D:/Vid2Trailer/video/Episodes/Alone.mp4"
# base directory of movie and other files
base_dir = "D:/Vid2Trailer/demo/"

"""
function captures and saves frames for each second 
input : base_dir = path of base directory, video_uri = path of video, movie_name = name of movie
output : void function
"""

def capture_frames(base_dir, video_uri, movie_name):
    # create the required folder in the base directory if not present already
    
    if not os.path.exists(base_dir + 'frames/' + movie_name):
        print("New directory created")
        os.makedirs(base_dir + 'frames/' + movie_name)
    
    # initialize and capture the movie using open cv library
    vidcap = cv2.VideoCapture(video_uri)
    success,image = vidcap.read()
    success = True
    count = 0
    # traverse through the moive, as soon as movie duration ends success variable becomes false and loop breaks
    while success:
        # capture the frames with difference of 1000ms
        vidcap.set(cv2.CAP_PROP_POS_MSEC,(count*1000))
        # file name for the image  is stored in such a way the it contains the time stamp of 
        # the image is in the movie, this will help us in extracting the clips for each face
        filename = base_dir + "frames/" + movie_name + "/" + movie_name + "%d.jpg" % (count-1)
        cv2.imwrite(filename, image)     
        # save frame as JPEG file    
        # move to the next required frame
        success,image = vidcap.read()
        print("Read a new frame: {} : {}".format(success,count))
        count += 1
    print ("Done!")

# calling the function capture and save the frame for each second from the movie
capture_frames(base_dir, video_uri, movie_name)

""" 
All the images from frames will be extrcated ans tore in the path = base_dir + "frames/" + movie_name 
"""
