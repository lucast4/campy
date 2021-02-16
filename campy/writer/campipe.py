"""

"""

from imageio_ffmpeg import write_frames
import os
import time
import logging
import sys

DEBUG = False

def OpenWriter(cam_params, filenum=0):
	n_cam = cam_params["n_cam"]

	folder_name = os.path.join(cam_params["videoFolder"], cam_params["cameraName"])
	if cam_params["cameraMake"] == "emu":
		fname = "emu" + cam_params["videoFilename"]
	else:
		fname = cam_params["videoFilename"]

	fname_str, fname_ext = os.path.splitext(fname)
	fname_str = f"{fname_str}-t{filenum}"

	if DEBUG:
		import numpy as np
		# add random number
		tmp = str(10000*np.random.rand())[:3]
		fname = f"{tmp}-{fname}"

	full_file_name = os.path.join(folder_name, f"{fname_str}{fname_ext}")
	# full_file_name = os.path.join(folder_name, fname)

	if not os.path.isdir(folder_name):
		os.makedirs(folder_name)
		print('Made directory {}.'.format(folder_name))
	else:
		print('Saving to directory {}.'.format(folder_name))

	# Load defaults
	pix_fmt_out = cam_params["pixelFormatOutput"]
	codec = cam_params["codec"]
	gpu_params = []

	# CPU compression
	if cam_params["gpuID"] == -1:
		print('Opened: {} using CPU to compress the stream.'.format(full_file_name))
		if pix_fmt_out == 'rgb0':
			pix_fmt_out = 'yuv420p'
		if cam_params["codec"] == 'h264':
			codec = 'libx264'
		elif cam_params["codec"] == 'h265':
			codec = 'libx265'
		gpu_params = ['-r:v', str(cam_params["frameRate"]),
					'-preset', 'fast',
					'-tune', 'fastdecode',
					'-crf', cam_params["quality"],
					'-bufsize', '20M',
					'-maxrate', '10M',
					'-bf:v', '4',
					'-vsync', '0',]

	# GPU compression
	else:
		print('Opened: {} using GPU {} to compress the stream.'.format(full_file_name, cam_params["gpuID"]))
		if cam_params["gpuMake"] == 'nvidia':
			if cam_params["codec"] == 'h264':
				codec = 'h264_nvenc'
			elif cam_params["codec"] == 'h265':
				codec = 'hevc_nvenc'
			gpu_params = ['-r:v', str(cam_params["frameRate"]), # important to play nice with vsync '0'
						'-preset', 'fast', # set to 'fast', 'llhp', or 'llhq' for h264 or hevc
						'-qp', cam_params["quality"],
						'-bf:v', '0',
						'-vsync', '0',
						'-2pass', '0',
						'-gpu', str(cam_params["gpuID"]),]
		elif cam_params["gpuMake"] == 'amd':
			if pix_fmt_out == 'rgb0':
				pix_fmt_out = 'yuv420p'
			if cam_params["codec"] == 'h264':
				codec = 'h264_amf'
			elif cam_params["codec"] == 'h265':
				codec = 'hevc_amf'
			gpu_params = ['-r:v', str(cam_params["frameRate"]),
						'-usage', 'lowlatency',
						'-rc', 'cqp', # constant quantization parameter
						'-qp_i', cam_params["quality"],
						'-qp_p', cam_params["quality"],
						'-qp_b', cam_params["quality"],
						'-bf:v', '0',
						'-hwaccel', 'auto',
						'-hwaccel_device', str(cam_params["gpuID"]),]
		elif cam_params["gpuMake"] == 'intel':
			if pix_fmt_out == 'rgb0':
				pix_fmt_out = 'nv12'
			if cam_params["codec"] == 'h264':
				codec = 'h264_qsv'
			elif cam_params["codec"] == 'h265':
				codec = 'hevc_qsv'
			gpu_params = ['-r:v', str(cam_params["frameRate"]),
						'-bf:v', '0',]

	# Initialize writer object (imageio-ffmpeg)
	while(True):
		try:
			try:
				print("Writing")
				print(cam_params)
				print(gpu_params)
				# assert False
				writer = write_frames(
					full_file_name,
					[cam_params["frameWidth"], cam_params["frameHeight"]], # size [W,H]
					fps=cam_params["frameRate"],
					quality=None,
					codec=codec,
					pix_fmt_in=cam_params["pixelFormatInput"], # 'bayer_bggr8', 'gray', 'rgb24', 'bgr0', 'yuv420p'
					pix_fmt_out=pix_fmt_out,
					bitrate=None,
					ffmpeg_log_level=cam_params["ffmpegLogLevel"], # 'warning', 'quiet', 'info'
					input_params=['-an'], # '-an' no audio
					output_params=gpu_params,
					)
				writer.send(None) # Initialize the generator
				# TODO: why images are tiled in saved file?
				break
			except Exception as e:
				print("Error (writing)")
				logging.error('Caught exception: {}'.format(e))
				time.sleep(0.1)

		except KeyboardInterrupt:
			break

	return writer

def WriteFrames(cam_params, writeQueue, stopQueue):
	n_cam = cam_params["n_cam"]

	# if save mjultiple files, keep track of filenum
	filenum = 0

	# Start ffmpeg video writer 
	writer = OpenWriter(cam_params, filenum)
	message = ''

	# Continue writing...
	while(True):
		try:
			if writeQueue:
				message = writeQueue.popleft()
				if not isinstance(message, str):
					# print("[WriteFrames] saving")
					writer.send(message)
				elif message=='STOP':
					print("STOP (done saving)")
					break
				elif message == 'NEWFILE':
					# close file, reopen a new file.
					print('Closing+reopining video writer for camera {}. Please wait...'.format(n_cam+1))
					time.sleep(1)
					writer.close()
					filenum += 1
					writer = OpenWriter(cam_params, filenum)
			else:
				time.sleep(0.0001)
		except KeyboardInterrupt:
			stopQueue.append('STOP GRABBING')

	# Closing up...
	print('Closing video writer for camera {}. Please wait...'.format(n_cam+1))
	time.sleep(1)
	writer.close()
