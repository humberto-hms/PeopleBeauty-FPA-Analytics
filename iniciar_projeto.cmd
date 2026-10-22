@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem ==================================================================
rem  People Beauty - FP&A Analytics
rem  Organizacao inicial do ambiente local (Windows CMD)
rem
rem  O que este script FAZ:
rem    - apresenta o projeto e as etapas de FP&A e BI;
rem    - cria as pastas do projeto que ainda nao existirem.
rem
rem  O que este script NAO FAZ:
rem    - nao apaga, move nem sobrescreve arquivos existentes;
rem    - nao executa comandos SQL nem gera dados ficticios;
rem    - nao instala ferramentas nem altera configuracoes do Windows.
rem      (a pagina de codigo do console e ajustada so durante a
rem      execucao, para exibir acentos, e restaurada ao final)
rem ==================================================================

rem Guarda a pagina de codigo atual para restaurar no final.
set "CP_ORIGINAL="
for /f "tokens=2 delims=:" %%A in ('chcp') do set "CP_ORIGINAL=%%A"
set "CP_ORIGINAL=%CP_ORIGINAL: =%"
set "CP_ORIGINAL=%CP_ORIGINAL:.=%"
chcp 65001 >nul

title People Beauty - FP^&A Analytics

rem Pasta onde este arquivo está (raiz do projeto).
set "RAIZ=%~dp0"
if "%RAIZ:~-1%"=="\" set "RAIZ=%RAIZ:~0,-1%"

set /a CRIADAS=0
set /a EXISTENTES=0
set /a ERROS=0

echo.
echo ==================================================================
echo   PEOPLE BEAUTY - FP^&A ANALYTICS
echo ==================================================================
echo.
echo   Portfólio de FP^&A e Business Intelligence para uma rede
echo   fictícia de varejo de beleza: 24 lojas e 1 unidade corporativa.
echo.
echo   Finalidade: analisar orçamento x realizado, receita, CMV,
echo   margem bruta, despesas operacionais, rentabilidade por loja,
echo   forecast financeiro e DRE gerencial, com recomendações
echo   executivas. Todos os dados serão fictícios.
echo.
echo ------------------------------------------------------------------
echo   ETAPAS DO PROJETO
echo ------------------------------------------------------------------
echo   1. Documentação     Escopo, premissas e plano de contas
echo   2. SQL Server       Banco, tabelas, chaves e relacionamentos
echo   3. Dados            Base fictícia e carga
echo   4. Análises SQL     Orçamento x realizado, DRE, rentabilidade
echo   5. Power BI         Modelo, medidas DAX e dashboard
echo   6. Resultados       Conclusões, forecast e recomendações
echo.
echo   IMPORTANTE: o banco de dados, as tabelas, a carga, as
echo   consultas, as views, as medidas DAX e o dashboard serão
echo   desenvolvidos MANUALMENTE pelo autor. Este script apenas
echo   organiza as pastas.
echo.
echo ------------------------------------------------------------------
echo   VERIFICANDO PASTAS EM:
echo   "%RAIZ%"
echo ------------------------------------------------------------------

if not exist "%RAIZ%\" (
    echo   [ERRO] Pasta raiz do projeto não encontrada.
    set /a ERROS+=1
    goto :resumo
)

for %%P in (01_Documentacao 02_SQL_Server 03_Dados 04_Analises_SQL 05_Power_BI 06_Resultados) do call :garantir_pasta "%%P"

echo.
echo ------------------------------------------------------------------
echo   VERIFICANDO ARQUIVOS PRINCIPAIS (somente leitura)
echo ------------------------------------------------------------------
for %%F in (README.md projeto_config.json .gitignore) do (
    if exist "%RAIZ%\%%F" (
        echo   [OK]     %%F encontrado
    ) else (
        echo   [AVISO]  %%F não encontrado. Recupere-o do repositório GitHub.
    )
)

:resumo
echo.
echo ==================================================================
echo   RESUMO
echo ==================================================================
echo   Pastas criadas agora : %CRIADAS%
echo   Pastas já existentes : %EXISTENTES%
echo   Erros                : %ERROS%
echo.
if %ERROS% GTR 0 (
    echo   [ERRO] A organização terminou com %ERROS% erro^(s^).
    echo   Verifique permissões de escrita na pasta e execute novamente.
    set "CODIGO_SAIDA=1"
) else (
    echo   [SUCESSO] Estrutura do projeto pronta.
    echo   Nenhum arquivo existente foi alterado ou excluído.
    echo.
    echo   Próximo passo: documentar as premissas em 01_Documentacao
    echo   e iniciar a modelagem no SQL Server ^(etapa manual^).
    set "CODIGO_SAIDA=0"
)
echo.
pause

if defined CP_ORIGINAL chcp %CP_ORIGINAL% >nul
endlocal & exit /b %CODIGO_SAIDA%

rem ------------------------------------------------------------------
rem  :garantir_pasta  -  cria a pasta somente se ela não existir
rem ------------------------------------------------------------------
:garantir_pasta
set "PASTA=%~1"
if exist "%RAIZ%\%PASTA%\" (
    echo   [OK]     %PASTA% já existe ^(preservada^)
    set /a EXISTENTES+=1
    goto :eof
)
if exist "%RAIZ%\%PASTA%" (
    echo   [ERRO]   Existe um ARQUIVO chamado %PASTA%. Nada foi alterado.
    set /a ERROS+=1
    goto :eof
)
mkdir "%RAIZ%\%PASTA%" 2>nul
if errorlevel 1 (
    echo   [ERRO]   Não foi possível criar %PASTA%
    set /a ERROS+=1
) else (
    echo   [CRIADA] %PASTA%
    set /a CRIADAS+=1
)
goto :eof
