"""YAML content schema validation for Advisor Guide generator."""


VALID_SECTION_TYPES = {
    "heading",
    "subsection",
    "body",
    "callout",
    "dark_panel",
    "gray_section",
    "table",
    "chart_image",
    "bullet_list",
    "source_note",
    "page_break",
}

REQUIRED_METADATA_KEYS = {"topic", "version", "logo_family"}
REQUIRED_COVER_KEYS = {"topic_display", "intro_heading", "intro_text"}


def validate_content(data):
    """Validate a parsed YAML content dict.

    Args:
        data: dict parsed from YAML.

    Returns:
        List of error strings. Empty list means valid.
    """
    errors = []

    # Metadata
    metadata = data.get("metadata")
    if not metadata:
        errors.append("Missing 'metadata' section.")
    else:
        for key in REQUIRED_METADATA_KEYS:
            if key not in metadata:
                errors.append(f"Missing metadata.{key}")

        family = metadata.get("logo_family", "")
        from . import brand_config
        if family and family not in brand_config.LOGO_FAMILIES:
            valid = ", ".join(brand_config.LOGO_FAMILIES.keys())
            errors.append(
                f"Unknown logo_family '{family}'. Valid options: {valid}"
            )

    # Cover
    cover = data.get("cover")
    if not cover:
        errors.append("Missing 'cover' section.")
    else:
        for key in REQUIRED_COVER_KEYS:
            if key not in cover:
                errors.append(f"Missing cover.{key}")

    # Sections
    sections = data.get("sections")
    if not sections:
        errors.append("Missing 'sections' list (need at least one section).")
    elif not isinstance(sections, list):
        errors.append("'sections' must be a list.")
    else:
        for i, sec in enumerate(sections):
            if not isinstance(sec, dict):
                errors.append(f"Section [{i}] must be a dict.")
                continue
            sec_type = sec.get("type")
            if not sec_type:
                errors.append(f"Section [{i}] missing 'type'.")
            elif sec_type not in VALID_SECTION_TYPES:
                errors.append(
                    f"Section [{i}] has invalid type '{sec_type}'. "
                    f"Valid: {', '.join(sorted(VALID_SECTION_TYPES))}"
                )

            # Type-specific validation
            if sec_type in ("heading", "subsection", "body", "callout"):
                if not sec.get("text"):
                    errors.append(f"Section [{i}] (type={sec_type}) missing 'text'.")

            if sec_type == "dark_panel":
                if not sec.get("heading"):
                    errors.append(f"Section [{i}] (type=dark_panel) missing 'heading'.")

            if sec_type == "table":
                if not sec.get("headers"):
                    errors.append(f"Section [{i}] (type=table) missing 'headers'.")
                if not sec.get("rows"):
                    errors.append(f"Section [{i}] (type=table) missing 'rows'.")

            if sec_type == "chart_image":
                if not sec.get("path"):
                    errors.append(f"Section [{i}] (type=chart_image) missing 'path'.")

            if sec_type == "bullet_list":
                if not sec.get("items"):
                    errors.append(f"Section [{i}] (type=bullet_list) missing 'items'.")

    return errors
