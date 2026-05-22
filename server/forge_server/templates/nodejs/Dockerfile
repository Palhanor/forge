FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .
RUN __FORGE_BUILD_CMD__

FROM node:20-alpine

WORKDIR /app

ENV PORT=__FORGE_PORT__

COPY package.json package-lock.json* ./
RUN npm install --omit=dev

__FORGE_RUNTIME_COPY__

EXPOSE __FORGE_PORT__

CMD __FORGE_START_CMD__
