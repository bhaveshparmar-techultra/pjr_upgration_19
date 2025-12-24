import base64
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResCompanyImage(TransactionCase):
    """Test cases for res.company.image model"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref('base.main_company')
        # Create a simple 1x1 pixel PNG image for testing
        cls.test_image = base64.b64encode(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00'
            b'\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00'
            b'\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        )

    def test_01_create_company_image(self):
        """Test creating a company image record"""
        company_image = self.env['res.company.image'].create({
            'name': 'Test Logo',
            'image': self.test_image,
            'company_id': self.company.id,
        })
        self.assertTrue(company_image.id, "Company image should be created")
        self.assertEqual(company_image.name, 'Test Logo')
        self.assertEqual(company_image.company_id, self.company)
        self.assertTrue(company_image.image, "Image should be stored")

    def test_02_company_image_required_fields(self):
        """Test that required fields are enforced"""
        with self.assertRaises(Exception):
            # Should fail without name
            self.env['res.company.image'].create({
                'image': self.test_image,
                'company_id': self.company.id,
            })

    def test_03_company_image_rec_name(self):
        """Test that rec_name is set to 'name'"""
        company_image = self.env['res.company.image'].create({
            'name': 'Logo for Display',
            'image': self.test_image,
            'company_id': self.company.id,
        })
        self.assertEqual(company_image.display_name, 'Logo for Display')

    def test_04_multiple_images_per_company(self):
        """Test that a company can have multiple images"""
        image1 = self.env['res.company.image'].create({
            'name': 'Logo 1',
            'image': self.test_image,
            'company_id': self.company.id,
        })
        image2 = self.env['res.company.image'].create({
            'name': 'Logo 2',
            'image': self.test_image,
            'company_id': self.company.id,
        })
        self.assertNotEqual(image1.id, image2.id)
        self.assertEqual(image1.company_id, image2.company_id)

    def test_05_search_company_image(self):
        """Test searching for company images"""
        self.env['res.company.image'].create({
            'name': 'Searchable Logo',
            'image': self.test_image,
            'company_id': self.company.id,
        })
        found = self.env['res.company.image'].search([
            ('name', 'ilike', 'Searchable')
        ])
        self.assertTrue(len(found) >= 1)
