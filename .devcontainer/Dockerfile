FROM mcr.microsoft.com/devcontainers/base:ubuntu

# Instala ferramentas básicas e dependências de build do pyenv
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        curl git build-essential libssl-dev zlib1g-dev \
        libbz2-dev libreadline-dev libsqlite3-dev \
        libncursesw5-dev xz-utils tk-dev libxml2-dev \
        libxmlsec1-dev libffi-dev liblzma-dev \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Instala pyenv e Python 3.14
ENV PYENV_ROOT="/home/vscode/.pyenv"
ENV PATH="$PYENV_ROOT/bin:$PYENV_ROOT/shims:$PATH"
RUN su vscode -c "curl https://pyenv.run | bash" \
    && su vscode -c "export PYENV_ROOT=/home/vscode/.pyenv && export PATH=\$PYENV_ROOT/bin:\$PYENV_ROOT/shims:\$PATH && pyenv install 3.14 && pyenv global 3.14"
