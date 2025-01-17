# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: _tensorflow_core/tensor_slice.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='_tensorflow_core/tensor_slice.proto',
  package='_tensorflow',
  syntax='proto3',
  serialized_pb=_b('\n#_tensorflow_core/tensor_slice.proto\x12\x0b_tensorflow\"\x81\x01\n\x10TensorSliceProto\x12\x34\n\x06\x65xtent\x18\x01 \x03(\x0b\x32$._tensorflow.TensorSliceProto.Extent\x1a\x37\n\x06\x45xtent\x12\r\n\x05start\x18\x01 \x01(\x03\x12\x10\n\x06length\x18\x02 \x01(\x03H\x00\x42\x0c\n\nhas_lengthB2\n\x18org.tensorflow.frameworkB\x11TensorSliceProtosP\x01\xf8\x01\x01\x62\x06proto3')
)
_sym_db.RegisterFileDescriptor(DESCRIPTOR)




_TENSORSLICEPROTO_EXTENT = _descriptor.Descriptor(
  name='Extent',
  full_name='_tensorflow.TensorSliceProto.Extent',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='start', full_name='_tensorflow.TensorSliceProto.Extent.start', index=0,
      number=1, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='length', full_name='_tensorflow.TensorSliceProto.Extent.length', index=1,
      number=2, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
    _descriptor.OneofDescriptor(
      name='has_length', full_name='_tensorflow.TensorSliceProto.Extent.has_length',
      index=0, containing_type=None, fields=[]),
  ],
  serialized_start=127,
  serialized_end=182,
)

_TENSORSLICEPROTO = _descriptor.Descriptor(
  name='TensorSliceProto',
  full_name='_tensorflow.TensorSliceProto',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='extent', full_name='_tensorflow.TensorSliceProto.extent', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[_TENSORSLICEPROTO_EXTENT, ],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=53,
  serialized_end=182,
)

_TENSORSLICEPROTO_EXTENT.containing_type = _TENSORSLICEPROTO
_TENSORSLICEPROTO_EXTENT.oneofs_by_name['has_length'].fields.append(
  _TENSORSLICEPROTO_EXTENT.fields_by_name['length'])
_TENSORSLICEPROTO_EXTENT.fields_by_name['length'].containing_oneof = _TENSORSLICEPROTO_EXTENT.oneofs_by_name['has_length']
_TENSORSLICEPROTO.fields_by_name['extent'].message_type = _TENSORSLICEPROTO_EXTENT
DESCRIPTOR.message_types_by_name['TensorSliceProto'] = _TENSORSLICEPROTO

TensorSliceProto = _reflection.GeneratedProtocolMessageType('TensorSliceProto', (_message.Message,), dict(

  Extent = _reflection.GeneratedProtocolMessageType('Extent', (_message.Message,), dict(
    DESCRIPTOR = _TENSORSLICEPROTO_EXTENT,
    __module__ = '_tensorflow_core.tensor_slice_pb2'
    # @@protoc_insertion_point(class_scope:_tensorflow.TensorSliceProto.Extent)
    ))
  ,
  DESCRIPTOR = _TENSORSLICEPROTO,
  __module__ = '_tensorflow_core.tensor_slice_pb2'
  # @@protoc_insertion_point(class_scope:_tensorflow.TensorSliceProto)
  ))
_sym_db.RegisterMessage(TensorSliceProto)
_sym_db.RegisterMessage(TensorSliceProto.Extent)


DESCRIPTOR.has_options = True
DESCRIPTOR._options = _descriptor._ParseOptions(descriptor_pb2.FileOptions(), _b('\n\030org.tensorflow.frameworkB\021TensorSliceProtosP\001\370\001\001'))
# @@protoc_insertion_point(module_scope)
