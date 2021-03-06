#!/usr/bin/env python
# Software License Agreement (BSD License)
# Copyright (c) 2018, jonas heinke j.h
# Empfaengt Strassenschild-Images und zugehoerige Labels
# Labels wurden von Prediction.py & Cnn.py ermittelt
# Die erkannten Verkehrsschilder beinflussen die Steuerung des Autos 

import numpy as np
# rospy for the subscriber
import rospy
from std_msgs.msg import String, Bool, Int32, Int16MultiArray
# ROS Image message
from sensor_msgs.msg import Image, CompressedImage
## Importtyp (j.h)
## from sensor_msgs.msg import CompressedImage
# ROS Image message -> OpenCV2 image converter
from cv_bridge import CvBridge, CvBridgeError
# OpenCV2 for saving an image
import cv2
# j.h keras musste nachinstalliert werden
from keras.datasets import mnist
import tensorflow as tf
# Instantiate CvBridge
bridge = CvBridge()
# image
from PIL import Image
import time
import os
import csv ###
'''
Empfaengt Daten vom Modul Prediction und gibt diese aus. Dazu gehoeren eine Klassennummer, ein Wahrscheinlichkeitswert und
	ein Kommentar. Zusaetzlich wir eine Beschreibung zur Klassennnumer in einer csv-Datei gelesen und ausgegeben.
	Das Bild, welches klassifiziert werden sollte, wird enbenfalls ausgegeben'
'''
class SubscribCar:
	def __init__(self):
		print("Subscribe image and prediction number (Konstruktor)")
		self.comment='' # Instanzvariable
		self.cv_bridge = CvBridge()
		# Subscriber fuer Vorhersage
		self.callbackRoadSignPrediction=rospy.Subscriber(name='/camera/output/specific/prediction',
			data_class=String,
			callback=self.callbackRoadSignPrediction,
			queue_size = 1) ##
		#Subscriber fuer Objektbild, passend zur Vorhersage	
		self.subscribPredictionImage=rospy.Subscriber(name='camera/output/specific/compressed_img_msgs',
			data_class=CompressedImage,
			callback=self.callbackRoadSignImage,
			queue_size = 1)  

	''' Empfaengt den Vorhersagestring 
	@param predictionStr - Vorhersagenummer | Wahrscheinlichkeitswert | Kommentar
	'''
	def callbackRoadSignPrediction(self, predictionStr):
		predictionNumber, probability, self.comment=predictionStr.data.split("|") # zerlege String
		label=self.readReferenz(predictionNumber) # hole Beschreibung
		print("Label of the predicted road sign: %2s : %13s(%-5.3f) %s" % (predictionNumber, self.comment, float(probability), label))
	''' Empfaengt das Bild, das klassifiziert wurde
	@param roadSignImage - Objektbild, Bild eines Verkehrszeichens
	'''
	def callbackRoadSignImage(self, roadSignImage):
	     # Ausgabe als Bild
		cv2.destroyAllWindows() #altes Bild loeschen
		np_array = np.fromstring(roadSignImage.data, np.uint8)
		# cv2.CV_LOAD_IMAGE_COLOR #cv2.IMREAD_COLOR, cv2.COLOR_BGR2HSV, cv2.COLOR_BGR2GRAY
		image_np = cv2.imdecode(np_array,  cv2.COLOR_RGB2HSV ) 
		cv2.imshow('SubsribCarCrt, Image: '+self.comment, image_np)
		cv2.waitKey(50) #mindestens eine ms Pause - hier zur Kontrolle
		
	
	''' Liest Beschreibung zur erkannten Klasse
	@param roadSignNumber - Klassennummmer des Verkehrszeichenbildes
	@return label - Beschreibung zur Klassennummer 
	'''
	def readReferenz(self, roadSignNumber):
		#label=""
		gtFile = open('nummerBezeichnungReferenz.csv', "r" ) # annotations file
		gtReader = csv.reader(gtFile, delimiter=',') # csv parser for annotations file, ## gtReader = csv.DictReader(gtFile, delimiter=';')
		gtReader.next() # skip header
		#gtReader.next() 
		label=''
		for row in gtReader:
			if roadSignNumber == row[0]:
				label= row[3]
		gtFile.close()
		return label	
	# -------------------------------------------------------------------------------------------------
def main():
	verbose = 0  # use 1 for debug

	# register node
	rospy.init_node('SubscribCar', anonymous=True)
	car=SubscribCar()
		
	try:
		rospy.spin()

	except KeyboardInterrupt:
		print "Shutting down ROS SubsciberCarCrt.py"
	cv2.destroyAllWindows()
		
if __name__ == '__main__':
	main()  ##Subsrib Image and Number
