from pyngrok import ngrok
import os

def start_ngrok():
    # Ensure NGROK_AUTH_TOKEN is correctly set
    auth_token = os.environ.get('NGROK_AUTH_TOKEN')
    if not auth_token:
        raise ValueError("NGROK_AUTH_TOKEN environment variable is not set.")

    ngrok.set_auth_token(auth_token)  # Set the ngrok auth token

    # Start the tunnel on port 8000
    url = ngrok.connect(8000)
    
    print(f'Ngrok tunnel URL: {url}')
    return url

# Start the ngrok tunnel
if __name__ == "__main__":
    tunnel_url = start_ngrok()
    print(f"Tunnel is live at {tunnel_url}")
