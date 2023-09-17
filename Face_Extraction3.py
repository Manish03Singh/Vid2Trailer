# import all the libraries
from os import listdir
from os.path import isfile, join
import os
from moviepy.editor import *
from pydub import AudioSegment
import math
from google.cloud import videointelligence_v1 as vi
import io
from skimage.metrics import structural_similarity as ssim
import cv2
import glob

# set the path of the google video intelligence API key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "D:/Vid2Trailer/video2trailer-41faedffbfea.json"


# set the ffmpeg file path
AudioSegment.converter = "C:/FFmpeg/bin/ffmpeg.exe"
AudioSegment.ffprobe   = "C:/FFmpeg/bin/ffprobe.exe"



"""
 function to process the video and extract faces, captions and shot changes
 input : video_uri = path of movie, languaue_code = language of movie
 output : return a lsit with detected shot changes information, detected caption information, 
          detected faces information
"""
def process_video(video_uri, language_code):
    
    # load the library
    video_client = vi.VideoIntelligenceServiceClient()
    
    # read the video from your device
    with io.open(video_uri, "rb") as f:
        input_content = f.read()
    
    # mention all the features 
    features = [
        vi.Feature.FACE_DETECTION,
        vi.Feature.SHOT_CHANGE_DETECTION,
        ]
    
    # mantion the features
    features1 = [vi.Feature.SPEECH_TRANSCRIPTION]
    
    video_context = vi.VideoContext()
    
    # define face configurations
    face_config = vi.FaceDetectionConfig(
        include_bounding_boxes=True, 
        include_attributes=True,
    )
    
    # define speech configurations
    caption_config = vi.SpeechTranscriptionConfig(
        language_code=language_code,
        enable_automatic_punctuation=True,
    )
    
    # mention the segment and config which has been intialized above
    context = vi.VideoContext(
        face_detection_config = face_config,
    )
    
    # mention the segment and config which has been intialized above
    context1 = vi.VideoContext(
        speech_transcription_config=caption_config,
    )
    
    # generate the request for processing by mentioning the required fields
    request = vi.AnnotateVideoRequest(
        input_content=input_content,
        features=features,
        video_context=context,
    )
    
    # generate the request for processing by mentioning the required fields
    request1 = vi.AnnotateVideoRequest(
        input_content=input_content,
        features=features1,
        video_context=context1,
    )
    
    # call the API to complete the requests
    print(f"Processing clip for face and shot : {video_uri}...")
    operation = video_client.annotate_video(request)
    response = operation.result()

    # call the API to complete the request
    print(f"Processing clip for speech: {video_uri}...")
    operation1 = video_client.annotate_video(request1)
    response1 = operation1.result()
    
    #retuen the values 
    return [response, response1]
    


"""
 function to find area fo the faces
 input : a,b = top left co ordinates of box of faces, c,d = bottom right co ordinates of box of faces
 output : return the area of the box
 """
def cal_area(a,b,c,d):
    # get all the co ordinates of the box
    x1 = x4 = a; x2 = x3 = c
    y1 = y2 = b; y3 = y4 = d
    
    # calulate area of the box
    a = x1 * y2 + x2 * y3 + x3 * y4 + x4 * y1
    b = x2 * y1 + x3 * y2 + x4 * y3 + x1 * y4
    
    area = abs(a - b)/2 
    
    return area



"""
function to store the time frames of all the words spoken in the movie
input : response = output element from process_video function which contains information
        about the detected caption
output : return a list which contains start time and end time for each detected word
"""
def video_speech(response):
    # First result only, as a single video is processed
    transcriptions = response.annotation_results[0].speech_transcriptions
    
    # store the starting and ending time for each word
    time_stamps = []
    
    for transcription in transcriptions:
        best_alternative = transcription.alternatives[0]
        
        for word in best_alternative.words:
            # start and end time for each detected word
            s = word.start_time.total_seconds()
            e = word.end_time.total_seconds()
            
            time_stamps.append([s, e])
        
    return time_stamps



