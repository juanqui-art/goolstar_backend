from rest_framework import serializers
from ..models.participantes import JugadorDocumento


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