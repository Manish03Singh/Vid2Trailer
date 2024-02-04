## Video to trailer

<p>The outcomes of the research paper implementation can be found at this link. Feel free to explore the results i.e., 
    <a href="https://drive.google.com/drive/folders/1ERS2DJhe46RSbsDMnYD58fzuDmyJDjBK?usp=sharing">Automatic Generated Trailers</a>
</p>

<p>Access the Research Paper <a href="https://drive.google.com/file/d/1gCyhtx5QcFZ3qiEdax-VKRi8goyTWXlf/view?usp=sharing">Here</a></p>

<p>Access the Abstract of the Research Paper Implementation - 
    <a href="https://docs.google.com/presentation/d/1cqr1PMEaycoEpb6BbBbNdgpN6SPolGNd/edit?usp=sharing&ouid=111838531212974621504&rtpof=true&sd=true">ppt</a>
</p>

# Description
<p>
This project focuses on Automatic Trailer Generation (ATG), aiming to create highly attractive videos while avoiding spoilers of the main plot. The process involves extracting various components from the video, such as Theme Music and Impressive Shots, and concatenating them to form a compelling trailer. Techniques like Audio Sentiment Analysis and Scene Composition Analysis are applied to enhance the trailer's appeal. Notable ATG approaches include Vid2Trailer, Point Process-Based Visual Attractiveness Model, and Human-AI Joint Trailer Generation. Vid2Trailer employs automated methods, while the Point Process-Based Model gauges visual attractiveness through eye movement analysis. Human-AI Joint Trailer Generation combines human creativity with AI to identify and sequence the best shots, utilizing techniques like Audio Visual Segmentation and Visual Sentiment Analysis. Early ATG techniques were grounded in video summarization, selecting key frames to preserve the storyline.</p>

<p>Vid2Trailer operates through three key stages: symbol extraction, impressive component extraction, and reconstruction. Extracted elements are strategically re-ordered to maximize viewer impact. Certain rules are applied for enhanced effectiveness, such as placing the title logo at the end and overlaying impressive speech at regular intervals on the theme music. The process is segmented into tasks including theme music extraction, title logo extraction, impressive speech extraction, impressive shot extraction, main character face extraction, and ultimately stitching all these components together to create the final trailer.</p>


# Title Logo Extraction
<p>The title logo serves as the primary visual representation of a movie, typically featured at the movie's outset along with other captions like the cast, production staff, and distributors. Title logo extraction focuses on identifying the largest font size captions in the initial part of the movie, as the title logo usually stands out with a larger font. Observations indicate that the title logo appears within the first 10% of the entire movie, leading to the application of Title Logo and Production House Name detection specifically on this initial segment for effective extraction.</p>

<p>The TEXT DETECTION feature of the Google Cloud Video Intelligence API was employed to identify text within a video. This feature analyzes frames, providing information on text duration and position in each frame. Utilizing text position data, the area of each detected text is calculated. Subsequently, all identified texts are sorted based on larger area and longer duration. The next step involves matching these texts against a predefined dictionary, retaining only those with word similarity surpassing a specified threshold. This process ensures accurate and filtered text detection in the video.</p>

<img src="/assets/figure.png" alt="image"/>
<span>Overview of V2T technical architecture</span><br>

<p>After obtaining all the accurately detected text, overlapping time intervals were merged. The next step involved extracting video clips based on the time stamps of the text, prioritizing those most likely to contain the title logo and production house name. To facilitate clip extraction, Python libraries pydub and moviepy.editor were utilized. These tools ensured efficient processing and extraction of relevant clips from the video based on the identified time stamps.</p>

# Theme Music Extraction

<p>The extraction of theme music is a crucial aspect in conveying the movie's mood. This process relies on two key observations: first, theme music tends to play for an extended duration compared to other music components, and second, the melody is recurrent throughout the movie. The extraction method involves identifying the most frequently used music segment with the longest duration based on these observations. Initially, the top 10% of the longest music segments from the original audio track are extracted. Subsequently, the most frequently used melody is detected from all the extracted segments, employing a melody matching technique. This involves extracting a 12-dimensional chroma vector from each music segment, defining the magnitude on each chroma within a 12-pitch class octave. This meticulous process ensures the accurate extraction of the movie's theme music.</p>

<p>The audio was extracted from the movie using moviepy.editor in Python, leading to the separation of the music and voice tracks. The music track was further processed for title music extraction by utilizing the spleeter library. The ina_speech_segmenter library was employed to generate a CSV file containing timestamps of music, noise, and silence within the music track. Clips exclusively containing music were then extracted using pydub based on the stored timestamps. The longest 10% of these clips were selected for processing, and a 12-dimensional chroma vector was calculated for each. Pairwise similarity was computed for all clips, allowing the determination of a repetitive score for each. The clips with the highest repetitive scores were identified as the movie's theme music. In cases where the top-scoring clip was insufficient for a trailer, it was merged with the next highest-scoring clip. Typically, each extracted clip's duration in the movie ranged from 120 to 150 seconds, necessitating merging only in specific instances.</p>

# Main Character Face Extraction

<p>Incorporating a brief segment into the Vid2Trailer method, we introduced a 1-2 second clip of a main character as a prelude. This snippet, extracted from a scene with minimal movement, serves to provide viewers with an initial glimpse of the movie's cast. By interspersing faces of prominent stars featured in the film, this section establishes the trailer's tone and generates excitement without revealing the entire ensemble. This strategic approach aims to captivate viewers by preserving surprises, ensuring that reactions during the movie itself are enhanced by the element of unpredictability.</p>

<p>The Google Cloud Video Intelligence API's FACE DETECTION, SPEECH TRANSCRIPTION, and SHOT CHANGE DETECTION features were utilized for comprehensive video analysis. Face Detection provided detailed data on all detected faces with their corresponding timestamps in the frames. Speech Transcription delivered captions for each frame, while Shot Change Detection identified time stamps for shot change sequences. The dlib library was employed to extract facial features from the detected faces. To achieve immobile and close-up shots of main characters, faces detected during shot changes and captioned frames were discarded. Dlib was further used to calculate the number of faces in each frame, retaining only those with a single face detected for close-up shots. The coordinates of the faces were stored to facilitate the calculation of face area, ensuring precision in the extraction process.</p>

<p>Chinese Whispers Clustering from dlib played a crucial role in clustering faces based on their facial features. The top clusters, identified by maximum size, represented the faces of the main character. From the leading cluster, faces with the maximum area were selected to generate close-up clips of the main character, with face area normalization applied. Subsequently, clips were extracted from these chosen faces. The next step involved selecting clips with the least mobility for each character. Mobility was determined by calculating frame similarity, where greater similarity indicated less movement in the clip. This process ensured the extraction of visually engaging clips with minimal character movement.</p>

<p>In the final step, the title logo, theme music, impressive speeches, impressive shots, and main character faces are meticulously arranged into the shot sequence. The production house name is strategically placed at the beginning of the trailer, while the title logo is inserted at the trailer's conclusion. Impressive speech segments overlay the theme music at regular intervals, adhering to specific rules designed to enhance the overall impact on viewers. This thoughtful arrangement ensures a captivating and impactful viewing experience for the audience.</p>

Codes and output of all the parts (Title Logo extraction, Theme Music extraction and,
Main character faces extraction) is uploaded on this link.
All the trailer my group made are uploaded on this link.
</p>

<br>
<p>Visit me on <a href='https://www.linkedin.com/in/manish-kumar-singh-12a28a190/' target='_blank'>linkedin</a> and <a href='https://twitter.com/Manish_03_Singh' target='_blank'>twitter</a></p>