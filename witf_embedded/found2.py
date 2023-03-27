# import cv2
# import objc
# # Set up AVFoundation capture session
import AVFoundation
import objc
import cv2
import numpy as np

from Foundation import NSObject
from libdispatch import dispatch_get_main_queue

AVCaptureVideoDataOutputSampleBufferDelegate = objc.protocolNamed('AVCaptureVideoDataOutputSampleBufferDelegate')


class VideoDelegate(NSObject, protocols=[AVCaptureVideoDataOutputSampleBufferDelegate]):
    def captureOutput_didOutputSampleBuffer_fromConnection_(self, output, sample_buffer, connection):
        print("Ran")
        # Convert the sample buffer to a CV image
        image = sample_buffer.toPixelBuffer()

        # Lock the base address of the CV image
        image.lockBaseAddress()

        # Get the CV image information
        width = image.width()
        height = image.height()
        bytes_per_row = image.bytesPerRow()
        pixel_format = image.pixelFormat()
        base_address = image.baseAddress()

        # Create a numpy array from the CV image data
        data = np.frombuffer(base_address, dtype=np.uint8)
        cv_image = data.reshape((height, bytes_per_row // 4, 4))
        cv_image = cv_image[:, :width, :]

        # Unlock the base address of the CV image
        image.unlockBaseAddress()

        # Convert the CV image to BGR format for display
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGBA2BGR)

        # Display the CV image in a window
        cv2.imshow("Camera Feed", cv_image)
        cv2.waitKey(1)


class Main:
    def __init__(self):
        self.device_type = [AVFoundation.AVCaptureDeviceTypeDeskViewCamera, AVFoundation.AVCaptureDeviceTypeExternalUnknown]
        self.media_type = AVFoundation.AVMediaTypeVideo
        self.position = AVFoundation.AVCaptureDevicePositionUnspecified

        self.device = AVFoundation.AVCaptureDeviceDiscoverySession.discoverySessionWithDeviceTypes_mediaType_position_(self.device_type, self.media_type, self.position).devices()[0]
        print('des', AVFoundation.AVCaptureDeviceDiscoverySession.discoverySessionWithDeviceTypes_mediaType_position_(self.device_type, self.media_type, self.position).devices())
        print(self.device.localizedName() + " " + self.device.deviceType())

        self.capture_input = AVFoundation.AVCaptureDeviceInput.deviceInputWithDevice_error_(self.device, None)[0]
        self.capture_output = AVFoundation.AVCaptureVideoDataOutput.alloc().init()

        self.queue = dispatch_get_main_queue()
        self.delegate = VideoDelegate.alloc().init()
        self.capture_output.setSampleBufferDelegate_queue_(self.delegate, self.queue)

        self.session = AVFoundation.AVCaptureSession.alloc().init()
        self.session.addInput_(self.capture_input)
        self.session.addOutput_(self.capture_output)
        self.session.startRunning()

        print('Cap input:', self.capture_input.device())
        print(self.capture_output.sampleBufferDelegate())
        print(VideoDelegate.pyobjc_classMethods.conformsToProtocol_(AVCaptureVideoDataOutputSampleBufferDelegate))

    def lock_config(self):
        self.device.lockForConfiguration_(None)

    def unlock_config(self):
        pass
        #self.device.unlockForConfiguration_()

    def set_zoom_factor(self, factor):
        print(self.device.minAvailableVideoZoomFactor())
        self.lock_config()
        self.device.setVideoZoomFactor_(factor)
        self.unlock_config()

    def is_center_stage_active(self):
        #print(self.device.centerStageControlMode()) DNE
        f = self.device.activeFormat()
        s = f.formatDescription()
        print(s)
        print('Center Stage', self.device.isCenterStageActive())
        print('Center Stage Toggle', self.device._setCenterStageEnabled_(False))


    def print_useful_stuff(self):
        print("Frame Duration:", (self.device.activeVideoMinFrameDuration()))
        print("Zoom factor:", self.device.videoZoomFactor())
        print("Focus Mode:", self.device.focusMode())
        print("Capture Input:", self.capture_input)
        print("Flash:", self.device.hasFlash())
        print("Flash Mode:", self.device.isFlashAvailable())
        print("Flash Mode:", self.device.isFlashActive())
        print("Has torch:", self.device.hasTorch())
        print("Torch active:", self.device.isTorchActive())
        print("Torch mode:", self.device.isTorchAvailable())
        # print("Torch mode:", self.device.setTorchMode_(AVFoundation.AVCaptureTorchModeA))
        print("Torch active:", self.device.isTorchActive())

        #print("Torch:", self.setTorchMode_())

    def get_connections(self):
        connections = self.capture_input.ports()[0].connections()
        for connection in connections:
            print(connection.description())


    def run(self):
        #self.set_zoom_factor(1)
       
        self.print_useful_stuff()
        self.is_center_stage_active()
        while True:
            # Wait for a key press or window close
            # print(self.session)
            # print(self.capture_output.sampleBufferDelegate())
            # print(VideoDelegate.pyobjc_classMethods.conformsToProtocol_(AVCaptureVideoDataOutputSampleBufferDelegate))

            # self.is_center_stage_active()
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break



def printAllDevices():
    allDevices = [
        AVFoundation.AVCaptureDeviceTypeExternalUnknown,
        AVFoundation.AVCaptureDeviceTypeBuiltInWideAngleCamera,
        AVFoundation.AVCaptureDeviceTypeBuiltInUltraWideCamera,
        AVFoundation.AVCaptureDeviceTypeBuiltInTelephotoCamera,
        AVFoundation.AVCaptureDeviceTypeBuiltInDualCamera,
        AVFoundation.AVCaptureDeviceTypeBuiltInDualWideCamera,
        AVFoundation.AVCaptureDeviceTypeBuiltInTripleCamera,
        AVFoundation.AVCaptureDeviceTypeDeskViewCamera
    ]
    media_type = AVFoundation.AVMediaTypeVideo
    position = AVFoundation.AVCaptureDevicePositionUnspecified
    devices = AVFoundation.AVCaptureDeviceDiscoverySession.discoverySessionWithDeviceTypes_mediaType_position_(allDevices, media_type, position).devices()

    for device in devices:
        print(device.localizedName() + " " + device.deviceType())


if __name__ == '__main__':
    # printAllDevices()
    # main = Main()
    # main.lock_config()
    # main.run()
    print(cv2.getBuildInformation())

# def setup():
#     device_type = [AVFoundation.AVCaptureDeviceTypeBuiltInTripleCamera, AVFoundation.AVCaptureDeviceTypeExternalUnknown]
#     media_type = AVFoundation.AVMediaTypeVideo
#     position = AVFoundation.AVCaptureDevicePositionUnspecified

#     device = AVFoundation.AVCaptureDeviceDiscoverySession.discoverySessionWithDeviceTypes_mediaType_position_(device_type, media_type, position).devices()[0]
#     print(device.localizedName() + " " + device.deviceType())

#     capture_input = AVFoundation.AVCaptureDeviceInput.deviceInputWithDevice_error_(device, None)[0]
#     capture_output = AVFoundation.AVCaptureVideoDataOutput.new()

#     queue = dispatch_get_main_queue()
#     delegate = VideoDelegate.alloc().init()

#     capture_output.setSampleBufferDelegate_queue_(delegate, queue)

#     session = AVFoundation.AVCaptureSession.alloc().init()
#     session.addInput_(capture_input)
#     session.addOutput_(capture_output)
#     session.startRunning()

#     print(capture_output.sampleBufferDelegate())
#     print(VideoDelegate.pyobjc_classMethods.conformsToProtocol_(AVCaptureVideoDataOutputSampleBufferDelegate))


#libdispatch = ctypes.cdll.LoadLibrary("/usr/lib/system/libdispatch.dylib")

# # Define the dispatch queue type and function signature
# dispatch_queue_t = ctypes.c_void_p
# dispatch_queue_create_func = libdispatch.dispatch_queue_create
# dispatch_queue_create_func.argtypes = [ctypes.c_char_p, ctypes.c_void_p]
# dispatch_queue_create_func.restype = dispatch_queue_t


# device_type = [AVFoundation.AVCaptureDeviceTypeBuiltInTripleCamera, AVFoundation.AVCaptureDeviceTypeExternalUnknown]
# media_type = AVFoundation.AVMediaTypeVideo
# position = AVFoundation.AVCaptureDevicePositionUnspecified

# device = AVFoundation.AVCaptureDeviceDiscoverySession.discoverySessionWithDeviceTypes_mediaType_position_(device_type, media_type, position).devices()[0]
# print(device.localizedName() + " " + device.deviceType())

# capture_input = AVFoundation.AVCaptureDeviceInput.deviceInputWithDevice_error_(device, None)[0]
# capture_output = AVFoundation.AVCaptureVideoDataOutput.alloc().init()

# session = AVFoundation.AVCaptureSession.alloc().init()
# # queue = dispatch_queue_create_func('my_queue'.encode('utf-8'), None)
# # output.setSampleBufferDelegate_queue_(output, queue)
# session.addInput_(capture_input)
# session.addOutput_(capture_output)

# # Create a video connection between the input and outpu

# # Set a delegate for the output stream
# delegate = VideoDelegate.alloc().init()
# queue = dispatch_queue_create_func('my_queue'.encode('utf-8'), None)
# capture_output.setSampleBufferDelegate_queue_(delegate, queue)

# # Start the session

# session.startRunning()

# time.sleep(50)





        