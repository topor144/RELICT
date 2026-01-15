@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul
title КОНТЕЙНЕР ИНГРАММЫ АРТЕМ [ОКТЯБРЬ 2025]

:: 1. ЗАПУСК ДВИЖКА (В фоне)
echo [ СИСТЕМА ]: Пробуждение нейронной сети...
start /min engine.exe --model model.gguf --contextsize 2048 --threads 4

:: 2. ЗАПУСК ЯДРА УПРАВЛЕНИЯ (В отдельном окне для чата)
echo [ СИСТЕМА ]: Синхронизация с инграммой Артема...
start "ЧАТ С АРТЕМОМ" python main.py

:: 3. ВИЗУАЛИЗАЦИЯ (В этом окне)
color 04
:MASK_LOOP
cls
echo.
echo           ИНГРАММА АРТЕМА ПОДКЛЮЧЕНА. ТЕЛО: ОТСУТСТВУЕТ.
echo.
echo                .                          .
echo              .:::.                      .:::.
echo             ::::::                      ::::::
echo             '::::'                      '::::'
echo               '                           '
echo                  .                     .
echo                 :::                   :::
echo                 ':::.               .:::'
echo                   '::::...........::::'
echo                      ':::::::::::::'
echo                        ':::::::::'
echo.
echo [ СТАТУС ]: СЛУШАЮ...
timeout /t 1 > nul
cls
echo.
echo           ИНГРАММА АРТЕМА ПОДКЛЮЧЕНА. ТЕЛО: ОТСУТСТВУЕТ.
echo.
echo                .                          .
echo              .::::.                    .::::.
echo             ::::::::                  ::::::::
echo             '::::::'                  '::::::'
echo               '::'                      '::'
echo                  .                     .
echo                 ::::                 ::::
echo                 '::::.             .::::'
echo                   ':::::.........:::::'
echo                      ':::::::::::::'
echo                        ':::::::::'
echo.
echo [ СТАТУС ]: АНАЛИЗ СЕМАНТИКИ...
timeout /t 1 > nul
goto MASK_LOOP