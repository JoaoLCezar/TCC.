# Configura variáveis de ambiente para usar PostgreSQL
# Edite os valores conforme seu ambiente antes de rodar

$env:USE_POSTGRES = '1'
$env:DB_NAME      = 'venda_facil_db'         # nome do banco
$env:DB_USER      = 'venda_user'             # usuário
$env:DB_PASSWORD  = '56771026'               # senha
$env:DB_HOST      = 'localhost'               # host
$env:DB_PORT      = '5432'                    # porta

Write-Host "PostgreSQL ON -> $env:DB_NAME@$env:DB_HOST:$env:DB_PORT (user=$env:DB_USER)"
Write-Host "Sugestão: executar migrações e subir o servidor:"
Write-Host ".\\venv\\Scripts\\python.exe manage.py migrate"
Write-Host ".\\venv\\Scripts\\python.exe manage.py runserver"