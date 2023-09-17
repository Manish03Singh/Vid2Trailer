# import all the required libraries
import os
import dlib
import glob
import math

# intialize the base directory/working directory 
base_dir = "D:/Vid2Trailer/demo/"
# initalize file name
movie_name = "Alone"

# load the pretrained model for face extraction
predictor_path = base_dir + "shape_predictor_5_face_landmarks.dat"
face_rec_model_path = base_dir + "dlib_face_recognition_resnet_model_v1.dat"

"""
function detecets and extracts faces from a frames using pre trained models 
input : base_dir = working folder path, movie_name = name of the movie
output : void function
"""
def extract_faces_from_frames(base_dir, movie_name):
    # folder location of frames stored for face extraction code
    faces_folder_path = base_dir + "frames/" + movie_name
    
    # create the folder if not present already
    if not os.path.exists(base_dir + 'clusters/' + movie_name):
        print("New directory created")
        os.makedirs(base_dir + 'clusters/' + movie_name)
        
    # folder loaction for storing thr clustrered faces pictures
    output_folder_path = base_dir + "clusters/" + movie_name

    # initialize and load the pretrained models 
    detector = dlib.get_frontal_face_detector()
    sp = dlib.shape_predictor(predictor_path)
    facerec = dlib.face_recognition_model_v1(face_rec_model_path)

    # initialize the lists
    descriptors = []
    images = []

    # set to store all the pic with single face detected in them
    face_ina_frame = set()

    # prestoring string lens for parsing
    len_of_path_dir = len(faces_folder_path)
    len_of_file_name = len(movie_name)

    sum1 = 0
    # read all the images from the folder specified by the "faces_folder_path"
    for f in glob.glob(os.path.join(faces_folder_path, "*.jpg")):
        print("Processing file: {}".format(f))
        # load the image in the RGB format
        # Ask the detector to find the bounding boxes of each face
        img = dlib.load_rgb_image(f)
        l = len(f)
    
        # Upsample the image 1 time. This will make everything bigger and allow us to detect more faces.
        dets = detector(img, 1)
    
        # if number of faces detected is 1 then store the key
        print("Number of faces detected: {}".format(len(dets)))
        if len(dets) == 1:
            sum1 = sum1 + 1
            # store the name of face with time stamp to make furhter processing easier
            face_ina_frame.add(int(f[len_of_path_dir + len_of_file_name + 1:l-4]))
        
        # Now process each face found.
        for k, d in enumerate(dets):
            # Get the landmarks/parts for the face in box d.
            shape = sp(img, d)

            # Compute the 128D vector that describes the face in img identified by shape.  
            face_descriptor = facerec.compute_face_descriptor(img, shape)
            # store the value for further processing
            descriptors.append(face_descriptor)
            images.append((img, shape,f[len_of_path_dir+1:l-4]))
        
    # Now let's cluster the faces using chinese whispers clustering we can adjust the clustring 
    # boundaries by changing the second parameter in the function
    labels = dlib.chinese_whispers_clustering(descriptors, 0.5)
    num_classes = len(set(labels))
    print("Number of clusters: {}".format(num_classes))

    # Find biggest class
    cluster = []
    for i in range(num_classes):
        cluster.append([])
    
    for i in range(len(labels)):
        cluster[labels[i]].append(i)

    # now we have clusters in sorted manner
    cluster.sort(reverse = True, key = lambda x : len(x))

    # store some cluters depeding on the condition imposed len(cluster[i]) < len(cluster[0]) / 3 and len(indices) > 4
    # above started conition can be varied accordingly
    indices = []
    for i in range(math.ceil(len(cluster))):
        # keep on appednig the cluster until the below condition doesnot holds
        if len(cluster[i]) < len(cluster[0]) / 3 and len(indices) > 4:
            break
        indices.append(i)
        
        
    # Ensure output directory exists, if not then create
    if not os.path.isdir(output_folder_path):
        os.makedirs(output_folder_path)

    # Save the extracted faces
    print("Saving faces in largest cluster to output folder...")
    for i in range(len(indices)):
        # initialize the path of the cluster to save the faces in it
        file_path = base_dir + "clusters/" + movie_name + "/clust" + str(i)
    
        # create the folder if doesn't exists already
        if not os.path.isdir(file_path):
            os.makedirs(file_path)
        
        count = 0
        for index in range(len(cluster[indices[i]])):
            # extract the features of faces
            img, shape, name = images[cluster[indices[i]][index]]
        
            # if image contains multiple faces then don't extract it
            if int(name[len_of_file_name:]) not in face_ina_frame:
                continue
        
            # name for the image is stored in such a way the it contains the time stamp of 
            # the image is in the movie, this will help us in extracting the clips for each face
            image_path = file_path + "/" + name + "_" + str(count) 
            print("{}".format(image_path))
            count = count + 1
            # save the extracted image
            dlib.save_face_chip(img, shape, image_path, size=150, padding=0.25)

# calling the functoion to extract the faces from frame and then storing them in desired output file
extract_faces_from_frames(base_dir, movie_name)


"""
Final clustered faces will be stored in the path = base_dir + "clusters/" + movie_name 
"""