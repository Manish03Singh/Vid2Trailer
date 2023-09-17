# import all required libraries
from moviepy.editor import *
import moviepy.editor as mp
import os
import glob
from pydub import AudioSegment
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import math
import csv
import spleeter
# set the ffmpeg files paths
AudioSegment.converter = "C:/FFmpeg/bin/ffmpeg.exe"
AudioSegment.ffprobe   = "C:/FFmpeg/bin/ffprobe.exe"

"""
Audio extraction from a video
"""

"""
function to split movie into continuious segments of 20mins length
input : video_uri = path of movie, path = folder where split clips will be stored
        movie_name = name of the movie
output : void function
"""
def split_movie(video_uri, path, movie_name):
    # load the movie
    clip = VideoFileClip(video_uri)
    # calculate the duration of the movie
    duration = clip.duration
    # initialize the variables
    time = 0; i = 1
    
    # create the folder if not present
    if not os.path.exists(path+ movie_name):
        print("New directory created")
        os.makedirs(path+ movie_name)
        
    # keep extracting movies until we exceed the movie duration
    while time <= duration:
        # extract clips of described length
        extract = clip.subclip(time,min(duration,time + 1200))
        # store it in the output folder path
        uri1 = path+ movie_name + "/" + movie_name + str(i) + ".mp4" 
        extract.write_videofile(uri1)
        # keep on increasing time
        time += 1200
        i += 1

# path of the folder where clips will be stored
path = "D:/Vid2Trailer/video/Episodes/"
# name of the movie for folder creation purpose
movie_name = "Alone"
# path of the movie
video_uri = "D:/Vid2Trailer/video/Episodes/Alone.mp4"

# calling the above funtion to slipt the movie in 20mins clips
split_movie(video_uri, path, movie_name)


"""
funtion to convert all the extracted clip from movie to mp3 format
input : folder_path = path where all extracted clip are stored, movie_name = name of the movie
output : void function
"""
def convert_to_mp3(folder_path, movie_name):
    i = 1
    # read all the files from the folder
    for uri in glob.glob(os.path.join(folder_path, "*.mp4")):
        # load the file
        my_clip = mp.VideoFileClip(uri)
        # convert it into mp3 format with a particular nameing convention as stated so that it can
        # be parsed easily later on
        my_clip.audio.write_audiofile(folder_path + movie_name + str(i) + ".mp3")
        i += 1

# call the above function to covert clips to mp3 format
convert_to_mp3(path + movie_name + "/", movie_name)



"""
Extracting Music track from a audio file
"""

"""
funtion uses spleeter libaray to split voice and muisc track form a mp3 file
input : folder_path = path of the folder which contains the extracted mp3 files
        output_path = path of folder where the processed audio and music track needs to be stored
output : return number of files processed
"""
def seprate_music_and_audio_track(folder_path, output_path):
    # move to the foler path
    os.chdir(folder_path)
    i = 0
    # read all the mp3 files from the folder_path
    #files = [f.path for f in os.scandir(path + movie_name) if f.is_dir()]
    for uri in glob.glob(os.path.join(folder_path, "*.mp3")):
        # calls the spleeter library to split the mp3 files
        # this library creats a new folder with input file name and stores music and vocal track 
        # in that folder, this folder is created in the output location
        call = "spleeter separate -p spleeter:2stems -d " + str(1200) + " -c mp3 -o " + output_path + " " + uri
        returned_value = os.system(call)
        print('returned value:', returned_value)
        i += 1
    
    return i

# output path where spleter processed files need to be stored
output_path = "D:/Vid2Trailer/demo/output"
# call the function to seperate the voice and music track
number_of_segments = seprate_music_and_audio_track(path + movie_name + "/", output_path)

# Combine all the extracted music segments
# total segments of movie
# store all the extracted audio and concatenate them to get orignal movie audio
"""
funtion combine music track for all the extracted music segments
input : number_of_segments = number of clips of movie, output_path = path of where extracted music and audio tracks are stored,
        movie_name = name of the movie
output : void function
"""
def combine_segments(segments, output_path, movie_name):
    # create the directory if not present already
    if not os.path.exists(output_path + "/"+ movie_name):
        print("New directory created")
        os.makedirs(output_path + "/"+ movie_name)
    
    # add all the music segments to get the music track for full movie
    final_audio = AudioSegment.from_mp3(output_path +  "/" + movie_name + str(1) + "/accompaniment.mp3")
    for i in range(2,segments + 1):
        print(i)
        final_audio = final_audio + AudioSegment.from_mp3(output_path +  "/" + movie_name + str(i) + "/accompaniment.mp3")
    
    # extract final muisc track
    final_audio.export(output_path +  "/" + movie_name + "/accompaniment.mp3", format = "mp3")
    
