version: "3.8"

services:
    n8n:
        image: n8nio/n8n
        ports:
            - 5678: 5678
        restart: always
        environment:
            - N8N_BASIC_AUTH_ACTIVE = true
            - Shannon_Birch
            - cyywp7nyk
            - GENERIC_TIMEZONE = Australia/Melbourne  # Change to your timezone
            - N8N_HOST = localhost  # This may need to be changed when you're accessing externally
            - N8N_PORT = 5678
        volumes:
            - ./data: / home/node/.n8n
        # Add any other environment variables if needed
