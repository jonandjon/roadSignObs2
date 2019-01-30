#!/usr/bin/env python
from cv_bridge import CvBridge
import cv2
import numpy as np
import rospy
#-# from keras.datasets import mnist
from keras.preprocessing.image import ImageDataGenerator, array_to_img, img_to_array, load_img # for roadSignObs
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import Bool, Int32
from PIL import Image
# from threading import Thread
import threading
import time
import sys
import os
import imageio
import csv ###
import random
import time #~
import Detector
## import subDetect #IN WORK <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

img_rows, img_cols = 32, 32  # input image dimensions
PAUSE = 5000 # Millisekunden
PUBLISH_RATE = 3 # fuer WebCam in Hz
USE_WEBCAM=False # True: WebCam, False: Strassenszenen aus dem Verzeichnis street
USE_COLORDETECT=True  # True: take detect per colorfilter, False: take image direct
# Instanz der Klasse ...
if USE_COLORDETECT: objectSign=Detector.ColorFilter()
else:		objectSign=Detector.NormImages()


# nur fuer Testzwecke benoetigt
ANALYSEBILD="objDetect/street/mitEinfahrtVerboten.jpg"  #"eineAusfahrt" #"mitKreuzung.jpg"#"mitEinfahrtVerboten.png"#eineAusfahrt #mitHalteverbot
OBJEKTBILD="objDetect/objekt/kreisRot2.jpg"

class PublishWebCam:
	def __init__(self):
		self.cv_bridge = CvBridge()
		# publish webcam
		self.publisher_webcam_comprs = rospy.Publisher("/camera/output/webcam/compressed_img_msgs",
                                                       CompressedImage,
                                                       queue_size=1)
													   
		# publish Frame
		self.publisher_fullcam_comprs = rospy.Publisher("/fullcamera/output/webcam/compressed_img_msgs",
                                                       CompressedImage,
                                                       queue_size=1)												

		if USE_WEBCAM==True:
			self.input_stream = cv2.VideoCapture(0)
			if not self.input_stream.isOpened():
				raise Exception('Camera stream did not open\n')
        rospy.loginfo("Publishing data...")
#--------------------------------------------------------------------------------------
	# liest ein zufaellige Strassen-Bilddateien -----------------------------------
	def readRoadPictures(self, rootpath="./objDetect/street/"):
		namesPictures = [] # images
		gtFile = open(rootpath + '/roadPictures.csv') # csv-Datei enthaelt Namen der zur Auswahl stehenden Bilddateien
		gtReader = csv.reader(gtFile, delimiter=';') # csv parser for annotations file
		gtReader.next() # skip header
		# loop over all images in current annotations file
		for row in gtReader:
			dateiname=rootpath + row[0]
			namesPictures.append(dateiname)
		gtFile.close()
		return namesPictures 
		
	''' veroeffentlicht Daten '''
	def cam_data(self, verbose=0):
		rate = rospy.Rate(PUBLISH_RATE)
		while not rospy.is_shutdown():
			# reactivate for webcam image. Pay attention to required subscriber buffer size.
			# See README.md for further information
			if USE_WEBCAM==True:
				print("WEBCAM is true!")
				# Methode zum veroeffentlichen des Vollbildes 
				camFrame=self.getCamFrame(verbose)
				rate.sleep() 
				allObjImages=objectSign.inFrame(camFrame)
				#fuer TEST# cv2.imwrite("objDetect/street/camFrame.png", camFrame)  #+++
				#         # cv2.imshow('camFrame in PublishCam', camFrame)
			else:  	# Strassenszenen aus Verzeichnis objDetect/street
				namesPictures=self.readRoadPictures() #rootpath="./TestImages"
				zufallsindex=random.randint(0, len(namesPictures)-1) #+++
				allObjImages=objectSign.inImages(namesPictures[zufallsindex])  #
			for img in allObjImages:
				#+# self.saveAsPPM(npImage=img, pfad='ABLAGE/') # zum Testen
				self.publish_camresize(img)
				#+time.sleep(PAUSE/1000)
				cv2.waitKey(PAUSE) 
			#+time.sleep(PAUSE/3000) # zusaetzliche Pause nach jedem big Picture
			cv2.destroyAllWindows() #*#
	
	''' Sendet Vollbilder der Webcam fortlaufend 
	    OPTIONAL  '''
	def getCamFrame(self, verbose=0):
		if self.input_stream.isOpened() and USE_WEBCAM:
			success, frame = self.input_stream.read()
			msg_frame = self.cv_bridge.cv2_to_compressed_imgmsg(frame)
			# -> Uebertragung der vollstaendigen-Camera-Bilder
			#OPTIONAL# self.publisher_fullcam_comprs.publish(msg_frame.header, msg_frame.format, msg_frame.data)
			if verbose:
				rospy.loginfo(msg_frame.header.seq)
				rospy.loginfo(msg_frame.format)
		return frame
	
	''' Sendet skaliertes Bild der WebCam '''
	''' Methode alternativ als Thread https://www.python-kurs.eu/threads.php '''	
	def publish_camresize(self, img):
		size=[img_rows, img_cols]
		try:
			print("obj publish", (int(time.time()))) # Kontrollausgabe
			if USE_COLORDETECT: # Objekte auf 32x32 skalieren
				image=array_to_img(img)
				jpgNormImage=image.resize(size)     # Standardgroesse herstellen
				img=img_to_array(jpgNormImage, data_format = "channels_last") ### als Numphy-Array
			#-# cv2.imshow('PublishCam', npImage) ###Kontrolle
			compressed_imgmsg = self.cv_bridge.cv2_to_compressed_imgmsg(img)
			# -> Sendet  Bild 
			self.publisher_webcam_comprs.publish(compressed_imgmsg)
		except:
			print("kein gueltiges Objekt") 
			
	''' Speichert ein nymphi-array als ppm-Bild'''	
	def saveAsPPM(self, npImage, pfad='ABLAGE/img.ppm' ):
		try:
			b, g, r = cv2.split(npImage)
			npImage=cv2.merge((r,g,b))
			now=str(time.time())
			datei=pfad + 'img'+now+'.ppm'
			#t# cv2.imwrite('ABLAGE/img'+ now +'.ppm', img) #CV_IMWRITE_PXM_BINARY
			# imageio.imwrite(datei, npImage, format='PPM-FI', flags=1) #'PPM-FI' (ascii)
			imageio.imwrite(datei, npImage, format='PPM') #'PPM-FI' (ascii)
		except:
			print("kein Objektbild") 
		
	
def main():
	verbose = 0  # use 1 for debug
	# register node
	rospy.init_node('PublishWebCam', anonymous=False)
	# Instanz der Klasse (Publisher)
	cam = PublishWebCam()
	# start publishing data
	cam.cam_data(verbose)
	try:
		rospy.spin()
	except rospy.ROSInterruptException:
        	pass
	cv2.destroyAllWindows()


if __name__ == '__main__':
	main()