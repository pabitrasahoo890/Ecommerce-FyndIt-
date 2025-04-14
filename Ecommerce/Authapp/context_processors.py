from Authapp.models import CustomUser, Cart,Wishlist

def cart_count(request):
    if request.user.is_authenticated:
        try:
            user = CustomUser.objects.get(id=request.user.id)  # Ensure CustomUser instance
            count = Cart.objects.filter(user=user).count()
        except CustomUser.DoesNotExist:
            count = 0
    else:
        count = 0

    return {"cart_count": count}

def wishlist_count(request):
    if request.user.is_authenticated:
        try:
            user = CustomUser.objects.get(id=request.user.id)  # Ensure CustomUser instance
            count = Wishlist.objects.filter(user=user).count()
        except CustomUser.DoesNotExist:
            count = 0
    else:
        count = 0

    return {"wishlist_count": count}

