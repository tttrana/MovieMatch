FROM node:20-slim AS build

WORKDIR /app

# Copy package files
COPY package.json yarn.lock* package-lock.json* ./

# Remove package-lock.json to avoid platform mismatch issues
RUN rm -f package-lock.json yarn.lock

# Install dependencies with fresh lock file for Linux platform
RUN npm install

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:20-slim

WORKDIR /app

# Install serve to run the production build
RUN npm install -g serve

# Copy built application from build stage
COPY --from=build /app/dist ./dist

# Expose port
EXPOSE 3000

# Serve the built application
CMD ["serve", "-s", "dist", "-l", "3000"]

# Serve the application
CMD ["serve", "-s", "dist", "-l", "3000"]
