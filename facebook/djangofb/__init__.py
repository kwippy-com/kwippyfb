import facebook

from django.http import HttpResponse, HttpResponseRedirect
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

__all__ = ['Facebook', 'FacebookMiddleware', 'get_facebook_client', 'require_login', 'require_add']

_thread_locals = local()

class Facebook(facebook.Facebook):
    def redirect(self, url):
        """
        Helper for Django which redirects to another page. If inside a
        canvas page, writes a <fb:redirect> instead to achieve the same effect.

        """
        if self.in_canvas:
            return HttpResponse('<fb:redirect url="%s" />' % (url, ))
        else:
            return HttpResponseRedirect(url)


def get_facebook_client():
    """
    Get the current Facebook object for the calling thread.

    """
    try:
        return _thread_locals.facebook
    except AttributeError:
        raise ImproperlyConfigured('Make sure you have the Facebook middleware installed.')


def require_login(next=None, internal=None):
    """
    Decorator for Django views that requires the user to be logged in.
    The FacebookMiddleware must be installed.

    Standard usage:
        @require_login()
        def some_view(request):
            ...

    Redirecting after login:
        To use the 'next' parameter to redirect to a specific page after login, a callable should
        return a path relative to the Post-add URL. 'next' can also be an integer specifying how many
        parts of request.path to strip to find the relative URL of the canvas page. If 'next' is None,
        settings.callback_path and settings.app_name are checked to redirect to the same page after logging
        in. (This is the default behavior.)
        @require_login(next=some_callable)
        def some_view(request):
            ...
    """
    def decorator(view):
        def newview(request, *args, **kwargs):
            next = newview.next
            internal = newview.internal

            try:
                fb = request.facebook
            except:
                raise ImproperlyConfigured('Make sure you have the Facebook middleware installed.')

            if internal is None:
                internal = request.facebook.internal

            if callable(next):
                next = next(request.path)
            elif isinstance(next, int):
                next = '/'.join(request.path.split('/')[next + 1:])
            elif next is None and fb.callback_path and request.path.startswith(fb.callback_path):
                next = request.path[len(fb.callback_path):]
            elif not isinstance(next, str):
                next = ''

            if not fb.check_session(request):
                #If user has never logged in before, the get_login_url will redirect to the TOS page
                return fb.redirect(fb.get_login_url(next=next))

            if internal and request.method == 'GET' and fb.app_name:
                return fb.redirect('%s%s' % (fb.get_app_url(), next))

            return view(request, *args, **kwargs)
        newview.next = next
        newview.internal = internal
        return newview
    return decorator


def require_add(next=None, internal=None, on_install=None):
    """
    Decorator for Django views that requires application installation.
    The FacebookMiddleware must be installed.
    
    Standard usage:
        @require_add()
        def some_view(request):
            ...

    Redirecting after installation:
        To use the 'next' parameter to redirect to a specific page after login, a callable should
        return a path relative to the Post-add URL. 'next' can also be an integer specifying how many
        parts of request.path to strip to find the relative URL of the canvas page. If 'next' is None,
        settings.callback_path and settings.app_name are checked to redirect to the same page after logging
        in. (This is the default behavior.)
        @require_add(next=some_callable)
        def some_view(request):
            ...

    Post-install processing:
        Set the on_install parameter to a callable in order to handle special post-install processing.
        The callable should take a request object as the parameter.
        @require_add(on_install=some_callable)
        def some_view(request):
            ...
    """
    def decorator(view):
        def newview(request, *args, **kwargs):
            next = newview.next
            internal = newview.internal

            try:
                fb = request.facebook
            except:
                raise ImproperlyConfigured('Make sure you have the Facebook middleware installed.')

            if internal is None:
                internal = request.facebook.internal

            if callable(next):
                next = next(request.path)
            elif isinstance(next, int):
                next = '/'.join(request.path.split('/')[next + 1:])
            elif next is None and fb.callback_path and request.path.startswith(fb.callback_path):
                next = request.path[len(fb.callback_path):]
            else:
                next = ''

            if not fb.check_session(request):
                if fb.added:
                    if request.method == 'GET' and fb.app_name:
                        return fb.redirect('%s%s' % (fb.get_app_url(), next))
                    return fb.redirect(fb.get_login_url(next=next))
                else:
                    return fb.redirect(fb.get_add_url(next=next))

            if not fb.added:
                return fb.redirect(fb.get_add_url(next=next))

            if 'installed' in request.GET and callable(on_install):
                on_install(request)

            if internal and request.method == 'GET' and fb.app_name:
                return fb.redirect('%s%s' % (fb.get_app_url(), next))

            return view(request, *args, **kwargs)
        newview.next = next
        newview.internal = internal
        return newview
    return decorator

# try to preserve the argspecs
try:
    import decorator
except ImportError:
    pass
else:
    require_login = lambda f: decorator.new_wrapper(require_login(f), f)
    require_add = lambda f: decorator.new_wrapper(require_add(f), f)

class FacebookMiddleware(object):
    """
    Middleware that attaches a Facebook object to every incoming request.
    The Facebook object created can also be accessed from models for the
    current thread by using get_facebook_client().

    """

    def __init__(self, api_key=None, secret_key=None, app_name=None, callback_path=None, internal=None):
        self.api_key = api_key or settings.FACEBOOK_API_KEY
        self.secret_key = secret_key or settings.FACEBOOK_SECRET_KEY
        self.app_name = app_name or getattr(settings, 'FACEBOOK_APP_NAME', None)
        self.callback_path = callback_path or getattr(settings, 'FACEBOOK_CALLBACK_PATH', None)
        self.internal = internal or getattr(settings, 'FACEBOOK_INTERNAL', True)

    def process_request(self, request):
        _thread_locals.facebook = request.facebook = Facebook(self.api_key, self.secret_key, app_name=self.app_name, callback_path=self.callback_path, internal=self.internal)
        if not self.internal and 'facebook_session_key' in request.session and 'facebook_user_id' in request.session:
            request.facebook.session_key = request.session['facebook_session_key']
            request.facebook.uid = request.session['facebook_user_id']

    def process_response(self, request, response):
        if not self.internal and request.facebook.session_key and request.facebook.uid:
            request.session['facebook_session_key'] = request.facebook.session_key
            request.session['facebook_user_id'] = request.facebook.uid
        return response
