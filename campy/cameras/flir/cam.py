"""
"""

import PySpin
import os
import time
import logging
import sys
import numpy as np
from collections import deque
import csv

DEBUG = False

class TriggerType:
	SOFTWARE = 1
	HARDWARE = 2

CHOSEN_TRIGGER = TriggerType.HARDWARE

# def ConfigureTrigger(camera):
# 	"""
# 	This function configures the camera to use a trigger. First, trigger mode is
# 	ensured to be off in order to select the trigger source. Trigger mode is
# 	then enabled, which has the camera capture only a single image upon the
# 	execution of the chosen trigger.
# 	 :param cam: Camera to configure trigger for.
# 	 :type cam: CameraPtr
# 	 :return: True if successful, False otherwise.
# 	 :rtype: bool
# 	"""

# 	print('*** CONFIGURING TRIGGER ***\n')
# 	if CHOSEN_TRIGGER == TriggerType.SOFTWARE:
# 		print('Software trigger chosen...')
# 	elif CHOSEN_TRIGGER == TriggerType.HARDWARE:
# 		print('Hardware trigger chose...')

# 	try:
# 		result = True
# 		# Ensure trigger mode off
# 		# The trigger must be disabled in order to configure whether the source
# 		# is software or hardware.
# 		if camera.TriggerMode.GetAccessMode() != PySpin.RW:
# 			print('Unable to disable trigger mode (node retrieval). Aborting...')
# 			return False
# 		camera.TriggerMode.SetValue(PySpin.TriggerMode_Off)
# 		print('Trigger mode disabled...')

# 		# Select trigger source
# 		# The trigger source must be set to hardware or software while trigger
# 		# mode is off.
# 		if camera.TriggerSource.GetAccessMode() != PySpin.RW:
# 			print('Unable to get trigger source (node retrieval). Aborting...')
# 			return False

# 		if CHOSEN_TRIGGER == TriggerType.SOFTWARE:
# 			camera.TriggerSource.SetValue(PySpin.TriggerSource_Software)
# 		elif CHOSEN_TRIGGER == TriggerType.HARDWARE:
# 			camera.TriggerSource.SetValue(PySpin.TriggerSource_Line0)

# 		# Turn trigger mode on
# 		# Once the appropriate trigger source has been set, turn trigger mode
# 		# on in order to retrieve images using the trigger.
# 		camera.TriggerMode.SetValue(PySpin.TriggerMode_On)
# 		print('Trigger mode turned back on...')

# 	except PySpin.SpinnakerException as ex:
# 		print('Error: %s' % ex)
# 		return False

# 	return result

def configure_exposure(cam):
    """
     This function configures a custom exposure time. Automatic exposure is turned
     off in order to allow for the customization, and then the custom setting is
     applied.

     :param cam: Camera to configure exposure for.
     :type cam: CameraPtr
     :return: True if successful, False otherwise.
     :rtype: bool
    """

    print('*** CONFIGURING EXPOSURE ***\n')

    try:
        result = True

        # Turn off automatic exposure mode
        #
        # *** NOTES ***
        # Automatic exposure prevents the manual configuration of exposure
        # times and needs to be turned off for this example. Enumerations
        # representing entry nodes have been added to QuickSpin. This allows
        # for the much easier setting of enumeration nodes to new values.
        #
        # The naming convention of QuickSpin enums is the name of the
        # enumeration node followed by an underscore and the symbolic of
        # the entry node. Selecting "Off" on the "ExposureAuto" node is
        # thus named "ExposureAuto_Off".
        #
        # *** LATER ***
        # Exposure time can be set automatically or manually as needed. This
        # example turns automatic exposure off to set it manually and back
        # on to return the camera to its default state.

        if cam.ExposureAuto.GetAccessMode() != PySpin.RW:
            print('Unable to disable automatic exposure. Aborting...')
            return False

        cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
        print('Automatic exposure disabled...')

        # Set exposure time manually; exposure time recorded in microseconds
        #
        # *** NOTES ***
        # Notice that the node is checked for availability and writability
        # prior to the setting of the node. In QuickSpin, availability and
        # writability are ensured by checking the access mode.
        #
        # Further, it is ensured that the desired exposure time does not exceed
        # the maximum. Exposure time is counted in microseconds - this can be
        # found out either by retrieving the unit with the GetUnit() method or
        # by checking SpinView.

        if cam.ExposureTime.GetAccessMode() != PySpin.RW:
            print('Unable to set exposure time. Aborting...')
            return False

        # Ensure desired exposure time does not exceed the maximum
        # exposure_time_to_set = 2000000.0
        exposure_time_to_set = 6000.0
        print(cam.ExposureTime.GetMax())
        exposure_time_to_set = min(cam.ExposureTime.GetMax(), exposure_time_to_set)
        cam.ExposureTime.SetValue(exposure_time_to_set)
        print('Shutter time set to %s us...\n' % exposure_time_to_set)

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        result = False

    return result



