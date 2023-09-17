# input - clip of starting 20mins of movies which will contain title and production name
# stores clip of the title and production name of the movie in the desired folder

# import required libraries
from fuzzywuzzy import fuzz
from datetime import timedelta
from google.cloud import videointelligence_v1 as vi
import os
import io
from moviepy.editor import *

# set the path of the google video intelligence API key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "D:/Vid2Trailer/video2trailer-41faedffbfea.json"


"""
input : path of video to be processed
        video_uri = path of video
        language_hints = mention the language for title if required
        segments = time stamps of the input video file
output : return list with all the texts detected in the video frames with their time durations 
         and co-ordinates on the screen
"""
def detect_text(video_uri, language_hints=None, segments=None):
    # call video intelligence API of GCP
    video_client = vi.VideoIntelligenceServiceClient()
    
    # method to read the video file from your device
    with io.open(video_uri, "rb") as file:
        input_content = file.read()
    
    # initialize TEXT_DETECTION feature 
    features = [vi.Feature.TEXT_DETECTION]
    
    # give value for lanuage hints if any
    config = vi.TextDetectionConfig(
        language_hints=language_hints,
    )
    
    # mention the segment and config which has been intialized above
    context = vi.VideoContext(
        segments=segments,
        text_detection_config=config,
    )
    
    # generate the request for processing by mentioning the required feilds
    request = vi.AnnotateVideoRequest(
        input_content=input_content,
        features=features,
        video_context=context,
    )
    
    # now start porcessing the request
    print(f"Processing video: {video_uri}...")
    operation = video_client.annotate_video(request)
    
    # return the output of the request
    return operation.result()


"""
Filters out dected text and then sorts them on their area and time duration
input : response = output of detect_text function
output : returns list of valid candidates for title
"""
def filter_possible_titles(response):
    # store the annotation results from the detext_text function result
    annotation_result = response.annotation_results[0]
    ans = []
    # analyse each detected text and search for a valid candidate
    for text_annotation in annotation_result.text_annotations:
        # if confidence of detected text if less the threshold then don't process it
        if text_annotation.segments[0].confidence < 0.9:
            continue
        
        # Get the time labels
        text_segment = text_annotation.segments[0]
        start_time = text_segment.segment.start_time_offset
        end_time = text_segment.segment.end_time_offset
        start = start_time.seconds + start_time.microseconds * 1e-6
        end = end_time.seconds + end_time.microseconds * 1e-6
        time = end - start
        text_label = text_annotation.text
        
    
        # Find the area of the title
        frame = text_segment.frames[0]
        coordinates = frame.rotated_bounding_box.vertices
        # calculate the area of text detected
        a = coordinates[0].x * coordinates[1].y + coordinates[1].x * coordinates[2].y + coordinates[2].x * coordinates[3].y + coordinates[3].x * coordinates[0].y
        b = coordinates[1].x * coordinates[0].y + coordinates[2].x * coordinates[1].y + coordinates[3].x * coordinates[2].y + coordinates[0].x * coordinates[3].y
        area = (a - b)/2
        # append the aera, time , text, end time, start time in a list
        ans.append([area,time,text_label,end,start])
    
    # Sort the list to get the text with largest area and longest time duration on the top
    ans.sort(reverse = True)
    return ans


"""
Calculates the similarity between the two strings
"""
def compare_string(s1, s2):
    return fuzz.ratio(s1, s2)


"""
From the list of detected text filters out the most appropriate candidates for the
movies title with its detected time frame
input : result = output from filter_possible_titles function, title_dictionary, production_dictionary = dictionary 
       of words containing movie title names, production names respectively
output : returns a list of title and production names with their time stamps
   """
