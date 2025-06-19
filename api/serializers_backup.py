from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Categoria, Equipo, Jugador, Jornada, Partido, Gol, Tarjeta, JugadorDocumento
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


class TorneoListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listado de torneos (solo campos esenciales)"""
    categoria_nombre = serializers.ReadOnlyField(source='categoria.nombre')
    
    class Meta:
        model = Torneo
        fields = [
            'id', 'nombre', 'categoria', 'categoria_nombre',
            'fecha_inicio', 'fecha_fin', 'activo', 'fase_actual'
        ]


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


# ============ SERIALIZERS PARA DOCUMENTOS DE JUGADORES ============

class JugadorDocumentoSerializer(serializers.ModelSerializer):
    """Serializer completo para documentos de jugadores con validaciones de seguridad."""
    
    # Campos calculados
    jugador_nombre = serializers.ReadOnlyField(source='jugador.nombre_completo')
    tamaño_archivo_mb = serializers.ReadOnlyField()
    url_documento = serializers.ReadOnlyField()
    esta_verificado = serializers.ReadOnlyField()
    
    # Campos de metadatos para información adicional
    verificado_por_username = serializers.ReadOnlyField(source='verificado_por.username')
    tipo_documento_display = serializers.ReadOnlyField(source='get_tipo_documento_display')
    estado_verificacion_display = serializers.ReadOnlyField(source='get_estado_verificacion_display')
    
    class Meta:
        model = JugadorDocumento
        fields = [
            'id', 'jugador', 'jugador_nombre', 'tipo_documento', 'tipo_documento_display',
            'archivo_documento', 'url_documento', 'estado_verificacion', 'estado_verificacion_display',
            'verificado_por', 'verificado_por_username', 'fecha_verificacion', 'comentarios_verificacion',
            'fecha_subida', 'fecha_actualizacion', 'tamaño_archivo', 'tamaño_archivo_mb',
            'formato_archivo', 'esta_verificado'
        ]
        read_only_fields = [
            'id', 'fecha_subida', 'fecha_actualizacion', 'tamaño_archivo', 
            'formato_archivo', 'verificado_por', 'fecha_verificacion'
        ]
    
    def validate_archivo_documento(self, value):
        """
        Validación adicional del archivo en el serializer.
        Las validaciones principales están en el modelo y validators.py
        """
        if value:
            # Verificar que el archivo tenga contenido
            if not hasattr(value, 'file') or not value.file:
                raise serializers.ValidationError("El archivo está vacío o corrupto.")
            
            # Verificar tamaño mínimo razonable (1KB)
            if hasattr(value.file, 'size') and value.file.size < 1024:
                raise serializers.ValidationError("El archivo es demasiado pequeño para ser un documento válido.")
        
        return value
    
    def validate(self, data):
        """
        Validación a nivel de serializer para reglas de negocio específicas.
        """
        # Validar que no se duplique el tipo de documento para el mismo jugador
        if 'jugador' in data and 'tipo_documento' in data:
            jugador = data['jugador']
            tipo_documento = data['tipo_documento']
            
            # Verificar si ya existe un documento del mismo tipo no rechazado
            existing_docs = JugadorDocumento.objects.filter(
                jugador=jugador,
                tipo_documento=tipo_documento,
                estado_verificacion__in=['pendiente', 'verificado']
            )
            
            # Si es una actualización, excluir el documento actual
            if self.instance:
                existing_docs = existing_docs.exclude(id=self.instance.id)
            
            if existing_docs.exists():
                raise serializers.ValidationError({
                    'tipo_documento': f'Ya existe un documento de tipo {tipo_documento} para este jugador.'
                })
        
        return data


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


class JugadorDocumentoUploadSerializer(serializers.ModelSerializer):
    """Serializer específico para subida de documentos (campos mínimos)."""
    
    class Meta:
        model = JugadorDocumento
        fields = ['jugador', 'tipo_documento', 'archivo_documento']
    
    def validate(self, data):
        """Validación específica para upload."""
        # Reutilizar la validación del serializer principal
        return super().validate(data)


class JugadorDocumentoVerificationSerializer(serializers.ModelSerializer):
    """Serializer específico para verificación de documentos."""
    
    class Meta:
        model = JugadorDocumento
        fields = ['estado_verificacion', 'comentarios_verificacion']
    
    def validate_estado_verificacion(self, value):
        """Validar estados de verificación permitidos."""
        allowed_states = [
            JugadorDocumento.EstadoVerificacion.VERIFICADO,
            JugadorDocumento.EstadoVerificacion.RECHAZADO,
            JugadorDocumento.EstadoVerificacion.RESUBIR
        ]
        
        if value not in allowed_states:
            raise serializers.ValidationError(
                f'Estado no válido. Estados permitidos: {", ".join(allowed_states)}'
            )
        
        return value
    
    def validate(self, data):
        """Validar que se proporcionen comentarios para rechazo."""
        estado = data.get('estado_verificacion')
        comentarios = data.get('comentarios_verificacion', '').strip()
        
        if estado == JugadorDocumento.EstadoVerificacion.RECHAZADO and not comentarios:
            raise serializers.ValidationError({
                'comentarios_verificacion': 'Los comentarios son obligatorios al rechazar un documento.'
            })
        
        return data


# ============ SERIALIZER ACTUALIZADO PARA JUGADOR CON DOCUMENTOS ============

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
