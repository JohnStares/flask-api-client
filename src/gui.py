from __future__ import annotations

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from tkinter.font import Font
import json
from threading import Thread
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass
from enum import Enum

# Import your existing classes
from src.req import FlaskAPIClient, Response


class RequestMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


@dataclass
class SavedRequest:
    """Data class for saved requests"""
    name: str
    method: str
    endpoint: str
    headers: str
    body: str
    timestamp: str


class APIRequestGUI:
    """Main GUI application for API testing"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Flask API Client - CSRF Auto")
        self.root.geometry("1400x900")
        
        # Initialize client (will be set later)
        self.client: Optional[FlaskAPIClient] = None
        self.base_url = tk.StringVar(value="http://localhost:5000/v1")
        self.cookie_file = Path("cookies.json")
        
        # Request state
        self.current_method = tk.StringVar(value="GET")
        self.current_endpoint = tk.StringVar()
        self.response_data: Optional[Response] = None
        
        # Saved requests
        self.saved_requests: Dict[str, SavedRequest] = {}
        self.requests_file = Path("saved_requests.json")
        self.load_saved_requests()
        
        # Setup UI
        self.setup_styles()
        self.setup_menu()
        self.setup_main_layout()
        self.setup_url_bar()
        self.setup_headers_section()
        self.setup_body_section()
        self.setup_response_section()
        self.setup_status_bar()
        
        # Initialize client
        self.init_client()
        
    def setup_styles(self):
        """Configure ttk styles for modern look"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Custom colors
        style.configure('Title.TLabel', font=('Helvetica', 12, 'bold'))
        style.configure('Response.TLabel', font=('Consolas', 10))
        style.configure('Send.TButton', background='#4CAF50', foreground='white')
        style.map('Send.TButton', background=[('active', '#45a049')])
        
    def setup_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Request", command=self.save_current_request)
        file_menu.add_command(label="Load Request", command=self.load_request_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Export Response", command=self.export_response)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Clear Headers", command=self.clear_headers)
        edit_menu.add_command(label="Clear Body", command=self.clear_body)
        edit_menu.add_command(label="Clear Cookies", command=self.clear_cookies)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Show Cookies", command=self.show_cookies_dialog)
        view_menu.add_command(label="Show Saved Requests", command=self.show_saved_requests)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
    def setup_main_layout(self):
        """Setup main container with paned windows"""
        # Main paned window
        self.main_pane = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        self.main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Top frame for request
        self.top_frame = ttk.Frame(self.main_pane)
        self.main_pane.add(self.top_frame, weight=1)
        
        # Bottom frame for response
        self.bottom_frame = ttk.Frame(self.main_pane)
        self.main_pane.add(self.bottom_frame, weight=1)
        
        # Request notebook
        self.request_notebook = ttk.Notebook(self.top_frame)
        self.request_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def setup_url_bar(self):
        """Setup URL and method selection"""
        url_frame = ttk.LabelFrame(self.top_frame, text="Request", padding="10")
        url_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Base URL
        ttk.Label(url_frame, text="Base URL:").grid(row=0, column=0, sticky=tk.W, padx=5)
        base_url_entry = ttk.Entry(url_frame, textvariable=self.base_url, width=40)
        base_url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # Method selection
        ttk.Label(url_frame, text="Method:").grid(row=0, column=2, sticky=tk.W, padx=(20,5))
        method_combo = ttk.Combobox(url_frame, textvariable=self.current_method, 
                                   values=[m.value for m in RequestMethod], 
                                   width=10, state="readonly")
        method_combo.grid(row=0, column=3, sticky=tk.W, padx=5)
        
        # Endpoint
        ttk.Label(url_frame, text="Endpoint:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        endpoint_entry = ttk.Entry(url_frame, textvariable=self.current_endpoint, width=80)
        endpoint_entry.grid(row=1, column=1, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Send button
        self.send_btn = ttk.Button(url_frame, text="🚀 SEND", command=self.send_request,
                                   style='Send.TButton', width=15)
        self.send_btn.grid(row=0, column=4, rowspan=2, padx=20, pady=5)
        
        # Configure grid weights
        url_frame.columnconfigure(1, weight=1)
        
    def setup_headers_section(self):
        """Setup headers input section"""
        headers_frame = ttk.LabelFrame(self.request_notebook, text="Headers", padding="10")
        self.request_notebook.add(headers_frame, text="Headers")
        
        # Headers text area with JSON formatting
        self.headers_text = scrolledtext.ScrolledText(headers_frame, height=8, 
                                                      font=('Consolas', 10))
        self.headers_text.pack(fill=tk.BOTH, expand=True)
        self.headers_text.insert(1.0, '{\n  "Content-Type": "application/json"\n}')
        
        # Format button
        btn_frame = ttk.Frame(headers_frame)
        btn_frame.pack(fill=tk.X, pady=(5,0))
        ttk.Button(btn_frame, text="Format JSON", 
                  command=lambda: self.format_json(self.headers_text)).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Clear", 
                  command=self.clear_headers).pack(side=tk.LEFT, padx=2)
        
    def setup_body_section(self):
        """Setup request body section"""
        body_frame = ttk.LabelFrame(self.request_notebook, text="Body", padding="10")
        self.request_notebook.add(body_frame, text="Body")
        
        # Body type selection
        self.body_type = tk.StringVar(value="json")
        type_frame = ttk.Frame(body_frame)
        type_frame.pack(fill=tk.X, pady=(0,5))
        ttk.Radiobutton(type_frame, text="JSON", variable=self.body_type, 
                       value="json").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frame, text="Form Data", variable=self.body_type, 
                       value="form").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frame, text="Raw", variable=self.body_type, 
                       value="raw").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frame, text="None", variable=self.body_type, 
                       value="none").pack(side=tk.LEFT, padx=5)
        
        # Body text area
        self.body_text = scrolledtext.ScrolledText(body_frame, height=12, 
                                                    font=('Consolas', 10))
        self.body_text.pack(fill=tk.BOTH, expand=True)
        self.body_text.insert(1.0, '{\n  \n}')
        
        # Buttons
        btn_frame = ttk.Frame(body_frame)
        btn_frame.pack(fill=tk.X, pady=(5,0))
        ttk.Button(btn_frame, text="Format JSON", 
                  command=lambda: self.format_json(self.body_text)).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Clear", 
                  command=self.clear_body).pack(side=tk.LEFT, padx=2)
        
    def setup_response_section(self):
        """Setup response display section"""
        response_frame = ttk.LabelFrame(self.bottom_frame, text="Response", padding="10")
        response_frame.pack(fill=tk.BOTH, expand=True)
        
        # Response notebook
        self.response_notebook = ttk.Notebook(response_frame)
        self.response_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Body tab
        self.response_body = scrolledtext.ScrolledText(self.response_notebook, 
                                                       font=('Consolas', 10))
        self.response_notebook.add(self.response_body, text="Body")
        
        # Headers tab
        self.response_headers_text = scrolledtext.ScrolledText(self.response_notebook, 
                                                               font=('Consolas', 10))
        self.response_notebook.add(self.response_headers_text, text="Headers")
        
        # Cookies tab
        self.response_cookies_text = scrolledtext.ScrolledText(self.response_notebook, 
                                                               font=('Consolas', 10))
        self.response_notebook.add(self.response_cookies_text, text="Cookies")
        
    def setup_status_bar(self):
        """Setup status bar at bottom"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(self.status_bar, text="Ready", relief=tk.SUNKEN)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.time_label = ttk.Label(self.status_bar, text="", relief=tk.SUNKEN, width=20)
        self.time_label.pack(side=tk.RIGHT)
        self.update_time()
        
    def init_client(self):
        """Initialize API client"""
        try:
            self.client = FlaskAPIClient(self.base_url.get(), self.cookie_file)
            self.status_label.config(text=f"✅ Client initialized: {self.base_url.get()}")
        except Exception as e:
            self.status_label.config(text=f"❌ Failed to initialize client: {str(e)}")
            
    def send_request(self):
        """Send request in separate thread"""
        if not self.client:
            messagebox.showerror("Error", "Client not initialized. Check base URL.")
            return
            
        # Validate endpoint
        endpoint = self.current_endpoint.get().strip()
        if not endpoint:
            messagebox.showerror("Error", "Please enter an endpoint")
            return
            
        # Disable send button during request
        self.send_btn.config(state=tk.DISABLED, text="⏳ SENDING...")
        self.status_label.config(text="Sending request...")
        
        # Start request thread
        thread = Thread(target=self._make_request)
        thread.daemon = True
        thread.start()
        
    def _make_request(self):
        """Execute the actual request"""
        try:
            method = self.current_method.get()
            endpoint = self.current_endpoint.get()
            
            # Parse headers
            headers = {}
            try:
                headers_text = self.headers_text.get(1.0, tk.END).strip()
                if headers_text:
                    headers = json.loads(headers_text)
            except json.JSONDecodeError as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Invalid headers JSON: {e}"))
                self.root.after(0, self._enable_send_button)
                return
            
            # Parse body based on type
            kwargs = {'headers': headers} if headers else {}
            
            if self.body_type.get() != "none":
                body_text = self.body_text.get(1.0, tk.END).strip()
                if body_text:
                    if self.body_type.get() == "json":
                        try:
                            kwargs['json'] = json.loads(body_text)
                        except json.JSONDecodeError as e:
                            self.root.after(0, lambda: messagebox.showerror("Error", f"Invalid JSON body: {e}"))
                            self.root.after(0, self._enable_send_button)
                            return
                    elif self.body_type.get() == "form":
                        kwargs['data'] = body_text
                    else:  # raw
                        kwargs['data'] = body_text
            
            # Make request
            start_time = datetime.now()
            response = getattr(self.client, method.lower())(endpoint, **kwargs)
            elapsed = (datetime.now() - start_time).total_seconds()
            
            # Update UI with response
            self.root.after(0, lambda: self._display_response(response, elapsed))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Request Error", str(e)))
            self.root.after(0, lambda: self.status_label.config(text=f"❌ Error: {str(e)}"))
        finally:
            self.root.after(0, self._enable_send_button)
            
    def _display_response(self, response, elapsed: float):
        """Display response in UI"""
        if isinstance(response, dict) and 'error' in response:
            # Error response
            self.response_body.delete(1.0, tk.END)
            self.response_body.insert(1.0, json.dumps(response, indent=2))
            self.status_label.config(text=f"❌ Error: {response.get('error', 'Unknown error')}")
            return
            
        # Successful response
        try:
            # Display body
            if hasattr(response, 'json'):
                try:
                    body = response.json()
                    formatted = json.dumps(body, indent=2)
                except:
                    formatted = response.text
            else:
                formatted = response.text
                
            self.response_body.delete(1.0, tk.END)
            self.response_body.insert(1.0, formatted)
            
            # Display headers
            headers_dict = dict(response.headers) if hasattr(response, 'headers') else {}
            self.response_headers_text.delete(1.0, tk.END)
            self.response_headers_text.insert(1.0, json.dumps(headers_dict, indent=2))
            
            # Display cookies
            cookies_dict = dict(response.cookies) if hasattr(response, 'cookies') else {}
            self.response_cookies_text.delete(1.0, tk.END)
            self.response_cookies_text.insert(1.0, json.dumps(cookies_dict, indent=2))
            
            # Update status
            status_code = response.status_code if hasattr(response, 'status_code') else 'N/A'
            status_color = "🟢" if status_code < 400 else "🔴"
            self.status_label.config(
                text=f"{status_color} {status_code} | {elapsed:.2f}s | {self.base_url.get()}{self.current_endpoint.get()}"
            )
            
        except Exception as e:
            self.status_label.config(text=f"❌ Error displaying response: {str(e)}")
            
    def _enable_send_button(self):
        """Re-enable send button"""
        self.send_btn.config(state=tk.NORMAL, text="🚀 SEND")
        
    def save_current_request(self):
        """Save current request to file"""
        name = tk.simpledialog.askstring("Save Request", "Enter request name:")
        if name:
            saved = SavedRequest(
                name=name,
                method=self.current_method.get(),
                endpoint=self.current_endpoint.get(),
                headers=self.headers_text.get(1.0, tk.END).strip(),
                body=self.body_text.get(1.0, tk.END).strip(),
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            self.saved_requests[name] = saved
            self.save_saved_requests()
            messagebox.showinfo("Success", f"Request '{name}' saved!")
            
    def load_request_dialog(self):
        """Show dialog to load saved request"""
        if not self.saved_requests:
            messagebox.showinfo("Info", "No saved requests found")
            return
            
        # Create selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Load Request")
        dialog.geometry("500x400")
        
        # Listbox with saved requests
        frame = ttk.Frame(dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(frame)
        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)
        
        for name in self.saved_requests.keys():
            listbox.insert(tk.END, name)
            
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def load_selected():
            selection = listbox.curselection()
            if selection:
                name = listbox.get(selection[0])
                req = self.saved_requests[name]
                self.current_method.set(req.method)
                self.current_endpoint.set(req.endpoint)
                self.headers_text.delete(1.0, tk.END)
                self.headers_text.insert(1.0, req.headers)
                self.body_text.delete(1.0, tk.END)
                self.body_text.insert(1.0, req.body)
                dialog.destroy()
                messagebox.showinfo("Loaded", f"Loaded request '{name}'")
                
        ttk.Button(frame, text="Load", command=load_selected).pack(pady=10)
        
    def show_saved_requests(self):
        """Show all saved requests"""
        if not self.saved_requests:
            messagebox.showinfo("Info", "No saved requests")
            return
            
        info = "\n\n".join([
            f"📁 {req.name}\n   Method: {req.method}\n   Endpoint: {req.endpoint}\n   Saved: {req.timestamp}"
            for req in self.saved_requests.values()
        ])
        messagebox.showinfo("Saved Requests", info)
        
    def show_cookies_dialog(self):
        """Show current cookies"""
        if not self.client:
            messagebox.showerror("Error", "Client not initialized")
            return
            
        cookies = self.client.cookie_manager.get_cookies_for_session()
        if not cookies:
            messagebox.showinfo("Cookies", "No cookies stored")
        else:
            cookie_text = json.dumps(cookies, indent=2)
            dialog = tk.Toplevel(self.root)
            dialog.title("Current Cookies")
            dialog.geometry("500x400")
            text = scrolledtext.ScrolledText(dialog, font=('Consolas', 10))
            text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text.insert(1.0, cookie_text)
            
    def show_about(self):
        """Show about dialog"""
        about_text = """Flask API Client v1.0
        