# call the function to combine all the extracted music tracks
combine_segments(number_of_segments,output_path, movie_name)



"""
Extracting and storing the time Stamps of the music tracks
"""


"""
function extrcats the time stamps for music segments, noise, no energy from a audio file and stores it into a csv 
file
input : folder_path = path of the folder that contains the mp3 file of combined muisc tracks for full movie
output : void function
"""
def extract_time_stamps(folder_path):
    # move to the folder path
    os.chdir(folder_path)
    # input file path
    input_file = folder_path + "/accompaniment.mp3"
    # output folder path
    output_file = folder_path
    # call the library to extract the csv file containing all the time stamps of music segments
    # a csv file will be stored in the output location
    call = "ina_speech_segmenter.py -i " + input_file + " -o " + output_file + " -e csv"
    returned_value = os.system(call)

# calling the function that extracts time stamps of muisc, noise, no enegry segment and stores it into a csv file
extract_time_stamps(output_path + "/" + movie_name)



"""
Cliping music segments based on the time stamps extracted from movie
"""

"""
function reads the csv file containing all the music,noise, no enegry time stamps and reads the time stamps containing
music segments
input : output_path = path containing the extracted csv file, movie_name = name of the movie
output : return a list containing all the time stamps of the music segments form the moive and 
sorts it in reverse order based on the time duration
"""
def find_music_time_stamps(output_path, movie_name):
    # path of the csv files containing all the time stamps
    c_path = output_path + "/" + movie_name + "/accompaniment"

    # store the csv file in  table
    with open(c_path +".csv",'r') as f:
        table = list(csv.reader(f,delimiter=';'))

    _time = []
    for t in range(1,len(table)):
        # processing table in desirable format
        x = table[t][0].split("\t")
    
        # only keep time stamps with music part
        if x[0] != 'music':
            continue
    
        # convert time stamps to float from string and store 
        _time.append([float(x[1]), float(x[2])])
        
    # sort the time segments depending upon time period
    _time.sort(key = lambda x : x[1] - x[0], reverse = True)
    
    return _time

# calling the function to extract and store all the time stamps with music in it
time = find_music_time_stamps(output_path, movie_name)




"""
function extracts the music segments from the mp3 file containing only the muisc track
input : time = output of find_music_time_stamps function, output_path = path of the folder 
        which has the muisc track of full movie, movie_name = name of the movie,
        extracted_music_path = path where extracted music from the movie will be stored
output : contains path of all the extracted music segments
"""
def extract_music_segments(time, output_path, movie_name, extracted_music_path):
    files = []
    # path of the mp3 file conataining the music track for full movie
    uri = output_path + "/" + movie_name + "/accompaniment.mp3"
    i = 0
    
    # create the folder if doesnot exists already
    if not os.path.exists(extracted_music_path + movie_name):
        print("New directory created")
        os.makedirs(extracted_music_path + movie_name)
        
    # store all the music segments
    for t in range(max(30,math.ceil(len(time)/10))):
        # convert to millisconds
        startTime = time[t][0]*1000
        endTime = time[t][1]*1000
    
        print("\t Time Stamps : {} - {}".format(startTime,endTime))
        # extract and store the audio of a particular time stamp
        song = AudioSegment.from_mp3(uri)
        extract = song[startTime:endTime]
        # path of the muisc segment to be extracted
        uri1 = extracted_music_path + movie_name +"/" + movie_name + str(i) + ".mp3"    
        i = i + 1
        
        # store the extracted data in mp3 format
        files.append([uri1, startTime, endTime])
        extract.export(uri1, format="mp3")
    
    return files

# path of the foler in which extracted music segments will be stored
extracted_music_path = "D:/Vid2Trailer/demo/Extracted/"

# calling the function which extracts the muisc sgemnest form the file containing full music track of the movie
audio_files = extract_music_segments(time, output_path, movie_name, extracted_music_path)



"""
Finding Theme music -- Calculating pair waise similarity and repetitive score
"""

"""
function calculates the music repetitive score of the music segments
input : audio_file = output of extract_music_segments function
output : return list of repetitve score of all the music segments
"""

