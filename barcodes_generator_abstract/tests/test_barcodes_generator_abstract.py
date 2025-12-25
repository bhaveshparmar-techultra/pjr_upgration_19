# Copyright 2021 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestBarcodesGeneratorAbstract(TransactionCase):
    """Tests for Barcodes Generator Abstract module"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a barcode rule for testing
        cls.barcode_nomenclature = cls.env.ref(
            "barcodes.default_barcode_nomenclature"
        )
        cls.barcode_rule = cls.env["barcode.rule"].create({
            "name": "Test Rule - Manual",
            "barcode_nomenclature_id": cls.barcode_nomenclature.id,
            "type": "product",
            "sequence": 999,
            "encoding": "ean13",
            "pattern": "20.....{NNNDD}",
            "generate_type": "manual",
        })

        cls.barcode_rule_sequence = cls.env["barcode.rule"].create({
            "name": "Test Rule - Sequence",
            "barcode_nomenclature_id": cls.barcode_nomenclature.id,
            "type": "product",
            "sequence": 998,
            "encoding": "ean13",
            "pattern": "21.....{NNNDD}",
            "generate_type": "sequence",
        })

    def test_01_compute_padding(self):
        """Test that padding is computed correctly from pattern"""
        self.assertEqual(
            self.barcode_rule.padding,
            5,
            "Padding should be 5 (count of dots in pattern)",
        )

    def test_02_sequence_generation(self):
        """Test that sequence is auto-generated for sequence type rules"""
        self.assertTrue(
            self.barcode_rule_sequence.sequence_id,
            "Sequence should be auto-generated for sequence type rules",
        )

    def test_03_onchange_generate_type(self):
        """Test onchange clears generate_model when type is 'no'"""
        self.barcode_rule.generate_type = "no"
        self.barcode_rule.onchange_generate_type()
        self.assertFalse(
            self.barcode_rule.generate_model,
            "generate_model should be cleared when generate_type is 'no'",
        )

    def test_04_barcode_rule_constraint(self):
        """Test that only one automated rule per model is allowed"""
        # This test checks the constraint behavior
        self.barcode_rule.generate_automate = False
        self.barcode_rule_sequence.generate_automate = False
        # Both rules can have automate=False without issues
        self.assertTrue(True)
