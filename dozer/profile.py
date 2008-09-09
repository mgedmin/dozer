import cProfile
import cPickle
import time


class Profiler(object):
    def __init__(self, app):
        """Profiles an application and saves the pickled version to a
        file
        """
        self.app = app
    
    def __call__(self, environ, start_response):
        prof = cProfile.Profile()
        globs = globals()
        local = {'environ':environ, 'start_response':start_response}
        prof.runctx('content = self.app(environ, start_response)', globs, local)
        results = prof.getstats()
        fname = str(time.time()).replace('.', '_') + '.pkl'
        output = open(fname, 'w')
        output.write(cPickle.dumps(results))
        output.close()
        return local['content']
