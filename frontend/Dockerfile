FROM node:22-alpine AS build

WORKDIR /app

# Update npm to latest version
RUN npm install -g npm@latest

# Copy package.json and package-lock.json from app directory
COPY app/package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application
COPY app/ .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Install curl for health checks
RUN apk add --no-cache curl

# Copy the built application
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
