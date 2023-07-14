The metadaclass now provides the method `_wrap_class_method`. This method
can be used to wrap class methods in a way that when the method is called
the logic is delegated to the aggregated class instance if it exists.
