from django import forms
from .models import CustomUser, ShippingAddress, Order, ContactUs
import re



class RegistrationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['name', 'phone', 'email', 'country', 'state', 'city', 'pincode']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mobile Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pincode'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not re.fullmatch(r'\d{10}', phone):  # Ensure phone number is exactly 10 digits
            raise forms.ValidationError("Enter a valid 10-digit mobile number.")
        if CustomUser.objects.filter(phone=phone).exists():
            raise forms.ValidationError("This phone number is already registered.")
        return phone

    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode')
        if not re.fullmatch(r'\d{6}', pincode):  # Ensure pincode is exactly 6 digits
            raise forms.ValidationError("Enter a valid 6-digit pincode.")
        return pincode

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email



class OTPVerificationForm(forms.Form):
    otp = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter OTP'}),
    )

    def clean_otp(self):
        otp = self.cleaned_data.get('otp')
        if not re.fullmatch(r'\d{6}', otp):  # Ensure OTP is exactly 6 digits
            raise forms.ValidationError("Invalid OTP format. Enter a 6-digit number.")
        return otp



class LoginForm(forms.Form):
    phone = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Mobile Number'}),
    )

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not re.fullmatch(r'\d{10}', phone):  
            raise forms.ValidationError("Enter a valid 10-digit mobile number.")

        if not CustomUser.objects.filter(phone=phone).exists():
            raise forms.ValidationError("This phone number is not registered.")
        return phone


class ShippingAddressForm(forms.ModelForm):
    class Meta:
        model = ShippingAddress
        fields = ['full_name', 'phone_number', 'street_address', 'city', 'state', 'country', 'postal_code']

        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Full Name"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone Number"}),
            "street_address": forms.Textarea(attrs={"class": "form-control", "placeholder": "Street Address", "rows": 2}),
            "city": forms.TextInput(attrs={"class": "form-control", "placeholder": "City"}),
            "state": forms.TextInput(attrs={"class": "form-control", "placeholder": "State"}),
            "country": forms.TextInput(attrs={"class": "form-control", "placeholder": "Country"}),
            "postal_code": forms.TextInput(attrs={"class": "form-control", "placeholder": "Postal Code"}),
        }


    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if not phone.isdigit():
            raise forms.ValidationError("Phone number should contain only digits.")
        if len(phone) < 10 or len(phone) > 10:
            raise forms.ValidationError("Enter a valid phone number (10 digits).")
        return phone

    def clean_postal_code(self):
        postal_code = self.cleaned_data.get('postal_code')

    # Check if postal code contains only digits and is exactly 6 characters long
        if not postal_code.isdigit() or len(postal_code) != 6:
            raise forms.ValidationError("Postal code must be exactly 6 digits.")

        return postal_code
    
class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['payment_method']

    def clean_payment_method(self):
        payment_method = self.cleaned_data.get('payment_method')
        if payment_method not in dict(Order.PAYMENT_METHOD_CHOICES):
            raise forms.ValidationError("Invalid payment method selected.")
        return payment_method
    

class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['name', 'email', 'city', 'state', 'country']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter First Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter Email'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter State'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Country'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and CustomUser.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError("Email is already in use.")
        return email
    

class ContactUsForm(forms.ModelForm):
    class Meta:
        model = ContactUs
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your Email'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Your Message', 'rows': 4}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email.endswith('@gmail.com'):  # Example: Restrict emails
            raise forms.ValidationError("Only Gmail addresses are allowed!")
        return email
    
