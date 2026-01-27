import json
import hmac
import hashlib

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone

from customers.models import Customer
from orders.models import Order, WompiConfig
from catalog.wompi_views import create_wompi_transaction


class WompiTransactionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='wompiuser',
            password='testpass123',
        )
        self.customer = Customer.objects.create(
            user=self.user,
            customer_type='normal',
            document_type='CC',
            document_number='123456789',
            phone='+573001234567',
            address='Calle 1 # 2-3',
            city='Bogotá',
            channel='website',
        )

        self.order = Order.objects.create(
            customer=self.customer,
            status='new',
            payment_method='wompi',
            subtotal=10000,
            iva_amount=0,
            shipping_cost=0,
            total=10000,
            shipping_address='Calle 1 # 2-3',
            shipping_city='Bogotá',
            shipping_phone='+573001234567',
        )

    def test_create_wompi_transaction_returns_error_when_inactive(self):
        config = WompiConfig.get_config()
        config.is_active = False
        config.public_key = 'pub_test_abc'
        config.save()

        wompi_data, error = create_wompi_transaction(self.order)
        assert wompi_data is None
        assert error

    def test_create_wompi_transaction_errors_without_public_key(self):
        config = WompiConfig.get_config()
        config.is_active = True
        config.public_key = ''
        config.save()

        wompi_data, error = create_wompi_transaction(self.order)
        assert wompi_data is None
        assert error

    def test_create_wompi_transaction_success_sets_reference(self):
        config = WompiConfig.get_config()
        config.is_active = True
        config.public_key = 'pub_test_abc'
        config.save()

        wompi_data, error = create_wompi_transaction(self.order)
        assert error is None
        assert wompi_data is not None
        assert wompi_data['reference'] == self.order.order_number

        self.order.refresh_from_db()
        assert self.order.wompi_reference == self.order.order_number


class WompiWebhookTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username='wompiwebhook',
            password='testpass123',
        )
        self.customer = Customer.objects.create(
            user=self.user,
            customer_type='normal',
            document_type='CC',
            document_number='987654321',
            phone='+573001234568',
            address='Calle 9 # 9-9',
            city='Bogotá',
            channel='website',
        )

        self.order = Order.objects.create(
            customer=self.customer,
            status='pending',
            payment_method='wompi',
            subtotal=10000,
            iva_amount=0,
            shipping_cost=0,
            total=10000,
            shipping_address='Calle 9 # 9-9',
            shipping_city='Bogotá',
            shipping_phone='+573001234568',
        )

    def _payload(
        self,
        status='APPROVED',
        amount_in_cents=1000000,
        tx_id='tx_1',
    ):
        return {
            'data': {
                'transaction': {
                    'id': tx_id,
                    'status': status,
                    'amount_in_cents': amount_in_cents,
                    'reference': self.order.order_number,
                }
            }
        }

    def _signature(self, payload, secret):
        signature_string = (
            f"{payload['data']['transaction']['id']}^"
            f"{payload['data']['transaction']['status']}^"
            f"{payload['data']['transaction']['amount_in_cents']}"
        )
        return hmac.new(
            secret.encode('utf-8'),
            signature_string.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()

    def test_webhook_approved_updates_order_paid(self):
        config = WompiConfig.get_config()
        config.is_active = True
        config.public_key = 'pub_test_abc'
        config.integrity_secret = ''
        config.save()

        payload = self._payload(
            status='APPROVED',
            amount_in_cents=1000000,
            tx_id='tx_ok',
        )

        response = self.client.post(
            '/wompi/webhook/',
            data=json.dumps(payload),
            content_type='application/json',
        )
        assert response.status_code == 200

        self.order.refresh_from_db()
        assert self.order.status == 'paid'
        assert self.order.wompi_status == 'APPROVED'
        assert self.order.wompi_transaction_id == 'tx_ok'
        assert self.order.paid_at is not None
        assert self.order.paid_at <= timezone.now()

    def test_webhook_invalid_signature_returns_400(self):
        config = WompiConfig.get_config()
        config.is_active = True
        config.public_key = 'pub_test_abc'
        config.integrity_secret = 'secret123'
        config.save()

        payload = self._payload(
            status='APPROVED',
            amount_in_cents=1000000,
            tx_id='tx_bad',
        )

        response = self.client.post(
            '/wompi/webhook/',
            data=json.dumps(payload),
            content_type='application/json',
            **{'HTTP_X_SIGNATURE': 'bad_signature'},
        )
        assert response.status_code == 400

        self.order.refresh_from_db()
        assert self.order.status == 'pending'

    def test_webhook_valid_signature_returns_200(self):
        config = WompiConfig.get_config()
        config.is_active = True
        config.public_key = 'pub_test_abc'
        config.integrity_secret = 'secret123'
        config.save()

        payload = self._payload(
            status='APPROVED',
            amount_in_cents=1000000,
            tx_id='tx_good',
        )
        signature = self._signature(payload, config.integrity_secret)

        response = self.client.post(
            '/wompi/webhook/',
            data=json.dumps(payload),
            content_type='application/json',
            **{'HTTP_X_SIGNATURE': signature},
        )
        assert response.status_code == 200

        self.order.refresh_from_db()
        assert self.order.status == 'paid'
        assert self.order.wompi_transaction_id == 'tx_good'
