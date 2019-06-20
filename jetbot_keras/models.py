import os
import numpy as np

from tensorflow.python import keras
from tensorflow.python.keras.layers import Input, Dense
from tensorflow.python.keras.models import Model, Sequential
from tensorflow.python.keras.layers import Convolution2D, MaxPooling2D, Reshape, BatchNormalization
from tensorflow.python.keras.layers import Activation, Dropout, Flatten, Cropping2D, Lambda
from tensorflow.python.keras.layers.merge import concatenate
from tensorflow.python.keras.layers import LSTM
from tensorflow.python.keras.layers.wrappers import TimeDistributed as TD
from tensorflow.python.keras.layers import Conv3D, MaxPooling3D, Cropping3D, Conv2DTranspose
import mlutils


def default_categorical(input_shape=(120, 160, 3), roi_crop=(0, 0)):

    opt = keras.optimizers.Adam()
    drop = 0.4

    img_in = Input(shape=input_shape, name='img_in')                      # First layer, input layer, Shape comes from camera.py resolution, RGB
    x = img_in
    x = Cropping2D(cropping=(roi_crop, (0,0)))(x) #trim configured pixels off top and bottom
    #x = Lambda(lambda x: x/127.5 - 1.)(x) # normalize and re-center
    x = BatchNormalization()(x)
    x = Convolution2D(24, (5,5), strides=(2,2), activation='relu', name="conv2d_1")(x)       # 24 features, 5 pixel x 5 pixel kernel (convolution, feauture) window, 2wx2h stride, relu activation
    x = Dropout(drop)(x)                                                      # Randomly drop out (turn off) 10% of the neurons (Prevent overfitting)
    x = Convolution2D(32, (5,5), strides=(2,2), activation='relu', name="conv2d_2")(x)       # 32 features, 5px5p kernel window, 2wx2h stride, relu activatiion
    x = Dropout(drop)(x)                                                      # Randomly drop out (turn off) 10% of the neurons (Prevent overfitting)
    if input_shape[0] > 32 :
        x = Convolution2D(64, (5,5), strides=(2,2), activation='relu', name="conv2d_3")(x)       # 64 features, 5px5p kernal window, 2wx2h stride, relu
    else:
        x = Convolution2D(64, (3,3), strides=(1,1), activation='relu', name="conv2d_3")(x)       # 64 features, 5px5p kernal window, 2wx2h stride, relu
    if input_shape[0] > 64 :
        x = Convolution2D(64, (3,3), strides=(2,2), activation='relu', name="conv2d_4")(x)       # 64 features, 3px3p kernal window, 2wx2h stride, relu
    elif input_shape[0] > 32 :
        x = Convolution2D(64, (3,3), strides=(1,1), activation='relu', name="conv2d_4")(x)       # 64 features, 3px3p kernal window, 2wx2h stride, relu
    x = Dropout(drop)(x)                                                      # Randomly drop out (turn off) 10% of the neurons (Prevent overfitting)
    x = Convolution2D(64, (3,3), strides=(1,1), activation='relu', name="conv2d_5")(x)       # 64 features, 3px3p kernal window, 1wx1h stride, relu
    x = Dropout(drop)(x)                                                      # Randomly drop out (turn off) 10% of the neurons (Prevent overfitting)
    # Possibly add MaxPooling (will make it less sensitive to position in image).  Camera angle fixed, so may not to be needed

    x = Flatten(name='flattened')(x)                                        # Flatten to 1D (Fully connected)
    x = Dense(100, activation='relu', name="fc_1")(x)                                    # Classify the data into 100 features, make all negatives 0
    x = Dropout(drop)(x)                                                      # Randomly drop out (turn off) 10% of the neurons (Prevent overfitting)
    x = Dense(50, activation='relu', name="fc_2")(x)                                     # Classify the data into 50 features, make all negatives 0
    x = Dropout(drop)(x)                                                      # Randomly drop out 10% of the neurons (Prevent overfitting)
    #categorical output of the angle
    angle_out = Dense(15, activation='softmax', name='angle_out')(x)        # Connect every input with every output and output 15 hidden units. Use Softmax to give percentage. 15 categories and find best one based off percentage 0.0-1.0

    #continous output of throttle
    throttle_out = Dense(20, activation='softmax', name='throttle_out')(x)      # Reduce to 1 number, Positive number only

    model = Model(inputs=[img_in], outputs=[angle_out, throttle_out])
    return model


