# Bibliotheca Alexandrina Museum RAG Application
import os
os.environ["USE_TF"] = "NO"

# Monkey patch protobuf MessageFactory to support GetPrototype (removed in protobuf 5.0.0+)
# which is still required by mediapipe and other dependencies.
try:
    from google.protobuf import message_factory
    if not hasattr(message_factory.MessageFactory, 'GetPrototype'):
        def GetPrototype(self, descriptor):
            return self.GetMessageClass(descriptor)
        message_factory.MessageFactory.GetPrototype = GetPrototype
except ImportError:
    pass
