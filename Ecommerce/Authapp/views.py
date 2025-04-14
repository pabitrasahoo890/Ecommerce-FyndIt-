from django.shortcuts import render, redirect, get_object_or_404,HttpResponse
from django.contrib.auth import login, logout, authenticate, get_backends
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser, Product, Subcategory, Category, Cart, Wishlist, ShippingAddress, OrderItem, Order
from .forms import RegistrationForm, OTPVerificationForm, LoginForm, ShippingAddressForm, PaymentMethodForm, UserProfileUpdateForm,ContactUsForm
import secrets
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import os
from dotenv import load_dotenv
from django.utils.timezone import now
from decimal import Decimal
from django.db import transaction
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from .utils import send_order_confirmation_email
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.core.mail import send_mail
import logging
logger = logging.getLogger(__name__)



# Load environment variables
load_dotenv()
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# Secure OTP Generator
def generate_otp():
    return str(secrets.randbelow(900000) + 100000)  # Always 6-digit OTP

def get_user_by_phone(phone):
    """Utility function to check if user exists."""
    return CustomUser.objects.filter(phone=phone).first()

# Ensure Phone Number is Indian (+91)
def format_phone_number(phone):
    """Ensure phone number starts with +91 (Indian Numbers Only)."""
    phone = phone.strip()  # Remove extra spaces
    if phone.startswith("+91"):  
        return phone  # Already formatted correctly
    elif phone.startswith("91") and len(phone) == 12:  
        return f"+{phone}"  # If user enters '91XXXXXXXXXX'
    elif len(phone) == 10 and phone.isdigit():  
        return f"+91{phone}"  # If user enters 'XXXXXXXXXX'
    else:
        raise ValueError("Invalid phone number. Enter a valid 10-digit Indian number.")

# Send OTP via Twilio (with Exception Handling)
def send_otp_via_twilio(phone, otp):
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        formatted_phone = format_phone_number(phone)  # Ensure correct format
        
        message = client.messages.create(
            body=f"Your OTP code is {otp}",
            from_=TWILIO_PHONE_NUMBER,
            to=formatted_phone  
        )
        return message.sid
    except TwilioRestException as e:
        print(f"Twilio Error: {e}")
        return None


# Registration View
def register_view(request):
    """Handles new user registration (stores data in session & sends OTP)"""
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data["phone"]

            # Check if user already exists
            if CustomUser.objects.filter(phone=phone).exists():
                messages.error(request, "This phone number is already registered.")
                return redirect("login")  # Redirect existing user to login

            # Store user data temporarily in session (not in DB)
            request.session["registration_data"] = form.cleaned_data

            # Generate & send OTP
            otp = generate_otp()
            request.session["otp"] = otp  # Store OTP in session
            send_otp_via_twilio(phone, otp)

            messages.success(request, "OTP sent to your phone number.")
            return redirect("otp_verify")  # Redirect to OTP verification page
    else:
        form = RegistrationForm()
    
    return render(request, "register.html", {"form": form})

