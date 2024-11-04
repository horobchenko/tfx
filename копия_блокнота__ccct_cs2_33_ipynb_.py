# -*- coding: utf-8 -*-
"""Копия блокнота "ccct_cs2_33.ipynb"

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1nkG8rJ6W2ltkPdqXQeveOnRGEnv7t0Zg

##### Copyright 2021 The TensorFlow Authors.
"""

#@title Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""# Simple TFX Pipeline Tutorial using Penguin dataset

***A Short tutorial to run a simple TFX pipeline.***

Note: We recommend running this tutorial in a Colab notebook, with no setup required!  Just click "Run in Google Colab".

<div class="buttons-wrapper">
  <a class="md-button" target="_blank" href=
     "https://www.tensorflow.org/tfx/tutorials/tfx/penguin_simple">
    <div class="buttons-content">
      <img src="https://www.tensorflow.org/images/tf_logo_32px.png">
      View on TensorFlow.org
    </div>
  </a>
  <a class="md-button" target="_blank" href=
     "https://colab.research.google.com/github/tensorflow/tfx/blob/master/docs/tutorials/tfx/penguin_simple.ipynb">
    <div class="buttons-content">
      <img src=
	   "https://www.tensorflow.org/images/colab_logo_32px.png">
      Run in Google Colab
    </div>
  </a>
  <a class="md-button" target="_blank" href=
     "https://github.com/tensorflow/tfx/tree/master/docs/tutorials/tfx/penguin_simple.ipynb">
    <div class="buttons-content">
      <img width="32px" src=
	   "https://www.tensorflow.org/images/GitHub-Mark-32px.png">
      View source on GitHub
    </div>
  </a>
  <a class="md-button" href=
     "https://storage.googleapis.com/tensorflow_docs/tfx/docs/tutorials/tfx/penguin_simple.ipynb">
    <div class="buttons-content">
      <img src=
	   "https://www.tensorflow.org/images/download_logo_32px.png">
      Download notebook
    </div>
  </a>
</div>

In this notebook-based tutorial, we will create and run a TFX pipeline
for a simple classification model.
The pipeline will consist of three essential TFX components: ExampleGen,
Trainer and Pusher. The pipeline includes the most minimal ML workflow like
importing data, training a model and exporting the trained model.

Please see
[Understanding TFX Pipelines](../../../guide/understanding_tfx_pipelines)
to learn more about various concepts in TFX.

## Set Up
We first need to install the TFX Python package and download
the dataset which we will use for our model.

### Upgrade Pip

To avoid upgrading Pip in a system when running locally,
check to make sure that we are running in Colab.
Local systems can of course be upgraded separately.
"""

try:
  import colab
  !pip install --upgrade pip
except:
  pass

"""### Install TFX

"""

!pip install -U tfx

"""### Did you restart the runtime?

If you are using Google Colab, the first time that you run
the cell above, you must restart the runtime by clicking
above "RESTART RUNTIME" button or using "Runtime > Restart
runtime ..." menu. This is because of the way that Colab
loads packages.

Check the TensorFlow and TFX versions.
"""

import tensorflow as tf
print('TensorFlow version: {}'.format(tf.__version__))
from tfx import v1 as tfx
print('TFX version: {}'.format(tfx.__version__))

"""### Set up variables

