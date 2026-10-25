
import os

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


# Read the deployed service URL from the environment.
# When it is absent, Resume Builder remains marked as unavailable.
RESUME_BUILDER_URL = (
    os.environ.get("RESUME_BUILDER_URL", "").strip().rstrip("/")
)


AI_TOOLS = [
    {
        "slug": "ai-chat",
        "name": "AI Chat Assistant",
        "category": "Productivity",
        "category_slug": "productivity",
        "icon": "\u2726",
        "description": "Ask questions, brainstorm ideas and explore concepts.",
        "available": False,
    },
    {
        "slug": "code-assistant",
        "name": "Code Assistant",
        "category": "Development",
        "category_slug": "development",
        "icon": "</>",
        "description": "Get help understanding code, debugging and solving problems.",
        "available": False,
    },
    {
        "slug": "study-assistant",
        "name": "Study Assistant",
        "category": "Education",
        "category_slug": "education",
        "icon": "\U0001F4DA",
        "description": "Learn complex topics through clear, structured explanations.",
        "available": False,
    },
    {
        "slug": "notes-generator",
        "name": "Notes Generator",
        "category": "Education",
        "category_slug": "education",
        "icon": "\U0001F4DD",
        "description": "Draft, rewrite and improve emails, posts and documents.",
        "available": False,
    },
    {
        "slug": "resume-builder",
        "name": "Resume Builder",
        "category": "Career",
        "category_slug": "career",
        "icon": "\U0001F4BC",
        "description": "Create and improve resumes for internships and jobs.",
        "available": bool(RESUME_BUILDER_URL),
        "url": RESUME_BUILDER_URL,
    },
    {
        "slug": "research-assistant",
        "name": "Research Assistant",
        "category": "Research",
        "category_slug": "research",
        "icon": "\U0001F52C",
        "description": "Organize research ideas and explore technical topics.",
        "available": False,
    },
    {
        "slug": "image-generator",
        "name": "AI Image Studio",
        "category": "Creative",
        "category_slug": "creative",
        "icon": "\U0001F3A8",
        "description": "Create visual assets from text prompts.",
        "available": False,
    },
]


@login_required
def dashboard(request):
    categories = [
        {"name": "All tools", "slug": "all"},
        {"name": "Education", "slug": "education"},
        {"name": "Development", "slug": "development"},
        {"name": "Writing", "slug": "writing"},
        {"name": "Research", "slug": "research"},
        {"name": "Career", "slug": "career"},
        {"name": "Creative", "slug": "creative"},
        {"name": "Productivity", "slug": "productivity"},
    ]

    context = {
        "tools": AI_TOOLS,
        "categories": categories,
        "total_tools": len(AI_TOOLS),
        "available_tools": sum(
            1 for tool in AI_TOOLS if tool["available"]
        ),
    }

    return render(
        request,
        "ai_studio/dashboard.html",
        context,
    )