# OTP Verification View
def otp_verify_view(request):
    form = OTPVerificationForm()

    if request.method == "POST":
        form = OTPVerificationForm(request.POST)
        entered_otp = request.POST.get("otp")
        stored_otp = request.session.get("otp")

        if stored_otp and entered_otp == stored_otp:
            user_data = request.session.get("registration_data", {})

            user, created = CustomUser.objects.get_or_create(
                phone=user_data.get("phone"),
                defaults={
                    "name": user_data.get("name", ""),
                    "email": user_data.get("email", ""),
                    "country": user_data.get("country", ""),
                    "state": user_data.get("state", ""),
                    "city": user_data.get("city", ""),
                    "pincode": user_data.get("pincode", ""),
                    "is_active": True
                }
            )

            # Ensure user is active
            if not user.is_active:
                user.is_active = True
                user.save()

            # Authenticate before login
            user = authenticate(request, username=user.phone)
            if user:
                login(request, user)
                request.session.modified = True  # ✅ Force session to save
                request.session.set_expiry(0)  # ✅ Keep session active
                print("User logged in successfully!")
            else:
                print("Authentication failed!")

            request.session.pop("registration_data", None)
            request.session.pop("otp", None)

            messages.success(request, "OTP verified successfully! Logged in.")
            return redirect("home")
        else:
            messages.error(request, "Invalid OTP. Please try again.")
            print("OTP mismatch!")

    return render(request, "otp_verify.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        if "otp" in request.POST:  # If OTP form is submitted
            otp_form = OTPVerificationForm(request.POST)
            if otp_form.is_valid():
                entered_otp = otp_form.cleaned_data['otp']
                stored_otp = request.session.get('otp')
                phone = request.session.get('phone')

                if stored_otp and entered_otp == stored_otp:
                    user = get_user_by_phone(phone)
                    
                    if user and user.is_active:# ✅ Check if user is active
                        backend = get_backends()[0]
                        backend_path = f"{backend.__module__}.{backend.__class__.__name__}"
                        login(request, user, backend=backend_path)
                        messages.success(request, "Login successful!")
                        return redirect("home")  # Redirect to homepage
                    else:
                        messages.error(request, "Account is inactive or does not exist.")
                else:
                    messages.error(request, "Invalid OTP. Try again.")

            return render(request, "otp_verify.html", {"otp_form": otp_form})

        else:  # If login form is submitted
            login_form = LoginForm(request.POST)
            if login_form.is_valid():
                phone = login_form.cleaned_data['phone']
                user = get_user_by_phone(phone)

                if user and user.is_active:  # ✅ Check if user is active before sending OTP
                    otp = generate_otp()

                    # Save OTP & phone in session
                    request.session['otp'] = otp
                    request.session['phone'] = phone

                    # Send OTP via Twilio
                    send_otp_via_twilio(phone, otp)

                    messages.success(request, "OTP sent successfully!")
                    return render(request, "otp_verify.html", {"form": OTPVerificationForm()})
                else:
                    messages.error(request, "Account is inactive or does not exist.")

    else:
        login_form = LoginForm()
        otp_form = OTPVerificationForm()

    return render(request, "login.html", {"form": login_form})


def logout_view(request):
    """Logs out the user & redirects to login page"""
    logout(request)
    return redirect("login")


def home_view(request):
    print("Is user authenticated:", request.user.is_authenticated)
    print("Current user:", request.user)

    # Fetch search query from request
    query = request.GET.get('q', '')

    # If search query exists, filter products; otherwise, show new arrivals
    if query:
        products = Product.objects.filter(name__istartswith=query)
    else:
        products = Product.objects.all().order_by('-id')[:30]  # Latest 30 products

    categories = Category.objects.prefetch_related("subcategory").all()  # Fetch categories & related subcategories
    cart_count = Cart.objects.filter(user=request.user).count() if request.user.is_authenticated else 0
    wishlist_count = Wishlist.objects.filter(user=request.user).count() if request.user.is_authenticated else 0

    return render(request, "home.html", {
        "user": request.user,
        "products": products,
        "categories": categories,
        "cart_count": cart_count,
        "wishlist_count": wishlist_count,
        "query": query  # Pass query to keep input field value
    })



def category_view(request, subcategory_slug):
    subcategory = get_object_or_404(Subcategory, slug=subcategory_slug)
    products = Product.objects.filter(subcategory=subcategory)

    return render(request, "home.html", {"products": products, "subcategory": subcategory})


def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, "product_detail.html", {"product": product})

@login_required(login_url='login')
def cart_view(request):
    return render(request, 'cart.html')

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
    
    if not created:
        cart_item.quantity += 1  # If product already in cart, increase quantity
    cart_item.save()

    messages.success(request, "Product added to cart!")

    return redirect("home")


@login_required
def update_cart(request, item_id):
    cart_item = get_object_or_404(Cart, id=item_id, user=request.user)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "increase":
            if cart_item.quantity < 5:  # Enforce max limit
                cart_item.quantity += 1
                messages.success(request, "Quantity updated successfully!")
            else:
                messages.warning(request, "Maximum quantity limit is 5!")
        
        elif action == "decrease" and cart_item.quantity > 1:
            cart_item.quantity -= 1
            messages.success(request, "Quantity decreased successfully!")

        cart_item.save()

    return redirect('cart_view')

# ✅ View Cart
@login_required
def cart_view(request):
    cart_items = Cart.objects.filter(user=request.user)
    total_price = sum(item.total_price() for item in cart_items)
    return render(request, "cart.html", {"cart_items": cart_items, "total_price": total_price})

# ✅ Remove product from cart
@login_required
def remove_from_cart(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    cart_item.delete()
    messages.error(request, "Product removed from cart!")
    return redirect("cart_view")


@login_required
def wishlist_view(request):
    """View wishlist items"""
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, "wishlist.html", {"wishlist_items": wishlist_items})

@login_required
def add_to_wishlist(request, product_id):
    """Add a product to the wishlist"""
    product = get_object_or_404(Product, id=product_id)
    
    # Check if product is already in wishlist
    if Wishlist.objects.filter(user=request.user, product=product).exists():
        messages.warning(request, "This product is already in your wishlist!")
    else:
        Wishlist.objects.create(user=request.user, product=product)
        messages.success(request, "Product added to wishlist!")

    return redirect("home")

