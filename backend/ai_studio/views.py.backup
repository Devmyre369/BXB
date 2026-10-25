from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


AI_TOOLS = [
    {
        "slug": "ai-chat",
        "name": "AI Chat Assistant",
        "category": "Productivity",
        "category_slug": "productivity",
        "icon": "✦",
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
        "icon": "📚",
        "description": "Learn complex topics through clear, structured explanations.",
        "available": False,
    },
    {
        "slug": "notes-generator",
        "name": "Notes Generator",
        "category": "Education",
        "category_slug": "education",
        "icon": "📝",
        "description": "Turn study material into organized revision notes.",
        "available": False,
    },
    {
        "slug": "quiz-generator",
        "name": "Quiz & Flashcard Generator",
        "category": "Education",
        "category_slug": "education",
        "icon": "🎯",
        "description": "Create practice questions and flashcards for revision.",
        "available": False,
    },
    {
        "slug": "pdf-summarizer",
        "name": "PDF Summarizer",
        "category": "Research",
        "category_slug": "research",
        "icon": "📄",
        "description": "Summarize long documents into useful takeaways.",
        "available": False,
    },
    {
        "slug": "ai-writer",
        "name": "AI Writer",
        "category": "Writing",
        "category_slug": "writing",
        "icon": "✍️",
        "description": "Draft, rewrite and improve emails, posts and documents.",
        "available": False,
    },
    {
        "slug": "resume-builder",
        "name": "Resume Builder",
        "category": "Career",
        "category_slug": "career",
        "icon": "💼",
        "description": "Create and improve resumes for internships and jobs.",
        "available": False,
    },
    {
        "slug": "research-assistant",
        "name": "Research Assistant",
        "category": "Research",
        "category_slug": "research",
        "icon": "🔬",
        "description": "Organize research ideas and explore technical topics.",
        "available": False,
    },
    {
        "slug": "image-generator",
        "name": "AI Image Studio",
        "category": "Creative",
        "category_slug": "creative",
        "icon": "🎨",
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