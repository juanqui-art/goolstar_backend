from django.db import migrations

def mark_migrations_as_applied(apps, schema_editor):
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO django_migrations (app, name, applied) "
        "SELECT 'api', '0007_equipo_estado_equipo_fecha_retiro', NOW() "
        "WHERE NOT EXISTS (SELECT 1 FROM django_migrations WHERE app='api' AND name='0007_equipo_estado_equipo_fecha_retiro');"
    )
    cursor.execute(
        "INSERT INTO django_migrations (app, name, applied) "
        "SELECT 'api', '0008_fix_transaccionpago_fields', NOW() "
        "WHERE NOT EXISTS (SELECT 1 FROM django_migrations WHERE app='api' AND name='0008_fix_transaccionpago_fields');"
    )

class Migration(migrations.Migration):
    dependencies = [
        ('api', '0006_alter_jugador_nivel_alter_jugador_posicion'),
    ]

    operations = [
        migrations.RunPython(mark_migrations_as_applied),
    ]