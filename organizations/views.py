from django.shortcuts import redirect


def choose(request):
    """This project serves one organisation, so the root opens its portal."""
    return redirect('/dscc/')
