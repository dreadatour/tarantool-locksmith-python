# coding: utf-8
"""Python bindings for Tarantool locksmith script.

Usage:

    >>> from tarantool_locksmith import Locksmith

    # Initialize
    >>> locksmith = Locksmith('127.0.0.1', 33013, user='test', password='test')

    # Acquire lock
    >>> lock1 = locksmith.acquire('foo', validity=60)
    >>> print(lock1)
    <Lock name='foo' uid='d1a96654-6491-441b-bd10-997abebc302e'>

    # Try to acquire lock again (returns `None`)
    >>> lock2 = locksmith.acquire('foo', validity=60)
    >>> print(lock2)
    None

    # Acquire another lock
    >>> lock3 = locksmith.acquire('bar', validity=1)
    >>> print(lock3)
    <Lock name='bar' uid='5fd0a4da-4409-4409-a8e7-1de197f9d90a'>
    # Wait for lock expire
    >>> time.sleep(2)

    # Acquire lock with timeout
    >>> locksmith.acquire('bar', validity=60, timeout=3)
    <Lock name='bar' uid='206e1c2d-cc0a-47e9-a7c0-7bac4eb6d806'>

    # Update lock1 validity
    >>> lock1.update(validity=30)
    True
    # Update lock validity with lock uid
    >>> locksmith.update('d1a96654-6491-441b-bd10-997abebc302e', validity=30)
    True

    # Update unknown or expired lock validity
    >>> lock3.update(validity=60)
    False

    # Release lock1
    >>> lock1.release()
    True
    # Release lock by lock uid
    >>> locksmith.release('d1a96654-6491-441b-bd10-997abebc302e')
    True

    # Release unknown or expired lock
    >>> lock3.release()
    False

See also: https://github.com/dreadatour/tarantool-locksmith-python
"""
import threading

import tarantool


class Lock(object):
    """ Tarantool lock object."""

    def __init__(self, locksmith, name, uid):
        self.locksmith = locksmith
        self.name = name
        self.uid = uid

    def __repr__(self):
        return "<Lock name='{0}' uid='{1}'>".format(self.name, self.uid)

    def update(self, validity):
        """Update lock validity time for `validity` seconds.

        Returns `True` if lock validity updated successful,
        `False` if lock is not acquired or expired.
        """
        return self.locksmith.update(self.uid, validity)

    def release(self):
        """Release lock.

        Returns `True` if lock released successful,
        `False` if lock is not acquired or expired.
        """
        return self.locksmith.release(self.uid)


class Locksmith(object):
    """Tarantool lock wrapper."""

    DatabaseError = tarantool.DatabaseError
    NetworkError = tarantool.NetworkError

    class BadConfigException(Exception):
        """Bad config deque exception."""
        pass

    class ZeroTupleException(Exception):
        """Zero tuple deque exception."""
        pass

    class BadTupleException(Exception):
        """Bad tuple deque exception."""
        pass

    def __init__(self, host='localhost', port=33013,
                 user=None, password=None, timeout=1.0):
        if not host or not port:
            raise Lock.BadConfigException(
                "Host and port params must be not empty"
            )

        if not isinstance(port, int):
            raise Lock.BadConfigException("Port must be int")

        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.timeout = timeout
        self.tubes = {}
        self._lockinst = threading.Lock()
        self._conclass = tarantool.Connection
        self._tnt = None

    @property
    def tarantool_connection(self):
        """Tarantool connection getter.

        Uses `tarantool.Connection` by default.
        """
        if self._conclass is None:
            self._conclass = tarantool.Connection
        return self._conclass

    @tarantool_connection.setter
    def tarantool_connection(self, con_cls):
        """Tarantool connection setter.

        Must be class with methods call and __init__.
        """
        if con_cls is None:
            self._conclass = tarantool.Connection
        elif 'call' in dir(con_cls) and '__init__' in dir(con_cls):
            self._conclass = con_cls
        else:
            raise TypeError("Connection class must have connect"
                            " and call methods or be None")
        self._tnt = None

    @property
    def tarantool_lock(self):
        """Tarantool lock getter.

        Use `threading.Lock` by default.
        """
        if self._lockinst is None:
            self._lockinst = threading.Lock()

        return self._lockinst

    @tarantool_lock.setter
    def tarantool_lock(self, lock):
        """Tarantool lock setter.

        Must be locking instance with methods __enter__ and __exit__.
        """
        if lock is None:
            self._lockinst = threading.Lock()
        elif '__enter__' in dir(lock) and '__exit__' in dir(lock):
            self._lockinst = lock
        else:
            raise TypeError("Lock class must have `__enter__`"
                            " and `__exit__` methods or be None")

    @property
    def tnt(self):
        """Get or create tarantool connection."""
        if self._tnt is None:
            with self.tarantool_lock:
                if self._tnt is None:
                    self._tnt = self.tarantool_connection(
                        self.host,
                        self.port,
                        user=self.user,
                        password=self.password,
                        socket_timeout=self.timeout
                    )
        return self._tnt

    def acquire(self, lock_name, validity, timeout=None):
        """Acquire lock.

        Lock will expired after `validity` seconds.

        Waits `timeout` seconds for lock acquired.
        If `timeout` is 0 - do not wait.
        If `timeout` is `None` - waits forever.

        Returns lock uid.
        """
        args = (lock_name, validity)
        if timeout is not None:
            args += (timeout,)

        the_tuple = self.tnt.call('locksmith:acquire', args)[0]

        if the_tuple[0] is not None:
            return Lock(self, the_tuple[1], the_tuple[2])

    def update(self, lock_uid, validity):
        """Update lock with uid `lock_uid` validity for `validity` seconds.

        Returns `True` if lock validity updated successful,
        `False` if lock is not acquired or expired.
        """
        the_tuple = self.tnt.call('locksmith:update', (lock_uid, validity))[0]

        return bool(the_tuple[0] is not None)

    def release(self, lock_uid):
        """Release lock with uid `lock_uid`.

        Returns `True` if lock released successful,
        `False` if lock is not acquired or expired.
        """
        the_tuple = self.tnt.call('locksmith:release', (lock_uid,))[0]

        return bool(the_tuple[0] is not None)

    def statistics(self):
        """Returns locks statistics."""
        return self.tnt.call('locksmith:statistics')[0][0]
