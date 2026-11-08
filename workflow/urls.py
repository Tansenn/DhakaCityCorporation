from django.urls import path

from . import views

urlpatterns = [
    path('tasks/', views.tasks, name='tasks'),
    path('tasks/<int:pk>/', views.task_detail, name='task_detail'),
    path('tasks/<int:pk>/decide/', views.task_decide, name='task_decide'),
    path('workflow/', views.templates_list, name='workflow_templates'),
    path('workflow/new/', views.template_form, name='workflow_template_create'),
    path('workflow/<int:pk>/', views.template_form, name='workflow_template_edit'),
    path('workflow/<int:template_pk>/step/new/', views.step_form,
         name='workflow_step_create'),
    path('workflow/<int:template_pk>/step/<int:pk>/', views.step_form,
         name='workflow_step_edit'),
    path('workflow/step/<int:pk>/delete/', views.step_delete,
         name='workflow_step_delete'),
    path('workflow/matrix/', views.matrix, name='authority_matrix'),
    path('workflow/matrix/<int:pk>/delete/', views.matrix_delete,
         name='authority_matrix_delete'),
    path('workflow/reminders/run/', views.run_reminders_now, name='run_reminders'),
    path('mis/workflow/', views.performance, name='workflow_performance'),
    path('workflow/instances/<int:pk>/', views.instance_detail,
         name='workflow_instance'),
]
