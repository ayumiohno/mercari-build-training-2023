FROM node:16-alpine
WORKDIR /app

RUN addgroup -S mercari && adduser -S trainee -G mercari

RUN npm config set unsafe-perm true

COPY package.json package.json
RUN npm install

COPY src src
COPY public public
COPY tsconfig.json tsconfig.json

RUN mkdir -p /app/node_modules/.cache
RUN chown -R trainee:mercari /app/node_modules/.cache
USER trainee

CMD ["npm", "start"]
