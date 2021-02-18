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
TRIGGERMODE = "Off" # "Off" % TODO make this param, i..e, camrera params.
# TODO: how to save camera settings PySpin?
NOSAVE = False # for debugging, to not save video or metadat.

def OpenCamera(cam_params, frameWidth=1152, frameHeight=1024):
    # Open and load features for all cameras
    print("=== Opening camera")
    n_cam = cam_params["n_cam"]
    cam_index = cam_params["cameraSelection"]
    camera_name = cam_params["cameraName"]

    cam_list = list_cameras()
    num_cameras = cam_list.GetSize()
    print('Number of cameras detected: %d' % num_cameras)

    # TODO: print device information.

    # Initialize camera object
    cam = Camera(index = cam_index)
    cam.init()

    # TODO: set pixelformat
    if False:
        if 'Bayer' in cam.PixelFormat:
            cam.PixelFormat = "RGB8"
    # cam.PixelFormat = "BGR8" # blackfly
    # cam.PixelFormat = "BayerGR8" # flea (default is BayerRG8)
    if True:
        print("Pixel format")
        print(cam.get_info("PixelFormat"))
        # cam.PixelFormat = "RGB8" # flea (default is BayerRG8)
        cam.PixelFormat = "BayerRG8" # flea (default is BayerRG8)
    else:
        cam.cam.PixelFormat.SetValue(PySpin.PixelFormat_BayerBG8)

    # TODO: set window smaller if desired
    if True:
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
    # # TODO, make this an option, but generally is triggering so dont need this.
    if False:
        try:
            cam.AcquisitionFrameRateEnable = True
        except:
            cam.AcquisitionFrameRateEnabled = True
        cam.AcquisitionFrameRateEnabled = True
        print(cam.get_info("AcquisitionFrameRate"))
        print(cam.get_info("AcquisitionFrameRateEnabled"))
        cam.AcquisitionFrameRate = cam_params["frameRate"]
    else:
        cam_params["frameRate"] = cam.AcquisitionFrameRate
    # TODO: why cam.AcquisitionFrameRate is throwing error?

    # To control the exposure settings, we need to turn off auto
    cam.GainAuto = 'Off'
    # Set the gain to 20 dB or the maximum of the camera.
    gain = min(20, cam.get_info('Gain')['max'])
    print("Setting gain to %.1f dB" % gain)
    cam.Gain = gain
    cam.ExposureAuto = 'Off'
    cam.ExposureTime = 4000 # microseconds

    # If we want an easily viewable image, turn on gamma correction.
    # NOTE: for scientific image processing, you probably want to
    #    _disable_ gamma correction!
    if False:
        try:
            cam.GammaEnabled = True
            cam.Gamma = 2.2
        except:
            print("Failed to change Gamma correction (not avaiable on some cameras).")

    # Other things:
    cam.AcquisitionMode = "Continuous"

    # configure
    # cam.TriggerMode=TRIGGERMODE # "Off"
    cam.TriggerMode=cam_params["triggerMode"] # "Off"
    cam.TriggerActivation = "RisingEdge"
    cam.TriggerSelector = "FrameStart"

    # get serial num
    cam_params['cameraSerialNo'] = cam.DeviceID

    # acquisition start
    cam.start() # Start recording

    camera = cam
    return camera, cam_params

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
    # filenum = 0 # keep track, for metadata saving purposes. only matter if saving
    # one file per trial.

    # Create dictionary for appending frame number and timestamp information
    # grabdata = {}
    # grabdata['timeStamp'] = []
    # grabdata['frameNumber'] = []
    # grabdata['newfile'] = []
    # grabdata["grabtime_firstframe"] = []
    grabdata = ResetGrabdata(cam_params, filenum=0)

    frameRate = cam_params['frameRate']
    recTimeInSec = cam_params['recTimeInSec']
    chunkLengthInSec = cam_params["chunkLengthInSec"]
    ds = cam_params["displayDownsample"]
    displayFrameRate = cam_params["displayFrameRate"]

    frameRatio = int(round(frameRate/displayFrameRate))
    numImagesToGrab = recTimeInSec*frameRate
    chunkLengthInFrames = int(round(chunkLengthInSec*frameRate))

    if cam_params["trialStructure"]:
        # then iti is used for timout 
        timeout = cam_params["trialITI"]
    else:
        timeout = None # then wait indefinitely

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
            print("STOPPING GRABBING")
            # CloseCamera(cam_params, camera, grabdata)
            writeQueue.append('STOP')
            # TODO: make option for this to end when long gap (inter trial interval).
            # TODO: make sure after this STOP, keeps going, with new file.
            CloseCamera(cam_params, camera, grabdata)
            break
        # Grab image from camera buffer if available
        # image_result = camera.get_image(wait=True)
        if True:
            # img = camera.get_array(timeout = 20) # msec
            img, tstamp = camera.get_array(timeout = cam_params['trialITI'], get_timestamp=True) # msec
        else:
            # image_result = camera.get_image(timeout = 20)
            image_result = camera.get_image()
            if not image_result.IsIncomplete():
                img  = ConvertImages(image_result)
                image_result.Release()
            else:
                img = None

        if img is not None:
            # Then got a frame

            # img  = ConvertImages(image_result)
            # image_converted = image_result.Convert(PySpin.PixelFormat_Mono8, PySpin.HQ_LINEAR)
            # img = image_converted.GetNDArray()

            # Get timestamp of grabbed frame from camera
            if cnt == 0:
                # timeFirstGrab2 = time.time_ns()
                timeFirstGrab = tstamp
            if framenum_thistrial==0:
                grabdata["grabtime_firstframe"]= timeFirstGrab/1e9

            # grabtime2 = (time.time_ns() - timeFirstGrab2)/1e9
            grabtime = (tstamp - timeFirstGrab)/1e9

            if len(grabdata['timeStamp'])>0:
                # then this is not first trial.
                inter_frame_time = 1000*(grabtime-grabdata['timeStamp'][-1])
                print("grabtime, inter_frame_time", grabtime, inter_frame_time)
                
                # uncomment this and above to compare two methods for getting time.
                # print(grabtime, grabtime2, (grabtime2-grabtime)*1000)

            # split file? This useful for trial-based recordings. (one video per trial)
            # (each trial separated by a long duration)
            grabdata['timeStamp'].append(grabtime)

            # Append numpy array to writeQueue for writer to append to file
            if not NOSAVE:
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
                print('Camera %i collected %i frames at %i fps (average over all rec).' % (n_cam,cnt,fps_count))

            # === print things
            if DEBUG:
                print(grabdata)
                print(len(writeQueue))
                if len(writeQueue)>30:
                    break
        else:
            if cam_params["trialStructure"]:
                if framenum_thistrial>0:
                    # Then this signals ed of a trial
                    print("ITI, filenum ended: ", grabdata["filenum"])
                    # Save this fil;e.

                    # INitialize new fil;e
                    writeQueue.append('NEWFILE')
                    if len(grabdata['newfile'])>0:
                        grabdata['newfile'][-1] = 1 # the last frame is the end of the old file.
                        # TODO, what is purpose of newfiel?

                    # TODO: save grabdata
                    # TODO: reset grabdata (for a new file).
                    SaveMetadata(cam_params, grabdata)

                    # update framenum and filenum (for next file)
                    framenum_thistrial = 0
                    # TODO: Reset grabdata, one for each file.
                    grabdata = ResetGrabdata(cam_params, grabdata["filenum"]+1)
                else:
                    # do nothing, have already saved previous trila
                    print("Ready for triggers.")
            else:
                # time.sleep(0.0001)
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


def ResetGrabdata(cam_params, filenum):
    grabdata = {}
    grabdata['timeStamp'] = []
    grabdata['frameNumber'] = []
    grabdata['newfile'] = []
    grabdata["grabtime_firstframe"] = []
    grabdata["frameNumberThisTrial"] = []
    grabdata["filenum"] = filenum
    return grabdata


def SaveMetadata(cam_params, grabdata):
    # TODO: look thru this. seems to be working.
    if NOSAVE:
        return
    n_cam = cam_params["n_cam"]

    full_folder_name = os.path.join(cam_params["videoFolder"], cam_params["cameraName"])

    meta = cam_params
    meta['timeStamp'] = grabdata['timeStamp'] # time since first frame first trial
    meta['frameNumber'] = grabdata['frameNumber'] # counting from rec onset.

    frame_count = grabdata['frameNumber'][-1]
    time_count = grabdata['timeStamp'][-1]
    fps_count = int(round(frame_count/time_count))
    print('Camera {} saved {} frames at {} fps.'.format(n_cam+1, frame_count, fps_count)) # TODO, this fps only accurate if one long file.

    if cam_params["trialStructure"]:
        suffix = f"-t{grabdata['filenum']}"
        print("suffix", suffix)
    else:
        suffix = ""

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