def configure_custom_image_settings(cam):
    """
    Configures a number of settings on the camera including offsets X and Y,
    width, height, and pixel format. These settings must be applied before
    BeginAcquisition() is called; otherwise, those nodes would be read only.
    Also, it is important to note that settings are applied immediately.
    This means if you plan to reduce the width and move the x offset accordingly,
    you need to apply such changes in the appropriate order.

    :param cam: Camera to configure settings on.
    :type cam: CameraPtr
    :return: True if successful, False otherwise.
    :rtype: bool
    """
    print('\n*** CONFIGURING CUSTOM IMAGE SETTINGS ***\n')

    try:
        result = True

        # Apply mono 8 pixel format
        #
        # *** NOTES ***
        # In QuickSpin, enumeration nodes are as easy to set as other node
        # types. This is because enum values representing each entry node
        # are added to the API.
        if cam.PixelFormat.GetAccessMode() == PySpin.RW:
            cam.PixelFormat.SetValue(PySpin.PixelFormat_Mono8)
            print('Pixel format set to %s...' % cam.PixelFormat.GetCurrentEntry().GetSymbolic())

        else:
            print('Pixel format not available...')
            result = False
            
        # Apply minimum to offset X
        #
        # *** NOTES ***
        # Numeric nodes have both a minimum and maximum. A minimum is retrieved
        # with the method GetMin(). Sometimes it can be important to check
        # minimums to ensure that your desired value is within range.
        if cam.OffsetX.GetAccessMode() == PySpin.RW:
            cam.OffsetX.SetValue(cam.OffsetX.GetMin())
            print('Offset X set to %d...' % cam.OffsetX.GetValue())

        else:
            print('Offset X not available...')
            result = False

        # Apply minimum to offset Y
        #
        # *** NOTES ***
        # It is often desirable to check the increment as well. The increment
        # is a number of which a desired value must be a multiple. Certain
        # nodes, such as those corresponding to offsets X and Y, have an
        # increment of 1, which basically means that any value within range
        # is appropriate. The increment is retrieved with the method GetInc().
        if cam.OffsetY.GetAccessMode() == PySpin.RW:
            cam.OffsetY.SetValue(cam.OffsetY.GetMin())
            print('Offset Y set to %d...' % cam.OffsetY.GetValue())

        else:
            print('Offset Y not available...')
            result = False

        # Set maximum width
        #
        # *** NOTES ***
        # Other nodes, such as those corresponding to image width and height,
        # might have an increment other than 1. In these cases, it can be
        # important to check that the desired value is a multiple of the
        # increment.
        #
        # This is often the case for width and height nodes. However, because
        # these nodes are being set to their maximums, there is no real reason
        # to check against the increment.
        if cam.Width.GetAccessMode() == PySpin.RW and cam.Width.GetInc() != 0 and cam.Width.GetMax != 0:
            cam.Width.SetValue(cam.Width.GetMax())
            print('Width set to %i...' % cam.Width.GetValue())

        else:
            print('Width not available...')
            result = False

        # Set maximum height
        #
        # *** NOTES ***
        # A maximum is retrieved with the method GetMax(). A node's minimum and
        # maximum should always be a multiple of its increment.
        if cam.Height.GetAccessMode() == PySpin.RW and cam.Height.GetInc() != 0 and cam.Height.GetMax != 0:
            cam.Height.SetValue(cam.Height.GetMax())
            print('Height set to %i...' % cam.Height.GetValue())

        else:
            print('Height not available...')
            result = False

    except PySpin.SpinnakerException as ex:
        print('Error: %s' % ex)
        return False

    return result



