import hashlib
import hmac
import json
from urllib.parse import urlencode
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from orders.models import Order, WompiConfig
from .models import Cart
from inventory.models import Warehouse, StockMovement


def get_wompi_config():
    """Obtiene la configuración activa de Wompi"""
    config = WompiConfig.get_config()
    if not config.is_active or not config.public_key:
        return None
    return config


def generate_wompi_integrity_signature(amount_in_cents, currency, reference, integrity_secret):
    signature_string = f"{reference}{amount_in_cents}{currency}{integrity_secret}"
    return hashlib.sha256(signature_string.encode('utf-8')).hexdigest()


def _get_inventory_user_for_order(order):
    user = getattr(getattr(order, 'customer', None), 'user', None)
    if user:
        return user

    User = get_user_model()
    return User.objects.filter(is_superuser=True).first() or User.objects.first()


def apply_inventory_deduction_for_paid_order(order):
    warehouse = Warehouse.objects.filter(is_main=True, is_active=True).first()
    if not warehouse:
        warehouse = Warehouse.objects.filter(is_active=True).first()
    if not warehouse:
        return

    inventory_user = _get_inventory_user_for_order(order)
    if not inventory_user:
        return

    reference = f"Orden {order.order_number}"
    for item in order.items.select_related('product').all():
        exists = StockMovement.objects.filter(
            product=item.product,
            warehouse=warehouse,
            movement_type='out',
            reference=reference,
        ).exists()
        if exists:
            continue

        StockMovement.objects.create(
            product=item.product,
            warehouse=warehouse,
            movement_type='out',
            quantity=-int(item.quantity),
            reference=reference,
            notes='Venta web (Wompi)',
            user=inventory_user,
        )


def create_wompi_transaction(order):
    """
    Prepara los datos para usar el widget de Wompi
    El widget se encarga de crear la transacción
    """
    config = get_wompi_config()
    if not config:
        return None, "Wompi no está configurado correctamente o está inactivo"

    if not (config.integrity_secret or '').strip():
        return None, "Wompi requiere firma de integridad. Configura el Secreto de Integridad."

    # Preparar los datos para el widget de Wompi
    amount_in_cents = int(order.total * 100)  # Wompi usa centavos
    currency = "COP"

    # Construir la URL de redirección
    try:
        from django.contrib.sites.models import Site
        current_site = Site.objects.get_current()
        if settings.DEBUG:
            base_url = "http://127.0.0.1:8000"
        else:
            base_url = f"https://{current_site.domain}"
    except Exception:
        if settings.DEBUG:
            base_url = "http://127.0.0.1:8000"
        else:
            base_url = "https://naturalmede.com"

    redirect_url = f"{base_url}/checkout/success/{order.id}/"
    if settings.DEBUG:
        redirect_url = ""

    # Datos para el widget (no requiere crear transacción previa)
    widget_data = {
        "amount_in_cents": amount_in_cents,
        "currency": currency,
        "reference": order.order_number,
        "public_key": config.public_key,
        "redirect_url": redirect_url,
    }

    widget_data["integrity_signature"] = generate_wompi_integrity_signature(
        amount_in_cents,
        currency,
        order.order_number,
        (config.integrity_secret or '').strip(),
    )

    params = {
        "mode": "widget",
        "public-key": config.public_key,
        "currency": "COP",
        "amount-in-cents": amount_in_cents,
        "reference": order.order_number,
    }
    if redirect_url:
        params["redirect-url"] = redirect_url

    widget_data["checkout_url"] = "https://checkout.wompi.co/p/?" + urlencode(params)

    # Guardar la referencia en la orden
    order.wompi_reference = order.order_number
    order.save()

    return widget_data, None


def generate_wompi_signature(data, secret):
    """
    Genera la firma para verificar el webhook de Wompi
    """
    signature_string = (
        f"{data['data']['transaction']['id']}^"
        f"{data['data']['transaction']['status']}^"
        f"{data['data']['transaction']['amount_in_cents']}"
    )
    signature = hmac.new(
        secret.encode('utf-8'),
        signature_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature


@csrf_exempt
@require_http_methods(["POST"])
def wompi_webhook(request):
    """
    Maneja el webhook de Wompi para confirmar pagos
    """
    try:
        data = json.loads(request.body)

        # Verificar la firma si está configurada
        config = WompiConfig.get_config()
        secret = (getattr(config, 'events_secret', '') or '').strip() or (config.integrity_secret or '').strip()
        if secret:
            received_signature = request.headers.get('X-Signature', '')
            expected_signature = generate_wompi_signature(
                data,
                secret,
            )

            if received_signature != expected_signature:
                return HttpResponse("Invalid signature", status=400)

        # Obtener información de la transacción
        transaction = data.get('data', {}).get('transaction', {})
        reference = transaction.get('reference')

        if not reference:
            return HttpResponse("No reference found", status=400)

        # Buscar la orden por referencia
        order = get_object_or_404(Order, order_number=reference)

        # Actualizar el estado de la orden según el estado de Wompi
        wompi_status = transaction.get('status')
        order.wompi_status = wompi_status
        order.wompi_transaction_id = transaction.get('id')

        if wompi_status == 'APPROVED':
            order.status = 'paid'
            from django.utils import timezone
            order.paid_at = timezone.now()
            order.save()

            apply_inventory_deduction_for_paid_order(order)

            try:
                user = getattr(order.customer, 'user', None)
                if user:
                    cart = Cart.objects.filter(user=user).first()
                    if cart:
                        cart.items.all().delete()
            except Exception:
                pass
        elif wompi_status in ['DECLINED', 'VOIDED', 'ERROR']:
            order.status = 'cancelled'
            order.save()

        return HttpResponse("OK", status=200)

    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)