"""
function to store the shot changes time stamps in the movie
input : response = output element from process_video function which contains information
        about the detected shot change
output : return a list containing all the time stamps for shot changes detected
"""
def video_shots(response):
    # First result only, as a single video is processed
    shots = response.annotation_results[0].shot_annotations
    
    # store the starting and ending time for each shot
    time_stamps = []
    for i, shot in enumerate(shots):
        # start and end time of the shots
        t1 = shot.start_time_offset.total_seconds()
        t2 = shot.end_time_offset.total_seconds()
        
        time_stamps.append([t1, t2])
        
    return time_stamps



"""
function to store the faces time frames and area in the movie
input : output element from process_video function which contains information
        about the detected faces
output : return a list containing start and end time of faces and 
         a dictionary containing area of each of those detected faces 
"""
def video_faces(response):
    # initialize a list and a dictionary
    faces = []
    store_faces = {}
    
    for annotation in response.annotation_results[0].face_detection_annotations:
        # process each detected face
        for track in annotation.tracks:
            # Each segment includes timestamped faces that include characteristics of the face detected
            s = track.segment.start_time_offset.seconds + track.segment.start_time_offset.microseconds / 1e6
            e = track.segment.end_time_offset.seconds + track.segment.end_time_offset.microseconds / 1e6
    
            # Grab the first timestamped face
            timestamped_object = track.timestamped_objects[0]
            box = timestamped_object.normalized_bounding_box
            
            # calulate the area of faces
            area = cal_area(box.left,box.top,box.right,box.bottom)
            faces.append([s, e])
            
            # store the faces and the key value in dictionary
            # this method of storing key will hlep in comparing faces values later on
            key = str(s) + "_" + str(e)
            
            # store the maximum value of faces detected
            if key not in store_faces:
                store_faces[key] = area
            else:
                store_faces[key] = max(area, store_faces[key])
    
    return [faces, store_faces]



"""
function to find out the duration for which any word is not being spoken
input : stamp = time stamp of second at which the faces is shown in the movie, 
        time_stamp = output of the video_speech function
output : return a the time stamp of region in which no words are spoken if such region exits
"""
def check_speech(stamp, time_stamp):
    # if we have no speech in movie then return to avoid errors
    if len(time_stamp) == 0:
        return [0,20000]
    
    # iterate to find the time frame which is just bigger than the stamp
    i = 0
    
    for i in range(len(time_stamp)):
        if time_stamp[i][0] > stamp:
            break
    
    # if it is the first pair itself then return
    if i == 0:
        return [0,time_stamp[0][0]]
        
    # if we have the stamp lying in between the words then return
    if time_stamp[i-1][1] > stamp:
        return []
    
    # return the time frames with no words spoken in them
    return [time_stamp[i-1][1] + 0.1, time_stamp[i][0] - 0.1]



"""
function to check the shot duration in which the stamp lies
input : stamp = time stamp of second at which the faces is shown in the movie, 
        time_stamp = output of the video_shots function
output : return the time staps of region in which the input stamp lies
"""
def check_shots(stamp, time_stamp):
    i = 0
    
    # check for the pair in which input stamp lies
    for i in range(len(time_stamp)):
        if time_stamp[i][0] > stamp:
            break
        
    return [time_stamp[i-1][0] + 0.1, time_stamp[i-1][1] - 0.1]



"""
function to find the faces time stamps
input : stamp = time stamp of second at which the faces is shown in the movie, 
        faces = output of the video_faces function
output : return the time stamps of region in which the input stamp lies
"""
def find_stamps(stamp, face):
    
    # check for the pair in which input stamp lies
    for t in face[0]:
        if t[0] <= stamp and t[1] >= stamp:
            return t
    
    return []



"""
function to calculate the final time frames for the clip to be extracted based in the
speech time frames and the shot change time frames
input : speech_time = output of check_speech function, shot_time = output of check_shots funciton
output : return final time interval by overlapping the input time intervals
"""
def time_frame(speech_time, shot_time):
    # find the intersection between the two intervals
    s = max(speech_time[0], shot_time[0])
    e = min(speech_time[1], shot_time[1])
    
    return [s, e]


# define the base directory and the file name
base_dir = "D:/Vid2Trailer/demo/clusters/"
file_name = "Alone"

