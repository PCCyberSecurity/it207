import http.server
import socketserver
import requests
import time

#import http.client
#http.client.HTTPConnection.debuglevel = 1

# Pool connections via a session - speeds up connections to web server
session = requests.Session()

# List of bad words to filter
bad_words = ['badword1', 'badword2', 'badword3', 'Hello']

def filter_bad_words(content):
    for word in bad_words:
        content = content.replace(word, '*' * len(word))
    return content

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    
    def do_GET(self):
        # The target URL will always be localhost:8000 with the requested path
        #target_url = f"http://localhost:8000{self.path}"
        target_url = f"http://127.0.0.1:8000{self.path}"
        
        try:
            print(f"Handling GET request for {target_url}")
            #start_request_time = time.time()  # Start timing the request to localhost:8000

            # Fetch the target website's content from localhost:8000
            #response = requests.get(target_url, timeout=(1,5))
            response = session.get(target_url, timeout=(3.05, 27))

            #end_request_time = time.time()
            #print(f"Request to {target_url} took {end_request_time - start_request_time:.6f} seconds")

            content = response.text

            # Filter out bad words from the response content (if it's text)
            content_type = response.headers.get('Content-Type', '')
            if 'text' in content_type:
                filtered_content = filter_bad_words(response.text)
            else:
                filtered_content = response.content  # non-text content (e.g., images)

            # Send the filtered content back to the client
            self.send_response(response.status_code)  #200)
            #self.send_header('Content-type', 'text/html')
            # Forward the original headers from the target server
            for header_key, header_value in response.headers.items():
                self.send_header(header_key, header_value)
            self.end_headers()
            
            # Write the filtered content back to the client
            if 'text' in content_type:
                self.wfile.write(filtered_content.encode('utf-8'))
            else:
                self.wfile.write(filtered_content)  # Binary content (e.g., images)

        except requests.Timeout:
            # Handle timeout errors by responding with a 504 status code
            self.send_response(504)
            self.end_headers()
            self.wfile.write(b"Error: Request to localhost:8000 timed out.")
        
        except requests.RequestException as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Error fetching the website from localhost:8000.")

# Use a threaded server to handle multiple requests concurrently
class ThreadedTCPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass
    

# Start the proxy server on port 8001
PORT = 8001
#with socketserver.TCPServer(("", PORT), ProxyHandler) as httpd:
with ThreadedTCPServer(("localhost", PORT), ProxyHandler) as httpd:
    print(f"Proxy server running on port {PORT}, forwarding requests to localhost:8000")
    httpd.serve_forever()
