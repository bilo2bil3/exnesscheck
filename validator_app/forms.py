from django import forms

class ClientValidationForm(forms.Form):
    client_id = forms.CharField(
        label="Client ID", 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter client ID'
        })
    )
    
    email = forms.EmailField(
        label="Email",
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        client_id = cleaned_data.get('client_id')
        email = cleaned_data.get('email')
        
        # Ensure at least one of client_id or email is provided
        if not client_id and not email:
            raise forms.ValidationError("Please provide either a Client ID or an Email address")
        
        return cleaned_data 