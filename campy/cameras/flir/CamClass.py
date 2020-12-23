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

class TriggerType:
	SOFTWARE = 1
	HARDWARE = 2

CHOSEN_TRIGGER = TriggerType.HARDWARE

class Camera():
	def __init__(self):
		pass

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


	def configure_custom_image_settings(self, cam):
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



	def ConfigureCustomImageSettings(self, cam_params, nodemap):
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

	def PrintDeviceInfo(self, nodemap):
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


	def configure_trigger(self, cam):
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



	def OpenCamera(self, cam_params, frameWidth=1152, frameHeight=1024):
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
				self.PrintDeviceInfo(nodemap_tldevice)

		# Initialize camera object
		camera = cam_list.GetByIndex(cam_index)
		camera.Init()
		self.configure_trigger(camera)
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
		frameWidth, frameHeight = self.ConfigureCustomImageSettings(cam_params, nodemap)
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

	def GrabFrames(self, cam_params, camera, writeQueue, dispQueue, stopQueue):
		n_cam = cam_params["n_cam"]

		cnt = 0
		timeout = 0

		# Create dictionary for appending frame number and timestamp information
		grabdata = {}
		grabdata['timeStamp'] = []
		grabdata['frameNumber'] = []

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
			if stopQueue or cnt >= numImagesToGrab:
				self.CloseCamera(cam_params, system, cam_list, camera, grabdata)
				writeQueue.append('STOP')
				break
			try:
				# Grab image from camera buffer if available
				image_result = camera.GetNextImage()
				if not image_result.IsIncomplete():
					img = np.asarray(image_result, dtype="uint8")
					# image_converted = image_result.Convert(PySpin.PixelFormat_Mono8, PySpin.HQ_LINEAR)
					# img = image_converted.GetNDArray()

					# Append numpy array to writeQueue for writer to append to file
					writeQueue.append(img)

					# Get timestamp of grabbed frame from camera
					if cnt == 0:
						timeFirstGrab = time.monotonic_ns()
					grabtime = (time.monotonic_ns() - timeFirstGrab)/1e9
					grabdata['timeStamp'].append(grabtime)

					cnt += 1
					grabdata['frameNumber'].append(cnt) # first frame = 1

					if cnt % frameRatio == 0:
						dispQueue.append(img[::ds,::ds])

					# Release grab object
					image_result.Release()

					if cnt % chunkLengthInFrames == 0:
						fps_count = int(round(cnt/grabtime))
						print('Camera %i collected %i frames at %i fps.' % (n_cam,cnt,fps_count))
				else:
					print('Image incomplete with image status %d ... \n' % image_result.GetImageStatus())
			# Else wait for next frame available
			except PySpin.SpinnakerException as ex:
				print('Error: %s' % ex)
				result = False
			except Exception as e:
				logging.error('Caught exception: {}'.format(e))

	def CloseCamera(self, cam_params, camera, grabdata):

		n_cam = cam_params["n_cam"]

		print('Closing camera {}... Please wait.'.format(n_cam+1))
		# Close Basler camera after acquisition stops
		while(True):
			try:
				try:
					self.SaveMetadata(cam_params,grabdata)
					time.sleep(1)
					camera.DeInit()
					camera.EndAcquisition()
					del camera
					break
				except:
					time.sleep(0.1)
			except KeyboardInterrupt:
				break

	def SaveMetadata(self, cam_params, grabdata):
		
		n_cam = cam_params["n_cam"]

		full_folder_name = os.path.join(cam_params["videoFolder"], cam_params["cameraName"])

		meta = cam_params
		meta['timeStamp'] = grabdata['timeStamp']
		meta['frameNumber'] = grabdata['frameNumber']

		frame_count = grabdata['frameNumber'][-1]
		time_count = grabdata['timeStamp'][-1]
		fps_count = int(round(frame_count/time_count))
		print('Camera {} saved {} frames at {} fps.'.format(n_cam+1, frame_count, fps_count))

		try:
			npy_filename = os.path.join(full_folder_name, 'frametimes.npy')
			x = np.array([meta['frameNumber'], meta['timeStamp']])
			np.save(npy_filename,x)
		except:
			pass

		csv_filename = os.path.join(full_folder_name, 'metadata.csv')
		meta = cam_params
		meta['totalFrames'] = grabdata['frameNumber'][-1]
		meta['totalTime'] = grabdata['timeStamp'][-1]
		keys = meta.keys()
		vals = meta.values()
		
		try:
			with open(csv_filename, 'w', newline='') as f:
				w = csv.writer(f, delimiter=',', quoting=csv.QUOTE_ALL)
				for row in meta.items():
					w.writerow(row)
		except:
			pass
