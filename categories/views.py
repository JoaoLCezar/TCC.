from django.shortcuts import render
from .models import Categoria

def listar_categorias(request):
    categorias = Categoria.objects.all()

    contexto = {
        'lista_de_categorias': categorias,
    }

    return render(request, 'categories/lista_categorias.html', contexto)

def criar_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)

        if form.is_valid():
            form.save()

            return redirect('categories:listar_categorias')
        
    else:
        form = CategoriaForm()

    context = {
        'form':form
    }
    return render(request, 'categories/form_categoria.html', context)


