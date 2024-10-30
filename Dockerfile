FROM --platform=linux/amd64 python:3.11-slim
EXPOSE 8501
ENV PIP_DEFAULT_TIMEOUT=100
ENV HOST 0.0.0.0
WORKDIR /app
COPY . ./
ENV TMPDIR='/var/tmp'
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
ENTRYPOINT ["streamlit", "run"]
CMD ["backend/app.py", "--server.fileWatcherType", "none"]

