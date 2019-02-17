from django.shortcuts import render
from .context_processors import export_neo4j_vars


def workflows(request):
    neo4j_vars = export_neo4j_vars(request)
    return render(request, 'workflows.html', {"projects_page": "active", "neo4j_vars": neo4j_vars})
