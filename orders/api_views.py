from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Order, OrderItem, ShippingRate
from .serializers import OrderSerializer, OrderItemSerializer, ShippingRateSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related('customer__user').prefetch_related('items__product')
    serializer_class = OrderSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtro por estado
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filtro por método de pago
        payment_filter = self.request.query_params.get('payment_method')
        if payment_filter:
            queryset = queryset.filter(payment_method=payment_filter)
        
        # Búsqueda
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(order_number__icontains=search) |
                Q(customer__user__first_name__icontains=search) |
                Q(customer__user__last_name__icontains=search)
            )
        
        return queryset.order_by('-created_at')

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response({'error': 'status is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar transición de estado
        if not self.is_valid_status_transition(order.status, new_status):
            return Response(
                {'error': f'Invalid status transition from {order.status} to {new_status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = new_status
        
        # Actualizar fechas según el estado
        if new_status == 'paid':
            order.paid_at = timezone.now()
        elif new_status == 'shipped':
            order.shipped_at = timezone.now()
        elif new_status == 'delivered':
            order.delivered_at = timezone.now()
        
        order.save()
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    def is_valid_status_transition(self, old_status, new_status):
        """Valida si la transición de estado es válida"""
        valid_transitions = {
            'new': ['pending', 'cancelled'],
            'pending': ['paid', 'cancelled'],
            'paid': ['shipped', 'cancelled'],
            'shipped': ['delivered'],
            'delivered': [],
            'cancelled': []
        }
        return new_status in valid_transitions.get(old_status, [])


class ShippingRateViewSet(viewsets.ModelViewSet):
    queryset = ShippingRate.objects.all()
    serializer_class = ShippingRateSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtro por ciudad
        city = self.request.query_params.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        # Solo activas
        active_only = self.request.query_params.get('active_only', 'true').lower() == 'true'
        if active_only:
            queryset = queryset.filter(is_active=True)
        
        return queryset.order_by('city', 'min_weight')


class OrderStatusUpdateAPIView(APIView):
    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        new_status = request.data.get('status')
        
        if not new_status:
            return Response({'error': 'status is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar transición de estado
        valid_transitions = {
            'new': ['pending', 'cancelled'],
            'pending': ['paid', 'cancelled'],
            'paid': ['shipped', 'cancelled'],
            'shipped': ['delivered'],
            'delivered': [],
            'cancelled': []
        }
        
        if new_status not in valid_transitions.get(order.status, []):
            return Response(
                {'error': f'Invalid status transition from {order.status} to {new_status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = new_status
        
        # Actualizar fechas según el estado
        if new_status == 'paid':
            order.paid_at = timezone.now()
        elif new_status == 'shipped':
            order.shipped_at = timezone.now()
        elif new_status == 'delivered':
            order.delivered_at = timezone.now()
        
        order.save()
        
        serializer = OrderSerializer(order)
        return Response(serializer.data)


class ShippingCostCalculateAPIView(APIView):
    def post(self, request):
        city = request.data.get('city')
        weight = request.data.get('weight')
        
        if not city or not weight:
            return Response(
                {'error': 'city and weight are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            weight = float(weight)
        except (ValueError, TypeError):
            return Response(
                {'error': 'weight must be a valid number'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cost = ShippingRate.get_shipping_cost(city, weight)
        
        return Response({
            'city': city,
            'weight': weight,
            'cost': cost
        })