Features:
✅ Automatic CSRF token injection
✅ Cookie persistence
✅ Request history
✅ JSON formatting
✅ Multi-tab interface

Built with Python & tkinter
"""
        messagebox.showinfo("About", about_text)
        
    def export_response(self):
        """Export response to file"""
        if not self.response_body.get(1.0, tk.END).strip():
            messagebox.showwarning("Warning", "No response to export")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            content = self.response_body.get(1.0, tk.END)
            with open(file_path, 'w') as f:
                f.write(content)
            messagebox.showinfo("Success", f"Response exported to {file_path}")
            
    def clear_headers(self):
        """Clear headers text"""
        self.headers_text.delete(1.0, tk.END)
        self.headers_text.insert(1.0, '{\n  "Content-Type": "application/json"\n}')
        
    def clear_body(self):
        """Clear body text"""
        self.body_text.delete(1.0, tk.END)
        self.body_text.insert(1.0, '{\n  \n}')
        
    def clear_cookies(self):
        """Clear all cookies"""
        if messagebox.askyesno("Confirm", "Clear all stored cookies?"):
            if self.client:
                self.client.clear_cookies()
                self.status_label.config(text="✅ Cookies cleared")
                
    def format_json(self, text_widget):
        """Format JSON in text widget"""
        try:
            content = text_widget.get(1.0, tk.END).strip()
            if content:
                parsed = json.loads(content)
                formatted = json.dumps(parsed, indent=2)
                text_widget.delete(1.0, tk.END)
                text_widget.insert(1.0, formatted)
        except json.JSONDecodeError:
            pass  # Not valid JSON, ignore
            
    def load_saved_requests(self):
        """Load saved requests from disk"""
        if self.requests_file.exists():
            try:
                with open(self.requests_file, 'r') as f:
                    data = json.load(f)
                    for name, req_data in data.items():
                        self.saved_requests[name] = SavedRequest(**req_data)
            except:
                pass
                
    def save_saved_requests(self):
        """Save requests to disk"""
        try:
            data = {name: req.__dict__ for name, req in self.saved_requests.items()}
            with open(self.requests_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save requests: {e}")
            
    def update_time(self):
        """Update time in status bar"""
        self.time_label.config(text=datetime.now().strftime("%H:%M:%S"))
        self.root.after(1000, self.update_time)
        
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = APIRequestGUI()
    app.run()