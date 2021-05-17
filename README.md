# Long Video Demo
https://drive.google.com/file/d/1B7S95qA6Q3HBiQav-nmqoOoADsOArAOi/view?usp=sharing

# Streaming Video Recorder
Use OpenCV-Python and Flask to create a web streaming video recorder for camera.

## Environment
* Python 2.7 or 3.5
* OpenCV 3.3.0

## How to Run 
1. Install **Flask**:

    ```
    pip install -r requirements.txt
    ```

2. Run the app:

    ```
    python server.py
    ```
    ![camera list in Python](screenshot/web-camera-video-recorder.PNG)

## TFX:
We implemented a working TFX Pipeline for WL-ASL Video Dataset.

To build the same, we processed the videos for book sign only and converted all the videos to TFRecords because of storage efficiency and parallel I/O operations. The JSON input for WL-ASL has frame start, frame end information, which we used to consider the start & stop of the frames where the actual signing happens for each video. Built the components - ImportExampleGen, StatisticsGen, SchemaGen, Transformer, Trainer, Model Resolver, Evaluator and Pusher components. We created a pipeline with the list of components to execute with sequence and feed that pipeline as input to LocalDagRunner, which is imported from tfx.orchestration. We are able to run the pipeline without Interactivecontext or manually running cells. And the models are evaluated agains the eval config which has checks for examplecount and accuracy and blesses only the model that satisfies the evaluation to Pusher. 

## Reference
* https://github.com/log0/video_streaming_with_flask_example

## Blog
[How to Build Web Camera Recorder Using OpenCV and Flask][1]

[0]:https://en.wikipedia.org/wiki/Microsoft_Windows_SDK
[1]:http://www.codepool.biz/web-camera-recorder-oepncv-flask.html