def calculate_repetitive_score(audio_files):
    # initialize the lists to store the values
    chromagram = []
    frames = []
    
    print("\tGeneratinng Chroma vectors")
    
    for uri in audio_files:
        # load audio file
        x , sr = librosa.load(uri[0])
        frames.append(len(x))
    
        # calculating appripriate hop_length value 
        hop_length = pow(2,math.floor(math.log2(sr/4)))
        
        # append chrooma vector for each segment
        chromagram.append(librosa.feature.chroma_cens(x, sr=sr, hop_length=hop_length))
    
    
    print("\tNormalizing chroma vectors")
    # Normalizing chroma vector for each frame within each segment
    for i in range(len(chromagram)):
        for k in range(len(chromagram[i][0])):
            ele = 0
            for l in range(len(chromagram[i])):
                ele = max(ele, chromagram[i][l][k])
            for l in range(len(chromagram[i])):
                chromagram[i][l][k] = chromagram[i][l][k]/ele

    
    print("\tCalculating pair wise similarity")
    # Calculating pair wise silimarity
    pair_wise_similarity = {} 
    
    for i in range(len(chromagram)):
        print("\t{}".format(i))
    
        for j in range(len(chromagram)):
            if i == j:
                continue
            # dictonary to store pair wise similarity for each pair of chroma vector for 
            # each pair of muisc segment
            pair_similarity = {}
        
            i_len = len(chromagram[i][0])
            j_len = len(chromagram[j][0])
        
            for k in range(i_len):
            
                for l in range(j_len):
                
                    diff_vec = []
                    # calulate elemet wise difference for each chroma vectors pair
                    for m in range(len(chromagram[i])):
                        diff_vec.append(chromagram[i][m][k]-chromagram[j][m][l])
                    
                    # calculate silimarity for each pair of chroma vector within each segment
                    pair_similarity[(k,l)] = (1 - (np.linalg.norm(diff_vec))/math.sqrt(12))
                
            # store the pair similarity for each pair of music segments
            pair_wise_similarity[(i,j)] = pair_similarity


    print("\tCalculating repetitive score")
    # Final calculation of repetitive score for each music segment
    repeated_score = []

    for i in range(len(chromagram)):
        #calculate no. of chroma vector in each sec
        n = math.floor((len(chromagram[i][0]) * sr)/frames[i])
        print("\t{}, {}".format(i, n))
    
        # selecting a window length from -t to t in seconds to calculate the similarity
        t = 10 
        total_val = 0
    
        for j in range(len(chromagram)):
            if i == j:
                continue
            # store the dictionary containing pair wise similarity for segment i,j
            check = pair_wise_similarity[(i,j)]
            max_overlap_val = 0
        
            i_len = len(chromagram[i][0])
            j_len = len(chromagram[j][0])
        
            for k in range(i_len):
            
                for l in range(j_len):
                           
                    overlap_val = 0
                    # calculate the overlapping score for each pair
                    for m in range(-n*t,n*t):
                        if (k+m,l+m) not in check:
                            continue
                        overlap_val = overlap_val + check[(k+m,l+m)]
                    
                    # store the max overlapping score
                    max_overlap_val = max(max_overlap_val, overlap_val)
            
            # sum the max overlapping score
            total_val = total_val  + max_overlap_val
        
        # store the repetitive score for each segment
        repeated_score.append([total_val, i+1]);

    repeated_score.sort(reverse = True);
    
    return repeated_score


# calling the function to calculate the repetitive score for the music segmnets
repetitive_score = calculate_repetitive_score(audio_files)

"""
function sorts the repetitve score based in the score and duration
input : repetitive_score = output of calculate_repetitive_score function, 
        audio_file = ouput of extract_music_segments function, threshold = cutoff value
output : return a new sorted list based on duration and repetitve score
"""
def find_max_score_and_duration_segments(repetitive_score, audio_files, threshold):
    final_score = []
    # max repetitve score
    max_score = repetitive_score[0][0];

    # calculate new score for each muisc segment and store it in a list 
    for seg in repetitive_score:
        if seg[0] != max_score and seg[0] < threshold * max_score:
            break
        final_score.append([seg[0], audio_files[seg[1] - 1][1], 
                                 audio_files[seg[1] - 1][2], seg[1]])

    # sort the list in reverse order to have muisc segment with highest score on top
    final_score.sort(key = lambda x : x[2] - x[1], reverse = True)
    print("\tFinal repetitive score list is generated")
    
    return final_score

