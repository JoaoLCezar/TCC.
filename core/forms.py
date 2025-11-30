# core/forms.py

from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm

class RegistroUsuarioForm(UserCreationForm):
    # Adicionamos campos extras que queremos no cadastro
    first_name = forms.CharField(label="Nome", max_length=30, required=True)
    last_name = forms.CharField(label="Sobrenome", max_length=30, required=True)
    email = forms.EmailField(label="E-mail", required=True)
    
    # Campo para escolher o Cargo (Grupo)
    grupo = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label="Cargo / Permissão",
        required=True,
        empty_label="Selecione um cargo"
    )

    class Meta:
        model = User
        # Campos que aparecerão no formulário (na ordem)
        fields = ['username', 'first_name', 'last_name', 'email', 'grupo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adiciona a classe form-control do Bootstrap em todos os campos
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            
    def save(self, commit=True):
        # 1. Salva o usuário (cria login e senha)
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # 2. Adiciona o usuário ao Grupo selecionado
            grupo_selecionado = self.cleaned_data['grupo']
            if grupo_selecionado:
                user.groups.add(grupo_selecionado)
                
        return user