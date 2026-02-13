from django.template.loader import get_template
from django.http import HttpResponse
# Ideally use xhtml2pdf or weasyprint. For this MVP, we will use a simple HTML print-friendly view.
# Real PDF generation requires installing libraries which might bloat the project right now.
# We will focus on a "Print Friendly" HTML page first.

def render_print_view(request, template_path, context):
    """
    Renders a template designed for printing (Ctrl+P -> Save as PDF).
    """
    template = get_template(template_path)
    html = template.render(context)
    return HttpResponse(html)