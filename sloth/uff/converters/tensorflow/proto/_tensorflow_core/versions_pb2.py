# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: _tensorflow_core/versions.proto

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
  name='_tensorflow_core/versions.proto',
  package='_tensorflow',
  syntax='proto3',
  serialized_pb=_b('\n\x1f_tensorflow_core/versions.proto\x12\x0b_tensorflow\"K\n\nVersionDef\x12\x10\n\x08producer\x18\x01 \x01(\x05\x12\x14\n\x0cmin_consumer\x18\x02 \x01(\x05\x12\x15\n\rbad_consumers\x18\x03 \x03(\x05\x42/\n\x18org.tensorflow.frameworkB\x0eVersionsProtosP\x01\xf8\x01\x01\x62\x06proto3')
)
_sym_db.RegisterFileDescriptor(DESCRIPTOR)




_VERSIONDEF = _descriptor.Descriptor(
  name='VersionDef',
  full_name='_tensorflow.VersionDef',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='producer', full_name='_tensorflow.VersionDef.producer', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='min_consumer', full_name='_tensorflow.VersionDef.min_consumer', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='bad_consumers', full_name='_tensorflow.VersionDef.bad_consumers', index=2,
      number=3, type=5, cpp_type=1, label=3,
      has_default_value=False, default_value=[],
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
  ],
  serialized_start=48,
  serialized_end=123,
)

DESCRIPTOR.message_types_by_name['VersionDef'] = _VERSIONDEF

VersionDef = _reflection.GeneratedProtocolMessageType('VersionDef', (_message.Message,), dict(
  DESCRIPTOR = _VERSIONDEF,
  __module__ = '_tensorflow_core.versions_pb2'
  # @@protoc_insertion_point(class_scope:_tensorflow.VersionDef)
  ))
_sym_db.RegisterMessage(VersionDef)


DESCRIPTOR.has_options = True
DESCRIPTOR._options = _descriptor._ParseOptions(descriptor_pb2.FileOptions(), _b('\n\030org.tensorflow.frameworkB\016VersionsProtosP\001\370\001\001'))
# @@protoc_insertion_point(module_scope)
