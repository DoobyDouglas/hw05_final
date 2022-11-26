from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Post, Group, Follow
from posts.forms import PostForm, CommentForm
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from django.views.decorators.cache import cache_page

User = get_user_model()

# Количество постов на странице
POSTS_ON_PAGE = 10


# Пэйджинатор
def paginator(request, post_list, page) -> Paginator:
    paginator = Paginator(post_list, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


# Cтраница профиля
def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    page_obj = paginator(request, post_list, 'page')
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author
        ).exists()
    else:
        following = False
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, template, context)


# Страница поста
def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm()
    author = post.author
    count = author.posts.count()
    comments = post.comments.all()
    context = {
        'post': post,
        'count': count,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


# Главная страница
@cache_page(20)
def index(request):
    template = 'posts/index.html'
    title = 'Последние обновления на сайте'
    post_list = Post.objects.all()
    page_obj = paginator(request, post_list, 'page')
    context = {
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, template, context)


# Страница с постами групп
def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.group_posts.all()
    page_obj = paginator(request, post_list, 'page')
    count = post_list.count()
    context = {
        'group': group,
        'page_obj': page_obj,
        'count': count,
    }
    return render(request, template, context)


# Cтраница для создания поста
@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm()
    context = {
        'form': form,
        'is_edit': False,
    }

    if request.method == 'GET':
        return render(request, template, context)
    if request.method == 'POST':
        form = PostForm(request.POST or None, files=request.FILES or None)
        if not form.is_valid():
            return render(request, template, context)
        post = form.save(commit=False)
        post.author = request.user
        post.save()
    return redirect('posts:profile', username=post.author)


# Cтраница для редактирования поста
@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, id=post_id)
    if post.author == request.user:
        form = PostForm(instance=post)
        if request.method == 'GET':
            context = {
                'form': form,
                'is_edit': True,
                'post': post,
            }
            return render(request, template, context)
        if request.method == 'POST':
            form = PostForm(
                request.POST or None,
                files=request.FILES or None,
                instance=post
            )
            if form.is_valid():
                form.save()
    return redirect('posts:post_detail', post_id)


# Cтраница для комментирования поста
@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


# Cтраница ленты
@login_required
def follow_index(request):
    template = 'posts/follow.html'
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator(request, post_list, 'page')
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if user != author:
        if not Follow.objects.filter(user=user, author=author).exists():
            Follow.objects.create(user=user, author=author)
    return redirect('posts:profile', username=author.username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(user=user, author=author):
        Follow.objects.filter(user=user, author=author).delete()
    return redirect('posts:profile', username=user.username)
