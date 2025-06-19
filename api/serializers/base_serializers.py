from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from ..models.base import Categoria, Torneo
from ..models.competicion import Jornada


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'


class JornadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Jornada
        fields = '__all__'


# Serializadores para Torneos
class TorneoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.ReadOnlyField(source='categoria.nombre')
    total_equipos = serializers.SerializerMethodField()
    
    class Meta:
        model = Torneo
        fields = '__all__'
    
    @extend_schema_field(serializers.IntegerField())
    def get_total_equipos(self, obj):
        return obj.equipos.filter(activo=True).count()
    
    def validate(self, data):
        """Validar que fecha_fin sea posterior a fecha_inicio"""
        if 'fecha_fin' in data and data.get('fecha_inicio') and data.get('fecha_fin'):
            if data['fecha_fin'] < data['fecha_inicio']:
                raise serializers.ValidationError({"fecha_fin": "La fecha de fin debe ser posterior a la fecha de inicio"})
        return data


class TorneoDetalleSerializer(serializers.ModelSerializer):
    categoria = CategoriaSerializer(read_only=True)
    total_equipos = serializers.SerializerMethodField()
    total_partidos = serializers.SerializerMethodField()
    partidos_jugados = serializers.SerializerMethodField()
    partidos_pendientes = serializers.SerializerMethodField()
    
    class Meta:
        model = Torneo
        fields = '__all__'
    
    @extend_schema_field(serializers.IntegerField())
    def get_total_equipos(self, obj):
        return obj.equipos.filter(activo=True).count()
    
    @extend_schema_field(serializers.IntegerField())
    def get_total_partidos(self, obj):
        return obj.partidos.count()
    
    @extend_schema_field(serializers.IntegerField())
    def get_partidos_jugados(self, obj):
        return obj.partidos.filter(completado=True).count()
    
    @extend_schema_field(serializers.IntegerField())
    def get_partidos_pendientes(self, obj):
        return obj.partidos.filter(completado=False).count()


class TorneoListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listado de torneos (solo campos esenciales)"""
    categoria_nombre = serializers.ReadOnlyField(source='categoria.nombre')
    
    class Meta:
        model = Torneo
        fields = [
            'id', 'nombre', 'categoria', 'categoria_nombre',
            'fecha_inicio', 'fecha_fin', 'activo', 'fase_actual'
        ]