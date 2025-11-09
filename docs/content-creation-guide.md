# Content Creation Guide

## Overview

This guide explains how to create and manage lesson content for the Promptheus bot. The system uses a JSON-based format with automatic loading, versioning, and hot reload capabilities.

## Repository Structure

Content is stored in the `promptheus-content` repository:

```
promptheus-content/
├── lessons/
│   ├── beginner/
│   ├── intermediate/
│   └── advanced/
├── docs/
│   ├── lesson-catalog.md
│   └── content-workflow.md
└── README.md
```

## File Naming Convention

### Location
- **Beginner lessons**: `lessons/beginner/`
- **Intermediate lessons**: `lessons/intermediate/`
- **Advanced lessons**: `lessons/advanced/`

### Naming Rules
- Use lowercase letters, numbers, and hyphens only
- Start with descriptive words
- No number prefixes needed (system sorts alphabetically)
- End with `.json` extension

**Examples:**
```
✅ Correct:
- introduction-to-prompting.json
- defining-ai-roles.json
- chain-of-thought-prompting.json
- advanced-context-management.json

❌ Wrong:
- 01_intro.json (numbered prefix)
- Introduction To Prompting.json (spaces, uppercase)
- intro-prompting.JSON (uppercase extension)
- lesson_1.json (underscores)
```

## JSON Format Specification

Each lesson is a JSON file with the following structure:

```json
{
  "title": "Introduction to Prompt Engineering",
  "skill_level": "beginner",
  "tags": ["fundamentals", "basics", "getting-started"],
  "theory_content": {
    "sections": [
      {
        "title": "What is Prompt Engineering?",
        "content": "Prompt engineering is the art and science of crafting effective prompts for AI language models. It involves understanding how different models respond to various input formats and optimizing prompts for specific tasks."
      },
      {
        "title": "Why Prompt Engineering Matters",
        "content": "Well-crafted prompts can significantly improve AI response quality, consistency, and usefulness. Poor prompts often lead to vague, irrelevant, or incorrect outputs."
      }
    ]
  },
  "examples": {
    "comparisons": [
      {
        "title": "Vague vs Specific Prompt",
        "bad_example": {
          "prompt": "Write something about dogs",
          "explanation": "Too vague - AI doesn't know what aspect to focus on"
        },
        "good_example": {
          "prompt": "Write a 200-word article about the history of golden retrievers as service dogs, including their temperament traits and training requirements",
          "explanation": "Specific requirements help AI generate focused, relevant content"
        }
      }
    ]
  },
  "exercises": {
    "prompts": [
      {
        "title": "Basic Prompt Improvement",
        "description": "Take this vague prompt and make it more specific and effective",
        "initial_prompt": "Tell me about cats",
        "evaluation_criteria": [
          "Clarity of intent",
          "Specificity of requirements",
          "Context provision",
          "Output format specification"
        ],
        "sample_solution": "Write a 300-word informative article about Maine Coon cats, covering their physical characteristics, temperament, history as a breed, and care requirements for new owners."
      }
    ]
  }
}
```

## Field Descriptions

### Required Fields

| Field            | Type   | Description                                       |
| ---------------- | ------ | ------------------------------------------------- |
| `title`          | string | Lesson title (3-100 characters)                   |
| `skill_level`    | string | Must be "beginner", "intermediate", or "advanced" |
| `tags`           | array  | List of strings for categorization                |
| `theory_content` | object | Educational content sections                      |
| `examples`       | object | Before/after prompt comparisons                   |
| `exercises`      | object | Interactive practice prompts                      |

### theory_content.sections[]

Each theory section contains:
- `title`: Section heading
- `content`: Main educational text (50-500 words recommended)

### examples.comparisons[]

Each comparison shows:
- `title`: Example name
- `bad_example`: Object with `prompt` and `explanation`
- `good_example`: Object with `prompt` and `explanation`

### exercises.prompts[]

Each exercise includes:
- `title`: Exercise name
- `description`: Instructions for the student
- `initial_prompt`: Starting prompt to improve
- `evaluation_criteria`: Array of assessment points
- `sample_solution`: Model improved prompt

## Content Guidelines

### Writing Style
- **Clear and concise**: Use simple language, avoid jargon
- **Educational**: Explain concepts progressively
- **Practical**: Focus on actionable techniques
- **Inclusive**: Avoid cultural biases, use neutral examples

### Content Length
- **Theory sections**: 50-200 words each
- **Examples**: 2-4 comparisons per lesson
- **Exercises**: 1-3 practice prompts per lesson
- **Total lesson**: 300-800 words

### Quality Standards
- ✅ **Do:**
  - Use real-world examples
  - Include evaluation criteria
  - Provide sample solutions
  - Test prompts manually
  - Use consistent formatting

- ❌ **Don't:**
  - Include offensive content
  - Use copyrighted material
  - Make unrealistic claims
  - Include personal opinions
  - Use complex technical terms without explanation

## Workflow

### 1. Development Process

1. **Choose skill level** based on complexity
2. **Create JSON file** in appropriate directory
3. **Write content** following format specification
4. **Validate JSON** syntax
5. **Test locally** (see testing section)
6. **Commit and push** to repository

### 2. Version Control

The system automatically:
- Creates version snapshots on changes
- Maintains change history
- Tracks content modifications
- Enables rollback if needed

### 3. Hot Reload

**Development mode:**
- File changes detected automatically
- Content reloaded without restart
- Changes visible immediately in bot

**Production mode:**
- Hot reload disabled for stability
- Requires application restart for content updates
- Use deployment process for production changes

## Validation

### JSON Schema Validation

Content is validated against a schema that checks:
- Required fields presence
- Data type correctness
- String length limits
- Array structure
- Enum value constraints

### Content Validation

Additional checks include:
- Slug uniqueness across skill levels
- Tag format and length
- Content hash generation
- Cross-reference integrity

## Testing Your Content

### Local Testing

1. **Start development server:**
```bash
cd promptheus
python -m src.main  # Development mode
```

2. **Make changes** to JSON files in `../promptheus-content/lessons/`

3. **Check logs** for reload confirmation:
```
INFO: Lesson content reloaded for skill level: beginner
INFO: Loaded 5 lessons from JSON files
```

4. **Test in bot:**
   - Send `/start` to reset
   - Navigate to your lesson
   - Verify content displays correctly

### Validation Script

Run the validation script to check your content:

```bash
cd promptheus
python scripts/validate_content.py ../promptheus-content
```

## Best Practices

### Content Organization
- Group related concepts in single lessons
- Progress from simple to complex within skill levels
- Ensure logical flow between lessons
- Avoid content duplication

### Maintenance
- Review and update examples regularly
- Monitor user feedback on exercises
- Update content based on AI model changes
- Archive outdated lessons rather than deleting

### Collaboration
- Use descriptive commit messages
- Document significant content changes
- Review content changes in pull requests
- Maintain consistency across similar lessons

## Troubleshooting

### Common Issues

**JSON syntax errors:**
- Use a JSON validator (online tools or VS Code extensions)
- Check for trailing commas
- Verify quote usage (double quotes only)

**Content not loading:**
- Check file path and naming
- Verify skill level directory
- Check application logs for errors

**Validation failures:**
- Review error messages carefully
- Check required fields
- Validate data types and formats

**Hot reload not working:**
- Ensure development mode is enabled
- Check file permissions
- Verify file watcher is active

## Support

For content creation assistance:
1. Check existing lessons for examples
2. Review this guide and JSON schema
3. Test changes locally first
4. Create pull request for review

## Examples

See the `lessons/` directory for complete examples of each skill level.