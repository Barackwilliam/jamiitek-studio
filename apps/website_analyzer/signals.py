from django.dispatch import Signal

# Sent after an analysis finishes with at least one analyzed page.
# Arguments: analysis.
analysis_finished = Signal()
