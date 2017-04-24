import datetime
import functools
import hashlib


class cached(object):
    """Decorator that caches a function's or class method's return value for cache_time_seconds.
    If called later before cache_time_seconds passed with the same arguments, the cached value
    is returned, and not re-evaluated.

    It compares hash of all function's arguments (str representation), including 'self' if that is object
    method. And string representation for 'self' would be
    "(<__main__.<CLASS NAME> object at <WRAPPED OBJECT INSTANCE ID>".
    So you need to use singleton if the object instances are the same.
    And if you change something in object instance aside of function arguments the decorator would not
    see that.
    """

    def __init__(self, cache_time_seconds, print_if_cached=None, evaluate_on_day_change=False):
        """
        :param cache_time_seconds: cache time
        :param evaluate_on_day_change: re-evaluate if current day is not the same as cached value
        :param print_if_cached: if specified the string will be printed if cached value returned.
                                Inside string can be '{time}' parameter.
        """
        super().__init__()
        self.cache_time_seconds = cache_time_seconds
        self.print_if_cached = print_if_cached
        self.evaluate_on_day_change = evaluate_on_day_change
        self.time = datetime.datetime.now() - datetime.timedelta(seconds=cache_time_seconds + 1)
        self.cache = {}

    def __call__(self, func):
        def cached_func(*args, **kw):
            hash = hashlib.sha256((func.__name__ + str(args) + str(kw)).encode('utf-8')).hexdigest()
            now = datetime.datetime.now()
            for item in list(self.cache): # we have to keep cache clean
                if (now - self.cache[item]['time']).total_seconds() > self.cache_time_seconds:
                    del self.cache[item]
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            if hash in self.cache \
                    and (today == self.cache[hash]['time'].replace(hour=0, minute=0, second=0, microsecond=0)
                            or not self.evaluate_on_day_change):
                if self.print_if_cached:
                    print(self.print_if_cached.format(time=self.cache[hash]['time']))
            else:
                self.cache[hash] = {
                    'value': func(*args, **kw),
                    'time': now
                }
            return self.cache[hash]['value']
        return cached_func

    def __get__(self, obj, objtype):
        return functools.partial(self.__call__, obj)


if __name__ == '__main__':
    import time

    class F(object):
        def __init__(self, n):
            self.n = n

        @cached(cache_time_seconds=0.01, print_if_cached='returned cached f1 at {time}')
        def f1(self, n):
            if n in (0, 1):
                return n
            return (n-1) + (n-2)

        @cached(cache_time_seconds=0.05, print_if_cached='returned cached f2 at {time}')
        def f2(self, n):
            return n * self.n

    @cached(cache_time_seconds=0.07, print_if_cached='returned cached f3 at {time}')
    def f3(n):
        return n

    f = F(10)
    assert f.f1(1) == 1
    assert f.f1(1) == 1
    time.sleep(0.2)
    assert f.f1(1) == 1
    assert f.f2(5) == 50
    assert f.f2(5) == 50
    time.sleep(0.1)
    assert f.f2(5) == 50
    f=F(20)
    assert f.f2(5) == 100
    assert f.f1(100) == 197
    assert f3(15) == 15
    assert f3(15) == 15
    print('should be 3 cached calls')