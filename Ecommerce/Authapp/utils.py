# Authapp/utils.py
from django.core.mail import send_mail
from django.conf import settings
def send_order_confirmation_email(order, order_items, recipient_email):
    subject = f"Order Confirmation - #{order.unique_order_id}"
    
    # Build plain text message
    message = f"""
    Thank you for your order!
    
    Order Details:
    ---------------
    Order Number: {order.unique_order_id}
    Date: {order.created_at.strftime('%B %d, %Y')}
    Payment Method: {order.get_payment_method_display()}
    Status: {order.status}
    
    Items:
    ------"""
    
    # Add order items
    for item in order_items:
        message += f"""
    - {item.product.name} 
      Qty: {item.quantity} × ₹{item.price} = ₹{item.quantity * item.price}"""
    
    # Add totals and shipping
    message += f"""
    
    Subtotal: ₹{order.total_amount}
    
    Shipping Information:
    --------------------
    {order.shipping_address.full_name}
    """
    message += f"""
    {order.shipping_address.city}, {order.shipping_address.state}
    {order.shipping_address.postal_code}
    {order.shipping_address.country}"""
    
    if order.shipping_address.phone_number:
        message += f"""
    Phone: {order.shipping_address.phone_number}"""
    
    message += """
    
    If you have any questions about your order, please contact our support team.
    
    Best regards,
    Fynd It"""
    
    # Send email
    send_mail(
        subject,
        message.strip(),  # Remove leading/trailing whitespace
        settings.DEFAULT_FROM_EMAIL,  # Uses DEFAULT_FROM_EMAIL from settings
        [recipient_email]
    )