# read the the files and folder present in the mentioned directory
cluster_folders = [f.path for f in os.scandir(base_dir+file_name) if f.is_dir()]

# define the movie path
uri = "D:/Vid2Trailer/video/Episodes/Alone.mp4"

# define the language of the movie to unploaded and processed by the GCP API
language_code = 'en-US'

# call the function to process the movie
response = process_video(uri, language_code)

# generate all the list of speech, shot change, faces time frames
speech = video_speech(response[1])
shot = video_shots(response[0])
face = video_faces(response[0])

# sort all the output from above function calls
speech.sort()
shot.sort()
face[0].sort()


# define a dictionay to store the values
characters_face_area = {}


"""
for all the stored faces it extracts the clip and stores it if duraing that time interval there is 
no spoken word detected and no shot change detected
"""
for path in cluster_folders:
    
    #load all the file present in the mentioned loaction for porcessing
    images = [f for f in listdir(path) if isfile(join(path, f))]
    
    # create the directory if not present already
    if not os.path.exists(path + "/clip"):
        print("New directory created")
        os.makedirs(path + "/clip")
    
    sz = len(shot)
    
    # now we start peocessing each cluster of faces
    clusters_face_area = []
    for i, t in enumerate(images):
        # extract the time stamp from the name of the file as we have saved the images name
        # with the time stamp on which they occur this will now help to extract the clips
        # of the faces in the time when they occur in the movie
        time_stamp = int(t[len(file_name):t.find('_')])
        
        # if time stamp extracted is not valid then continue
        if time_stamp == -1:
            continue
        
        # this condition is applicable is a part of movie is to be processed
        # if time stamp of movie exceed the time stamp of last detected shot change then don't process it
        if time_stamp > shot[sz-1][1]:
            continue
        
        # now since we know the time stamp of occurence of image in the movie this will 
        # help us to find a interval from speech detected, shot change detected and then
        # finally extract clip from the movie
        
        # calculate the speech time frames and shot changes time frames by calling below functions
        speech_time = check_speech(time_stamp, speech)
        shot_time = check_shots(time_stamp, shot)   
        face_time = find_stamps(time_stamp, face)
        
        # if we fail to find a silent speech segment of face apearing in that time stamp then don't process that frame
        if len(speech_time) == 0 or len(face_time) == 0:
            continue
        
        # calulate the final time frames by call this funtion
        time = time_frame(speech_time, shot_time)
        
        # don't include clips with shortrt time durations
        if time[1] - time[0] < 0.8:
            continue
        
        # if the time duration is very large we ony take a small part of it
        if time[1] - time[0] > 1:
            time = [(time[1] + time[0])/2 - 0.5, (time[1] + time[0])/2 + 0.5]
        
        
        # now extract the clip and store it in specified location
        clip = VideoFileClip(uri)
        extract = clip.subclip(time[0],time[1])
        
        # path of the clip to be stored
        uri1 = path +"/clip/" + file_name + str(i) + ".mp4" 
        
        # extract and store the clip in specified loaction 
        extract.write_videofile(uri1)
        
        # store the face area form the dictionay of faces we genereated earlier and path of the clip
        # this will be use in further processing
        clusters_face_area.append([uri1, face[1][str(face_time[0]) + "_" + str(face_time[1])]])
        
    # for each cluster store the values, this will help in further deciding the final clip
    clusters_face_area.sort(reverse = True, key = lambda x : x[1])   
    characters_face_area[path[len(base_dir + file_name)+1:]] = clusters_face_area
        


