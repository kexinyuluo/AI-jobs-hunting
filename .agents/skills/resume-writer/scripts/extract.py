"""Extract resume content from a DOCX file into the tailored.yaml schema.

Usage:
    python .agents/skills/resume-writer/scripts/extract.py path/to/resume.docx
    python .agents/skills/resume-writer/scripts/extract.py path/to/resume.docx --output applications/0_profile/extracted.yaml

This is a bootstrap tool. The extraction is best-effort — review
and clean up the generated YAML. Complex layouts (tables, multi-column,
text boxes) may produce messy output.

Output schema matches what render.py expects (see resume-writer SKILL.md).
"""

import argparse
import re
import sys
from pathlib import Path

import yaml
from docx import Document


SECTION_KEYWORDS = {
    "summary": ["summary", "professional summary", "objective", "profile", "about"],
    "experience": ["experience", "work experience", "professional experience", "employment"],
    "education_skills": ["education & skills", "education and skills"],
    "skills": ["skills", "technical skills", "core competencies", "technologies"],
    "education": ["education", "academic"],
    "certifications": ["certifications", "certificates", "licenses"],
    "projects": ["projects", "personal projects", "side projects"],
}


def classify_section(text: str) -> str | None:
    normalized = text.strip().lower()
    for section, keywords in SECTION_KEYWORDS.items():
        for kw in keywords:
            if kw in normalized:
                return section
    return None


def extract_paragraphs(docx_path: str) -> list[dict]:
    doc = Document(docx_path)
    paragraphs = []
    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue
        paragraphs.append({
            "text": text,
            "style": p.style.name if p.style else "Normal",
            "bold": any(r.bold for r in p.runs if r.bold),
        })
    return paragraphs


def is_heading(para: dict) -> bool:
    style = para["style"].lower()
    if "heading" in style:
        return True
    if para["bold"] and len(para["text"]) < 40:
        return True
    if para["text"].isupper() and len(para["text"]) < 40:
        return True
    return False


def looks_like_bullet(text: str) -> bool:
    return bool(re.match(r"^[\u2022\u2023\u25E6\u2043\-\*\>]\s", text))


def clean_bullet(text: str) -> str:
    return re.sub(r"^[\u2022\u2023\u25E6\u2043\-\*\>]\s*", "", text).strip()


def is_project_title(text: str) -> bool:
    """Heuristic: project titles are short-ish, bold, and don't start with bullet chars."""
    if looks_like_bullet(text):
        return False
    if len(text) > 100:
        return False
    return True


