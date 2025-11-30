@echo off
echo ========================================
echo     VendaFacil - Iniciando Servidor
echo ========================================
echo.

REM Configurar PostgreSQL
set USE_POSTGRES=1
set DB_NAME=venda_facil_db
set DB_USER=venda_user
set DB_PASSWORD=56771026
set DB_HOST=localhost
set DB_PORT=5432

echo PostgreSQL configurado: %DB_NAME%@%DB_HOST%:%DB_PORT%
echo Usuario: %DB_USER%
echo.
echo Iniciando servidor Django...
echo.

REM Ativar ambiente virtual e rodar servidor
call venv\Scripts\activate.bat
python manage.py runserver

pause