"""
normalizes the faces area and then distributes them into classes and picks most frequent class among 
top 3 classes and class with maximum area
"""
cluster_clip = {}
for key in characters_face_area:
    # define a lsit to store the area and path for all the clip distributed in classes
    dict_clip = [[],[],[],[],[],[],[],[],[],[],[]]
    max_area = 0
    
    # find max area of a faces among all the fraces in a cluster
    for find in characters_face_area[key]:
        max_area = max(max_area, find[1])

    # normalize all the faces in the cluster
    for i in range(len(characters_face_area[key])):
        characters_face_area[key][i][1] = characters_face_area[key][i][1] / max_area
    
    # now we distribute all the faces in the clases
    for i in range(len(characters_face_area[key])):
        val = math.ceil(10*characters_face_area[key][i][1])
        
        # add the faces and area to the class which it belongs
        dict_clip[val].append([characters_face_area[key][i][0],characters_face_area[key][i][1]])
    
    key_val = 0
    val1 = 0
    # select the class with the highest frequency of clips
    
    for k in range(8,len(dict_clip)):
        # select the most frequent class among top 3 classes
        if len(dict_clip[k]) > val1:
            key_val = k
            val1 = len(dict_clip[k])
            
    if len(dict_clip) != 0:
        # store the most frequent and maximum area class for each cluster in a dictionary for further processing        
        cluster_clip[key] = dict_clip[key_val]
        if key_val != 10:
            for vid in dict_clip[10]:
                cluster_clip[key].append(vid)



"""
finds simmilarity amoung frames thus helps in finding the clip for each cluster to find a 
clip with minimum movement
"""
# initlialize the dictionary to store the path if clip which has minimum movement i.e., the 
# clip which is most suitable candidate for each cluster
final_cluster_clip = {}

for clust in cluster_clip:
    score = []
    # find similarity for each clip within each cluster
    for k in cluster_clip[clust]:
        images = []
        
        # capture the video using opencv library
        cap = cv2.VideoCapture(k[0])
        ret = True; frm = -1;
        count = 0;
        
        # while the ret is true keep on reading the frames 
        while ret :
            ret, frm = cap.read()
            # store every 5th frame from the clip for comparision
            if ret and count%5 == 0:
                images.append(frm)
            elif ret == False:
                break
            count += 1
            
        # calculate the similarity value for clip 
        simlarityIndex = 0
        for i in range(len(images)-1):
            simlarityIndex = simlarityIndex + ssim(images[i+1], images[i], multichannel=True)

        # normalize the simlarityIndex value
        simlarityIndex = simlarityIndex / len(images)
        # store the value for each clip in a cluster
        score.append([simlarityIndex,k[0]])
        
    # sort the list containing the simlarityindex value to have a clip with minimum movement on top
    score.sort(reverse = True, key = lambda x : x[0])
    
    if len(score) == 0:
        continue
    # store path of the clip with minimum movement from each cluster 
    final_cluster_clip[clust] = score[0][1]
        


"""
extract the clip with minimum movement from each cluster and store then in new loaction
"""
# create the folder if not present already
if not os.path.exists(base_dir + file_name + "/extracted_clips"):
    print("New directory created")
    os.makedirs(base_dir + file_name + "/extracted_clips")

# store the final clip for each cluster and that will be the final clips
for clust in final_cluster_clip:
    # path of clip having minimum movement from each cluster
    uri0 = final_cluster_clip[clust]
    # load the clip
    clip = VideoFileClip(uri0)
    
    # extract the clip
    extract = clip.subclip()
    
    # define path of the final clip to be stored
    path = base_dir + file_name 
    uri1 = path + "/extracted_clips/" + clust + "_" + uri0[len(path+clust)+7:len(uri0)-4] + ".mp4" 
    # store the final clip for each cluster 
    extract.write_videofile(uri1)
    
    

"""
mute the background sound of the extracted clip with minimum movement 
"""
# move to this directory
os.chdir(base_dir + file_name + "/extracted_clips")
# use ffmpeg call to mute the clips
call= f'for /r %i in (*.mp4) do ffmpeg -i "%i" -filter:a "volume=0" "%i_mute.mp4"'
os.system(call)



"""
delete the files which have sound as they are not required anymore
"""
# read all the clips present in the folder
for uri in glob.glob(os.path.join(base_dir + file_name + "/extracted_clips", "*.mp4")):
    # find all the unmute clips and remove them
    if (uri[len(uri) - 8:len(uri) - 4]) != "mute":
        os.remove(uri)
        
        
"""
All the final clips of faces of main character are in the folder path  = base_dir + file_name + "/extracted_clips"
"""