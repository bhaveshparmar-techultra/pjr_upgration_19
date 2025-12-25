# Copyright (C) 2016-Today GRAP (http://www.grap.coop)
# Copyright (C) 2016-Today La Louve (http://www.lalouve.net)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestBarcodesGeneratorProduct(TransactionCase):
    """Tests 'Barcodes Generator for Products'"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ProductTemplate = cls.env["product.template"]
        cls.ProductProduct = cls.env["product.product"]
        cls.BarcodeRule = cls.env["barcode.rule"]

        # Create barcode rules for testing
        cls.barcode_nomenclature = cls.env.ref(
            "barcodes.default_barcode_nomenclature"
        )

        cls.barcode_rule_manually = cls.BarcodeRule.create({
            "name": "Test Rule - Manual Product",
            "barcode_nomenclature_id": cls.barcode_nomenclature.id,
            "type": "product",
            "sequence": 997,
            "encoding": "ean13",
            "pattern": "20.....{NNNDD}",
            "generate_type": "manual",
            "generate_model": "product.product",
        })

        cls.barcode_rule_sequence = cls.BarcodeRule.create({
            "name": "Test Rule - Sequence Product",
            "barcode_nomenclature_id": cls.barcode_nomenclature.id,
            "type": "product",
            "sequence": 996,
            "encoding": "ean13",
            "pattern": "21.....{NNNDD}",
            "generate_type": "sequence",
            "generate_model": "product.product",
        })

    def test_01_manual_generation_template(self):
        """Test manual barcode generation for product template"""
        template = self.ProductTemplate.create({
            "name": "Test Template Mono Variant",
            "barcode_rule_id": self.barcode_rule_manually.id,
            "barcode_base": 54321,
        })
        template.generate_barcode()
        self.assertEqual(
            template.barcode,
            "2054321000001",
            "Incorrect Manual Barcode Generation for non varianted Template."
            " Pattern: %s - Base: %s"
            % (template.barcode_rule_id.pattern, template.barcode_base),
        )

    def test_02_manual_generation_product(self):
        """Test manual barcode generation for product variant"""
        template = self.ProductTemplate.create({
            "name": "Test Template Multi Variant",
        })
        product = self.ProductProduct.create({
            "name": "Test Variant 1",
            "product_tmpl_id": template.id,
            "barcode_rule_id": self.barcode_rule_manually.id,
            "barcode_base": 12345,
        })
        product.generate_barcode()
        self.assertEqual(
            product.barcode,
            "2012345000001",
            "Incorrect Manual Barcode Generation for varianted Product."
            " Pattern: %s - Base: %s"
            % (product.barcode_rule_id.pattern, product.barcode_base),
        )

    def test_03_sequence_generation_product(self):
        """Test sequence-based barcode generation for product"""
        product = self.ProductProduct.create({
            "name": "Test Product with Sequence",
            "barcode_rule_id": self.barcode_rule_sequence.id,
        })
        # Generate base using sequence
        product.generate_base()
        self.assertTrue(
            product.barcode_base > 0,
            "Barcode base should be generated from sequence",
        )
        # Generate barcode
        product.generate_barcode()
        self.assertTrue(
            product.barcode,
            "Barcode should be generated",
        )
        self.assertTrue(
            product.barcode.startswith("21"),
            "Barcode should start with pattern prefix '21'",
        )

    def test_04_generate_type_related_field(self):
        """Test that generate_type is correctly related from barcode_rule_id"""
        product = self.ProductProduct.create({
            "name": "Test Product Generate Type",
            "barcode_rule_id": self.barcode_rule_manually.id,
        })
        self.assertEqual(
            product.generate_type,
            "manual",
            "Generate type should be 'manual' from related barcode rule",
        )

    def test_05_barcode_rule_domain(self):
        """Test that barcode rule has correct generate_model"""
        self.assertEqual(
            self.barcode_rule_manually.generate_model,
            "product.product",
            "Barcode rule should have generate_model set to 'product.product'",
        )

    def test_06_template_generate_base(self):
        """Test generate_base on product template delegates to variant"""
        template = self.ProductTemplate.create({
            "name": "Test Template for Base Generation",
            "barcode_rule_id": self.barcode_rule_sequence.id,
        })
        template.generate_base()
        self.assertTrue(
            template.barcode_base > 0,
            "Template barcode_base should be set via variant",
        )

    def test_07_product_without_rule(self):
        """Test product without barcode rule"""
        product = self.ProductProduct.create({
            "name": "Test Product No Rule",
        })
        self.assertFalse(
            product.barcode_rule_id,
            "Product should have no barcode rule",
        )
        self.assertEqual(
            product.barcode_base,
            0,
            "Barcode base should be 0 without rule",
        )
