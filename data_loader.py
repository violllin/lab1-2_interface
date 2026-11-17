def load_matrix_from_txt(filepath):
    matrix = []
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                # Пропускаем пустые строки и комментарии
                if not line or line.startswith('#'):
                    continue

                # Заменяем запятые на пробелы для универсальности
                line = line.replace(',', ' ')

                # Извлекаем числа
                row = [int(x) for x in line.split()]
                if row:
                    matrix.append(row)
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
    return matrix