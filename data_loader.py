def load_dataset_from_txt(filepath, n_steps=10):
    """
    Универсальный парсер: собирает все числа из файла,
    первые 100 чисел интерпретирует как матрицу 10x10,
    остальные — как вероятности ошибок и параметры таблицы шагов.
    """
    tokens = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('\ufeff'):  # BOM
                    line = line.lstrip('\ufeff')
                if '#' in line:
                    line = line[:line.find('#')]
                line = line.replace(',', ' ')
                for word in line.split():
                    tokens.append(word)
    except Exception as e:
        print(f"Ошибка при чтении файла {filepath}: {e}")
        return None

    if not tokens:
        return None

    it_idx = 0

    # 1. Матрица маршрутов (10 строк по 10 элементов)
    rows, cols = 10, 10
    cells = []
    for _ in range(rows):
        row = []
        for _ in range(cols):
            if it_idx < len(tokens):
                # Пробуем перевести в int, если не получается (например, попался float) — округляем или ставим 0
                val_str = tokens[it_idx]
                it_idx += 1
                try:
                    row.append(int(val_str))
                except ValueError:
                    try:
                        row.append(int(float(val_str)))
                    except ValueError:
                        row.append(0)
            else:
                row.append(0)
        cells.append(row)

    # 2. Вероятности ошибок P_m_i (10 штук)
    P_m_i = []
    for _ in range(n_steps):
        if it_idx < len(tokens):
            val_str = tokens[it_idx]
            it_idx += 1
            try:
                P_m_i.append(float(val_str))
            except ValueError:
                P_m_i.append(0.1)
        else:
            P_m_i.append(0.1)

    # 3. Таблица шагов ([константы, μ], по 2 числа на шаг)
    consts = []
    mus = []
    for _ in range(n_steps):
        c_val = 0.0
        mu_val = 5.0

        if it_idx < len(tokens):
            try:
                c_val = float(tokens[it_idx])
            except ValueError:
                pass
            it_idx += 1

        if it_idx < len(tokens):
            try:
                mu_val = float(tokens[it_idx])
            except ValueError:
                pass
            it_idx += 1

        consts.append(c_val)
        mus.append(mu_val)

    t_step = [consts, mus]

    return {
        "cells": cells,
        "P_m_i": P_m_i,
        "t_step": t_step
    }