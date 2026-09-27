"""Offline metadata regressions: python -m unittest discover -s scripts."""
import unittest
import xml.etree.ElementTree as ET

from optimize_svg import optimize


class OptimizerTests(unittest.TestCase):
    def test_expanded_editor_attributes_are_removed(self):
        source = '''<svg xmlns="http://www.w3.org/2000/svg"
          xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
          inkscape:version="1" xml:space="preserve">
          <title>Example</title><g inkscape:label="Layer">
          <path stroke="currentColor" d="M0 0L2 2"/></g></svg>'''
        result = optimize(source)
        self.assertNotIn("inkscape", result)
        self.assertNotIn("xml:space", result)
        self.assertIn('stroke="currentColor"', result)

    def test_nested_metadata_is_removed_but_referenced_defs_survive(self):
        source = '''<svg xmlns="http://www.w3.org/2000/svg">
          <title>Example</title><g><metadata>editor data</metadata>
          <defs><clipPath id="crop"><rect width="24" height="24"/></clipPath></defs>
          <path clip-path="url(#crop)" stroke="currentColor" d="M0 0L2 2"/>
          <defs><metadata>empty after cleanup</metadata></defs></g></svg>'''
        root = ET.fromstring(optimize(source))
        ns = {"svg": "http://www.w3.org/2000/svg"}
        self.assertEqual(root.findall(".//svg:metadata", ns), [])
        self.assertEqual(len(root.findall(".//svg:defs", ns)), 1)
        self.assertEqual(root.find(".//svg:clipPath", ns).get("id"), "crop")


if __name__ == "__main__":
    unittest.main()