def default_n_linear(num_outputs, input_shape=(120, 160, 3), roi_crop=(0, 0)):

    drop = 0.1

    img_in = Input(shape=input_shape, name='img_in')
    x = img_in
    x = Cropping2D(cropping=(roi_crop, (0,0)))(x) #trim pixels off top and bottom
    #x = Lambda(lambda x: x/127.5 - 1.)(x) # normalize and re-center
    x = BatchNormalization()(x)
    x = Convolution2D(24, (5,5), strides=(2,2), activation='relu', name="conv2d_1")(x)
    x = Dropout(drop)(x)
    x = Convolution2D(32, (5,5), strides=(2,2), activation='relu', name="conv2d_2")(x)
    x = Dropout(drop)(x)
    x = Convolution2D(64, (5,5), strides=(2,2), activation='relu', name="conv2d_3")(x)
    x = Dropout(drop)(x)
    x = Convolution2D(64, (3,3), strides=(1,1), activation='relu', name="conv2d_4")(x)
    x = Dropout(drop)(x)
    x = Convolution2D(64, (3,3), strides=(1,1), activation='relu', name="conv2d_5")(x)
    x = Dropout(drop)(x)

    x = Flatten(name='flattened')(x)
    x = Dense(100, activation='relu')(x)
    x = Dropout(drop)(x)
    x = Dense(50, activation='relu')(x)
    x = Dropout(drop)(x)

    outputs = []

    for i in range(num_outputs):
        outputs.append(Dense(1, activation='linear', name='n_outputs' + str(i))(x))

    model = Model(inputs=[img_in], outputs=outputs)

    return model


def rnn_lstm(seq_length=3, num_outputs=2, image_shape=(120,160,3)):


    img_seq_shape = (seq_length,) + image_shape
    img_in = Input(batch_shape = img_seq_shape, name='img_in')
    drop_out = 0.3

    x = Sequential()
    x.add(TD(Cropping2D(cropping=((40,0), (0,0))), input_shape=img_seq_shape )) #trim 60 pixels off top
    x.add(TD(BatchNormalization()))
    x.add(TD(Convolution2D(24, (5,5), strides=(2,2), activation='relu')))
    x.add(TD(Dropout(drop_out)))
    x.add(TD(Convolution2D(32, (5,5), strides=(2,2), activation='relu')))
    x.add(TD(Dropout(drop_out)))
    x.add(TD(Convolution2D(32, (3,3), strides=(2,2), activation='relu')))
    x.add(TD(Dropout(drop_out)))
    x.add(TD(Convolution2D(32, (3,3), strides=(1,1), activation='relu')))
    x.add(TD(Dropout(drop_out)))
    x.add(TD(MaxPooling2D(pool_size=(2, 2))))
    x.add(TD(Flatten(name='flattened')))
    x.add(TD(Dense(100, activation='relu')))
    x.add(TD(Dropout(drop_out)))

    x.add(LSTM(128, return_sequences=True, name="LSTM_seq"))
    x.add(Dropout(.1))
    x.add(LSTM(128, return_sequences=False, name="LSTM_out"))
    x.add(Dropout(.1))
    x.add(Dense(128, activation='relu'))
    x.add(Dropout(.1))
    x.add(Dense(64, activation='relu'))
    x.add(Dense(10, activation='relu'))
    x.add(Dense(num_outputs, activation='linear', name='model_outputs'))

    return x



