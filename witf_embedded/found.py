# import cv2
# import objc
# # Set up AVFoundation capture session
# allDevices = [
#     AVFoundation.AVCaptureDeviceTypeExternalUnknown,
#     AVFoundation.AVCaptureDeviceTypeBuiltInWideAngleCamera,
#     AVFoundation.AVCaptureDeviceTypeBuiltInUltraWideCamera,
#     AVFoundation.AVCaptureDeviceTypeBuiltInTelephotoCamera,
#     AVFoundation.AVCaptureDeviceTypeBuiltInDualCamera,
#     AVFoundation.AVCaptureDeviceTypeBuiltInDualWideCamera,
#     AVFoundation.AVCaptureDeviceTypeBuiltInTripleCamera,
#     AVFoundation.AVCaptureDeviceTypeDeskViewCamera

# ]

import AVFoundation
import time
import cv2
import objc
from AppKit import NSAutoreleasePool, NSRunLoop, NSDate
import ctypes

# Import the libdispatch library
libdispatch = ctypes.cdll.LoadLibrary("/usr/lib/system/libdispatch.dylib")

# Define the dispatch queue type and function signature
dispatch_queue_t = ctypes.c_void_p
dispatch_queue_create_func = libdispatch.dispatch_queue_create
dispatch_queue_create_func.argtypes = [ctypes.c_char_p, ctypes.c_void_p]
dispatch_queue_create_func.restype = dispatch_queue_t

device_type = [AVFoundation.AVCaptureDeviceTypeBuiltInTripleCamera, AVFoundation.AVCaptureDeviceTypeExternalUnknown]
media_type = AVFoundation.AVMediaTypeVideo
position = AVFoundation.AVCaptureDevicePositionUnspecified
device = AVFoundation.AVCaptureDeviceDiscoverySession.discoverySessionWithDeviceTypes_mediaType_position_(device_type, media_type, position).devices()[0]

print(device.localizedName() + " " + device.deviceType())
capture_input = AVFoundation.AVCaptureDeviceInput.deviceInputWithDevice_error_(device, None)[0]
output = AVFoundation.AVCaptureVideoDataOutput.alloc().init()
session = AVFoundation.AVCaptureSession.alloc().init()
queue = dispatch_queue_create_func('my_queue'.encode('utf-8'), None)
output.setSampleBufferDelegate_queue_(output, queue)
print(output.availableVideoCodecTypes())
session.addInput_(capture_input)
session.addOutput_(output)
session.startRunning()

# Define the captureOutput_didOutputSampleBuffer_fromConnection_ function
@objc.python_method
def captureOutput_didOutputSampleBuffer_fromConnection_(self, output, sampleBuffer, connection):
    image_buffer = objc.lookUpClass('CIImage').imageWithCVImageBuffer_(sampleBuffer)
    image = cv2.cvtColor(image_buffer, cv2.COLOR_BGR2RGB)

    # Display the video frame
    cv2.imshow('frame', image)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        session.stopRunning()
        cv2.destroyAllWindows()
        exit(0)

# Set the delegate for the capture output
output.captureOutput_didOutputSampleBuffer_fromConnection_ = captureOutput_didOutputSampleBuffer_fromConnection_

time.sleep(50)
# Retrieve and display video frames
with objc.autorelease_pool():
    NSRunLoop.currentRunLoop().run()


# device = AVFoundation.AVCaptureDevice.defaultDeviceWithMediaType_("video")
# input = AVFoundation.AVCaptureDeviceInput.deviceInputWithDevice_error_(device, None)
# output = AVFoundation.AVCaptureVideoDataOutput.alloc().init()
# output.setSampleBufferDelegate_queue_(None, objc.nil)
# session.addOutput_(output)
# session.startRunning()

# # Set up OpenCV window
# cv2.namedWindow("iPhone Camera", cv2.WINDOW_NORMAL)

# # Main loop
# while True:
#     # Capture frame from AVFoundation
#     sample_buffer = output.copyNextSampleBuffer()
#     image_buffer = AVFoundation.AVCaptureStillImageOutput.jpegStillImageNSDataRepresentation_(sample_buffer)
#     frame = cv2.imdecode(np.frombuffer(image_buffer, np.uint8), -1)
    
#     # Display frame in OpenCV window
#     cv2.imshow("iPhone Camera", frame)
    
#     # Check for user input
#     key = cv2.waitKey(1)
#     if key == ord("q"):
#         break

# # Clean up
# cv2.destroyAllWindows()
# session.stopRunning()


# class VideoDelegate(object):
#     def captureOutput_didOutputSampleBuffer_fromConnection_(self, output, sample_buffer, connection):
#         # Convert the sample buffer to a CV image
#         image = sample_buffer.toPixelBuffer()

#         # Lock the base address of the CV image
#         image.lockBaseAddress()

#         # Get the CV image information
#         width = image.width()
#         height = image.height()
#         bytes_per_row = image.bytesPerRow()
#         pixel_format = image.pixelFormat()
#         base_address = image.baseAddress()

#         # Create a numpy array from the CV image data
#         data = np.frombuffer(base_address, dtype=np.uint8)
#         cv_image = data.reshape((height, bytes_per_row // 4, 4))
#         cv_image = cv_image[:, :width, :]

#         # Unlock the base address of the CV image
#         image.unlockBaseAddress()

#         # Convert the CV image to BGR format for display
#         cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGBA2BGR)

#         # Display the CV image in a window
#         cv2.imshow("Camera Feed", cv_image)
#         cv2.waitKey(1)