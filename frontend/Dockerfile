FROM node:18-alpine as build

WORKDIR /app

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

# Copy the built application
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