# threshold
diff = 0.95
# calling the function to get new score for each music segments
final_repeated_score = find_max_score_and_duration_segments(repetitive_score, audio_files, diff)



"""
function generates the music features like amplitude vs time, sampling rate
input : file = path of the extracted music segmnets
output : return extracted music features i.e., music ampltiudes, music sampling rate
"""
def sample_theme_music(file):
    # extract the music file
    x , sr = librosa.load(file)
    print(type(x), type(sr))

    # plot the graph
    plt.figure(figsize=(14, 5))
    librosa.display.waveplot(x, sr=sr)
    
    return [x,sr]

# a list to store music features
theme_music = []
length = 0
i = 0
# process segments until we get a total of 300sec of music track
while length < 300 and i < len(final_repeated_score):
    # call the function to extract the music features
    val = sample_theme_music(audio_files[final_repeated_score[i][3] - 1][0])
    i += 1
    # calculate the new length
    length += len(val[0])/val[1]
    theme_music.append(val)
    
"""
funciton removes low amplitude part from starting and ending of theme music
input : threshold = a list containing all the values of threshold to find the best fit
        x, sr = music feratures
output : new time stamp for each muisc segment
"""
# funtion to discard the low amplitude music at the start and end
def find_time(threshold,x,sr):
    music = []
    length = len(x);
    
    # taking average to reduce the anomaly due to ramdom spike in amplitudes 
    for i in range(length):
        amp_sum = 0
        for j in range(max(0, i - 10), min(length - 1, i + 10)):
            amp_sum += abs(x[j])
        music.append(amp_sum/(20))
    
    # find max value to filter undesired values
    max_amp = max(music)
    stamps = []
    
    for thres in threshold:
        # check sample from starting that suffice the condition 
        for k in range(len(music)):
            if music[k] > thres[1] * max_amp:
                break
        
        # check sample from ending that suffice the condition
        for l in range(len(music)-1,-1,-1):
            if music[l] > thres[0] * max_amp:
                break
        # time = sample number / sampling rate
        stamps = [k/sr, l/sr]
        
        #if we have sufficient time duration then keep it else continue
        if stamps[1] - stamps[0] > 90:
            break
    
    # return time stamps       
    return stamps


# generate all the combinations of the threshold values
threshold = []
for i in range(50,35,-1):
    for j in range(50,20,-1):
        threshold.append([i/100,j/100])

# call the funciton to get the time stamps
time_stamp = []
for music in theme_music:
    time_stamp.append(find_time(threshold,music[0],music[1]))

"""
function to extract and store the music segments
input : time_stamp : list conating output from find_time function, audio_path = path of the muisc segment
outpt : return path of the new file
"""
# extract the required time stamps of the song and the save it in mp3 format
def final_theme_music(time_stamp,audio_path):
    song = AudioSegment.from_mp3(audio_path)
    extract = song[time_stamp[0] * 1000 : time_stamp[1] * 1000]

    # name of the final theme music file
    uri = audio_path[:len(audio_path)-4] + '-extracted.mp3'
    # extracting the theme music file in mp3 format
    extract.export(uri,format = 'mp3')
    print("\tPath of theme music is : {}".format(uri))
    return uri

# store the path for final extracted trimed music segmnets
extracted_theme_musics = []


# calling function to extact music segmnet and store their paths
for i in  range(len(theme_music)):
    extracted_theme_musics.append(final_theme_music(time_stamp[i],audio_files[final_repeated_score[i][3] - 1][0]))

"""
merge all the different music segments to make a one single theme music and store it in 
required path
"""
# concatinate all the extraced trimed muisc segments
final_extracted_theme_music = AudioSegment.from_mp3(extracted_theme_musics[0])
for i in range(1, len(extracted_theme_musics)):
    final_extracted_theme_music = final_extracted_theme_music + AudioSegment.from_mp3(extracted_theme_musics[i])

# create the folder if doesnot exists already
if not os.path.exists(extracted_music_path + movie_name + "/ThemeMusic"):
        print("New directory created")
        os.makedirs(extracted_music_path + movie_name + "/ThemeMusic")
        
# extract the final theme music
final_extracted_theme_music.export(extracted_music_path + movie_name + "/ThemeMusic/theme_music.mp3", format = "mp3")
    

""" 
Final theme music for the movie will be stored in path = extracted_music_path + movie_name + "/ThemeMusic/",
with name of "theme_music.mp3" 
"""