def ConfigureCustomImageSettings(cam_params, nodemap):
	"""
	Configures a number of settings on the camera including offsets  X and Y, width,
	height, and pixel format. These settings must be applied before BeginAcquisition()
	is called; otherwise, they will be read only. Also, it is important to note that
	settings are applied immediately. This means if you plan to reduce the width and
	move the x offset accordingly, you need to apply such changes in the appropriate order.
	:param nodemap: GenICam nodemap.
	:type nodemap: INodeMap
	:return: True if successful, False otherwise.
	:rtype: bool
	"""
	print('\n*** CONFIGURING CUSTOM IMAGE SETTINGS *** \n')
	try:
		result = True

		# Set maximum width
		#
		# *** NOTES ***
		# Other nodes, such as those corresponding to image width and height,
		# might have an increment other than 1. In these cases, it can be
		# important to check that the desired value is a multiple of the
		# increment. However, as these values are being set to the maximum,
		# there is no reason to check against the increment.
		node_width = PySpin.CIntegerPtr(nodemap.GetNode('Width'))
		print("[cam.py] checking node_width")
		print(PySpin.IsAvailable(node_width))
		print(PySpin.IsWritable(node_width))
		if PySpin.IsAvailable(node_width) and PySpin.IsWritable(node_width):
			width_to_set = cam_params["frameWidth"] # node_width.GetMax()
			node_width.SetValue(width_to_set)
			print('Width set to %i...' % node_width.GetValue())
		else:
			 print('Width not available...')

		# Set maximum height
		# *** NOTES ***
		# A maximum is retrieved with the method GetMax(). A node's minimum and
		# maximum should always be a multiple of its increment.
		node_height = PySpin.CIntegerPtr(nodemap.GetNode('Height'))
		if PySpin.IsAvailable(node_height) and PySpin.IsWritable(node_height):
			height_to_set = cam_params["frameHeight"]
			node_height.SetValue(height_to_set)
			print('Height set to %i...' % node_height.GetValue())
		else:
			print('Height not available...')

	except PySpin.SpinnakerException as ex:
		print('Error: %s' % ex)
		assert False
	print("DONE configuring")
	return width_to_set, height_to_set

def PrintDeviceInfo(nodemap):
	"""
	This function prints the device information of the camera from the transport
	layer; please see NodeMapInfo example for more in-depth comments on printing
	device information from the nodemap.
	:param nodemap: Transport layer device nodemap.
	:param cam_num: Camera number.
	:type nodemap: INodeMap
	:type cam_num: int
	:returns: True if successful, False otherwise.
	:rtype: bool
	"""
	try:
		result = True
		node_device_information = PySpin.CCategoryPtr(nodemap.GetNode('DeviceInformation'))
		if PySpin.IsAvailable(node_device_information) and PySpin.IsReadable(node_device_information):
			features = node_device_information.GetFeatures()
			for feature in features:
				node_feature = PySpin.CValuePtr(feature)
				print('%s: %s' % (node_feature.GetName(),
								  node_feature.ToString() if PySpin.IsReadable(node_feature) else 'Node not readable'))
		else:
			print('Device control information not available.')
	except PySpin.SpinnakerException as ex:
		print('Error: %s' % ex)
		assert False


