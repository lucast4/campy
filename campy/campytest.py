from campy import campy as cp


n_cam = 0
fname = "/Users/lucas/code/campy/configs/config_flir.yaml"
params = cp.LoadConfig(fname)
cam_params = cp.CreateCamParams(params, n_cam)

if False:
	cp.AcquireOneCamera2(n_cam, params)
else:
	cp.AcquireSingleThread(n_cam, params)