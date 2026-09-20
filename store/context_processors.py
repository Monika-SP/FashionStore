from .models import CartItem, Wishlist


def cart_count(request):

    count = 0
    wishlist_count = 0

    if request.user.is_authenticated:

        count = sum(
            item.quantity
            for item in CartItem.objects.filter(
                user=request.user
            )
        )

        wishlist_count = Wishlist.objects.filter(
            user=request.user
        ).count()

    return {
        "cart_count": count,
        "wishlist_count": wishlist_count,
    }