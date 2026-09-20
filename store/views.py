from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from .models import (
    Product,
    CartItem,
    Order,
    OrderItem,
    Wishlist
)


def home(request):

    products = Product.objects.filter(
        is_available=True
    )

    women_products = products.filter(
        category__name__iexact="Women"
    )[:4]

    men_products = products.filter(
        category__name__iexact="Men"
    )[:4]

    accessory_products = products.filter(
        category__name__iexact="Accessories"
    )[:4]

    return render(
        request,
        "store/home.html",
        {
            "products": products,
            "women_products": women_products,
            "men_products": men_products,
            "accessory_products": accessory_products,
        }
    )


def shop(request):

    products = Product.objects.filter(
        is_available=True
    )

    category = request.GET.get("category")

    search_query = request.GET.get(
        "q",
        ""
    ).strip()

    if category:

        products = products.filter(
            category__name__iexact=category
        )

    if search_query:

        products = products.filter(
            Q(name__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    wishlist_ids = []

    if request.user.is_authenticated:

        wishlist_ids = Wishlist.objects.filter(
            user=request.user,
            product__in=products
        ).values_list(
            "product_id",
            flat=True
        )

    return render(
        request,
        "store/shop.html",
        {
            "products": products,
            "selected_category": category,
            "search_query": search_query,
            "wishlist_ids": wishlist_ids,
        }
    )


def product_detail(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True
    )

    sizes = product.sizes.all()

    is_wishlisted = False

    if request.user.is_authenticated:

        is_wishlisted = Wishlist.objects.filter(
            user=request.user,
            product=product
        ).exists()

    return render(
        request,
        "store/product_detail.html",
        {
            "product": product,
            "sizes": sizes,
            "is_wishlisted": is_wishlisted,
        }
    )


@login_required(login_url="login")
def add_to_cart(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True
    )

    if request.method != "POST":

        return redirect(
            "product_detail",
            product_id=product.id
        )

    size = request.POST.get(
        "size",
        ""
    ).strip()

    if product.sizes.exists() and not size:

        return redirect(
            "product_detail",
            product_id=product.id
        )

    if not size:

        size = None

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product,
        size=size
    )

    if created:

        cart_item.quantity = 1

    else:

        cart_item.quantity += 1

    cart_item.save()

    return redirect("cart")


@login_required(login_url="login")
def cart(request):

    cart_items = CartItem.objects.filter(
        user=request.user
    ).select_related("product")

    cart_total = 0

    for item in cart_items:

        item.total_price = (
            item.product.price *
            item.quantity
        )

        cart_total += item.total_price

    return render(
        request,
        "store/cart.html",
        {
            "cart_items": cart_items,
            "cart_total": cart_total,
        }
    )


@login_required(login_url="login")
def remove_from_cart(request, item_id):

    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        user=request.user
    )

    cart_item.delete()

    return redirect("cart")


@login_required(login_url="login")
def increase_quantity(request, item_id):

    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        user=request.user
    )

    cart_item.quantity += 1

    cart_item.save()

    return redirect("cart")


@login_required(login_url="login")
def decrease_quantity(request, item_id):

    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        user=request.user
    )

    if cart_item.quantity > 1:

        cart_item.quantity -= 1

        cart_item.save()

    else:

        cart_item.delete()

    return redirect("cart")


@login_required(login_url="login")
def checkout(request):

    cart_items = CartItem.objects.filter(
        user=request.user
    ).select_related("product")

    if not cart_items.exists():

        return redirect("cart")

    cart_total = 0

    for item in cart_items:

        item.total_price = (
            item.product.price *
            item.quantity
        )

        cart_total += item.total_price

    if request.method == "POST":

        customer_name = request.POST.get(
            "customer_name"
        )

        email = request.POST.get(
            "email"
        )

        address = request.POST.get(
            "address"
        )

        order = Order.objects.create(
            user=request.user,
            customer_name=customer_name,
            email=email,
            address=address,
            total_amount=cart_total
        )

        for item in cart_items:

            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
                size=item.size
            )

        cart_items.delete()

        return redirect(
            "order_success",
            order_id=order.id
        )

    return render(
        request,
        "store/checkout.html",
        {
            "cart_items": cart_items,
            "cart_total": cart_total,
        }
    )


@login_required(login_url="login")
def order_success(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    return render(
        request,
        "store/order_success.html",
        {
            "order": order
        }
    )


@login_required(login_url="login")
def my_orders(request):

    orders = Order.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "store/my_orders.html",
        {
            "orders": orders
        }
    )


@login_required(login_url="login")
def order_details(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    order_items = OrderItem.objects.filter(
        order=order
    ).select_related("product")

    return render(
        request,
        "store/order_details.html",
        {
            "order": order,
            "order_items": order_items,
        }
    )


@login_required(login_url="login")
def profile(request):

    return render(
        request,
        "store/profile.html"
    )


# =========================
# WISHLIST
# =========================

@login_required(login_url="login")
def toggle_wishlist(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True
    )

    wishlist_item = Wishlist.objects.filter(
        user=request.user,
        product=product
    ).first()

    if wishlist_item:

        wishlist_item.delete()

    else:

        Wishlist.objects.create(
            user=request.user,
            product=product
        )

    return redirect(
        request.META.get(
            "HTTP_REFERER",
            "shop"
        )
    )


@login_required(login_url="login")
def wishlist(request):

    wishlist_items = Wishlist.objects.filter(
        user=request.user
    ).select_related(
        "product",
        "product__category"
    ).order_by("-created_at")

    return render(
        request,
        "store/wishlist.html",
        {
            "wishlist_items": wishlist_items
        }
    )


@login_required(login_url="login")
def remove_from_wishlist(request, product_id):

    Wishlist.objects.filter(
        user=request.user,
        product_id=product_id
    ).delete()

    return redirect("wishlist")


# =========================
# REGISTER
# =========================

def register(request):

    if request.method == "POST":

        username = request.POST.get(
            "username"
        )

        email = request.POST.get(
            "email"
        )

        password = request.POST.get(
            "password"
        )

        confirm_password = request.POST.get(
            "confirm_password"
        )

        if password != confirm_password:

            return render(
                request,
                "store/register.html",
                {
                    "error": "Passwords do not match."
                }
            )

        if User.objects.filter(
            username=username
        ).exists():

            return render(
                request,
                "store/register.html",
                {
                    "error": "Username already exists."
                }
            )

        if User.objects.filter(
            email=email
        ).exists():

            return render(
                request,
                "store/register.html",
                {
                    "error": "Email already exists."
                }
            )

        User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        return redirect("login")

    return render(
        request,
        "store/register.html"
    )


# =========================
# LOGIN
# =========================

def login_view(request):

    if request.method == "POST":

        username = request.POST.get(
            "username"
        )

        password = request.POST.get(
            "password"
        )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(
                request,
                user
            )

            return redirect("home")

        return render(
            request,
            "store/login.html",
            {
                "error": "Invalid username or password."
            }
        )

    return render(
        request,
        "store/login.html"
    )


# =========================
# LOGOUT
# =========================

def logout_view(request):

    logout(request)

    return redirect("home")