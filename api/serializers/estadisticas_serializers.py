from rest_framework import serializers
from ..models.estadisticas import EstadisticaEquipo


class EstadisticaEquipoSerializer(serializers.ModelSerializer):
    equipo_nombre = serializers.ReadOnlyField(source='equipo.nombre')
    grupo = serializers.ReadOnlyField(source='equipo.grupo')
    
    class Meta:
        model = EstadisticaEquipo
        fields = [
            'id', 'equipo', 'equipo_nombre', 'torneo',
            'grupo',
            'puntos', 'partidos_jugados', 'partidos_ganados', 'partidos_empatados', 'partidos_perdidos',
            'goles_favor', 'goles_contra', 'diferencia_goles',
            'tarjetas_amarillas', 'tarjetas_rojas'
        ]
        read_only_fields = fields


class TablaposicionesSerializer(serializers.Serializer):
    grupo = serializers.CharField(max_length=20, required=False)
    equipos = EstadisticaEquipoSerializer(many=True, read_only=True)
    
    class Meta:
        # Esto ayuda a drf-spectacular a generar mejores tipos
        ref_name = 'TablaPosiciones'


# ============ SERIALIZERS PARA ESTADÍSTICAS OPTIMIZADAS ============

class EstadisticaEquipoListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para tabla de posiciones (solo campos de estadísticas)"""
    equipo_nombre = serializers.ReadOnlyField(source='equipo.nombre')
    
    class Meta:
        model = EstadisticaEquipo
        fields = [
            'equipo', 'equipo_nombre', 'puntos', 'partidos_jugados',
            'partidos_ganados', 'partidos_empatados', 'partidos_perdidos',
            'goles_favor', 'goles_contra', 'diferencia_goles'
        ]


class TablaposicionesOptimizadaSerializer(serializers.Serializer):
    """Serializer optimizado para tabla de posiciones sin campos innecesarios"""
    grupo = serializers.CharField(max_length=20, required=False)
    equipos = EstadisticaEquipoListSerializer(many=True, read_only=True)
    
    class Meta:
        ref_name = 'TablaPosicionesOptimizada'