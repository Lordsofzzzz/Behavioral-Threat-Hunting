FROM node:22-bookworm-slim

WORKDIR /app

COPY package.json package.json
COPY package-lock.json package-lock.json
COPY tsconfig.json tsconfig.json
COPY next.config.js next.config.js
COPY next-env.d.ts next-env.d.ts
COPY pages pages
COPY components components
COPY lib lib
COPY src src

RUN npm ci
RUN npm run build

EXPOSE 3001
CMD ["npm", "run", "start"]