def find_title(result, title_dictionary, production_dictionary):
    # set to store the titles
    ans = set({})
    # list to store the titles
    intervals = []
    # set to store the title start time
    titles_s = {}
    # set to store the title end time
    titles_e = {}
    # set to store the title area
    titles_a = {}
    
    
    # Finds out the best match form the possible titles input
    for titles in result:
        
        a = 0
        b = titles[2]
        # for each word in the dictionary check for word which has maximum similarity with possible title name
        for s in title_dictionary:
            c = compare_string(titles[2], s)
            if a < c:
                a = c
                b = s
        # for each word in the dictionary check for word which has maximum similarity with possible production name
        for s in production_dictionary:
            c = compare_string(titles[2], s)
            if a < c:
                a = c
                b = s
                
        # Filter out based on Threshold
        if(a < 74):
            continue
        
        print("\tConfidence : {}, Title : {}".format(a, titles[2]));
        # store the values for text, start time and end time
        text_label = b
        start_time = titles[4]
        end_time = titles[3]
        
        # Merge the time intervals for the titles wtih different time samples to maximize the total time frame
        # if a new title is encountered add it to the set and set it start and end time
        # if a title is already present in the set then check for title area if it lies in
        # the desired region then merge the time intervals
        if text_label not in titles_s:
            titles_s[text_label] = start_time
            titles_a[text_label] = titles[0]
        elif text_label in titles_s:
            if titles[0] >= titles_a[text_label] / 4 and titles[0] <= 4 * titles_a[text_label]:
                titles_s[text_label] = min(start_time, titles_s[text_label])
        if text_label not in titles_e:
            titles_e[text_label] = end_time
        elif text_label in titles_e:
            if titles[0] >= titles_a[text_label] / 4 and titles[0] <= 4 * titles_a[text_label]:
                titles_e[text_label] = max(end_time, titles_e[text_label])
            
        # if title name is not present in the set then add them in the set
        if text_label not in ans:
            ans.add(text_label)
    
    # for each title if time duratuon if more then 1 sec then add it the list containing 
    # the ouput titles
    for element in ans:
        if(titles_e[element] - titles_s[element] >= 1):
            intervals.append([titles_s[element], titles_e[element], element])
            
    # return the final output
    return intervals


"""
Merges the overlapping intervals
input : intervals = output from the find_title function, video_uri = path of the video file, 
        base_directory = path of folder where titile and prodcution name clips are to be stored, 
        title_dictionary, production_dictionary = dictionaries containing possible names
output : void function
"""
def merge(intervals, video_uri, base_directory, title_dictionary, production_dictionary):
    if len(intervals) == 0: 
        return 
    # sort the list based on the start time
    intervals = sorted(intervals, key = lambda x : x[0])
    res = [intervals[0]]
    
    # Merge the intervals of the titles if overlapping
    for i in intervals[1:]:
        if res[-1][1] >= i[0]:
            res[-1][1] = max(i[1], res[-1][1])
        else:
            res.append(i)
    
    
    for e in res:
        print("\tTitle : {}, Start Time : {}s, EndTime : {}s".format(e[2], e[0], e[1]))
    
    # extract the clips of the title and production name
    for e in res:
        # load the video file
        clip = VideoFileClip(video_uri)
        
        # extract the clip within the time stamp
        extract = clip.subclip(e[0],e[1] - 0.2)
        
        # path of the clip
        uri1 = base_directory
        
        # if clip is title name then store it with (15000,15000).mp4 name for further porcessing
        if e[2] in title_dictionary:
            uri1 += "/(20000,20000).mp4"
            
        # if clip is production name then store it with (0,0).mp4 name for further porcessing
        if e[2] in production_dictionary:
            uri1 += "/(0,0).mp4"
            
        #store the clip
        extract.write_videofile(uri1)
    
"""movies url list"""
movies = ["D:/Vid2Trailer/video/Episodes/JohnWick.mp4"]

"""movie title name list"""
title_dictionary = {"John Wick", "JOHN WICK", "john wick", "John", "Wick", "JOHN",
                    "WICK", "john", "wick"}

"""production name list"""
production_dictionary = {"A LIONSGATE COMPANY", "A Lionsgate Company", "A", "LIONSGATE",
                         "COMPANY", "a lionsgate company"}

for video_uri in movies:
    # store the movie to extract the satring 20mins of clip for further video processing
    clip = VideoFileClip(video_uri)
    
    # set the end time to extract the clip
    end_time = 1200
    extract = clip.subclip(0,end_time)
    
    # set the base directory and moive name 
    base_directory = "D:/Vid2Trailer/demo/TitleVideos/"
    movie_name = "JohnWick"
    
    # create the new folder if doesnot exists already
    if not os.path.exists(base_directory + movie_name):
        print("New directory created")
        os.makedirs(base_directory + movie_name)
    
    # extract and store the clip
    uri1 = base_directory + movie_name + "/title_video.mp4" 
    extract.write_videofile(uri1)
    
    # set the time segments for the video to be processed
    segment = vi.VideoSegment(
        start_time_offset=timedelta(seconds=0),
        end_time_offset=timedelta(seconds=end_time),
        )
    
    # call the function to detect all the text present in the video
    response = detect_text(uri1, segments=[segment])
    
    # filter all the possible candidates for the text by calling this function
    result = filter_possible_titles(response)
    
    # find the appropriate title and production name by matching it with the dictionaries
    ans = find_title(result, title_dictionary, production_dictionary)
    
    # merge all the overlaping segments, extract and store the title clips in requied folder
    merge(ans, uri1, base_directory + movie_name, title_dictionary, production_dictionary)
    

""" 
Movie title and production name clip will be stored in the path = base_directory + movie_name
with the naming convention a mentioned eariler 
"""
