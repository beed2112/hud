FROM python:3
RUN apt-get update
RUN apt-get install -y bash-completion
RUN apt-get install -y git && pip install --upgrade pip
RUN pip install python-socketio \
    websocket-client \
    termcolor \
    git+https://github.com/PawelGorny/deuces.git
RUN git clone  https://github.com/beed2112/hud.git
ENTRYPOINT ["/bin/bash"]

