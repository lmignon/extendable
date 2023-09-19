1.2.1 (2023-09-19)
==================

Bugfixes
--------

- Fix isinstance and issublcass method on multi levels inheritance hierarchy. (`#14 <https://github.com/lmignon/extendable/pull/14>`_)


1.2.0 (2023-07-28)
==================

Features
--------

- Add a  `before_init_registry` hook method into the `ExtendableRegistryListener` class.
  This methods allows you to udpate the list of modules to load into the registry if
  you need to do so. (`#before_hook <https://github.com/lmignon/extendable/pull/13>`_)


1.1.0 (2023-07-15)
==================

Features
--------

- Simpler syntax for defining a class extending another class. The `extends` parameter now accepts `True` as its value. `class PersonExt(Person, extends=True)` means that `PersonExt` extends its first base class: `Person`. This is equivalent to `class PersonExt(Person, extends=Person)`. (`#2 <https://github.com/lmignon/extendable/issues/2>`_)


1.0.0 (2023-07-14)
==================

Features
--------

- Access to the context variable used to store the current extended Classes
  returns None if no context is available. Previously the access to the context
  throws an exception if no context was available.
- Calls to the classmethod "_get_assembled_cls" now raises RegistryNotInitializedError
  if the registry is not initialized.
- The metadaclass now provides the method `_wrap_class_method`. This method
  can be used to wrap class methods in a way that when the method is called
  the logic is delegated to the aggregated class if it exists.


0.0.5 (2023-07-13)
==================

Bugfixes
--------

- Preserve kwargs values in class defintion to ensure to properly create a concrete class with the same attributes as the original one.


0.0.4 (2023-06-26)
==================

Bugfixes
--------

- Fix registry rebuild (`Details <https://github.com/lmignon/extendable/pull/8/commits/120c1b749081f48893ca74d711091621c3c3481e>`_)
- Add missing type annotation


Deprecations and Removals
-------------------------

- Drop support fo py3.6


0.0.3 (2022-11-01)
==================

Bugfixes
--------

-  Fix error when '__qualname__' is not provided (`#6 <https://github.com/lmignon/extendable/issues/6>`_)


0.0.2 (2022-06-15)
==================

Bugfixes
--------

- Fix compatibility issue with py3.11. (`#4 <https://github.com/lmignon/extendable/issues/4>`_)


v0.0.1 (2021-30-12)
===================

First release.
