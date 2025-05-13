"""
Pruebas para los modelos financieros del sistema GoolStar.
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from api.models.base import Categoria, Torneo
from api.models.participantes import Equipo, Arbitro, Jugador
from api.models.competicion import Partido, Tarjeta
from api.models.financiero import TipoTransaccion, TransaccionPago, PagoArbitro


class TransaccionPagoModelTest(TestCase):
    """Pruebas para el modelo TransaccionPago."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.categoria = Categoria.objects.create(nombre="VARONES", costo_inscripcion=Decimal('100.00'))
        self.torneo = Torneo.objects.create(nombre="Torneo", categoria=self.categoria, fecha_inicio=timezone.now().date())
        self.equipo = Equipo.objects.create(nombre="Equipo", categoria=self.categoria, torneo=self.torneo)
        self.jugador = Jugador.objects.create(
            primer_nombre="Carlos", primer_apellido="Gómez", 
            cedula="1234567890", equipo=self.equipo, numero_dorsal=10
        )
        self.rival = Equipo.objects.create(nombre="Rival", categoria=self.categoria, torneo=self.torneo)
        self.partido = Partido.objects.create(
            torneo=self.torneo, equipo_1=self.equipo, equipo_2=self.rival, fecha=timezone.now()
        )
        
        # Crear transacciones de diferentes tipos
        self.abono = TransaccionPago.objects.create(
            equipo=self.equipo,
            tipo=TipoTransaccion.ABONO_INSCRIPCION,
            monto=Decimal('50.00'),
            es_ingreso=True,
            concepto="Abono inicial"
        )
        
        self.pago_arbitro = TransaccionPago.objects.create(
            equipo=self.equipo,
            partido=self.partido,
            tipo=TipoTransaccion.PAGO_ARBITRO,
            monto=Decimal('10.00'),
            es_ingreso=False,
            concepto="Pago árbitro partido 1"
        )
        
        # Crear tarjeta para multa
        self.tarjeta = Tarjeta.objects.create(
            jugador=self.jugador,
            partido=self.partido,
            tipo=Tarjeta.Tipo.AMARILLA
        )
        
        self.multa = TransaccionPago.objects.create(
            equipo=self.equipo,
            partido=self.partido,
            tipo=TipoTransaccion.MULTA_AMARILLA,
            monto=Decimal('2.00'),
            es_ingreso=True,
            concepto="Multa por tarjeta amarilla",
            tarjeta=self.tarjeta,
            jugador=self.jugador
        )

    def test_transaccion_abono_creation(self):
        """Verifica que la transacción de abono se crea correctamente."""
        self.assertEqual(self.abono.equipo, self.equipo)
        self.assertIsNone(self.abono.partido)
        self.assertEqual(self.abono.tipo, "abono_inscripcion")
        self.assertEqual(self.abono.monto, Decimal('50.00'))
        self.assertTrue(self.abono.es_ingreso)
        self.assertEqual(self.abono.concepto, "Abono inicial")
        self.assertIsNone(self.abono.tarjeta)
        self.assertIsNone(self.abono.jugador)

    def test_transaccion_pago_arbitro_creation(self):
        """Verifica que la transacción de pago a árbitro se crea correctamente."""
        self.assertEqual(self.pago_arbitro.equipo, self.equipo)
        self.assertEqual(self.pago_arbitro.partido, self.partido)
        self.assertEqual(self.pago_arbitro.tipo, "pago_arbitro")
        self.assertEqual(self.pago_arbitro.monto, Decimal('10.00'))
        self.assertFalse(self.pago_arbitro.es_ingreso)
        self.assertEqual(self.pago_arbitro.concepto, "Pago árbitro partido 1")

    def test_transaccion_multa_creation(self):
        """Verifica que la transacción de multa se crea correctamente."""
        self.assertEqual(self.multa.equipo, self.equipo)
        self.assertEqual(self.multa.partido, self.partido)
        self.assertEqual(self.multa.tipo, "multa_amarilla")
        self.assertEqual(self.multa.monto, Decimal('2.00'))
        self.assertTrue(self.multa.es_ingreso)
        self.assertEqual(self.multa.tarjeta, self.tarjeta)
        self.assertEqual(self.multa.jugador, self.jugador)

    def test_transaccion_str(self):
        """Verifica que el método __str__ funcione correctamente."""
        self.assertEqual(str(self.abono), "Equipo - Abono a Inscripción - $50.00")
        self.assertEqual(str(self.pago_arbitro), "Equipo - Pago de Árbitro - $10.00")
        self.assertEqual(str(self.multa), "Equipo - Multa por Tarjeta Amarilla - $2.00")

    def test_es_ingreso_property(self):
        """Verifica que la propiedad es_ingreso funcione correctamente."""
        self.assertTrue(self.abono.es_ingreso)
        self.assertTrue(self.multa.es_ingreso)
        self.assertFalse(self.pago_arbitro.es_ingreso)

    def test_es_gasto_property(self):
        """Verifica que la propiedad es_gasto funcione correctamente."""
        self.assertFalse(self.abono.es_gasto)
        self.assertFalse(self.multa.es_gasto)
        self.assertTrue(self.pago_arbitro.es_gasto)