def build_3d_cnn(w, h, d, s, num_outputs):
    #Credit: https://github.com/jessecha/DNRacing/blob/master/3D_CNN_Model/model.py
    '''
        w : width
        h : height
        d : depth
        s : n_stacked
    '''
    input_shape=(s, h, w, d)

    model = Sequential()
    #First layer
    model.add(Cropping3D(cropping=((0,0), (50,10), (0,0)), input_shape=input_shape) ) #trim pixels off top

    # Second layer
    model.add(Conv3D(
        filters=16, kernel_size=(3,3,3), strides=(1,3,3),
        data_format='channels_last', padding='same')
    )
    model.add(Activation('relu'))
    model.add(MaxPooling3D(
        pool_size=(1,2,2), strides=(1,2,2), padding='valid', data_format=None)
    )
    # Third layer
    model.add(Conv3D(
        filters=32, kernel_size=(3,3,3), strides=(1,1,1),
        data_format='channels_last', padding='same')
    )
    model.add(Activation('relu'))
    model.add(MaxPooling3D(
        pool_size=(1, 2, 2), strides=(1,2,2), padding='valid', data_format=None)
    )
    # Fourth layer
    model.add(Conv3D(
        filters=64, kernel_size=(3,3,3), strides=(1,1,1),
        data_format='channels_last', padding='same')
    )
    model.add(Activation('relu'))
    model.add(MaxPooling3D(
        pool_size=(1,2,2), strides=(1,2,2), padding='valid', data_format=None)
    )
    # Fifth layer
    model.add(Conv3D(
        filters=128, kernel_size=(3,3,3), strides=(1,1,1),
        data_format='channels_last', padding='same')
    )
    model.add(Activation('relu'))
    model.add(MaxPooling3D(
        pool_size=(1,2,2), strides=(1,2,2), padding='valid', data_format=None)
    )
    # Fully connected layer
    model.add(Flatten())

    model.add(Dense(256))
    model.add(BatchNormalization())
    model.add(Activation('relu'))
    model.add(Dropout(0.5))

    model.add(Dense(256))
    model.add(BatchNormalization())
    model.add(Activation('relu'))
    model.add(Dropout(0.5))

    model.add(Dense(num_outputs))
    #model.add(Activation('tanh'))

    return model



def default_latent(num_outputs, input_shape):

    drop = 0.2

    img_in = Input(shape=input_shape, name='img_in')
    x = img_in
    x = Lambda(lambda x: x/255.)(x) # normalize
    x = Convolution2D(24, (5,5), strides=(2,2), activation='relu', name="conv2d_1")(x)
    x = Dropout(drop)(x)
    x = Convolution2D(32, (5,5), strides=(2,2), activation='relu', name="conv2d_2")(x)
    x = Dropout(drop)(x)
    x = Convolution2D(32, (5,5), strides=(2,2), activation='relu', name="conv2d_3")(x)
    x = Dropout(drop)(x)
    x = Convolution2D(32, (3,3), strides=(1,1), activation='relu', name="conv2d_4")(x)
    x = Dropout(drop)(x)
    x = Convolution2D(32, (3,3), strides=(1,1), activation='relu', name="conv2d_5")(x)
    x = Dropout(drop)(x)
    x = Convolution2D(64, (3,3), strides=(2,2), activation='relu', name="conv2d_6")(x)
    x = Dropout(drop)(x)
    x = Convolution2D(64, (3,3), strides=(2,2), activation='relu', name="conv2d_7")(x)
    x = Dropout(drop)(x)
    x = Convolution2D(10, (1,1), strides=(2,2), activation='relu', name="latent")(x)

    y = Conv2DTranspose(filters=64, kernel_size=(3,3), strides=2, name="deconv2d_1")(x)
    y = Conv2DTranspose(filters=64, kernel_size=(3,3), strides=2, name="deconv2d_2")(y)
    y = Conv2DTranspose(filters=32, kernel_size=(3,3), strides=2, name="deconv2d_3")(y)
    y = Conv2DTranspose(filters=32, kernel_size=(3,3), strides=2, name="deconv2d_4")(y)
    y = Conv2DTranspose(filters=32, kernel_size=(3,3), strides=2, name="deconv2d_5")(y)
    y = Conv2DTranspose(filters=1, kernel_size=(3,3), strides=2, name="img_out")(y)

    x = Flatten(name='flattened')(x)
    x = Dense(256, activation='relu')(x)
    x = Dropout(drop)(x)
    x = Dense(100, activation='relu')(x)
    x = Dropout(drop)(x)
    x = Dense(50, activation='relu')(x)
    x = Dropout(drop)(x)

    outputs = [y]

    for i in range(num_outputs):
        outputs.append(Dense(1, activation='linear', name='n_outputs' + str(i))(x))

    model = Model(inputs=[img_in], outputs=outputs)

    return model