def extract_to_yaml(docx_path: str) -> dict:
    paragraphs = extract_paragraphs(docx_path)
    if not paragraphs:
        print(f"Warning: no text content found in {docx_path}", file=sys.stderr)
        return {}

    result = {
        "name": "",
        "contact_line": "",
        "summary_bullets": [],
        "education_line": "",
        "skills": [],
        "employer": {
            "company": "",
            "role": "",
            "dates": "",
            "location": "",
            "projects": [],
        },
    }

    # First paragraph is often the name
    if len(paragraphs[0]["text"]) < 60 and not classify_section(paragraphs[0]["text"]):
        result["name"] = paragraphs[0]["text"]

    # Second paragraph is often the contact line
    if len(paragraphs) > 1 and not classify_section(paragraphs[1]["text"]):
        contact_text = paragraphs[1]["text"]
        if "@" in contact_text or "linkedin" in contact_text.lower():
            result["contact_line"] = contact_text

    current_section = None
    raw_sections: dict[str, list[str]] = {}

    for para in paragraphs:
        text = para["text"]

        if is_heading(para) or (not para["bold"] and len(text) < 40):
            section = classify_section(text)
            if section:
                current_section = section
                if section not in raw_sections:
                    raw_sections[section] = []
                continue

        if current_section:
            raw_sections.setdefault(current_section, []).append(text)

    # Summary -> bullet list
    if "summary" in raw_sections:
        result["summary_bullets"] = raw_sections["summary"]

    # Education & Skills (combined section)
    if "education_skills" in raw_sections:
        for line in raw_sections["education_skills"]:
            lower = line.lower()
            if lower.startswith("education:"):
                result["education_line"] = line.split(":", 1)[1].strip()
            elif ":" in line:
                parts = line.split(":", 1)
                label = parts[0].strip()
                items = parts[1].strip()
                # Handle multi-line within one paragraph (newline-separated)
                for subline in line.split("\n"):
                    subline = subline.strip()
                    if ":" in subline:
                        sub_parts = subline.split(":", 1)
                        sub_label = sub_parts[0].strip()
                        sub_items = sub_parts[1].strip()
                        if sub_label.lower() == "education":
                            result["education_line"] = sub_items
                        else:
                            result["skills"].append({"label": sub_label, "items": sub_items})
                break  # Already handled via split
            else:
                result["skills"].append({"label": "Skills", "items": line})
    else:
        # Separate sections
        if "education" in raw_sections:
            result["education_line"] = " ".join(raw_sections["education"])
        if "skills" in raw_sections:
            for line in raw_sections["skills"]:
                cleaned = clean_bullet(line) if looks_like_bullet(line) else line
                if ":" in cleaned:
                    parts = cleaned.split(":", 1)
                    result["skills"].append({"label": parts[0].strip(), "items": parts[1].strip()})
                else:
                    result["skills"].append({"label": "Skills", "items": cleaned})

    # Experience -> employer with projects
    if "experience" in raw_sections:
        lines = raw_sections["experience"]
        current_project = None

        for line in lines:
            # First non-bullet line with company indicators is employer header
            if not result["employer"]["company"] and not looks_like_bullet(line):
                # Try to parse "Company – Role  Dates | Location"
                for sep in [" – ", " - "]:
                    if sep in line:
                        parts = line.split(sep, 1)
                        result["employer"]["company"] = parts[0].strip()
                        remainder = parts[1] if len(parts) > 1 else ""
                        if " | " in remainder:
                            role_dates, location = remainder.rsplit(" | ", 1)
                            result["employer"]["location"] = location.strip()
                            # Split role and dates (dates are usually at the end)
                            date_match = re.search(r'(\d{4}\s*[–-]\s*(?:Present|\d{4}))', role_dates)
                            if date_match:
                                result["employer"]["dates"] = date_match.group(1).strip()
                                result["employer"]["role"] = role_dates[:date_match.start()].strip()
                            else:
                                result["employer"]["role"] = role_dates.strip()
                        else:
                            result["employer"]["role"] = remainder.strip()
                        break
                continue

            if looks_like_bullet(line) or line.startswith("•"):
                cleaned = clean_bullet(line) if looks_like_bullet(line) else line.lstrip("• ").strip()
                if current_project:
                    current_project["bullets"].append(cleaned)
            elif is_project_title(line) and result["employer"]["company"]:
                current_project = {"title": line, "bullets": []}
                result["employer"]["projects"].append(current_project)
            else:
                # Bold non-bullet text under experience is likely a project bullet (no bullet marker)
                if current_project:
                    current_project["bullets"].append(line)
                elif result["employer"]["company"]:
                    current_project = {"title": line, "bullets": []}
                    result["employer"]["projects"].append(current_project)

    return result


def main():
    parser = argparse.ArgumentParser(description="Extract resume content from DOCX to YAML")
    parser.add_argument("docx_path", help="Path to the DOCX resume file")
    parser.add_argument("--output", "-o", default=None,
                        help="Output YAML path (default: prints to stdout)")
    args = parser.parse_args()

    docx_path = Path(args.docx_path)
    if not docx_path.exists():
        print(f"Error: {docx_path} not found", file=sys.stderr)
        sys.exit(1)

    data = extract_to_yaml(str(docx_path))

    yaml_str = yaml.dump(data, default_flow_style=False, allow_unicode=True,
                         sort_keys=False, width=120)

    header = (
        "# Extracted from: {}\n"
        "# Review and clean up — extraction is best-effort.\n"
        "# Schema: name, contact_line, summary_bullets, education_line, skills, employer.projects\n\n"
    ).format(docx_path.name)

    output = header + yaml_str

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output)
        print(f"Extracted resume content to {output_path}")
    else:
        print(output)

    print("Please review the output and fix any extraction errors.", file=sys.stderr)


if __name__ == "__main__":
    main()
