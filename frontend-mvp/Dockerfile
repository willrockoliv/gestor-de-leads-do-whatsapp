
# Estágio 1: Build da aplicação React/Vite
FROM node:20-alpine as builder

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia os arquivos de dependências primeiro (aproveita o cache do Docker)
COPY package*.json ./

# Instala as dependências
RUN npm install

# Copia o resto do código da aplicação
COPY . .

# Faz o build de produção (gera a pasta /dist)
RUN npm run build

# Estágio 2: Servidor Web Nginx
FROM nginx:alpine

# Copia os arquivos compilados do estágio anterior para a pasta padrão do Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# (Opcional) Configuração para SPA: garante que rotas do React funcionem se a página for recarregada.
# Se você adicionar React Router no futuro, descomente a linha abaixo e crie um nginx.conf
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expõe a porta 80 do container
EXPOSE 80

# Inicia o Nginx
CMD ["nginx", "-g", "daemon off;"]

