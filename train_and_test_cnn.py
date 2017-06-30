# ----------------------------------------------------
# train and test a convolutional neural network
# ----------------------------------------------------

import tensorflow as tf 
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import os

import tarfile
from six.moves import urllib

# import the  convolutional neural network class
from models.cnn.cnn import CNN

from scripts.train_cnn 				import train_cnn
from scripts.from_github.cifar10 	import maybe_download_and_extract

import configs.config as cnfg


########
# MAIN #
########

def main():

	# weight_initialization options #
	# 
	# 'resume'						: 	resume training from latest checkpoint in weights/log_folder_name/run_name if possible, otherwise default
	# 'from_folder'					: 	load last checkpoint from folder given in 
	# 'pre_trained_encoding'		:	load encoding weights from an auto-encoder
	# 'default'						: 	init weights at random

	initialization_mode = 'resume'

	model_weights_directory = 'weights/02_CIFAR_cnn_pre_training/random-init' # used if initialization_mode == 'from_folder' (relative path)

	pre_trained_conv_weights_directory = 'weights/25_cae_mnist_mse/MNIST_mse_relu_scaled_tanh_strided_conv(0.001)'


	DATASET = "CIFAR10"

	if DATASET == "MNIST":
		# load mnist
		from tensorflow.examples.tutorials.mnist import input_data
		dataset = input_data.read_data_sets("MNIST_data/", one_hot=True)
		input_size = (28, 28)
		num_classes = 10
		one_hot_labels = True
		nhwd_shape = False

	elif DATASET == "CKPLUS":
		import scripts.load_ckplus as load_ckplus
		dataset = load_ckplus.read_data_sets(one_hot=True)
		input_size = (49,64)
		num_classes = load_ckplus.NUM_CLASSES
		one_hot_labels = True
		nhwd_shape = False

	elif DATASET=="CIFAR10":
		dataset 		= "cifar_10" 	# signals the train_cnn function that it needs to load the data via cifar_10_input.py
		one_hot_labels 	= False			# changes the error functions because this cifar-10 version doesn't use a one-hot encoding
		input_size 		= (24, 24, 3) 
		num_classes 	= 1
		nhwd_shape 		= True

		maybe_download_and_extract()

	if nhwd_shape == False:

		# input variables: x (images), y_ (labels), keep_prob (dropout rate)
		x  = tf.placeholder(tf.float32, [None, input_size[0]*input_size[1]], name='input_digits')
		# reshape the input to NHWD format
		x_image = tf.reshape(x, [-1, input_size[0], input_size[1], 1])

	else: 

		x = tf.placeholder(tf.float32, [None, input_size[0], input_size[1], input_size[2]], name='input_images')
		x_image = x

	if one_hot_labels:
		y_ = tf.placeholder(tf.float32, [None, num_classes], name='target_labels')
	else:
		y_ = tf.placeholder(tf.int64,   [None], name='target_labels')


	keep_prob = tf.placeholder(tf.float32)

	

	## #### ##
	# CONFIG # 
	## #### ##

	use_config_file 	= False
	config_file_path 	= 'configs/config.ini'

	# ------------------------------------------------------

	# ARCHITECTURE

	# TODO Sabbir: Begin parameters that should be stored in config ----------------
	# feature extraction parameters
	filter_dims 	= [(5,5), (5,5)]
	hidden_channels = [16, 16] 
	pooling_type  = 'strided_conv' # dont change, std::bac_alloc otherwise (TODO: understand why)
	strides = None # other strides should not work yet
	activation_function = 'relu'

	# fc-layer parameters:
	dense_depths = []

	# TRAINING
	# training parameters:
	batch_size 		= 128
	max_iterations	= 51
	chk_iterations 	= 10
	dropout_k_p		= 0.5

	# only optimize dense layers and leave convolutions as they are
	fine_tuning_only = False
	# TODO Sabbir: End parameters that should be stored in config -------------------


	# TODO Sabbir:  -if use_config_file is true, use behaviour from train_and_test_cnn_using_config, loading the parameters from the config file in config_file_path
	# 				-if false, initialize the variables like above (let us enter the values here (e.g. max_iterations = 1001)) 
	if use_config_file:
		# load config file to class 
		# config class = ... 
		# batchsize = configclas.. 
		pass
	else:
		# move manual config stuff here
		pass

	# -------------------------------------------------------

	# construct names for logging

	architecture_str 	= 'a'  + '_'.join(map(lambda x: str(x[0]) + str(x[1]), filter_dims)) + '-' + '_'.join(map(str, hidden_channels)) + '-' + activation_function
	training_str 		= 'tr' + str(batch_size) + '_' + '_' + str(dropout_k_p)
	

	log_folder_name = '03_CIFAR_cnn_resume_test'
	# run_name 		= 'reference_net' + 'test' + 'cifar' + architecture_str + training_str
	run_name = 'random_init'

	log_path = os.path.join('logs', log_folder_name, run_name)

	# folder to store the training weights in:
	model_save_parent_dir = 'weights'
	save_path = os.path.join(model_save_parent_dir, log_folder_name, run_name)
	check_dirs = [model_save_parent_dir, os.path.join(model_save_parent_dir, log_folder_name), os.path.join(model_save_parent_dir, log_folder_name), os.path.join(model_save_parent_dir, log_folder_name, run_name), os.path.join(model_save_parent_dir, log_folder_name, run_name, 'best')]
	
	for directory in check_dirs:
		if not os.path.exists(directory):
			os.makedirs(directory)


	## ###### ##
	# TRAINING #
	## ###### ##

	init_iteration = 0

	cnn = CNN(x_image, y_, keep_prob, filter_dims, hidden_channels, dense_depths, pooling_type, activation_function, one_hot_labels=one_hot_labels)

	sess = tf.Session() 
	sess.run(tf.global_variables_initializer())

	# add logwriter for tensorboard
	writer = tf.summary.FileWriter(log_path, sess.graph)


	initialization_finished = False

	if initialization_mode == 'resume' or initialization_mode == 'from_folder':
		# initialize training with weights from a previous training 

		cwd = os.getcwd()

		if initialization_mode == 'from_folder':
			chkpnt_file_path = os.path.join(cwd, model_weights_directory)
		else:
			chkpnt_file_path = os.path.join(cwd, save_path)

		saver = tf.train.Saver(cnn.all_variables_dict)
		latest_checkpoint = tf.train.latest_checkpoint(chkpnt_file_path)

		print(latest_checkpoint)

		if latest_checkpoint is not None:

			print('Found checkpoint')

			init_iteration = int(latest_checkpoint.split('-')[-1]) + 1

			best_accuracy_so_far = float(latest_checkpoint.split('-')[-2])

			print('iteration is: {}'.format(init_iteration))
			print('accuracy is: {}'.format(best_accuracy_so_far))

			if initialization_mode == 'from_folder':
				print('retrieved weights from checkpoint, begin with new iteration 0')
				init_iteration = 0

			saver.restore(sess, latest_checkpoint)

			train_cnn(sess, cnn, dataset, x, y_, keep_prob, dropout_k_p, batch_size, init_iteration,  max_iterations, chk_iterations, writer, fine_tuning_only, save_path, best_accuracy_so_far)

			initialization_finished = True

		else:
			print('No checkpoint was found, beginning with iteration 0')


	elif initialization_mode == 'pre_trained_encoding':

		if pre_trained_conv_weights_directory is not None:

			print('Trying to load conv weights from file')

			cwd = os.getcwd()
			chkpnt_file_path = os.path.join(cwd, pre_trained_conv_weights_directory)

			print('Looking for checkpoint in {}'.format(chkpnt_file_path))

			saver = tf.train.Saver()
			latest_checkpoint = tf.train.latest_checkpoint(chkpnt_file_path)

			print('Latest checkpoint is: {}'.format(latest_checkpoint))

			if latest_checkpoint is not None:

				cnn.load_encoding_weights(sess, latest_checkpoint)

				print('Initialized the CNN with encoding weights found in {}'.format(latest_checkpoint))


	if not initialization_finished:
		# always train a new autoencoder 
		train_cnn(sess, cnn, dataset, x, y_, keep_prob, dropout_k_p, batch_size, init_iteration, max_iterations, chk_iterations, writer, fine_tuning_only, save_path)


	# TODO Sabbir: store the current config in a config file in the logs/log_folder_name/run_name folder 

	writer.close()
	sess.close()



if __name__ == '__main__':
	main()