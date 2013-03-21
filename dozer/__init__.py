from dozer.leak import Dozer
from dozer.logview import Logview
from dozer.profile import Profiler


def profile_filter_factory(global_conf, **kwargs):
    def filter(app):
        return Profiler(app, global_conf, **kwargs)
    return filter


def profile_filter_app_factory(app, global_conf, **kwargs):
    return Profiler(app, global_conf, **kwargs)


def dozer_filter_factory(global_conf, **kwargs):
    def filter(app):
        return Dozer(app, global_conf, **kwargs)
    return filter


def dozer_filter_app_factory(app, global_conf, **kwargs):
    return Dozer(app, global_conf, **kwargs)


def logview_filter_factory(global_conf, **kwargs):
    def filter(app):
        return Logview(app, global_conf, **kwargs)
    return filter


def logview_filter_app_factory(app, global_conf, **kwargs):
    return Logview(app, global_conf, **kwargs)

