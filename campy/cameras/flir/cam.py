import PySpin
import os
import time
import logging
import sys
import numpy as np
from collections import deque
import csv
from simple_pyspin import Camera, list_cameras

DEBUG = False

def OpenCamera(cam_params, frameWidth=1152, frameHeight=1024):
    # Open and load features for all cameras
    print("=== Opening camera")
    n_cam = cam_params["n_cam"]
    cam_index = cam_params["cameraSelection"]
    camera_name = cam_params["cameraName"]
    result = True

    cam_list = list_cameras()
    num_cameras = cam_list.GetSize()
    print('Number of cameras detected: %d' % num_cameras)

    # TODO: replace with simple_pyspin.
    if False:
        for i, camera in enumerate(cam_list):
            if i == cam_index:
                # Retrieve TL device nodemap
                nodemap_tldevice = camera.GetTLDeviceNodeMap()
                # Print device information
                print('Printing device information for camera %d... \n' % i)
                PrintDeviceInfo(nodemap_tldevice)

    # Initialize camera object
    cam = Camera(index = cam_index)
    cam.init()

    if False:
        if 'Bayer' in cam.PixelFormat:
            cam.PixelFormat = "RGB8"
    cam.PixelFormat = "BGR8"

    # Set the area of interest (AOI) to the middle half
    # cam.Width = cam.SensorWidth // 2
    if False:
        hmax = cam.get_info("Height")["max"]
        wmax = cam.get_info("Width")["max"]
        cam.Width = wmax
        # cam.Height = cam.SensorHeight // 2
        # cam.Height = cam.SensorHeight // 2
        cam.Height = hmax
        cam.OffsetX = 0
        cam.OffsetY = 0
        # Configure custom image settings
        # frameWidth, frameHeight = ConfigureCustomImageSettings(cam_params, nodemap)
        cam_params["frameWidth"] = cam.Width
        cam_params["frameHeight"] = cam.Height
    else:
        cam.Width = cam_params["frameWidth"]
        cam.Height = cam_params["frameHeight"] 


    # To change the frame rate, we need to enable manual control
    # cam.AcquisitionFrameRateAuto = 'Off'
    cam.AcquisitionFrameRateEnable = True
    cam.AcquisitionFrameRate = cam_params["frameRate"]

    # To control the exposure settings, we need to turn off auto
    cam.GainAuto = 'Off'
    # Set the gain to 20 dB or the maximum of the camera.
    gain = min(20, cam.get_info('Gain')['max'])
    print("Setting gain to %.1f dB" % gain)
    cam.Gain = gain
    cam.ExposureAuto = 'Off'
    cam.ExposureTime = 5000 # microseconds

    # If we want an easily viewable image, turn on gamma correction.
    # NOTE: for scientific image processing, you probably want to
    #    _disable_ gamma correction!
    try:
        cam.GammaEnabled = True
        cam.Gamma = 2.2
    except:
        print("Failed to change Gamma correction (not avaiable on some cameras).")

    # Other things:
    cam.AcquisitionMode = "Continuous"

    # configure
    cam.TriggerMode="Off"

    # get serial num
    cam_params['cameraSerialNo'] = cam.DeviceID

    # acquisition start
    cam.start() # Start recording
    if False:
        imgs = [cam.get_array() for n in range(10)] # Get 10 frames
        cam.stop() # Stop recording

    camera = cam
    return camera, cam_params


# def GrabFramesTrials(cam_params, camera, writeQueue, dispQueue, stopQueue, v1=False):
#     """
#     v1, use old version where intertrial interval is based on time between successive frames. this 
#     problem is that saves after frame 0. new version saves during ITI istelf. detects ITI based on 
#     duration of timeout for getNextFrame.
#     """

#     n_cam = cam_params["n_cam"]

#     cnt = 0 # cumulative frames over all files.
#     timeout = 0
#     framenum_thistrial = 0 # framenum within this trial (i.e., file)
#     filenum = 0 # keep track, for metadata saving purposes. only matter if saving
#     # one file per trial.

#     # Create dictionary for appending frame number and timestamp information
#     # grabdata = {}
#     # grabdata['timeStamp'] = []
#     # grabdata['frameNumber'] = []
#     # grabdata['newfile'] = []
#     # grabdata["grabtime_firstframe"] = []
#     grabdata = ResetGrabdata(cam_params)

#     frameRate = cam_params['frameRate']
#     recTimeInSec = cam_params['recTimeInSec']
#     chunkLengthInSec = cam_params["chunkLengthInSec"]
#     ds = cam_params["displayDownsample"]
#     displayFrameRate = cam_params["displayFrameRate"]

