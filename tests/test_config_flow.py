"""Tests for config_flow validation helpers."""
from custom_components.eau_grand_lyon.config_flow import _is_valid_email


class TestIsValidEmail:
    def test_valid_email(self):
        assert _is_valid_email("user@example.com")

    def test_strips_whitespace(self):
        assert _is_valid_email("  user@example.com  ")

    def test_subdomain_email(self):
        assert _is_valid_email("user@mail.example.co.uk")

    def test_plus_tag(self):
        assert _is_valid_email("user+tag@example.com")

    def test_missing_at(self):
        assert not _is_valid_email("notanemail")

    def test_missing_domain(self):
        assert not _is_valid_email("user@")

    def test_missing_local(self):
        assert not _is_valid_email("@example.com")

    def test_empty_string(self):
        assert not _is_valid_email("")

    def test_spaces_only(self):
        assert not _is_valid_email("   ")

    def test_none(self):
        assert not _is_valid_email(None)
