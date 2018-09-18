# !/usr/bin/env python
# -*- coding:utf-8 -*-

import numpy as np

import keras
from keras import optimizers
from keras import backend as K
from keras.losses import categorical_crossentropy as logloss
from keras.metrics import categorical_accuracy, top_k_categorical_accuracy
from keras.datasets import cifar10
from keras.preprocessing.image import ImageDataGenerator
from keras.engine.topology import Input, Container
from keras.engine.training import Model
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten, advanced_activations, BatchNormalization
from keras.layers import Conv2D, MaxPooling2D, Convolution2D, pooling, Lambda, concatenate
from keras.callbacks import ModelCheckpoint, ReduceLROnPlateau
import os

batch_size = 100
num_classes = 10
epochs = 300
num_predictions = 20

# The data, split between train and test sets:
(x_train, y_train), (x_test, y_test) = cifar10.load_data()
print('x_train shape:', x_train.shape)
print(x_train.shape[0], 'train samples')
print(x_test.shape[0], 'test samples')

y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)

data_dir = './data/'

train_logits = np.load(data_dir + 'train_logits.npy')[()]
val_logits = np.load(data_dir + 'val_logits.npy')[()]

y_train_ =

temperature = 5.0


def knowledge_distillation_loss(y_true, y_pred, lambda_const):
    # split in
    #    onehot hard true targets
    #    logits from xception
    y_true, logits = y_true[:, :num_classes], y_true[:, num_classes:]

    # convert logits to soft targets
    y_soft = K.softmax(logits / temperature)

    # split in
    #    usual output probabilities
    #    probabilities made softer with temperature
    y_pred, y_pred_soft = y_pred[:, :num_classes], y_pred[:, num_classes:]

    return lambda_const * logloss(y_true, y_pred) + logloss(y_soft, y_pred_soft)


def accuracy(y_true, y_pred):
    y_true = y_true[:, :num_classes]
    y_pred = y_pred[:, :num_classes]
    return categorical_accuracy(y_true, y_pred)


def categorical_crossentropy(y_true, y_pred):
    y_true = y_true[:, :num_classes]
    y_pred = y_pred[:, :num_classes]
    return logloss(y_true, y_pred)


# logloss with only soft probabilities and targets
def soft_logloss(y_true, y_pred):
    logits = y_true[:, num_classes:]
    y_soft = K.softmax(logits/temperature)
    y_pred_soft = y_pred[:, num_classes:]
    return logloss(y_soft, y_pred_soft)


input_layer = Input(x_train.shape[1:])
x = Convolution2D(32, (3, 3), padding='same')(input_layer)
x = BatchNormalization()(x)
x = advanced_activations.LeakyReLU(alpha=0.1)(x)
x = MaxPooling2D((2, 2), strides=(2, 2))(x)
x = Dropout(0.5)(x)
x = Convolution2D(32, (3, 3), padding='same')(x)
x = BatchNormalization()(x)
x = advanced_activations.LeakyReLU(alpha=0.1)(x)
x = Convolution2D(32, (3, 3), padding='same')(x)
x = BatchNormalization()(x)
x = advanced_activations.LeakyReLU(alpha=0.1)(x)
x = MaxPooling2D((2, 2), strides=(2, 2))(x)
x = Dropout(0.5)(x)
x = Convolution2D(32, (3, 3), padding='same')(x)
x = BatchNormalization()(x)
x = advanced_activations.LeakyReLU(alpha=0.1)(x)

x = pooling.GlobalAveragePooling2D()(x)
logits = Dense(10, activation=None)(x)
probabilities = Activation('softmax')(logits)

logits_T = Lambda(lambda x: x/temperature)(logits)
probabilities_T = Activation('softmax')(logits_T)

output = concatenate([probabilities, probabilities_T])
model = Model(input_layer, output)

lambda_const = 0.07

model.compile(
    optimizer=optimizers.SGD(lr=1e-1, momentum=0.9, nesterov=True),
    loss=lambda y_true, y_pred: knowledge_distillation_loss(y_true, y_pred, lambda_const),
    metrics=[accuracy, categorical_crossentropy, soft_logloss]
)



model.fit(
    x_train, y_train_,
    batch_size=batch_size,
    epochs=epochs,
    validation_data=(x_test, y_test_),
    verbose=1, shuffle=True,
    callbacks=[
        ModelCheckpoint(filepath="./models/model.ep{epoch:02d}.h5"),
        ReduceLROnPlateau(monitor='val_accuracy', factor=0.1, patience=2, epsilon=0.007)
    ],
)


