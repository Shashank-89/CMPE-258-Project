# Copyright 2021 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Build Movinet for video classification.
Reference: https://arxiv.org/pdf/2103.11511.pdf
"""
from typing import Mapping

from absl import logging
import tensorflow as tf

from official.vision.beta.modeling import backbones
from official.vision.beta.modeling import factory_3d as model_factory
import cfg

import movinet_layers


@tf.keras.utils.register_keras_serializable(package='Vision')
class MovinetClassifier(tf.keras.Model):
  """A video classification class builder."""

  def __init__(self,
               backbone: tf.keras.Model,
               num_classes: int,
               input_specs: Mapping[str, tf.keras.layers.InputSpec] = None,
               dropout_rate: float = 0.0,
               kernel_initializer: str = 'HeNormal',
               kernel_regularizer: tf.keras.regularizers.Regularizer = None,
               bias_regularizer: tf.keras.regularizers.Regularizer = None,
               output_states: bool = False,
               **kwargs):
    """Movinet initialization function.
    Args:
      backbone: A 3d backbone network.
      num_classes: Number of classes in classification task.
      input_specs: Specs of the input tensor.
      dropout_rate: Rate for dropout regularization.
      kernel_initializer: Kernel initializer for the final dense layer.
      kernel_regularizer: Kernel regularizer.
      bias_regularizer: Bias regularizer.
      output_states: if True, output intermediate states that can be used to run
          the model in streaming mode. Inputting the output states of the
          previous input clip with the current input clip will utilize a stream
          buffer for streaming video.
      **kwargs: Keyword arguments to be passed.
    """
    if not input_specs:
      input_specs = {
          'image': tf.keras.layers.InputSpec(shape=[None, None, None, None, 3])
      }

    self._num_classes = num_classes
    self._input_specs = input_specs
    self._dropout_rate = dropout_rate
    self._kernel_initializer = kernel_initializer
    self._kernel_regularizer = kernel_regularizer
    self._bias_regularizer = bias_regularizer
    self._output_states = output_states

    # Keras model variable that excludes @property.setters from tracking
    self._self_setattr_tracking = False

    inputs = {
        name: tf.keras.Input(shape=state.shape[1:], name=f'states/{name}')
        for name, state in input_specs.items()
    }
    states = inputs.get('states', {})

    endpoints, states = backbone(dict(image=inputs['image'], states=states))
    x = endpoints['head']

    x = movinet_layers.ClassifierHead(
        head_filters=backbone._head_filters,
        num_classes=num_classes,
        dropout_rate=dropout_rate,
        kernel_initializer=kernel_initializer,
        kernel_regularizer=kernel_regularizer,
        conv_type=backbone._conv_type)(x)

    if output_states:
      inputs['states'] = {
          k: tf.keras.Input(shape=v.shape[1:], name=k)
          for k, v in states.items()
      }

    outputs = (x, states) if output_states else x

    super(MovinetClassifier, self).__init__(
        inputs=inputs, outputs=outputs, **kwargs)

    # Move backbone after super() call so Keras is happy
    self._backbone = backbone

  @property
  def checkpoint_items(self):
    """Returns a dictionary of items to be additionally checkpointed."""
    return dict(backbone=self.backbone)

  @property
  def backbone(self):
    return self._backbone

  def get_config(self):
    config = {
        'backbone': self._backbone,
        'num_classes': self._num_classes,
        'input_specs': self._input_specs,
        'dropout_rate': self._dropout_rate,
        'kernel_initializer': self._kernel_initializer,
        'kernel_regularizer': self._kernel_regularizer,
        'bias_regularizer': self._bias_regularizer,
        'output_states': self._output_states,
    }
    return config

  @classmethod
  def from_config(cls, config, custom_objects=None):
    # Each InputSpec may need to be deserialized
    # This handles the case where we want to load a saved_model loaded with
    # `tf.keras.models.load_model`
    if config['input_specs']:
      for name in config['input_specs']:
        if isinstance(config['input_specs'][name], dict):
          config['input_specs'][name] = tf.keras.layers.deserialize(
              config['input_specs'][name])
    return cls(**config)


@model_factory.register_model_builder('movinet')
def build_movinet_model(
    input_specs: tf.keras.layers.InputSpec,
    model_config: cfg.MovinetModel,
    num_classes: int,
    l2_regularizer: tf.keras.regularizers.Regularizer = None):
  """Builds movinet model."""
  logging.info('Building movinet model with num classes: %s', num_classes)
  if l2_regularizer is not None:
    logging.info('Building movinet model with regularizer: %s',
                 l2_regularizer.get_config())

  input_specs_dict = {'image': input_specs}
  backbone = backbones.factory.build_backbone(
      input_specs=input_specs,
      backbone_config=model_config.backbone,
      norm_activation_config=model_config.norm_activation,
      l2_regularizer=l2_regularizer)
  model = MovinetClassifier(
      backbone,
      num_classes=num_classes,
      kernel_regularizer=l2_regularizer,
      input_specs=input_specs_dict,
      dropout_rate=model_config.dropout_rate)
  return model