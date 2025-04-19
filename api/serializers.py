from rest_framework import serializers
from .models import Categoria, Equipo, Jugador, Jornada, Partido, Gol, Tarjeta

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
    
    class Meta:
        model = Gol
        fields = '__all__'

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