#     frameRatio = int(round(frameRate/displayFrameRate))
#     numImagesToGrab = recTimeInSec*frameRate
#     chunkLengthInFrames = int(round(chunkLengthInSec*frameRate))

#     grabbing = False
#     if False:
#         if cam_params["trigConfig"] and cam_params["settingsConfig"]:
#             grabbing = True
#     else:
#         grabbing = True
#     print(cam_params["cameraName"], "ready to trigger.")

#     while(grabbing):
#         if stopQueue or cnt >= numImagesToGrab: # TODO, also add limit within each file.
#             # Stop experiment.
#             # CloseCamera(cam_params, camera, grabdata)
#             writeQueue.append('STOP')
#             # TODO: make option for this to end when long gap (inter trial interval).
#             # TODO: make sure after this STOP, keeps going, with new file.
#             break
#         try:
#             # Grab image from camera buffer if available
#             try:
#                 if v1:
#                     image_result = camera.get_image(wait=False)
#                 else:
#                     image_result = camera.get_image(wait=False)

#                 if not image_result.IsIncomplete():
#                     img  = ConvertImages(image_result)
#                     # image_converted = image_result.Convert(PySpin.PixelFormat_Mono8, PySpin.HQ_LINEAR)
#                     # img = image_converted.GetNDArray()

#                     # Get timestamp of grabbed frame from camera
#                     if cnt == 0:
#                         timeFirstGrab = time.monotonic_ns()
#                         grabdata["grabtime_firstframe"]=timeFirstGrab/1e9
#                     grabtime = (time.monotonic_ns() - timeFirstGrab)/1e9
#                     if len(grabdata['timeStamp'])>0:
#                         inter_frame_time = 1000*(grabtime-grabdata['timeStamp'][-1])
#                         print("grabtime, inter_frame_time", grabtime, inter_frame_time)
#                         # TODO: printing above, make working when metadat one for each fil;e.

#                     # split file? This useful for trial-based recordings. (one video per trial)
#                     # (each trial separated by a long duration)
#                     if v1:
#                         # This moved to outside this loop.
#                         if cam_params['trialStructure'] and len(grabdata['timeStamp'])>0:
#                             if inter_frame_time>cam_params['trialITI']:
#                                 writeQueue.append('NEWFILE')
#                                 grabdata['newfile'].append(1)
#                                 filenum += 1
#                                 # TODO: save grabdata
#                                 # TODO: reset grabdata (for a new file).
#                                 SaveMetadata(cam_params, grabdata, suffix=f"-t{filenum}")
#                                 grabdata = ResetGrabdata(cam_params)
#                             else:
#                                 grabdata['newfile'].append(0)
                    
#                     grabdata['timeStamp'].append(grabtime)

#                     # Append numpy array to writeQueue for writer to append to file
#                     writeQueue.append(img)
#                     framenum_thistrial += 1
#                     cnt += 1
#                     grabdata["frameNumberThisTrial"].append(framenum_thistrial)
#                     grabdata['frameNumber'].append(cnt) # first frame = 1

#                     if cnt % frameRatio == 0:
#                         dispQueue.append(img[::ds,::ds])

#                     # Release grab object
#                     image_result.Release()

#                     if cnt % chunkLengthInFrames == 0:
#                         fps_count = int(round(cnt/grabtime))
#                         print('Camera %i collected %i frames at %i fps.' % (n_cam,cnt,fps_count))

#                     # === print things
#                     if DEBUG:
#                         print(grabdata)
#                         print(len(writeQueue))
#                         if len(writeQueue)>30:
#                             break
#                 else:
#                     print("Image incomplete (why?)")
#                     print('Image incomplete with image status %d ... \n' % image_result.GetImageStatus())
#                     assert False
#             except PySpin.SpinnakerException as ex:
#                 if framenum_thistrial>0:
#                     if not v1:
#                         # then is trial end

#                         print("ITI, filenum ended: ", filenum)
#                         # Save this fil;e.

#                         # INitialize new fil;e
#                         writeQueue.append('NEWFILE')
#                         if len(grabdata['newfile'])>0:
#                             grabdata['newfile'][-1] = 1 # the last frame is the end of the old file.

#                         # TODO: save grabdata
#                         # TODO: reset grabdata (for a new file).
#                         SaveMetadata(cam_params, grabdata, suffix=f"-t{filenum}")
#                         grabdata = ResetGrabdata(cam_params)

