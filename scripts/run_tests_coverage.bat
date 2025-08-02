@echo off
echo ================================================
echo      TESTS AVEC RAPPORT DE COUVERTURE
echo ================================================

echo.
echo [1/4] Installation des dependances...
call npm install
pip install -r requirements.txt

echo.
echo [2/4] Tests Frontend avec couverture...
call npm run test:coverage

echo.
echo [3/4] Tests Backend avec couverture...
python -m pytest tests/backend/ --cov=backend --cov-report=html:tests/coverage/backend --cov-report=term-missing

echo.
echo [4/4] Generation du rapport combine...
echo Rapports generes:
echo - Frontend: tests/coverage/
echo - Backend: tests/coverage/backend/
echo.

echo ================================================
echo    RAPPORTS DE COUVERTURE DISPONIBLES
echo ================================================
echo Frontend: tests/coverage/lcov-report/index.html
echo Backend: tests/coverage/backend/index.html
echo.
pause
