from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from .forms import ClientValidationForm
from .services import ExnessApiClient
from .models import ClientValidation
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ClientValidatorView(View):
    template_name = 'validator_app/validator.html'
    
    def get(self, request, *args, **kwargs):
        form = ClientValidationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request, *args, **kwargs):
        form = ClientValidationForm(request.POST)
        context = {'form': form}
        
        if form.is_valid():
            client_id = form.cleaned_data.get('client_id')
            email = form.cleaned_data.get('email')
            
            # Check client registration via the API
            if client_id:
                # Use check_client_registration for client IDs
                result = ExnessApiClient.check_client_registration(client_id=client_id)
            else:
                # Use check_client_affiliation for emails - this uses the /api/v1/referral-agents/affiliation/ endpoint
                result = ExnessApiClient.check_client_affiliation(email)
            
            # Handle API errors
            if 'error' in result:
                messages.error(request, result['error'])
                return render(request, self.template_name, context)
            
            # Standardize the result structure for both methods
            # check_client_registration returns is_registered
            # check_client_affiliation returns is_affiliated
            is_registered = result.get('is_registered', result.get('is_affiliated', False))
            
            # Store results in context for template rendering
            context['result'] = result
            context['is_registered'] = is_registered
            
            # If client is registered and has data, store it
            if is_registered and result.get('client_data'):
                client_data = result['client_data']
                
                # Parse registration date if available
                reg_date = None
                if client_data.get('reg_date'):
                    try:
                        reg_date = datetime.strptime(client_data['reg_date'], '%Y-%m-%d')
                    except (ValueError, TypeError):
                        logger.warning(f"Could not parse reg_date: {client_data.get('reg_date')}")
                
                # Create or update client validation record
                client_validation, created = ClientValidation.objects.update_or_create(
                    client_id=client_data.get('client_account', client_id or email),
                    defaults={
                        'is_registered': True,
                        'reg_date': reg_date,
                        'client_account': client_data.get('client_account', ''),
                        'client_account_type': client_data.get('client_account_type', ''),
                        'volume_lots': client_data.get('volume_lots', 0),
                        'volume_mln_usd': client_data.get('volume_mln_usd', 0),
                        'reward': client_data.get('reward', 0),
                        'reward_usd': client_data.get('reward_usd', 0),
                    }
                )
                
                context['client_validation'] = client_validation
            elif is_registered and result.get('accounts'):
                # Handle the affiliation endpoint response structure which includes 'accounts'
                accounts = result.get('accounts', [])
                account_id = accounts[0] if accounts else email
                
                client_validation, created = ClientValidation.objects.update_or_create(
                    client_id=account_id,
                    defaults={
                        'is_registered': True,
                        'client_account': account_id,
                        'client_account_type': 'Affiliated',  # Indicate this came from affiliation endpoint
                    }
                )
                
                context['client_validation'] = client_validation
            else:
                # For non-registered clients, just record the fact they are not registered
                client_validation = ClientValidation.objects.create(
                    client_id=client_id or email,
                    is_registered=False
                )
                context['client_validation'] = client_validation
        
        return render(request, self.template_name, context) 