@login_required
def remove_from_wishlist(request, product_id):
    """Remove a product from the wishlist"""
    product = get_object_or_404(Product, id=product_id)
    wishlist_item = Wishlist.objects.filter(user=request.user, product=product)
    
    if wishlist_item.exists():
        wishlist_item.delete()
        messages.success(request, "Product removed from wishlist!")
    else:
        messages.error(request, "Product was not found in your wishlist!")

    return redirect("wishlist")

@login_required
def move_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Remove from Wishlist
    Wishlist.objects.filter(user=request.user, product_id=product_id).delete()

    # Add to Cart
    cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
    cart_item.quantity += 1
    cart_item.save()

    return redirect("wishlist")


@login_required(login_url='login')  # Redirects to login page if user is not authenticated
def move_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Check if the product is already in the wishlist
    wishlist_exists = Wishlist.objects.filter(user=request.user, product=product).exists()

    if wishlist_exists:
        messages.warning(request, "This product is already in your wishlist.")
    else:
        # Remove from cart only if it's not already in the wishlist
        Cart.objects.filter(user=request.user, product=product).delete()

        # Add to wishlist
        Wishlist.objects.create(user=request.user, product=product)
        messages.success(request, "Product moved to wishlist.")

    return redirect('cart_view')  # Redirect back to the cart page


# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@login_required(login_url='login')
def checkout_view(request):
    cart_items = Cart.objects.filter(user=request.user)
    total_amount = sum(item.product.price * item.quantity for item in cart_items)

    if not cart_items:
        messages.error(request, "Your cart is empty.")
        return redirect("cart_view")

    saved_address = ShippingAddress.objects.filter(user=request.user).first()
    shipping_form = ShippingAddressForm(instance=saved_address) if saved_address else ShippingAddressForm()
    payment_form = PaymentMethodForm()

    if request.method == "POST":
        shipping_form = ShippingAddressForm(request.POST)
        payment_form = PaymentMethodForm(request.POST)

        if shipping_form.is_valid() and payment_form.is_valid():
            # Check stock availability before proceeding
            for item in cart_items:
                if item.product.stock < item.quantity:
                    messages.error(request, f"Not enough stock for {item.product.name}.")
                    return redirect("cart_view")

            # Save or update shipping address
            shipping_address = shipping_form.save(commit=False)
            shipping_address.user = request.user
            shipping_address.save()

            payment_method = payment_form.cleaned_data["payment_method"]
            print(payment_method)

            if payment_method == "COD":
                with transaction.atomic():
                    order = Order.objects.create(
                        user=request.user,
                        shipping_address=shipping_address,
                        total_amount=total_amount,
                        payment_method=payment_method,
                        status="Pending",
                    )

                    for item in cart_items:
                        product = item.product
                        product.stock -= item.quantity
                        product.save()

                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            quantity=item.quantity,
                            price=item.product.price,
                        )
                    cart_items.delete()
                    order_items = OrderItem.objects.filter(order=order)
                    send_order_confirmation_email(order, order_items, request.user.email)

                messages.success(request, "Your order has been placed successfully!")
                return redirect("order_confirmation", order_id=order.unique_order_id)

            elif payment_method == "ONLINE":
                # Store cart items in session for later verification
                cart_data = [
                    {
                        'product_id': item.product.id,
                        'quantity': item.quantity,
                        'price': float(item.product.price)
                    } for item in cart_items
                ]
                
                request.session['online_order_data'] = {
                    'shipping_address_id': shipping_address.id,
                    'total_amount': float(total_amount),
                    'cart_data': cart_data,
                    'payment_method': payment_method,
                }

                # Create Razorpay Order
                try:
                    razorpay_order = razorpay_client.order.create({
                        "amount": int(float(total_amount) * 100),  # Amount in paisa
                        "currency": "INR",
                        "payment_capture": "1",
                    })
                    return redirect("razorpay_payment", order_id=razorpay_order['id'])
                except Exception as e:
                    import traceback
                    traceback.print_exc() 
                    messages.error(request, f"Payment gateway error: {str(e)}")
                    return redirect("checkout")

    return render(
        request,
        "checkout.html",
        {
            "cart_items": cart_items,
            "total_amount": total_amount,
            "shipping_form": shipping_form,
            "payment_form": payment_form,
        },
    )

@login_required(login_url='login')
def razorpay_payment_view(request, order_id):
    if 'online_order_data' not in request.session:
        messages.error(request, "Invalid payment session.")
        return redirect("checkout_view")

    return render(request, "razorpay_payment.html", {
        "razorpay_order_id": order_id,
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        "total_amount": request.session['online_order_data']['total_amount'],
        "callback_url": request.build_absolute_uri(reverse('razorpay_success')),
    })

