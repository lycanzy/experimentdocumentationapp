from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('experiment/create/', views.experiment_create, name='experiment_create'),
    path('experiment/<str:experiment_id>/', views.experiment_detail, name='experiment_detail'),
    path('experiment/<str:experiment_id>/flow/create/', views.flow_create, name='flow_create'),
    path('flow/<str:flow_id>/', views.flow_detail, name='flow_detail'),
    path('flow/<str:flow_id>/step/create/', views.step_create, name='step_create'),
    path('step/<str:step_id>/', views.step_detail, name='step_detail'),
    path('step/<str:step_id>/sample/add/', views.add_sample, name='add_sample'),
    path('step/<str:step_id>/metadata/add/', views.add_metadata, name='add_metadata'),
    path('step/<str:step_id>/delete/', views.delete_step, name='delete_step'),
]
