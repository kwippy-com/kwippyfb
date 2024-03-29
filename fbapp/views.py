from django.http import HttpResponse
from django.views.generic.simple import direct_to_template

# Import the Django helpers
import facebook.djangofb as facebook

# The User model defined in models.py
from models import User

# We'll require login for our canvas page. This
# isn't necessarily a good idea, as we might want
# to let users see the page without granting our app
# access to their info. See the wiki for details on how
# to do this.
@facebook.require_login()
def canvas(request):
    # Get the User object for the currently logged in user
    user = User.objects.get_current()

    # Check if we were POSTed the user's new language of choice
    if 'language' in request.POST:
        user.language = request.POST['language'][:64]
        user.save()

    # User is guaranteed to be logged in, so pass canvas.fbml
    # an extra 'fbuser' parameter that is the User object for
    # the currently logged in user.
    return direct_to_template(request, 'canvas.fbml', extra_context={'fbuser': user})

@facebook.require_login()
def ajax(request):
    return HttpResponse('hello world')

@facebook.require_login()
def callback(request):
    #name = request.facebook.users.getInfo([request.facebook.uid], ['first_name'])[0]['first_name']
    return render_to_response('canvas.fbml', {'name': 'hi'})