@csrf_exempt
@login_required(login_url='login')
def razorpay_success_view(request):
    if request.method == "POST":
        try:
            # Get payment details
            razorpay_payment_id = request.POST.get("razorpay_payment_id")
            razorpay_order_id = request.POST.get("razorpay_order_id")
            razorpay_signature = request.POST.get("razorpay_signature")
            

            # Verify payment signature
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            client.utility.verify_payment_signature(params_dict)
            
            # Check session data exists
            if 'online_order_data' not in request.session:
                raise Exception("Session data missing")
                
            order_data = request.session['online_order_data']
            
            # Verify stock again
            with transaction.atomic():
                for item in order_data['cart_data']:
                    product = Product.objects.get(id=item['product_id'])
                    if product.stock < item['quantity']:
                        raise Exception(f"Insufficient stock for {product.name}")
                
                # Create order
                order = Order.objects.create(
                    user=request.user,
                    shipping_address_id=order_data['shipping_address_id'],
                    total_amount=order_data['total_amount'],
                    payment_method=order_data['payment_method'],
                )
                
                # Create order items
                for item in order_data['cart_data']:
                    product = Product.objects.get(id=item['product_id'])
                    product.stock -= item['quantity']
                    product.save()
                    
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=item['quantity'],
                        price=item['price'],
                    )
                
                # Clear cart and session
                Cart.objects.filter(user=request.user).delete()
                del request.session['online_order_data']
                order_items = OrderItem.objects.filter(order=order)
                send_order_confirmation_email(order, order_items, request.user.email)
                
                messages.success(request, "Payment successful! Order placed.")
                return redirect("order_confirmation", order_id=order.unique_order_id)
                
        except razorpay.errors.SignatureVerificationError as e:
            messages.error(request, "Payment verification failed. Please contact support.")
        except Product.DoesNotExist as e:
            messages.error(request, "Product no longer available.")
        except Exception as e:
            messages.error(request, f"Error processing your order: {str(e)}")
        
    return redirect("checkout")

@login_required(login_url='login')
def order_confirmation_view(request, order_id):
    try:
        order = Order.objects.get(unique_order_id=order_id, user=request.user)  # Use unique_order_id instead of id
    except Order.DoesNotExist:
        return redirect('home')  # Redirect to home if order is not found

    return render(request, 'order_confirmation.html', {'order': order})


@login_required(login_url='login')
def profile_update_view(request):
    user = request.user  # Get logged-in user
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully")
            return redirect('home')  # Redirect to profile page
    else:
        form = UserProfileUpdateForm(instance=user)

    return render(request, 'profile.html', {'form': form})


@login_required(login_url='login')
def order_list_view(request):
    status_filter = request.GET.get('status', '')  # Get filter value from query params
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    if status_filter:
        orders = orders.filter(status=status_filter)

    return render(request, "order_list.html", {"orders": orders, "status_filter": status_filter})


@login_required(login_url='login')
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, unique_order_id=order_id, user=request.user)
    item_order = OrderItem.objects.filter(order=order)
    return render(request, "order_detail.html", {"order": order, "item_order":item_order})


@login_required(login_url='login')
def generate_invoice(request, order_id):
    order = get_object_or_404(Order, unique_order_id=order_id, user=request.user)
    items = OrderItem.objects.filter(order=order)

    template_path = "invoice_template.html"  # Create this template
    context = {"order": order, "items": items}

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Invoice_{order.unique_order_id}.pdf"'

    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        messages.error(request, "Failed to generate the invoice. Please try again.")
        return redirect("order_detail", order_id=order.unique_order_id)  # Redirect back to order details page
    
    return response


def contact_us(request):
    if request.method == 'POST':
        form = ContactUsForm(request.POST)
        if form.is_valid():
            # Save to database
            contact = form.save()
            
            # Send email
            subject = f"New Contact: {form.cleaned_data['subject']}"
            message = f"""
            From: {form.cleaned_data['name']} <{form.cleaned_data['email']}>
            Subject: {form.cleaned_data['subject']}
            
            Message:
            {form.cleaned_data['message']}
            """
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.ADMIN_EMAIL],
                    fail_silently=False
                )
                messages.success(request, 'Your message has been sent successfully!')
                return redirect('home')
            except Exception as e:
                messages.error(request, 'Failed to send message. Please try again later.')
                # Log the error if needed
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ContactUsForm()
    
    return render(request, 'contact_us.html', {'form': form})

def about(request):
    return render(request, 'about.html')
