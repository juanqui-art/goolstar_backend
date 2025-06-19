from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from ..models.participantes import Equipo, Jugador, JugadorDocumento
from .base_serializers import CategoriaSerializer


class EquipoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.ReadOnlyField(source='categoria.nombre')
    
    class Meta:
        model = Equipo
        fields = '__all__'


class JugadorSerializer(serializers.ModelSerializer):
    equipo_nombre = serializers.ReadOnlyField(source='equipo.nombre')
    nombre_completo = serializers.SerializerMethodField()
    
    class Meta:
        model = Jugador
        fields = '__all__'
    
    @extend_schema_field(serializers.CharField())
    def get_nombre_completo(self, obj):
        nombres = f"{obj.primer_nombre} {obj.segundo_nombre or ''}".strip()
        apellidos = f"{obj.primer_apellido} {obj.segundo_apellido or ''}".strip()
        return f"{nombres} {apellidos}".strip()


# Serializadores anidados para mostrar información más detallada
class EquipoDetalleSerializer(serializers.ModelSerializer):
    categoria = CategoriaSerializer(read_only=True)
    jugadores = JugadorSerializer(many=True, read_only=True)
    
    class Meta:
        model = Equipo
        fields = '__all__'


# ============ SERIALIZERS OPTIMIZADOS ============
# Versiones optimizadas para mejorar rendimiento de respuestas

class EquipoListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listado de equipos (solo campos esenciales)"""
    categoria_nombre = serializers.ReadOnlyField(source='categoria.nombre')
    
    class Meta:
        model = Equipo
        fields = [
            'id', 'nombre', 'categoria', 'categoria_nombre', 
            'activo', 'estado', 'fecha_registro'
        ]


class JugadorListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listado de jugadores (solo campos esenciales)"""
    equipo_nombre = serializers.ReadOnlyField(source='equipo.nombre')
    
    class Meta:
        model = Jugador
        fields = [
            'id', 'primer_nombre', 'primer_apellido', 'segundo_apellido',
            'cedula', 'equipo', 'equipo_nombre', 'numero_dorsal', 'posicion'
        ]


# ============ SERIALIZER ACTUALIZADO PARA JUGADOR CON DOCUMENTOS ============

# Forward declaration para evitar import circular
class JugadorDocumentoListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listado de documentos (solo campos esenciales)."""
    
    jugador_nombre = serializers.ReadOnlyField(source='jugador.nombre_completo')
    tipo_documento_display = serializers.ReadOnlyField(source='get_tipo_documento_display')
    estado_verificacion_display = serializers.ReadOnlyField(source='get_estado_verificacion_display')
    tamaño_archivo_mb = serializers.ReadOnlyField()
    
    class Meta:
        model = JugadorDocumento
        fields = [
            'id', 'jugador', 'jugador_nombre', 'tipo_documento', 'tipo_documento_display',
            'estado_verificacion', 'estado_verificacion_display', 'fecha_subida',
            'tamaño_archivo_mb', 'formato_archivo'
        ]


class JugadorConDocumentosSerializer(JugadorSerializer):
    """Extiende JugadorSerializer para incluir documentos relacionados."""
    
    documentos = JugadorDocumentoListSerializer(many=True, read_only=True)
    total_documentos = serializers.SerializerMethodField()
    documentos_verificados = serializers.SerializerMethodField()
    documentos_pendientes = serializers.SerializerMethodField()
    
    class Meta(JugadorSerializer.Meta):
        # Como JugadorSerializer usa '__all__', mantenemos eso y agregamos los campos extra
        fields = '__all__'
    
    @extend_schema_field(serializers.IntegerField())
    def get_total_documentos(self, obj):
        """Obtener total de documentos del jugador."""
        return obj.documentos.count()
    
    @extend_schema_field(serializers.IntegerField())
    def get_documentos_verificados(self, obj):
        """Obtener total de documentos verificados."""
        return obj.documentos.filter(
            estado_verificacion=JugadorDocumento.EstadoVerificacion.VERIFICADO
        ).count()
    
    @extend_schema_field(serializers.IntegerField())
    def get_documentos_pendientes(self, obj):
        """Obtener total de documentos pendientes."""
        return obj.documentos.filter(
            estado_verificacion=JugadorDocumento.EstadoVerificacion.PENDIENTE
        ).count()