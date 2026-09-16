from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone

from .forms import ContactForm, FriendLookupForm, LocationForm, LoginForm, MessageForm, PostForm, ProfileForm, SignUpForm, SwitchAccountForm
from .models import ChatMessage, Friendship, Post, Profile, SharedLocation, Support


def home(request):
    posts = Post.objects.select_related('author__profile').all()
    friends = []
    pending = []
    if request.user.is_authenticated:
        friends = User.objects.filter(Q(sent_friendships__addressee=request.user, sent_friendships__status=Friendship.Status.ACCEPTED) | Q(received_friendships__requester=request.user, received_friendships__status=Friendship.Status.ACCEPTED)).exclude(pk=request.user.pk).select_related('profile').distinct()
        pending = Friendship.objects.filter(addressee=request.user, status=Friendship.Status.PENDING).select_related('requester__profile')
    return render(request, 'home.html', {'posts': posts, 'friends': friends, 'pending': pending, 'post_form': PostForm(), 'friend_form': FriendLookupForm()})


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Пост опубликован анонимно.')
        else:
            messages.error(request, 'Проверь текст поста и формат изображения.')
    return redirect('home')


@login_required
def support_post(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, pk=post_id)
        support, created = Support.objects.get_or_create(post=post, user=request.user)
        if not created:
            support.delete()
            messages.info(request, 'Поддержка убрана.')
        else:
            messages.success(request, 'Ты поддержал этот пост.')
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def delete_post(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, pk=post_id, author=request.user)
        post.delete()
        messages.success(request, 'Публикация удалена.')
    return redirect(request.META.get('HTTP_REFERER', 'home'))


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = SignUpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        pseudonym = form.cleaned_data['pseudonym']
        user = User.objects.create_user(username=pseudonym, password=form.cleaned_data['password'])
        Profile.objects.get_or_create(user=user, defaults={'pseudonym': pseudonym})
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        request.session.set_expiry(60 * 60 * 24 * 30)
        request.session['accounts'] = [user.username]
        return redirect('home')
    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        if request.POST.get('remember'):
            request.session.set_expiry(60 * 60 * 24 * 30)
        else:
            request.session.set_expiry(0)
        accounts = request.session.get('accounts', [])
        if form.get_user().username not in accounts:
            accounts.append(form.get_user().username)
        request.session['accounts'] = accounts[-3:]
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect('home')
    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user, defaults={'pseudonym': request.user.username})
    form = ProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        request.user.username = form.cleaned_data['pseudonym']
        request.user.save(update_fields=['username'])
        messages.success(request, 'Профиль обновлён.')
        return redirect('profile')
    return render(request, 'profile.html', {'form': form, 'posts': request.user.posts.all()})


@login_required
def switch_account(request):
    form = SwitchAccountForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(request, username=form.cleaned_data['pseudonym'].lower(), password=form.cleaned_data['password'])
        if user:
            login(request, user)
            accounts = request.session.get('accounts', [])
            if user.username not in accounts:
                accounts.append(user.username)
            request.session['accounts'] = accounts[-3:]
            messages.success(request, f'Выполнен вход как @{user.profile.pseudonym}.')
            return redirect('home')
        form.add_error(None, 'Неверный псевдоним или пароль.')
    return render(request, 'auth/switch.html', {'form': form, 'accounts': request.session.get('accounts', [])})


@login_required
def add_friend(request):
    form = FriendLookupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        pseudonym = form.cleaned_data['pseudonym'].lstrip('@').lower()
        target = Profile.objects.filter(pseudonym=pseudonym).first()
        if not target or target.user == request.user:
            messages.error(request, 'Пользователь не найден.')
        elif Friendship.objects.filter(requester=request.user, addressee=target.user).exists() or Friendship.objects.filter(requester=target.user, addressee=request.user).exists():
            messages.info(request, 'Запрос уже существует.')
        else:
            Friendship.objects.create(requester=request.user, addressee=target.user)
            messages.success(request, 'Запрос отправлен.')
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def accept_friend(request, friendship_id):
    friendship = get_object_or_404(Friendship, pk=friendship_id, addressee=request.user, status=Friendship.Status.PENDING)
    friendship.status = Friendship.Status.ACCEPTED
    friendship.save(update_fields=['status'])
    messages.success(request, f'@{friendship.requester.profile.pseudonym} теперь в друзьях.')
    return redirect('home')


