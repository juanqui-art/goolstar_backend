from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

# Clases de throttling personalizadas para endpoints críticos
class LoginRateThrottle(AnonRateThrottle):
    """
    Rate limiting específico para login: máximo 5 intentos por minuto por IP.
    Previene ataques de fuerza bruta en autenticación.
    """
    scope = 'login'

class RegisterRateThrottle(AnonRateThrottle):
    """
    Rate limiting específico para registro: máximo 3 registros por minuto por IP.
    Previene spam de cuentas y abuso del sistema de registro.
    """
    scope = 'register'

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vista personalizada para obtener pares de tokens JWT.
    Extiende la vista TokenObtainPairView para devolver información adicional del usuario.
    Con rate limiting: máximo 5 intentos de login por minuto por IP.
    """
    throttle_classes = [LoginRateThrottle]
    
    def post(self, request, *args, **kwargs):
        """
        Obtiene un par de tokens JWT (access y refresh) tras la autenticación.
        
        Parámetros requeridos en el body:
        - username: nombre de usuario
        - password: contraseña
        
        Retorna:
        - access: Token JWT de acceso (corta duración)
        - refresh: Token JWT de refresco (larga duración)
        - user_id: ID del usuario autenticado
        - email: Correo del usuario (si existe)
        - is_staff: Indica si el usuario es staff o no
        """
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == status.HTTP_200_OK:
            user = User.objects.get(username=request.data.get('username'))
            response.data['user_id'] = user.id
            response.data['email'] = user.email
            response.data['is_staff'] = user.is_staff
            
        return response

class RegistroUsuarioView(APIView):
    """
    Vista para registrar nuevos usuarios en el sistema.
    Con rate limiting: máximo 3 registros por minuto por IP.
    """
    permission_classes = [AllowAny]
    throttle_classes = [RegisterRateThrottle]
    
    def post(self, request):
        """
        Registra un nuevo usuario y devuelve sus tokens JWT.
        
        Parámetros requeridos en el body:
        - username: nombre de usuario único
        - password: contraseña
        - email: correo electrónico (opcional)
        
        Retorna:
        - access: Token JWT de acceso
        - refresh: Token JWT de refresco
        - user_id: ID del usuario creado
        - email: Correo del usuario
        """
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email', '')
        
        # Validaciones básicas
        if not username or not password:
            return Response(
                {'error': 'Username y password son obligatorios'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Verificar si el usuario ya existe
        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'El usuario ya existe'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Crear el usuario
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Generar tokens JWT para el usuario
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user_id': user.id,
            'email': user.email
        }, status=status.HTTP_201_CREATED)
