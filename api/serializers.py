from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Categoria, Equipo, Jugador, Jornada, Partido, Gol, Tarjeta
from .models.base import Torneo
from .models.estadisticas import EstadisticaEquipo

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'

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

class JornadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Jornada
        fields = '__all__'

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
class EquipoDetalleSerializer(serializers.ModelSerializer):
    categoria = CategoriaSerializer(read_only=True)
    jugadores = JugadorSerializer(many=True, read_only=True)
    
    class Meta:
        model = Equipo
        fields = '__all__'

class PartidoDetalleSerializer(serializers.ModelSerializer):
    equipo_1 = EquipoSerializer(read_only=True)
    equipo_2 = EquipoSerializer(read_only=True)
    jornada = JornadaSerializer(read_only=True)
    goles = GolSerializer(many=True, read_only=True)
    tarjetas = TarjetaSerializer(many=True, read_only=True)
    
    class Meta:
        model = Partido
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

class EstadisticaEquipoSerializer(serializers.ModelSerializer):
    equipo_nombre = serializers.ReadOnlyField(source='equipo.nombre')
    
    class Meta:
        model = EstadisticaEquipo
        fields = [
            'id', 'equipo', 'equipo_nombre', 'torneo', 
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
