# filepath: market-research-platform/frontend/Dockerfile
# React frontend container

FROM node:18-alpine

WORKDIR /app

# Copy package files and install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy application code
COPY . .

# Expose dev server port
EXPOSE 3000

# Start React dev server
CMD ["npm", "start"]
