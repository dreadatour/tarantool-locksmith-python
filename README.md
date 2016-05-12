Python bindings for tarantool locksmith module
==============================================

[Locksmith](https://github.com/dreadatour/tarantool-locksmith) is an application-level library that provides distributed locks for [tarantool 1.6](http://tarantool.org).

Install
-------

```
pip install -e https://github.com/dreadatour/tarantool-locksmith-python
```

Usage
-----

0. Initialize:

	```Python
	from tarantool_locksmith import Locksmith

	# Initialize
	>>> locksmith = Locksmith('127.0.0.1', 33013, user='test', password='test')
	```

1. Acquire lock:

	```Python
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
	```

2. Update lock validity:

	```Python
	# Update lock1 validity
	>>> lock1.update(validity=30)
	True
	# Update lock validity with lock uid
	>>> locksmith.update('d1a96654-6491-441b-bd10-997abebc302e', validity=30)
	True

	# Update unknown or expired lock validity
	>>> lock3.update(validity=60)
	False
	```

3. Release lock:

	```Python
	# Release lock1
	>>> lock1.release()
	True
	# Release lock by lock uid
	>>> locksmith.release('d1a96654-6491-441b-bd10-997abebc302e')
	True

	# Release unknown or expired lock
	>>> lock3.release()
	False
	```

4. Get locksmith statistics:

	```Python
	>>> locksmith.statistics()
	{
		'calls': {
			'acquire': 1,
		  	'acquire_success': 1,
	  		'update': 1,
	  		'update_success': 1,
	 		'release': 1,
	  		'release_success': 1,
	  		'watchdog_release': 1,
		  	'lock_create': 1,
		  	'lock_update': 1,
		  	'lock_delete': 1
	  	},
	 	'locks': {
	 		'count': 0
	 	},
	 	'consumers': {
	 		'waiting': 0
	 	}
	 }
	 ```