#                         # update framenum and filenum (for next file)
#                         framenum_thistrial = 0
#                         filenum += 1
#                         # TODO: Reset grabdata, one for each file.
#                 else:
#                     # do nothing, have already saved previous trila
#                     print("Ready for triggers.")



#                 # if len(grabdata["frameNumber"])>0:
#                 # else:
#                 #   print("Ready for triggers.")

#         # Else wait for next frame available
#         except PySpin.SpinnakerException as ex:
#             print('Error: %s' % ex)
#             result = False
#         except Exception as e:
#             logging.error('Caught exception: {}'.format(e))

def ConvertImages(image_result):
    if False:
        print(img)
        print(image_result)
        print(img.GetNDArray())
        print(np.asarray(img.GetNDArray(), dtype="uint8"))
        assert False
    image_converted = image_result.Convert(PySpin.PixelFormat_Mono8, PySpin.HQ_LINEAR)
    if False:
        # to devbug why videos images are tiled.
        image_converted.Save("/tmp/tmp.png")
    img = np.asarray(image_converted.GetNDArray(), dtype="uint8")

    return img


def GrabFrames(cam_params, camera, writeQueue, dispQueue, stopQueue, v1=False):
    """
    v1, use old version where intertrial interval is based on time between successive frames. this 
    problem is that saves after frame 0. new version saves during ITI istelf. detects ITI based on 
    duration of timeout for getNextFrame.
    """

    n_cam = cam_params["n_cam"]

    cnt = 0 # cumulative frames over all files.
    timeout = 0
    framenum_thistrial = 0 # framenum within this trial (i.e., file)
    filenum = 0 # keep track, for metadata saving purposes. only matter if saving
    # one file per trial.

    # Create dictionary for appending frame number and timestamp information
    # grabdata = {}
    # grabdata['timeStamp'] = []
    # grabdata['frameNumber'] = []
    # grabdata['newfile'] = []
    # grabdata["grabtime_firstframe"] = []
    grabdata = ResetGrabdata(cam_params)

    frameRate = cam_params['frameRate']
    recTimeInSec = cam_params['recTimeInSec']
    chunkLengthInSec = cam_params["chunkLengthInSec"]
    ds = cam_params["displayDownsample"]
    displayFrameRate = cam_params["displayFrameRate"]

    frameRatio = int(round(frameRate/displayFrameRate))
    numImagesToGrab = recTimeInSec*frameRate
    chunkLengthInFrames = int(round(chunkLengthInSec*frameRate))

    grabbing = False
    if False:
        if cam_params["trigConfig"] and cam_params["settingsConfig"]:
            grabbing = True
    else:
        grabbing = True
    print(cam_params["cameraName"], "ready to trigger.")

    while(grabbing):
        if stopQueue or cnt >= numImagesToGrab: # TODO, also add limit within each file.
            # Stop experiment.
            print("HERE (cam.py)")
            # CloseCamera(cam_params, camera, grabdata)
            writeQueue.append('STOP')
            # TODO: make option for this to end when long gap (inter trial interval).
            # TODO: make sure after this STOP, keeps going, with new file.
            break
        # Grab image from camera buffer if available
        try:
            # image_result = camera.get_image(wait=True)
            if True:
                img = camera.get_array(timeout = 20) # msec
            else:
                image_result = camera.get_image(timeout = 20)
                if not image_result.IsIncomplete():
                    img  = ConvertImages(image_result)
                    image_result.Release()
                else:
                    img = None


            # img  = ConvertImages(image_result)
            # image_converted = image_result.Convert(PySpin.PixelFormat_Mono8, PySpin.HQ_LINEAR)
            # img = image_converted.GetNDArray()

            # Get timestamp of grabbed frame from camera
            if cnt == 0:
                timeFirstGrab = time.monotonic_ns()
                grabdata["grabtime_firstframe"]=timeFirstGrab/1e9
            grabtime = (time.monotonic_ns() - timeFirstGrab)/1e9
            if len(grabdata['timeStamp'])>0:
                inter_frame_time = 1000*(grabtime-grabdata['timeStamp'][-1])
                print("grabtime, inter_frame_time", grabtime, inter_frame_time)
                # TODO: printing above, make working when metadat one for each fil;e.

            # split file? This useful for trial-based recordings. (one video per trial)
            # (each trial separated by a long duration)
            grabdata['timeStamp'].append(grabtime)

            # Append numpy array to writeQueue for writer to append to file
            writeQueue.append(img)
            framenum_thistrial += 1
            cnt += 1
            grabdata["frameNumberThisTrial"].append(framenum_thistrial)
            grabdata['frameNumber'].append(cnt) # first frame = 1

            if cnt % frameRatio == 0:
                dispQueue.append(img[::ds,::ds])

            # Release grab object
            # image_result.Release()

            if cnt % chunkLengthInFrames == 0:
                fps_count = int(round(cnt/grabtime))
                print('Camera %i collected %i frames at %i fps.' % (n_cam,cnt,fps_count))

            # === print things
            if DEBUG:
                print(grabdata)
                print(len(writeQueue))
                if len(writeQueue)>30:
                    break
        except PySpin.SpinnakerException as ex:
            if cam_params["trialStructure"]:
                if framenum_thistrial>0:
                    # then is trial end

                    print("ITI, filenum ended: ", filenum)
                    # Save this fil;e.

                    # INitialize new fil;e
                    writeQueue.append('NEWFILE')
                    if len(grabdata['newfile'])>0:
                        grabdata['newfile'][-1] = 1 # the last frame is the end of the old file.

                    # TODO: save grabdata
                    # TODO: reset grabdata (for a new file).
                    SaveMetadata(cam_params, grabdata, suffix=f"-t{filenum}")
                    grabdata = ResetGrabdata(cam_params)

                    # update framenum and filenum (for next file)
                    framenum_thistrial = 0
                    filenum += 1
                    # TODO: Reset grabdata, one for each file.
                else:
                    # do nothing, have already saved previous trila
                    print("Ready for triggers.")
            else:
                print("Waiting for frames")




        #     # if len(grabdata["frameNumber"])>0:
        #     # else:
        #     #   print("Ready for triggers.")

        # # Else wait for next frame available
        # except PySpin.SpinnakerException as ex:
        #     print('Error: %s' % ex)
        #     result = False
        # except Exception as e:
        #     logging.error('Caught exception: {}'.format(e))


