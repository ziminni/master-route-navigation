import unittest
import os
import json
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
# project_root = (os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))
# if project_root not in sys.path:
#     sys.path.insert(0, project_root)
print(sys.path)


from .section_service import (
    SectionService,
    SectionValidationError,
    SectionStorageError,
    SectionNotFoundError
)

class TestSectionService(unittest.TestCase):
    
    def setUp(self):
        """Create service with test JSON file"""
        self.test_file = "test_data/test_sections.json"
        self.service = SectionService(self.test_file)
    
    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        if os.path.exists(f"{self.test_file}.tmp"):
            os.remove(f"{self.test_file}.tmp")
    
    # CREATE Tests
    def test_create_section_success(self):
        """Test successful section creation with all fields"""
        data = {
            "section": "3A",
            "program": "BS Computer Science",
            "curriculum": "2023-2024",
            "year": "3rd",
            "capacity": 40,
            "type": "Lecture",
            "remarks": "Regular"
        }
        result = self.service.create(data)
        
        # Verify auto-generated fields
        self.assertEqual(result['id'], 1)
        self.assertIsNotNone(result['created_at'])
        self.assertIsNotNone(result['updated_at'])
        
        # Verify input data preserved
        self.assertEqual(result['section'], "3A")
        self.assertEqual(result['capacity'], 40)
    
    def test_create_missing_required_field(self):
        """Test creation fails with missing required field"""
        data = {
            "section": "3A",
            "program": "BS CS"
            # Missing: curriculum, year, capacity, type, remarks
        }
        
        with self.assertRaises(SectionValidationError) as ctx:
            self.service.create(data)
        
        self.assertIn("Missing required fields", str(ctx.exception))
    
    def test_create_invalid_capacity(self):
        """Test creation fails with negative capacity"""
        data = {
            "section": "3A",
            "program": "BS CS",
            "curriculum": "2023",
            "year": "3rd",
            "capacity": -5,
            "type": "Lecture",
            "remarks": "Test"
        }
        
        with self.assertRaises(SectionValidationError) as ctx:
            self.service.create(data)
        
        self.assertIn("positive", str(ctx.exception).lower())
    
    def test_create_invalid_type(self):
        """Test creation fails with invalid type"""
        data = {
            "section": "3A",
            "program": "BS CS",
            "curriculum": "2023",
            "year": "3rd",
            "capacity": 40,
            "type": "InvalidType",
            "remarks": "Test"
        }
        
        with self.assertRaises(SectionValidationError) as ctx:
            self.service.create(data)
        
        self.assertIn("Invalid type", str(ctx.exception))
    
    def test_create_auto_increment_id(self):
        """Test ID auto-increments correctly"""
        data = {
            "section": "3A",
            "program": "BS CS",
            "curriculum": "2023",
            "year": "3rd",
            "capacity": 40,
            "type": "Lecture",
            "remarks": "Test"
        }
        
        first = self.service.create(data)
        self.assertEqual(first['id'], 1)
        
        data['section'] = "3B"
        second = self.service.create(data)
        self.assertEqual(second['id'], 2)
        
        data['section'] = "3C"
        third = self.service.create(data)
        self.assertEqual(third['id'], 3)
    
    # READ Tests
    def test_get_all_empty(self):
        """Test get_all returns empty list when no sections"""
        result = self.service.get_all()
        self.assertEqual(result, [])
    
    def test_get_all_multiple_sections(self):
        """Test get_all returns all sections"""
        # Create 3 sections
        for i in range(3):
            self.service.create({
                "section": f"3{chr(65+i)}",
                "program": "BS CS",
                "curriculum": "2023",
                "year": "3rd",
                "capacity": 40,
                "type": "Lecture",
                "remarks": "Test"
            })
        
        result = self.service.get_all()
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['section'], "3A")
        self.assertEqual(result[1]['section'], "3B")
        self.assertEqual(result[2]['section'], "3C")
    
    def test_get_by_id_found(self):
        """Test get_by_id returns correct section"""
        created = self.service.create({
            "section": "3A",
            "program": "BS CS",
            "curriculum": "2023",
            "year": "3rd",
            "capacity": 40,
            "type": "Lecture",
            "remarks": "Test"
        })
        
        result = self.service.get_by_id(created['id'])
        self.assertIsNotNone(result)
        self.assertEqual(result['section'], "3A")
    
    def test_get_by_id_not_found(self):
        """Test get_by_id returns None for non-existent ID"""
        result = self.service.get_by_id(999)
        self.assertIsNone(result)
    
    # UPDATE Tests
    def test_update_section_success(self):
        """Test successful section update"""
        created = self.service.create({
            "section": "3A",
            "program": "BS CS",
            "curriculum": "2023",
            "year": "3rd",
            "capacity": 40,
            "type": "Lecture",
            "remarks": "Test"
        })
        
        updated = self.service.update(created['id'], {
            "capacity": 50,
            "remarks": "Updated"
        })
        
        self.assertEqual(updated['capacity'], 50)
        self.assertEqual(updated['remarks'], "Updated")
        self.assertEqual(updated['section'], "3A")  # Unchanged
        self.assertNotEqual(updated['updated_at'], created['updated_at'])
    
    def test_update_nonexistent_section(self):
        """Test update fails for non-existent section"""
        with self.assertRaises(SectionNotFoundError):
            self.service.update(999, {"capacity": 50})
    
    def test_update_preserves_id(self):
        """Test update cannot change section ID"""
        created = self.service.create({
            "section": "3A",
            "program": "BS CS",
            "curriculum": "2023",
            "year": "3rd",
            "capacity": 40,
            "type": "Lecture",
            "remarks": "Test"
        })
        
        # Try to change ID (should be ignored)
        updated = self.service.update(created['id'], {
            "id": 999,
            "capacity": 50
        })
        
        self.assertEqual(updated['id'], created['id'])  # ID unchanged
    
    def test_update_preserves_created_at(self):
        """Test update preserves original created_at"""
        created = self.service.create({
            "section": "3A",
            "program": "BS CS",
            "curriculum": "2023",
            "year": "3rd",
            "capacity": 40,
            "type": "Lecture",
            "remarks": "Test"
        })
        
        updated = self.service.update(created['id'], {"capacity": 50})
        
        self.assertEqual(updated['created_at'], created['created_at'])
    
    # DELETE Tests
    def test_delete_section_success(self):
        """Test successful section deletion"""
        created = self.service.create({
            "section": "3A",
            "program": "BS CS",
            "curriculum": "2023",
            "year": "3rd",
            "capacity": 40,
            "type": "Lecture",
            "remarks": "Test"
        })
        
        result = self.service.delete(created['id'])
        self.assertTrue(result)
        
        # Verify actually deleted
        sections = self.service.get_all()
        self.assertEqual(len(sections), 0)
    
    def test_delete_nonexistent_section(self):
        """Test delete returns False for non-existent section"""
        result = self.service.delete(999)
        self.assertFalse(result)
    
    def test_delete_preserves_other_sections(self):
        """Test delete only removes target section"""
        s1 = self.service.create({
            "section": "3A", "program": "BS CS", "curriculum": "2023",
            "year": "3rd", "capacity": 40, "type": "Lecture", "remarks": "Test"
        })
        s2 = self.service.create({
            "section": "3B", "program": "BS CS", "curriculum": "2023",
            "year": "3rd", "capacity": 40, "type": "Lecture", "remarks": "Test"
        })
        s3 = self.service.create({
            "section": "3C", "program": "BS CS", "curriculum": "2023",
            "year": "3rd", "capacity": 40, "type": "Lecture", "remarks": "Test"
        })
        
        # Delete middle section
        self.service.delete(s2['id'])
        
        sections = self.service.get_all()
        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0]['id'], s1['id'])
        self.assertEqual(sections[1]['id'], s3['id'])
    
    # SEARCH Tests
    def test_search_single_criteria(self):
        """Test search with single filter"""
        self.service.create({
            "section": "3A", "program": "BS CS", "curriculum": "2023",
            "year": "3rd", "capacity": 40, "type": "Lecture", "remarks": "Test"
        })
        self.service.create({
            "section": "4A", "program": "BS IT", "curriculum": "2023",
            "year": "4th", "capacity": 35, "type": "Laboratory", "remarks": "Test"
        })
        
        results = self.service.search({"year": "3rd"})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['section'], "3A")
    
    def test_search_multiple_criteria(self):
        """Test search with multiple filters (AND logic)"""
        self.service.create({
            "section": "3A", "program": "BS CS", "curriculum": "2023",
            "year": "3rd", "capacity": 40, "type": "Lecture", "remarks": "Test"
        })
        self.service.create({
            "section": "3B", "program": "BS CS", "curriculum": "2023",
            "year": "3rd", "capacity": 35, "type": "Laboratory", "remarks": "Test"
        })
        
        results = self.service.search({
            "program": "BS CS",
            "year": "3rd",
            "type": "Laboratory"
        })
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['section'], "3B")
    
    def test_search_no_matches(self):
        """Test search returns empty list when no matches"""
        self.service.create({
            "section": "3A", "program": "BS CS", "curriculum": "2023",
            "year": "3rd", "capacity": 40, "type": "Lecture", "remarks": "Test"
        })
        
        results = self.service.search({"year": "5th"})
        self.assertEqual(len(results), 0)
    
    # EDGE CASES
    def test_data_persistence_across_instances(self):
        """Test data persists when creating new service instance"""
        # Create section with first instance
        service1 = SectionService(self.test_file)
        created = service1.create({
            "section": "3A", "program": "BS CS", "curriculum": "2023",
            "year": "3rd", "capacity": 40, "type": "Lecture", "remarks": "Test"
        })
        
        # Create new instance and verify data exists
        service2 = SectionService(self.test_file)
        result = service2.get_by_id(created['id'])
        self.assertIsNotNone(result)
        self.assertEqual(result['section'], "3A")
    
    def test_concurrent_operations_simulation(self):
        """Test multiple operations in sequence"""
        # Create
        s1 = self.service.create({
            "section": "3A", "program": "BS CS", "curriculum": "2023",
            "year": "3rd", "capacity": 40, "type": "Lecture", "remarks": "Test"
        })
        
        # Update
        self.service.update(s1['id'], {"capacity": 50})
        
        # Create another
        s2 = self.service.create({
            "section": "3B", "program": "BS CS", "curriculum": "2023",
            "year": "3rd", "capacity": 40, "type": "Lecture", "remarks": "Test"
        })
        
        # Delete first
        self.service.delete(s1['id'])
        
        # Verify final state
        sections = self.service.get_all()
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0]['id'], s2['id'])

# Run tests
if __name__ == '__main__':
    unittest.main()