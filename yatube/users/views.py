from django.views.generic import CreateView
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from .forms import CreationForm, UserEditForm, ProfileEditForm
from users.models import Profile


User = get_user_model()


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'

    def form_valid(self, form):
        user = form.save(commit=False)
        user.save()
        Profile.objects.create(user=user)
        return super().form_valid(form)


@login_required
def profile_edit(request):
    template = 'users/profile_edit.html'
    if request.method == 'POST':
        user_form = UserEditForm(request.POST or None, instance=request.user)
        profile_form = ProfileEditForm(
            request.POST or None,
            files=request.FILES or None,
            instance=request.user.profile,
        )
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)
        profile = Profile.objects.get(user=request.user)
        return render(request,
                      template,
                      {'user_form': user_form,
                       'profile_form': profile_form,
                       'profile': profile,
                       })
    return redirect('posts:profile', username=request.user)