class PagoArbitroModelTest(TestCase):
    """Pruebas para el modelo PagoArbitro."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.categoria = Categoria.objects.create(nombre="VARONES", costo_arbitraje=Decimal('10.00'))
        self.torneo = Torneo.objects.create(nombre="Torneo", categoria=self.categoria, fecha_inicio=timezone.now().date())
        self.equipo1 = Equipo.objects.create(nombre="Equipo 1", categoria=self.categoria, torneo=self.torneo)
        self.equipo2 = Equipo.objects.create(nombre="Equipo 2", categoria=self.categoria, torneo=self.torneo)
        self.arbitro = Arbitro.objects.create(nombres="Roberto", apellidos="Martínez")
        
        self.partido = Partido.objects.create(
            torneo=self.torneo, 
            equipo_1=self.equipo1, 
            equipo_2=self.equipo2, 
            arbitro=self.arbitro,
            fecha=timezone.now()
        )
        
        self.pago_equipo1 = PagoArbitro.objects.create(
            arbitro=self.arbitro,
            partido=self.partido,
            equipo=self.equipo1,
            monto=Decimal('5.00'),
            pagado=False
        )
        
        self.pago_equipo2 = PagoArbitro.objects.create(
            arbitro=self.arbitro,
            partido=self.partido,
            equipo=self.equipo2,
            monto=Decimal('5.00'),
            pagado=True,
            metodo_pago="Efectivo"
        )

    def test_pago_arbitro_creation(self):
        """Verifica que el pago a árbitro se crea correctamente."""
        self.assertEqual(self.pago_equipo1.arbitro, self.arbitro)
        self.assertEqual(self.pago_equipo1.partido, self.partido)
        self.assertEqual(self.pago_equipo1.equipo, self.equipo1)
        self.assertEqual(self.pago_equipo1.monto, Decimal('5.00'))
        self.assertFalse(self.pago_equipo1.pagado)
        self.assertIsNone(self.pago_equipo1.fecha_pago)
        self.assertEqual(self.pago_equipo1.metodo_pago, "")

    def test_pago_arbitro_pagado_creation(self):
        """Verifica que el pago a árbitro pagado se crea correctamente."""
        self.assertEqual(self.pago_equipo2.arbitro, self.arbitro)
        self.assertEqual(self.pago_equipo2.partido, self.partido)
        self.assertEqual(self.pago_equipo2.equipo, self.equipo2)
        self.assertEqual(self.pago_equipo2.monto, Decimal('5.00'))
        self.assertTrue(self.pago_equipo2.pagado)
        self.assertIsNotNone(self.pago_equipo2.fecha_pago)
        self.assertEqual(self.pago_equipo2.metodo_pago, "Efectivo")

    def test_pago_arbitro_str(self):
        """Verifica que el método __str__ funcione correctamente."""
        self.assertEqual(
            str(self.pago_equipo1), 
            f"Pago a {self.arbitro} por {self.equipo1.nombre} - {self.partido}"
        )

    def test_actualizar_estado_partido(self):
        """Verifica que se actualice el estado de pago en el partido."""
        # Verificar estado inicial
        self.assertFalse(self.partido.equipo_1_pago_arbitro)
        self.assertTrue(self.partido.equipo_2_pago_arbitro)
        
        # Marcar como pagado el pago del equipo 1
        self.pago_equipo1.pagado = True
        self.pago_equipo1.save()
        
        # Refrescar el partido desde la base de datos
        self.partido.refresh_from_db()
        
        # Verificar que se actualizó el estado
        self.assertTrue(self.partido.equipo_1_pago_arbitro)
        self.assertTrue(self.partido.equipo_2_pago_arbitro)