@login_required
def share_location(request):
    form = LocationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        friend = get_object_or_404(User, pk=form.cleaned_data['friend_id'])
        is_friend = Friendship.objects.filter(requester=request.user, addressee=friend, status=Friendship.Status.ACCEPTED).exists() or Friendship.objects.filter(requester=friend, addressee=request.user, status=Friendship.Status.ACCEPTED).exists()
        if is_friend:
            SharedLocation.objects.filter(owner=request.user, friend=friend, is_active=True).update(is_active=False)
            SharedLocation.objects.create(owner=request.user, friend=friend, latitude=form.cleaned_data['latitude'], longitude=form.cleaned_data['longitude'])
            Profile.objects.filter(user=request.user).update(latitude=form.cleaned_data['latitude'], longitude=form.cleaned_data['longitude'], location_updated=timezone.now())
            messages.success(request, f'Метка доступна для @{friend.profile.pseudonym}.')
    return redirect('home')


def map_data(request):
    markers = []
    if request.user.is_authenticated:
        visible = SharedLocation.objects.filter(friend=request.user, is_active=True).select_related('owner__profile')
        visible = list(visible) + list(SharedLocation.objects.filter(owner=request.user, is_active=True).select_related('friend__profile'))
        own_profile = request.user.profile
        if own_profile.latitude is not None and own_profile.longitude is not None:
            markers.append({'lat': float(own_profile.latitude), 'lng': float(own_profile.longitude), 'label': 'Моя точка'})
        for location in visible:
            label = location.owner.profile.pseudonym if location.owner_id != request.user.id else 'моя метка'
            markers.append({'lat': float(location.latitude), 'lng': float(location.longitude), 'label': f'@{label}'})
    return JsonResponse(markers, safe=False)


def map_view(request):
    friends = []
    pending = []
    if request.user.is_authenticated:
        friends = User.objects.filter(
            Q(sent_friendships__addressee=request.user, sent_friendships__status=Friendship.Status.ACCEPTED)
            | Q(received_friendships__requester=request.user, received_friendships__status=Friendship.Status.ACCEPTED)
        ).exclude(pk=request.user.pk).select_related('profile').distinct()
        pending = Friendship.objects.filter(
            Q(requester=request.user) | Q(addressee=request.user),
            status=Friendship.Status.PENDING,
        ).select_related('requester__profile', 'addressee__profile')
    return render(request, 'map.html', {'friend_form': FriendLookupForm(), 'friends': friends, 'pending': pending})


@login_required
def save_my_location(request):
    if request.method == 'POST':
        try:
            latitude = float(request.POST.get('latitude'))
            longitude = float(request.POST.get('longitude'))
            if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
                raise ValueError
        except (TypeError, ValueError):
            messages.error(request, 'Координаты не распознаны.')
            return redirect('home')
        Profile.objects.filter(user=request.user).update(latitude=latitude, longitude=longitude, location_updated=timezone.now())
        messages.success(request, 'Твоя точка сохранена на карте.')
    return redirect(request.META.get('HTTP_REFERER', 'home'))


def are_friends(first, second):
    return Friendship.objects.filter(
        Q(requester=first, addressee=second) | Q(requester=second, addressee=first),
        status=Friendship.Status.ACCEPTED,
    ).exists()


@login_required
def chat_list(request):
    friends = User.objects.filter(
        Q(sent_friendships__addressee=request.user, sent_friendships__status=Friendship.Status.ACCEPTED)
        | Q(received_friendships__requester=request.user, received_friendships__status=Friendship.Status.ACCEPTED)
    ).exclude(pk=request.user.pk).select_related('profile').distinct()
    selected = request.GET.get('with')
    selected_friend = friends.filter(pk=selected).first() if selected else friends.first()
    messages_list = []
    if selected_friend:
        messages_list = ChatMessage.objects.filter(
            Q(sender=request.user, recipient=selected_friend) | Q(sender=selected_friend, recipient=request.user)
        ).select_related('sender__profile', 'recipient__profile')
    return render(request, 'chat.html', {'friends': friends, 'selected_friend': selected_friend, 'chat_messages': messages_list, 'message_form': MessageForm()})


@login_required
def send_message(request, user_id):
    recipient = get_object_or_404(User.objects.select_related('profile'), pk=user_id)
    if not are_friends(request.user, recipient):
        messages.error(request, 'Общаться можно только с принятым другом.')
        return redirect('chat')
    form = MessageForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        ChatMessage.objects.create(sender=request.user, recipient=recipient, **form.cleaned_data)
    return redirect(f'/chat/?with={recipient.id}')


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        message = form.save(commit=False)
        if request.user.is_authenticated:
            message.pseudonym = request.user.profile.pseudonym
        message.save()
        messages.success(request, 'Сообщение отправлено в anonka.')
        return redirect('contact')
    return render(request, 'contact.html', {'form': form})