def configure_trigger(cam):
	"""
	This function configures the camera to use a trigger. First, trigger mode is
	ensured to be off in order to select the trigger source. Trigger mode is
	then enabled, which has the camera capture only a single image upon the
	execution of the chosen trigger.

	 :param cam: Camera to configure trigger for.
	 :type cam: CameraPtr
	 :return: True if successful, False otherwise.
	 :rtype: bool
	"""
	print('*** CONFIGURING TRIGGER ***\n')
	if CHOSEN_TRIGGER == TriggerType.SOFTWARE:
		print('Software trigger chosen...')
	elif CHOSEN_TRIGGER == TriggerType.HARDWARE:
		print('Hardware trigger chose...')

	cam.TriggerMode.SetValue(PySpin.TriggerMode_Off)
	cam.TriggerSource.SetValue(PySpin.TriggerSelector_FrameStart)

	if CHOSEN_TRIGGER == TriggerType.SOFTWARE:
		cam.TriggerSource.SetValue(PySpin.TriggerSource_Software)

	elif CHOSEN_TRIGGER == TriggerType.HARDWARE:
		cam.TriggerSource.SetValue(PySpin.TriggerSource_Line0)

	if False:
		cam.TriggerOverlap.SetValue(PySpin.TriggerOverlap_ReadOut)
	cam.TriggerMode.SetValue(PySpin.TriggerMode_On)

def PrepareCamera(camera, cam_params):
	camera.Init()
	configure_trigger(camera)
	camera.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
	cam_params['cameraSerialNo'] = camera.TLDevice.DeviceSerialNumber.GetValue()
	nodemap = camera.GetNodeMap()
	frameWidth, frameHeight = ConfigureCustomImageSettings(cam_params, nodemap)
	configure_exposure(camera)
	cam_params["frameWidth"] = frameWidth
	cam_params["frameHeight"] = frameHeight
	# TODO: make a cameraParams (like in basler version).
	# TODO: index cameras using serial numbers.


def OpenCamera(cam_params, frameWidth=1152, frameHeight=1024):
	# Open and load features for all cameras
	print("=== Opening camera")
	n_cam = cam_params["n_cam"]
	cam_index = cam_params["cameraSelection"]
	camera_name = cam_params["cameraName"]
	result = True

	# Retrieve singleton reference to system object
	system = PySpin.System.GetInstance()
	cam_list = system.GetCameras()
	# for cam in cam_list:
	# 	del cam
	# cam_list.Clear()
	# system.ReleaseInstance()
	# system = PySpin.System.GetInstance()
	# cam_list = system.GetCameras()

	num_cameras = cam_list.GetSize()
	print('Number of cameras detected: %d' % num_cameras)

	for i, camera in enumerate(cam_list):
		if i == cam_index:
			# Retrieve TL device nodemap
			nodemap_tldevice = camera.GetTLDeviceNodeMap()
			# Print device information
			print('Printing device information for camera %d... \n' % i)
			PrintDeviceInfo(nodemap_tldevice)

	# Initialize camera object
	camera = cam_list.GetByIndex(cam_index)
	camera.Init()
	configure_trigger(camera)
	camera.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)

	# Retrieve GenICam nodemap
	nodemap = camera.GetNodeMap()

	# Set acquisition mode to continuous
	# node_acquisition_mode = PySpin.CEnumerationPtr(nodemap.GetNode('AcquisitionMode'))
	# if not PySpin.IsAvailable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
	# 	print('Unable to set acquisition mode to continuous (node retrieval; camera %d). Aborting... \n' % i)
	# 	assert False
	# node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName('Continuous')
	# if not PySpin.IsAvailable(node_acquisition_mode_continuous) or not PySpin.IsReadable(
	# 		node_acquisition_mode_continuous):
	# 	print('Unable to set acquisition mode to continuous (entry \'continuous\' retrieval %d). \
	# 	Aborting... \n' % i)
	# 	assert False
	# acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()
	# node_acquisition_mode.SetIntValue(acquisition_mode_continuous)

	# Get device metadata from camera object

	# node_device_serial_number = PySpin.CStringPtr(camera.GetTLDeviceNodeMap().GetNode('DeviceSerialNumber'))
	# if PySpin.IsAvailable(node_device_serial_number) and PySpin.IsReadable(node_device_serial_number):
	# 	device_serial_number = node_device_serial_number.GetValue()
	# else:
	# 	device_serial_number = []
	# cam_params['cameraSerialNo'] = device_serial_number
	cam_params['cameraSerialNo'] = camera.TLDevice.DeviceSerialNumber.GetValue()


	# cam_params['cameraModel'] = camera.GetDeviceInfo().GetModelName()
	print("Opened", camera_name, "serial#", cam_params['cameraSerialNo'])


	# Configure trigger
	# trigConfig = ConfigureTrigger(camera)

	# Configure custom image settings
	frameWidth, frameHeight = ConfigureCustomImageSettings(cam_params, nodemap)
	cam_params["frameWidth"] = frameWidth
	cam_params["frameHeight"] = frameHeight

	# Start grabbing frames
	camera.BeginAcquisition()

	print("here")

	if False:
		print("Grabbing)")
		camera.GetNextImage()

		# Clear camera list before releasing system
		del camera
		cam_list.Clear() # Do we need "cam_list" open while grabbing?
		system.ReleaseInstance() # Do we need "system" open while grabbing?
		camera = None

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

