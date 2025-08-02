@echo off
echo ================================================
echo         EXECUTION DES TESTS UNITAIRES
echo ================================================

echo.
echo [1/3] Installation des dependances JavaScript...
call npm install

echo.
echo [2/3] Execution des tests Frontend (JavaScript)...
call npm test

echo.
echo [3/3] Execution des tests Backend (Python)...
python -m pytest tests/backend/ -v

echo.
echo ================================================
echo         TESTS TERMINES
echo ================================================
pause
