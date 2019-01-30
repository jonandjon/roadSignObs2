#!/usr/bin/env python
import cv2
import roslib
import rospy
import tensorflow as tf
import keras
import numpy as np
from keras import backend as k
from keras import callbacks		
from keras.datasets import mnist 
from cv_bridge import CvBridge
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import Bool, Int32, String, Int16MultiArray
from keras.layers import Conv2D, MaxPooling2D 
from keras.layers import Dense, Dropout, Flatten 
from keras.models import Sequential 
from keras.preprocessing.image import ImageDataGenerator, array_to_img, img_to_array, load_img 
from PIL import Image
import time
import os
import tensorflow as tf
import Cnn       # mein Modul mit Klassen
## from thread import start_new_thread 
## from threading import Thread
OBJ_ROWS, OBJ_COLS= 32, 32 # input image dimensions
''' Instanz der Klasse: Verkehrsschilder Objekt=Modul.Klasse()   '''
cnn=Cnn.Gtsrb(OBJ_ROWS, OBJ_COLS) 

''' Kommunikation und Aufruf der Vorhersageklasse (CNN): '''
class Prediction:
	''' Konstruktor	 '''	
	def __init__(self):
	
		self.cv_bridge = CvBridge()

		print("Hier ist der Prediction-Konstruktor")
		
						 
		## publish back the prediction images '/camera/input/specific/comment
		self.publisherPrediction = rospy.Publisher("/camera/output/specific/prediction",
								 String,
								 queue_size=1)								
		
		## publish back the prediction images
		self.publisherPredictionImage = rospy.Publisher("/camera/output/specific/compressed_img_msgs",
								 CompressedImage,
								 queue_size=1)
	

		# Subscriber der fuer Objektbilder 32 x32 Pixel -------------------------
		self. subscribCam = rospy.Subscriber('/camera/output/webcam/compressed_img_msgs',
							CompressedImage,
							self.callbackObjImage,
							queue_size = 1)
							
                # Subscriber deeines Stassenbildes, Objekte noch nicht detektiert --------
		self. subscribCam = rospy.Subscriber('/camera/output/webcam/compressed_img_msgs',
							CompressedImage,
							self.callbackStreetImage,
							queue_size = 1)								
	''' Verarbeitet ein Objektbild 32x32 Pixel '''											
	def callbackObjImage(self, Cam):
		# print ('CALLBECK: object images of type: "%s"' % Cam.format)
		np_arr = np.fromstring(Cam.data, np.uint8)
		image_np = cv2.imdecode(np_arr, cv2.IMREAD_COLOR ) #cv2.CV_LOAD_IMAGE_COLOR
		np_image=img_to_array(image_np, data_format='channels_last')
		(h,w,c) = np_image.shape
		if h>OBJ_ROWS: return
		
		print("Objektbild im Format (shape): ", h, w, c)
		## Bildbewertung
		prediction, probability, predictionComment= cnn.predictImage(np_image)
		prediction= str(prediction) + "|"+ predictionComment # Eine Uebertragung -> SYNCHRON
		# Sende Prediction-Label und das dazugehoerige Bild zurueck #
		self.publisherPrediction.publish(prediction)
		#t# cv2.imshow('object images in Prediction', image_np) ## test
		self.publisherPredictionImage.publish(Cam) # wird nur weitergereicht
		cv2.waitKey(10)
	
	''' Verarbeitet das Strassenbild 1280x720 Pixel'''	
	def callbackStreetImage(self, Cam):
		np_arr = np.fromstring(Cam.data, np.uint8)
		image_np = cv2.imdecode(np_arr, cv2.IMREAD_COLOR ) #cv2.CV_LOAD_IMAGE_COLOR
		npImage=img_to_array(image_np, data_format = "channels_last")
		b, g, r = cv2.split(npImage)
		npImage=cv2.merge((r,g,b))

		(h,w,c) = npImage.shape
		if h<=OBJ_ROWS: return
		
		print("Strassenbild im Format (shape): ", h, w, c)
		frameObjImage=npImage.copy()
		frameObjImage=self.findObjects(npImage, frameObjImage)
		# zur Kontrolle ##
		#cv2.imshow("frame image from find objects ", frameObjImage)
		
		#bild=Image.fromarray(frameObjImage)
		self.saveArry(frameObjImage,name="v_frameObjImag")
		print("callbackStreetImage - END")	
		self.publisherPredictionImage.publish(Cam) 

		
		
	''' Vollstaendiges Durchsuchen eines Strassenbildes mit variablen Rahmen (kernels)'''	
	def findObjects(self, image, frameObjImage):
		### IN WORK ###
		
		(hmax,wmax,c) = image.shape
		kmax=hmax
		if hmax>wmax: kmax=wmax
		objSize=[OBJ_ROWS, OBJ_COLS]
		k=(OBJ_ROWS*3)  # anfangswert: Kantenlaenge des Rahmens
		while k<kmax: # vergleich mit endwert
			print("k= ", k)
			for x in range (0, wmax-k, int(k/8)):
				#t# print("- x= ", x)
				for y in range (0, hmax-k, int(k/3)):
					#t# print("-- y= ", y)
					x1=x+k
					y1=y+k
					objImg=image[y:y1,x:x1]
				
					img=array_to_img(objImg, data_format = "channels_last")
					normImg=img.resize(objSize)     # Standardgroesse herstellen
					objImg=img_to_array(normImg, data_format = "channels_last") ### als Numphy-Array
					prediction, probability, predictionComment= cnn.predictImage(objImg)
					#t# self.saveArry(objImg, "x_objImg"+str(k)+str(x)+str(y)+"p"+str(probability))
					if probability > 0.97 and prediction<43: # ab 43 ist trash
						cv2.rectangle(frameObjImage,(x,y),(x1,y1),(0,0,255),1)
						#t#self.saveArry(objImg, "y_np"+str(k)+"pd"+str(prediction)+"p"+str(probability))
						#t#time.sleep(30)
						
					if probability > 0.99 and prediction<43:
						cv2.rectangle(frameObjImage,(x,y),(x1,y1),(0,255,0),1)
						print("PROBABILITY: ", probability)
						self.saveArry(objImg, "z_np"+str(k)+"pd"+str(prediction)+"p"+str(probability))
						self.saveArry(img, "z_im"+str(k)+"pd"+str(prediction)+"p"+str(probability))
						#cv2.imshow("objects: "+str(probability), objImg)
						#t#time.sleep(30)
			k=k+int(k/3) # schrittweite variabel, daher keine Zaehlschleife
		
		self.saveArry(image,name="u_image")
		return frameObjImage
			
	def saveArry(self, nparray, name="nparray"):
		image=array_to_img(nparray, data_format = "channels_last")
		image.save("./resultImg/"+name+".jpg")
		
	def saveImg(self, image, name="nparray"):
		image.save("./resultImg/"+name+".jpg")
	
	
	''' Methoden der Klasse
	## a) Hilfsmethoden
	# Speichert ein Bild der Trainings-Menge mit Index'''
	def saveBild(self, imageIndex):  ## for test
		(self.imagesTrain, self.labelsTrain), (self.imagesTest, self.labelsTest) = mnist.load_data()
		npArrayBild=np.expand_dims(self.imagesTest[imageIndex], axis=0) 
		label=self.labelsTest[imageIndex]
		## wandle in ein Bild um
		bild=Image.fromarray(npArrayBild[0])
		## speichert das Bild mit dem Dateinamen
		zeit=time.strftime("%H:%M:%S")
		filenameTrain="B"+str(imageIndex) +"L"+str(label)+"_"+zeit+".jpg"
		bild.save(filenameTrain)
		bild.close()
	''' -------------------------------------------------------------------------------------------- '''
def main():
		print("try in main")
		# register node
		rospy.init_node('prediction', anonymous=False)
		# init Prediction
		pred = Prediction()
		# TESTREGION: TESTEN MIT BEKANNTEM BILD 
		##  Bild aus der Trainingnge wird ausgewaehlt 
		imageIndex=7 # wie in Camera Pseudo (es ist uebrigend die Ziffer 4 die zu erkennen ist)
		### Trainingsmodell, DEEP LEARNING TRAINING 
		### TEST:Predict an Images and load Trainimages
		inputLabel, predictionLabel= cnn.predictTestImage(imageIndex)
		print("Bereit zum Empfang der Bilder zur Prediction ... ")
		try:
			rospy.spin()
		except KeyboardInterrupt:
			print "Shutting down ROS SubsciberCam"
		cv2.destroyAllWindows()	

if __name__ == '__main__':
	main()