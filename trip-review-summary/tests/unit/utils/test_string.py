"""Unit tests for string utilities."""

from review_summary.utils.string import clean_str


class TestCleanStr:
    """Test suite for clean_str function."""

    def test_basic_string(self) -> None:
        """Test cleaning a basic string without special characters."""
        result = clean_str("Hello World")
        assert result == "Hello World"

    def test_html_escape_sequences(self) -> None:
        """Test unescaping HTML escape sequences."""
        result = clean_str("&lt;div&gt;Hello&lt;/div&gt;")
        assert result == "<div>Hello</div>"

    def test_html_entities(self) -> None:
        """Test unescaping common HTML entities."""
        result = clean_str("&amp; &quot; &#39; &copy;")
        assert result == "& \" ' ©"

    def test_leading_trailing_whitespace(self) -> None:
        """Test removal of leading and trailing whitespace."""
        result = clean_str("  Hello World  ")
        assert result == "Hello World"

    def test_control_characters_removal(self) -> None:
        """Test removal of control characters (0x00-0x1f)."""
        # Including null, tab, newline, carriage return
        result = clean_str("Hello\x00\x01\x02World")
        assert result == "HelloWorld"

    def test_newline_and_tab_removal(self) -> None:
        """Test removal of newline and tab characters."""
        result = clean_str("Hello\nWorld\tTest")
        assert result == "HelloWorldTest"

    def test_extended_control_characters(self) -> None:
        """Test removal of extended control characters (0x7f-0x9f)."""
        result = clean_str("Hello\x7f\x80\x9fWorld")
        assert result == "HelloWorld"

    def test_combined_html_and_control_chars(self) -> None:
        """Test cleaning string with both HTML entities and control chars."""
        result = clean_str("&lt;tag&gt;\nHello\x00World")
        assert result == "<tag>HelloWorld"

    def test_empty_string(self) -> None:
        """Test cleaning an empty string."""
        result = clean_str("")
        assert result == ""

    def test_whitespace_only_string(self) -> None:
        """Test cleaning a string with only whitespace."""
        result = clean_str("   \t\n   ")
        assert result == ""

    def test_unicode_characters_preserved(self) -> None:
        """Test that valid Unicode characters are preserved."""
        result = clean_str("你好世界 🌍 Привет")
        assert result == "你好世界 🌍 Привет"

    def test_numeric_html_entities(self) -> None:
        """Test numeric HTML entities."""
        result = clean_str("&#65;&#66;&#67;")
        assert result == "ABC"

    def test_hex_html_entities(self) -> None:
        """Test hexadecimal HTML entities."""
        result = clean_str("&#x41;&#x42;&#x43;")
        assert result == "ABC"

    def test_multiple_spaces_preserved(self) -> None:
        """Test that internal multiple spaces are preserved."""
        result = clean_str("Hello  World")
        assert result == "Hello  World"

    def test_real_world_html_snippet(self) -> None:
        """Test cleaning a real-world HTML snippet."""
        input_str = "  &lt;p&gt;This is a &quot;test&quot;&lt;/p&gt;\n  "
        result = clean_str(input_str)
        assert result == '<p>This is a "test"</p>'

    def test_mixed_control_characters(self) -> None:
        """Test various control characters in one string."""
        result = clean_str("Start\x01\x02\x03\x1f\x7f\x9fEnd")
        assert result == "StartEnd"

    def test_carriage_return_linefeed(self) -> None:
        """Test removal of CRLF sequences."""
        result = clean_str("Line1\r\nLine2\rLine3")
        assert result == "Line1Line2Line3"

    def test_special_symbols_preserved(self) -> None:
        """Test that special symbols are preserved."""
        result = clean_str("Price: $100.00 (10% off)")
        assert result == "Price: $100.00 (10% off)"

    def test_url_like_string(self) -> None:
        """Test cleaning URL-like strings."""
        result = clean_str("https://example.com?param=value&amp;other=123")
        assert result == "https://example.com?param=value&other=123"

    def test_nested_html_entities(self) -> None:
        """Test handling of nested/complex HTML entities."""
        result = clean_str("&amp;lt;")
        assert result == "&lt;"

    def test_malformed_entities_preserved(self) -> None:
        """Test that malformed entities are handled gracefully."""
        result = clean_str("&invalidxyz;")
        assert result == "&invalidxyz;"

    def test_already_clean_string(self) -> None:
        """Test that already clean strings pass through unchanged."""
        input_str = "This is a clean string with normal text."
        result = clean_str(input_str)
        assert result == input_str

    def test_only_control_characters(self) -> None:
        """Test string containing only control characters."""
        result = clean_str("\x00\x01\x02\x1f\x7f")
        assert result == ""

    def test_mixed_whitespace_and_control_chars(self) -> None:
        """Test combination of whitespace and control characters."""
        result = clean_str("  \x00Hello\x01 \tWorld\x02  ")
        assert result == "Hello World"

    def test_common_punctuation_preserved(self) -> None:
        """Test that common punctuation is preserved."""
        result = clean_str("Hello, World! How are you? I'm fine.")
        assert result == "Hello, World! How are you? I'm fine."

    def test_mathematical_operators_preserved(self) -> None:
        """Test that mathematical operators are preserved."""
        result = clean_str("1 + 2 = 3, 5 - 3 = 2, 2 * 3 = 6")
        assert result == "1 + 2 = 3, 5 - 3 = 2, 2 * 3 = 6"

    def test_backspace_character(self) -> None:
        """Test removal of backspace character."""
        result = clean_str("Hello\x08World")
        assert result == "HelloWorld"

    def test_form_feed_character(self) -> None:
        """Test removal of form feed character."""
        result = clean_str("Page1\x0cPage2")
        assert result == "Page1Page2"

    def test_vertical_tab_character(self) -> None:
        """Test removal of vertical tab character."""
        result = clean_str("Line1\x0bLine2")
        assert result == "Line1Line2"

    def test_escape_character(self) -> None:
        """Test removal of escape character."""
        result = clean_str("Text\x1bWithEscape")
        assert result == "TextWithEscape"