def ResetGrabdata(cam_params):
	grabdata = {}
	grabdata['timeStamp'] = []
	grabdata['frameNumber'] = []
	grabdata['newfile'] = []
	grabdata["grabtime_firstframe"] = []
	grabdata["frameNumberThisTrial"] = []
	return grabdata


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
			# CloseCamera(cam_params, camera, grabdata)
			writeQueue.append('STOP')
			# TODO: make option for this to end when long gap (inter trial interval).
			# TODO: make sure after this STOP, keeps going, with new file.
			break
		try:
			# Grab image from camera buffer if available
			try:
				if v1:
					image_result = camera.GetNextImage()
				else:
					image_result = camera.GetNextImage(cam_params['trialITI'])

				if not image_result.IsIncomplete():
					img  = ConvertImages(image_result)
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
					if v1:
						# This moved to outside this loop.
						if cam_params['trialStructure'] and len(grabdata['timeStamp'])>0:
							if inter_frame_time>cam_params['trialITI']:
								writeQueue.append('NEWFILE')
								grabdata['newfile'].append(1)
								filenum += 1
								# TODO: save grabdata
								# TODO: reset grabdata (for a new file).
								SaveMetadata(cam_params, grabdata, suffix=f"-t{filenum}")
								grabdata = ResetGrabdata(cam_params)
							else:
								grabdata['newfile'].append(0)
					
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
					image_result.Release()

					if cnt % chunkLengthInFrames == 0:
						fps_count = int(round(cnt/grabtime))
						print('Camera %i collected %i frames at %i fps.' % (n_cam,cnt,fps_count))

					# === print things
					if DEBUG:
						print(grabdata)
						print(len(writeQueue))
						if len(writeQueue)>30:
							break
				else:
					print("Image incomplete (why?)")
					print('Image incomplete with image status %d ... \n' % image_result.GetImageStatus())
					assert False
			except PySpin.SpinnakerException as ex:
				if framenum_thistrial>0:
					if not v1:
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



				# if len(grabdata["frameNumber"])>0:
				# else:
				# 	print("Ready for triggers.")

		# Else wait for next frame available
		except PySpin.SpinnakerException as ex:
			print('Error: %s' % ex)
			result = False
		except Exception as e:
			logging.error('Caught exception: {}'.format(e))

def CloseCamera(cam_params, camera, grabdata):

	n_cam = cam_params["n_cam"]

	print('Closing camera {}... Please wait.'.format(n_cam+1))
	# Close Basler camera after acquisition stops
	# TODO: fix camera closing
	try:
		SaveMetadata(cam_params,grabdata)
		time.sleep(1)
		camera.EndAcquisition()		
		camera.DeInit()
		del camera
	except Exception as err: 
		print(err)
		print("TRIED TO CLOSE, FAILED")
		time.sleep(0.1)

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
