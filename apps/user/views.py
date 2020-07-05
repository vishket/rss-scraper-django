import django.contrib.auth.forms as auth_forms
import django.contrib.auth.views as auth_views
from django import urls
from django.contrib import auth
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView


class Login(auth_views.LoginView):
    template_name = "user/login.html"


class Signup(CreateView):
    template_name = "user/signup.html"
    form_class = auth_forms.UserCreationForm
    success_url = urls.reverse_lazy("home")

    def form_valid(self, *args, **kwargs):
        resp = super().form_valid(*args, **kwargs)
        user = self.object
        auth.login(self.request, user)
        return resp


class Welcome(TemplateView):
    template_name = "user/welcome.html"