def ResetGrabdata(cam_params):
    grabdata = {}
    grabdata['timeStamp'] = []
    grabdata['frameNumber'] = []
    grabdata['newfile'] = []
    grabdata["grabtime_firstframe"] = []
    grabdata["frameNumberThisTrial"] = []
    return grabdata


def SaveMetadata(cam_params, grabdata, suffix=""):
    # TODO: look thru this. seems to be working.
    n_cam = cam_params["n_cam"]

    full_folder_name = os.path.join(cam_params["videoFolder"], cam_params["cameraName"])

    meta = cam_params
    meta['timeStamp'] = grabdata['timeStamp']
    meta['frameNumber'] = grabdata['frameNumber']

    frame_count = grabdata['frameNumber'][-1]
    time_count = grabdata['timeStamp'][-1]
    fps_count = int(round(frame_count/time_count))
    print('Camera {} saved {} frames at {} fps.'.format(n_cam+1, frame_count, fps_count)) # TODO, this fps only accurate if one long file.

    print("suffix", suffix)

    try:
        npy_filename = os.path.join(full_folder_name, f"frametimes{suffix}.npy")
        x = np.array([meta['frameNumber'], meta['timeStamp']])
        np.save(npy_filename,x)
        print(f"Saved numpy at: {npy_filename}")
    except Exception as err:
        print(err)
        pass

    csv_filename = os.path.join(full_folder_name, f"metadata{suffix}.csv")
    meta = cam_params
    meta['totalFrames'] = grabdata['frameNumber'][-1]
    meta['totalTime'] = grabdata['timeStamp'][-1]
    for k in ['newfile']:
        meta[k] = grabdata[k]
    meta["grabtime_firstframe"] = grabdata["grabtime_firstframe"]
    # TODO: Save all the other metaparams in grabdata too.

    keys = meta.keys()
    vals = meta.values()
    
    try:
        print(f"Saved metadat at: {csv_filename}")
        with open(csv_filename, 'w', newline='') as f:
            w = csv.writer(f, delimiter=',', quoting=csv.QUOTE_ALL)
            for row in meta.items():
                w.writerow(row)
    except Exception as err:
        print(err)
        pass

def CloseCamera(cam_params, camera, grabdata):
    n_cam = cam_params["n_cam"]

    print('Closing camera {}... Please wait.'.format(n_cam+1))
    # Close Basler camera after acquisition stops
    # TODO: fix camera closing
    try:
        SaveMetadata(cam_params,grabdata)
        time.sleep(1)
        camera.stop()
        camera.close()
        # camera.EndAcquisition()     
        # camera.DeInit()
        # del camera
    except Exception as err: 
        print(err)
        print("TRIED TO CLOSE, FAILED")
        time.sleep(0.1)
