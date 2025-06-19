from rest_framework import serializers
from ..models.competicion import Partido, Gol, Tarjeta
from .base_serializers import JornadaSerializer
from .participantes_serializers import EquipoSerializer


class PartidoSerializer(serializers.ModelSerializer):
    equipo_1_nombre = serializers.ReadOnlyField(source='equipo_1.nombre')
    equipo_2_nombre = serializers.ReadOnlyField(source='equipo_2.nombre')
    jornada_nombre = serializers.ReadOnlyField(source='jornada.nombre', default=None)
    
    class Meta:
        model = Partido
        fields = '__all__'


class GolSerializer(serializers.ModelSerializer):
    jugador_nombre = serializers.ReadOnlyField(source='jugador.__str__')
    partido_descripcion = serializers.ReadOnlyField(source='partido.__str__')
    
    # Campos optimizados para reducir consultas adicionales
    equipo_nombre = serializers.ReadOnlyField(source='jugador.equipo.nombre')
    torneo_nombre = serializers.ReadOnlyField(source='partido.torneo.nombre')
    fecha_partido = serializers.SerializerMethodField()
    
    class Meta:
        model = Gol
        fields = '__all__'
        
    def get_fecha_partido(self, obj):
        """Retorna la fecha del partido formateada"""
        if hasattr(obj, 'partido') and obj.partido and hasattr(obj.partido, 'fecha'):
            return obj.partido.fecha.strftime('%d/%m/%Y %H:%M')
        return None


class TarjetaSerializer(serializers.ModelSerializer):
    jugador_nombre = serializers.ReadOnlyField(source='jugador.__str__')
    partido_descripcion = serializers.ReadOnlyField(source='partido.__str__')
    
    class Meta:
        model = Tarjeta
        fields = '__all__'


# Serializadores anidados para mostrar información más detallada
class PartidoDetalleSerializer(serializers.ModelSerializer):
    equipo_1 = EquipoSerializer(read_only=True)
    equipo_2 = EquipoSerializer(read_only=True)
    jornada = JornadaSerializer(read_only=True)
    goles = GolSerializer(many=True, read_only=True)
    tarjetas = TarjetaSerializer(many=True, read_only=True)
    
    class Meta:
        model = Partido
        fields = '__all__'


# ============ SERIALIZERS OPTIMIZADOS ============

class PartidoListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listado de partidos (solo campos esenciales)"""
    equipo_1_nombre = serializers.ReadOnlyField(source='equipo_1.nombre')
    equipo_2_nombre = serializers.ReadOnlyField(source='equipo_2.nombre')
    
    class Meta:
        model = Partido
        fields = [
            'id', 'fecha', 'equipo_1', 'equipo_1_nombre', 
            'equipo_2', 'equipo_2_nombre', 'goles_equipo_1', 
            'goles_equipo_2', 'completado'
        ]


class GolListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listado de goles (solo campos esenciales)"""
    jugador_nombre = serializers.ReadOnlyField(source='jugador.__str__')
    equipo_nombre = serializers.ReadOnlyField(source='jugador.equipo.nombre')
    
    class Meta:
        model = Gol
        fields = [
            'id', 'jugador', 'jugador_nombre', 'equipo_nombre',
            'partido', 'minuto', 'autogol'
        ]


class TarjetaListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listado de tarjetas (solo campos esenciales)"""
    jugador_nombre = serializers.ReadOnlyField(source='jugador.__str__')
    equipo_nombre = serializers.ReadOnlyField(source='jugador.equipo.nombre')
    
    class Meta:
        model = Tarjeta
        fields = [
            'id', 'jugador', 'jugador_nombre', 'equipo_nombre',
            'partido', 'tipo', 'fecha', 'pagada'
        ]