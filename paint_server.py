import socket
import json
import threading

# In-memory storage for users
# users = [
#     {"id": 1, "name": "Alice"},
#     {"id": 2, "name": "Bob"}
# ]

paint_board = {"colors": [[1, 1], [0, 1]]}

def parse_request(request_data):
    """Parse HTTP request and return method, path, headers, and body"""
    try:
        lines = request_data.split('\r\n')
        if not lines:
            return None, None, None, None
        
        # Parse request line
        method, path, _ = lines[0].split(' ')
        
        # Parse headers
        headers = {}
        body_start = 0
        for i, line in enumerate(lines[1:], 1):
            if line == '':
                body_start = i + 1
                break
            key, value = line.split(': ', 1)
            headers[key.lower()] = value
        
        # Parse body
        body = '\r\n'.join(lines[body_start:]).strip()
        return method, path, headers, body
    except Exception:
        return None, None, None, None

def handle_get_paint_board():
    """Handle GET /paint_board request"""
    return {
        "status": "200 OK",
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(paint_board)
    }

def handle_post_user(body):
    """Handle POST /paint_board request"""
    try:
        data = json.loads(body)
        if not isinstance(data.get("name"), str):
            raise ValueError("Invalid name")
        
        new_user = {
            "id": len(paint_board) + 1,
            "name": data["name"]
        }
        paint_board.append(new_user)
        
        return {
            "status": "201 Created",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(new_user)
        }
    except (json.JSONDecodeError, ValueError):
        return {
            "status": "400 Bad Request",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Invalid request body"})
        }

def handle_request(client_socket, request_data):
    """Process HTTP request and send response"""
    method, path, headers, body = parse_request(request_data)
    
    if not method:
        response = {
            "status": "400 Bad Request",
            "headers": {"Content-Type": "text/plain"},
            "body": "Bad Request"
        }
    elif method == "GET" and path == "/paint_board":
        response = handle_get_paint_board()
    # elif method == "POST" and path == "/paint_board":
    #     response = handle_post_user(body)
    else:
        response = {
            "status": "404 Not Found",
            "headers": {"Content-Type": "text/plain"},
            "body": "Not Found"
        }
    
    # Build HTTP response
    response_headers = "\r\n".join(f"{k}: {v}" for k, v in response["headers"].items())
    response_data = (
        f"HTTP/1.1 {response['status']}\r\n"
        f"{response_headers}\r\n"
        f"Content-Length: {len(response['body'])}\r\n"
        f"\r\n"
        f"{response['body']}"
    )
    
    client_socket.send(response_data.encode())
    client_socket.close()

def main():
    """Main server function"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('localhost', 5012))
    server_socket.listen(5)
    
    print("Server running on http://localhost:5012")
    
    try:
        while True:
            client_socket, addr = server_socket.accept()
            request_data = client_socket.recv(1024).decode()
            
            # Handle each client in a separate thread
            thread = threading.Thread(
                target=handle_request,
                args=(client_socket, request_data)
            )
            thread.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()
