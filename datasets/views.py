from django.shortcuts import render


def datasets(request):
    context = {"datasets_page": "active"}
    return render(request, 'datasets.html', context)


def dataset_detail(request):
    context = {"datasets_page": "active"}
    return render(request, 'datasets.html', context)


def dataset_new(request):
    context = {"datasets_page": "active"}
    return render(request, 'datasets.html', context)


def dataset_edit(request):
    context = {"datasets_page": "active"}
    return render(request, 'datasets.html', context)


def dataset_delete(request):
    context = {"datasets_page": "active"}
    return render(request, 'datasets.html', context)


def templates(request):
    context = {"tempates_page": "active"}
    return render(request, 'templates.html', context)


def template_detail(request):
    context = {"tempates_page": "active"}
    return render(request, 'templates.html', context)


def template_new(request):
    context = {"tempates_page": "active"}
    return render(request, 'templates.html', context)


def template_edit(request):
    context = {"tempates_page": "active"}
    return render(request, 'templates.html', context)


def template_delete(request):
    context = {"tempates_page": "active"}
    return render(request, 'templates.html', context)
