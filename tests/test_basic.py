"""
Basic unit tests for openrouter-free-agents.
Runs without requiring external API network calls.
"""

import unittest
from core.roles import ROLE_PRESETS


class TestRoles(unittest.TestCase):
    def test_default_roles_exist(self):
        self.assertIn("coder", ROLE_PRESETS)
        self.assertIn("architect", ROLE_PRESETS)
        self.assertIn("security", ROLE_PRESETS)
        self.assertIn("general", ROLE_PRESETS)

    def test_role_structure(self):
        for role_name, config in ROLE_PRESETS.items():
            self.assertIn("system_prompt", config, f"Role {role_name} missing system_prompt")
            self.assertIn("preferred_models", config, f"Role {role_name} missing preferred_models")
            self.assertTrue(len(config["preferred_models"]) > 0, f"Role {role_name} has empty preferred_models")
            self.assertIsInstance(config.get("temperature", 0.2), (int, float))


if __name__ == "__main__":
    unittest.main()