There are some variables used to define a pipeline. You can customize these
variables as you want. By default all output from the pipeline will be
generated under the current directory.
"""

import os

PIPELINE_NAME = "ccct_cs2_33"

# Output directory to store artifacts generated from the pipeline.
PIPELINE_ROOT = os.path.join('pipelines', PIPELINE_NAME)
# Path to a SQLite DB file to use as an MLMD storage.
METADATA_PATH = os.path.join('metadata', PIPELINE_NAME, 'metadata.db')
# Output directory where created models from the pipeline will be exported.
SERVING_MODEL_DIR = os.path.join('serving_model', PIPELINE_NAME)

from absl import logging
logging.set_verbosity(logging.INFO)  # Set default logging level.

"""### Prepare example data
We will download the example dataset for use in our TFX pipeline. The dataset we
are using is
[Palmer Penguins dataset](https://allisonhorst.github.io/palmerpenguins/articles/intro.html)
which is also used in other
[TFX examples](https://github.com/tensorflow/tfx/tree/master/tfx/examples/penguin).

There are four numeric features in this dataset:

- culmen_length_mm
- culmen_depth_mm
- flipper_length_mm
- body_mass_g

All features were already normalized to have range [0,1]. We will build a
classification model which predicts the `species` of penguins.

Because TFX ExampleGen reads inputs from a directory, we need to create a
directory and copy dataset to it.
"""

import urllib.request
import tempfile

DATA_ROOT = tempfile.mkdtemp(prefix='tfx-cs2data')  # Create a temporary directory.
_data_url = 'https://raw.githubusercontent.com/horobchenko/tfx/refs/heads/CCCT/data_1.csv'
_data_filepath = os.path.join(DATA_ROOT, "data.csv")
urllib.request.urlretrieve(_data_url, _data_filepath)

"""Take a quick look at the CSV file."""

!head {_data_filepath}

"""You should be able to see five values. `species` is one of 0, 1 or 2, and all
other features should have values between 0 and 1.

## Create a pipeline

TFX pipelines are defined using Python APIs. We will define a pipeline which
consists of following three components.
- CsvExampleGen: Reads in data files and convert them to TFX internal format
for further processing. There are multiple
[ExampleGen](../../../guide/examplegen)s for various
formats. In this tutorial, we will use CsvExampleGen which takes CSV file input.
- Trainer: Trains an ML model.
[Trainer component](../../../guide/trainer) requires a
model definition code from users. You can use TensorFlow APIs to specify how to
train a model and save it in a _saved_model_ format.
- Pusher: Copies the trained model outside of the TFX pipeline.
[Pusher component](../../../guide/pusher) can be thought
of as a deployment process of the trained ML model.

Before actually define the pipeline, we need to write a model code for the
Trainer component first.

### Write model training code

We will create a simple DNN model for classification using TensorFlow Keras
API. This model training code will be saved to a separate file.

In this tutorial we will use
[Generic Trainer](../../../guide/trainer#generic_trainer)
of TFX which support Keras-based models. You need to write a Python file
containing `run_fn` function, which is the entrypoint for the `Trainer`
component.
"""

_trainer_module_file = 'ccct_trainer.py'

# Commented out IPython magic to ensure Python compatibility.
# %%writefile {_trainer_module_file}
# 
# from typing import List
# from absl import logging
# import tensorflow as tf
# from tensorflow import keras
# from tensorflow_transform.tf_metadata import schema_utils
# 
# from tfx import v1 as tfx
# from tfx_bsl.public import tfxio
# from tensorflow_metadata.proto.v0 import schema_pb2
# 
# _FEATURE_KEYS = [
#     'cycle', 'time'
# ]
# _LABEL_KEY = 'indicator'
# 
# _TRAIN_BATCH_SIZE = 6
# _EVAL_BATCH_SIZE = 6
# 
# # Since we're not generating or creating a schema, we will instead create
# # a feature spec.  Since there are a fairly small number of features this is
# # manageable for this dataset.
# _FEATURE_SPEC = {
#     **{
#         feature: tf.io.FixedLenFeature(shape=[1], dtype=tf.float32)
#            for feature in _FEATURE_KEYS
#        },
#     _LABEL_KEY: tf.io.FixedLenFeature(shape=[1], dtype=tf.int64)
# }
# 
# 
# def _input_fn(file_pattern: List[str],
#               data_accessor: tfx.components.DataAccessor,
#               schema: schema_pb2.Schema,
#               batch_size: int = 6) -> tf.data.Dataset:
#   """Generates features and label for training.
# 
#   Args:
#     file_pattern: List of paths or patterns of input tfrecord files.
#     data_accessor: DataAccessor for converting input to RecordBatch.
#     schema: schema of the input data.
#     batch_size: representing the number of consecutive elements of returned
#       dataset to combine in a single batch
# 
#   Returns:
#     A dataset that contains (features, indices) tuple where features is a
#       dictionary of Tensors, and indices is a single Tensor of label indices.
#   """
#   return data_accessor.tf_dataset_factory(
#       file_pattern,
#       tfxio.TensorFlowDatasetOptions(
#           batch_size=batch_size, label_key=_LABEL_KEY),
#       schema=schema).repeat()
# 
# 
# def _build_keras_model() -> tf.keras.Model:
#   """Creates a DNN Keras model for classifying penguin data.
# 
#   Returns:
#     A Keras Model.
#   """
#   # The model below is built with Functional API, please refer to
#   # https://www.tensorflow.org/guide/keras/overview for all API options.
#   inputs = [keras.layers.Input(shape=(1,), name=f) for f in _FEATURE_KEYS]
#   d = keras.layers.concatenate(inputs)
#   for _ in range(2):
#     d = keras.layers.Dense(8, activation='relu')(d)
#   outputs = keras.layers.Dense(2)(d)
# 
#   model = keras.Model(inputs=inputs, outputs=outputs)
#   model.compile(
#       optimizer=keras.optimizers.Adam(1e-2),
#       loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
#       metrics=[keras.metrics.SparseCategoricalAccuracy()])
# 
#   model.summary(print_fn=logging.info)
#   return model
# 
# 
# # TFX Trainer will call this function.
# def run_fn(fn_args: tfx.components.FnArgs):
#   """Train the model based on given args.
# 
#   Args:
#     fn_args: Holds args used to train the model as name/value pairs.
#   """
# 
#   # This schema is usually either an output of SchemaGen or a manually-curated
#   # version provided by pipeline author. A schema can also derived from TFT
#   # graph if a Transform component is used. In the case when either is missing,
#   # `schema_from_feature_spec` could be used to generate schema from very simple
#   # feature_spec, but the schema returned would be very primitive.
#   schema = schema_utils.schema_from_feature_spec(_FEATURE_SPEC)
# 
#   train_dataset = _input_fn(
#       fn_args.train_files,
#       fn_args.data_accessor,
#       schema,
#       batch_size=_TRAIN_BATCH_SIZE)
#   eval_dataset = _input_fn(
#       fn_args.eval_files,
#       fn_args.data_accessor,
#       schema,
#       batch_size=_EVAL_BATCH_SIZE)
# 
#   model = _build_keras_model()
#   model.fit(
#       train_dataset,
#       steps_per_epoch=fn_args.train_steps,
#       validation_data=eval_dataset,
#       validation_steps=fn_args.eval_steps)
# 
#   # The result of the training should be saved in `fn_args.serving_model_dir`
#   # directory.
#   model.save(fn_args.serving_model_dir, save_format='tf')

from tfx.orchestration.experimental.interactive.interactive_context import InteractiveContext
context = InteractiveContext()
example_gen = tfx.components.CsvExampleGen(input_base=DATA_ROOT)
context.run(example_gen)

DATA_ROOT

example_gen.outputs['examples'].get()

import pprint as pp
# Get the URI of the output artifact representing the training examples, which is a directory
train_uri = os.path.join(example_gen.outputs['examples'].get()[0].uri, 'Split-train')

# Get the list of files in this directory (all compressed TFRecord files)
tfrecord_filenames = [os.path.join(train_uri, name)
                      for name in os.listdir(train_uri)]

# Create a `TFRecordDataset` to read these files
dataset = tf.data.TFRecordDataset(tfrecord_filenames, compression_type="GZIP")

# Iterate over the first 3 records and decode them.
for tfrecord in dataset.take(3):
  serialized_example = tfrecord.numpy()
  example = tf.train.Example()
  example.ParseFromString(serialized_example)
  pp.pprint(example)

"""Now you have completed all preparation steps to build a TFX pipeline.

### Write a pipeline definition

We define a function to create a TFX pipeline. A `Pipeline` object
represents a TFX pipeline which can be run using one of the pipeline
orchestration systems that TFX supports.
"""

def _create_pipeline(pipeline_name: str, pipeline_root: str, data_root: str,
                     module_file: str, serving_model_dir: str,
                     metadata_path: str) -> tfx.dsl.Pipeline:
  """Creates a three component penguin pipeline with TFX."""
  # Brings data into the pipeline.
  example_gen = tfx.components.CsvExampleGen(input_base=data_root)

  # Uses user-provided Python function that trains a model.
  trainer = tfx.components.Trainer(
      module_file=module_file,
      examples=example_gen.outputs['examples'],
      train_args=tfx.proto.TrainArgs(num_steps=100),
      eval_args=tfx.proto.EvalArgs(num_steps=5))

  # Pushes the model to a filesystem destination.
  pusher = tfx.components.Pusher(
      model=trainer.outputs['model'],
      push_destination=tfx.proto.PushDestination(
          filesystem=tfx.proto.PushDestination.Filesystem(
              base_directory=serving_model_dir)))

  # Following three components will be included in the pipeline.
  components = [
      example_gen,
      trainer,
      pusher,
  ]

  return tfx.dsl.Pipeline(
      pipeline_name=pipeline_name,
      pipeline_root=pipeline_root,
      metadata_connection_config=tfx.orchestration.metadata
      .sqlite_metadata_connection_config(metadata_path),
      components=components)

"""## Run the pipeline

TFX supports multiple orchestrators to run pipelines.
In this tutorial we will use `LocalDagRunner` which is included in the TFX
Python package and runs pipelines on local environment.
We often call TFX pipelines "DAGs" which stands for directed acyclic graph.

`LocalDagRunner` provides fast iterations for development and debugging.
TFX also supports other orchestrators including Kubeflow Pipelines and Apache
Airflow which are suitable for production use cases.

See
[TFX on Cloud AI Platform Pipelines](/tutorials/tfx/cloud-ai-platform-pipelines)
or
[TFX Airflow Tutorial](/tutorials/tfx/airflow_workshop)
to learn more about other orchestration systems.

Now we create a `LocalDagRunner` and pass a `Pipeline` object created from the
function we already defined.

The pipeline runs directly and you can see logs for the progress of the pipeline including ML model training.
"""

tfx.orchestration.LocalDagRunner().run(
  _create_pipeline(
      pipeline_name=PIPELINE_NAME,
      pipeline_root=PIPELINE_ROOT,
      data_root=DATA_ROOT,
      module_file=_trainer_module_file,
      serving_model_dir=SERVING_MODEL_DIR,
      metadata_path=METADATA_PATH))

"""You should see "INFO:absl:Component Pusher is finished." at the end of the
logs if the pipeline finished successfully. Because `Pusher` component is the
last component of the pipeline.

The pusher component pushes the trained model to the `SERVING_MODEL_DIR` which
is the `serving_model/penguin-simple` directory if you did not change the
variables in the previous steps. You can see the result from the file browser
in the left-side panel in Colab, or using the following command:
"""

# List files in created model directory.
!find {SERVING_MODEL_DIR}

"""## Next steps

You can find more resources on https://www.tensorflow.org/tfx/tutorials.

Please see
[Understanding TFX Pipelines](../../../guide/understanding_tfx_pipelines)
to learn more about various concepts in TFX.

"""