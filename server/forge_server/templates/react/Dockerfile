FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .
RUN __FORGE_BUILD_CMD__

FROM node:20-alpine

RUN npm install -g serve@14

WORKDIR /app
COPY --from=build /app/dist ./dist

EXPOSE __FORGE_PORT__

CMD ["serve", "-s", "dist", "-l", "__FORGE_PORT__"]
