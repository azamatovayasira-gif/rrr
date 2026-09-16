from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('switch-account/', views.switch_account, name='switch_account'),
    path('post/create/', views.create_post, name='create_post'),
    path('post/<int:post_id>/support/', views.support_post, name='support_post'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('friends/add/', views.add_friend, name='add_friend'),
    path('friends/<int:friendship_id>/accept/', views.accept_friend, name='accept_friend'),
    path('location/share/', views.share_location, name='share_location'),
    path('api/map-data/', views.map_data, name='map_data'),
    path('map/', views.map_view, name='map'),
    path('location/save/', views.save_my_location, name='save_my_location'),
    path('chat/', views.chat_list, name='chat'),
    path('chat/<int:user_id>/send/', views.send_message, name='send_message'),
    path('contact/', views.contact, name='contact'),
]
