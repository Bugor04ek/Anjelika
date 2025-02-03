# Используем базовый образ Windows Server Core
FROM mcr.microsoft.com/windows/servercore:ltsc2019

# Загрузка и установка Python 3.10.9
RUN curl -o python-3.12.0.exe https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe && \
    start /wait python-3.12.0.exe /quiet InstallAllUsers=1 PrependPath=1 && \
    del python-3.12.0.exe

# Обновление pip
RUN python -m ensurepip && \
    python -m pip install --upgrade pip

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект в контейнер
COPY . .

# Указываем порт
EXPOSE 8801

# Команда для запуска приложения
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8801", "--workers", "4"]
