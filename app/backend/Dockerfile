FROM node:22-slim

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY migrations ./migrations
COPY src ./src

EXPOSE 4000
CMD ["node", "src/index.js"]
