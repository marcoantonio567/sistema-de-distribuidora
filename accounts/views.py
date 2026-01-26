from django.shortcuts import render, redirect
from django.views.generic import View, TemplateView
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from orders.models import Order
from .models import UserProfile
import logging

logger = logging.getLogger('accounts')


class RegisterView(View):
    """View for user registration"""
    
    def get(self, request):
        return render(request, 'accounts/register.html')
    
    def post(self, request):
        try:
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '').strip()
            confirm_password = request.POST.get('confirm_password', '').strip()
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            zip_code = request.POST.get('zip_code', '').strip()
            address_street = request.POST.get('address_street', '').strip()
            address_number = request.POST.get('address_number', '').strip()
            address_complement = request.POST.get('address_complement', '').strip()
            neighborhood = request.POST.get('neighborhood', '').strip()
            city = request.POST.get('city', '').strip()
            state = request.POST.get('state', '').strip()
            
            # Validation
            if not all([username, email, password, confirm_password]):
                messages.error(request, 'Por favor, preencha todos os campos obrigatórios.')
                return render(request, 'accounts/register.html')
            
            if password != confirm_password:
                messages.error(request, 'As senhas não coincidem.')
                return render(request, 'accounts/register.html')
            
            if len(password) < 8:
                messages.error(request, 'A senha deve ter pelo menos 8 caracteres.')
                return render(request, 'accounts/register.html')
            
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Este nome de usuário já está em uso.')
                return render(request, 'accounts/register.html')
            
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Este email já está em uso.')
                return render(request, 'accounts/register.html')
            
            if phone:
                digits = ''.join(ch for ch in phone if ch.isdigit())
                if len(digits) < 10 or len(digits) > 11:
                    messages.error(request, 'Telefone inválido. Informe DDD e número com 10 ou 11 dígitos.')
                    return render(request, 'accounts/register.html')
            
            cep_digits = ''.join(ch for ch in zip_code if ch.isdigit())
            if len(cep_digits) != 8:
                messages.error(request, 'CEP inválido. Informe 8 dígitos.')
                return render(request, 'accounts/register.html')
            
            if not all([address_street, address_number, neighborhood, city, state]):
                messages.error(request, 'Por favor, preencha o endereço completo.')
                return render(request, 'accounts/register.html')
            
            # Create user
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                
                UserProfile.objects.create(
                    user=user,
                    phone=phone,
                    zip_code=zip_code,
                    address_street=address_street,
                    address_number=address_number,
                    address_complement=address_complement,
                    neighborhood=neighborhood,
                    city=city,
                    state=state.upper()
                )
                
                # Transfer guest orders to user
                if request.session.session_key:
                    Order.objects.filter(
                        session_key=request.session.session_key,
                        user__isnull=True
                    ).update(user=user)
                
                # Login user
                login(request, user)
                
                logger.info(f"New user registered: {username}")
                messages.success(request, 'Conta criada com sucesso! Bem-vindo!')
                
                return redirect('home')
                
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            messages.error(request, 'Erro ao criar conta. Por favor, tente novamente.')
            return render(request, 'accounts/register.html')


class ProfileView(TemplateView):
    """View for user profile"""
    template_name = 'accounts/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.user.is_authenticated:
            user = self.request.user
            context['user'] = user
            
            # Get user orders
            context['orders'] = Order.objects.filter(
                user=user
            ).select_related('shipping_address').prefetch_related('items__product').order_by('-created_at')[:10]
            
            # Get order statistics
            context['total_orders'] = Order.objects.filter(user=user).count()
            context['pending_orders'] = Order.objects.filter(user=user, status='pending').count()
            context['completed_orders'] = Order.objects.filter(user=user, status='delivered').count()
        
        return context
