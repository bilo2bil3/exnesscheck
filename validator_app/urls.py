from django.urls import path
from .views import ClientValidatorView

app_name = 'validator_app'

urlpatterns = [
    path('', ClientValidatorView.as_view(), name='validator'),
] 