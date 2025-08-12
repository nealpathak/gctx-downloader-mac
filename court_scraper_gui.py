#!/usr/bin/env python3
"""
Galveston County Court Document Scraper - Modern GUI
Professional interface designed for legal professionals
"""

import os
import sys
import threading
import time
import json
from pathlib import Path
from tkinter import filedialog, messagebox
import customtkinter as ctk

# Import the existing scraper
from court_scraper import GalvestonCourtScraper

class CourtScraperGUI:
    """Modern GUI for Galveston County Court Document Scraper"""
    
    def __init__(self):
        # Set appearance mode and color theme
        ctk.set_appearance_mode("light")  # Professional light mode for legal office
        ctk.set_default_color_theme("blue")  # Professional blue theme
        
        # Initialize main window
        self.root = ctk.CTk()
        self.root.title("Galveston County Court Document Scraper")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Variables
        self.case_number = ctk.StringVar()
        self.download_path = ctk.StringVar(value=str(Path.home() / "Downloads" / "Court Documents"))
        self.is_downloading = False
        self.scraper = None
        self.download_thread = None
        
        # Create interface
        self.create_widgets()
        
        # Load recent cases
        self.recent_cases = self.load_recent_cases()
        self.update_recent_cases_dropdown()
        
    def create_widgets(self):
        """Create the main interface"""
        
        # Main container with padding
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ctk.CTkFrame(main_frame)
        header_frame.pack(fill="x", padx=20, pady=(20, 30))
        
        title_label = ctk.CTkLabel(
            header_frame, 
            text="🏛️ Galveston County Court Document Scraper",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Automatically download court documents from public records",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle_label.pack(pady=(0, 10))
        
        # Case Number Section
        case_frame = ctk.CTkFrame(main_frame)
        case_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        case_label = ctk.CTkLabel(case_frame, text="Case Number", font=ctk.CTkFont(size=16, weight="bold"))
        case_label.pack(anchor="w", padx=20, pady=(20, 5))
        
        case_input_frame = ctk.CTkFrame(case_frame)
        case_input_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        self.case_entry = ctk.CTkEntry(
            case_input_frame,
            textvariable=self.case_number,
            placeholder_text="Enter case number (e.g., 25-CV-0880)",
            font=ctk.CTkFont(size=14),
            height=40
        )
        self.case_entry.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=10)
        
        # Recent cases dropdown
        self.recent_dropdown = ctk.CTkComboBox(
            case_input_frame,
            values=["Recent Cases..."],
            command=self.on_recent_case_selected,
            width=150
        )
        self.recent_dropdown.pack(side="right", padx=(5, 10), pady=10)
        
        # Example formats
        example_label = ctk.CTkLabel(
            case_frame,
            text="Examples: 25-CV-0880 (Civil), 20-FD-1967 (Family), 24-CR-1234 (Criminal)",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        example_label.pack(anchor="w", padx=20, pady=(0, 20))
        
        # Download Location Section
        location_frame = ctk.CTkFrame(main_frame)
        location_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        location_label = ctk.CTkLabel(location_frame, text="Download Location", font=ctk.CTkFont(size=16, weight="bold"))
        location_label.pack(anchor="w", padx=20, pady=(20, 5))
        
        location_input_frame = ctk.CTkFrame(location_frame)
        location_input_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.location_entry = ctk.CTkEntry(
            location_input_frame,
            textvariable=self.download_path,
            font=ctk.CTkFont(size=12),
            height=35
        )
        self.location_entry.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=10)
        
        browse_button = ctk.CTkButton(
            location_input_frame,
            text="Browse",
            command=self.browse_download_location,
            width=100
        )
        browse_button.pack(side="right", padx=(5, 10), pady=10)
        
        # Action Section
        action_frame = ctk.CTkFrame(main_frame)
        action_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Download button
        self.download_button = ctk.CTkButton(
            action_frame,
            text="📥 Download Court Documents",
            command=self.start_download,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            fg_color="#1f538d",
            hover_color="#164470"
        )
        self.download_button.pack(pady=20, padx=20)
        
        # Progress Section
        progress_frame = ctk.CTkFrame(main_frame)
        progress_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        progress_label = ctk.CTkLabel(progress_frame, text="Progress", font=ctk.CTkFont(size=16, weight="bold"))
        progress_label.pack(anchor="w", padx=20, pady=(20, 5))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", padx=20, pady=(10, 5))
        self.progress_bar.set(0)
        
        # Progress text
        self.progress_text = ctk.CTkLabel(
            progress_frame,
            text="Ready to download court documents",
            font=ctk.CTkFont(size=12)
        )
        self.progress_text.pack(anchor="w", padx=20, pady=(0, 10))
        
        # Results text area
        self.results_text = ctk.CTkTextbox(progress_frame, height=200, font=ctk.CTkFont(size=11))
        self.results_text.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # Action buttons frame
        buttons_frame = ctk.CTkFrame(progress_frame)
        buttons_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        self.open_folder_button = ctk.CTkButton(
            buttons_frame,
            text="📂 Open Download Folder",
            command=self.open_download_folder,
            state="disabled"
        )
        self.open_folder_button.pack(side="left", padx=(0, 10), pady=10)
        
        self.clear_log_button = ctk.CTkButton(
            buttons_frame,
            text="Clear Log",
            command=self.clear_log,
            fg_color="gray",
            hover_color="darkgray"
        )
        self.clear_log_button.pack(side="right", padx=(10, 0), pady=10)
        
    def load_recent_cases(self):
        """Load recent cases from file"""
        try:
            recent_file = Path("recent_cases.json")
            if recent_file.exists():
                with open(recent_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception:
            return []
    
    def save_recent_cases(self):
        """Save recent cases to file"""
        try:
            with open("recent_cases.json", 'w') as f:
                json.dump(self.recent_cases, f)
        except Exception:
            pass
    
    def update_recent_cases_dropdown(self):
        """Update the recent cases dropdown"""
        if self.recent_cases:
            self.recent_dropdown.configure(values=["Recent Cases..."] + self.recent_cases[:10])
        
    def on_recent_case_selected(self, value):
        """Handle recent case selection"""
        if value != "Recent Cases..." and value in self.recent_cases:
            self.case_number.set(value)
    
    def add_recent_case(self, case_number):
        """Add case to recent cases"""
        if case_number not in self.recent_cases:
            self.recent_cases.insert(0, case_number)
            # Keep only last 10 cases
            self.recent_cases = self.recent_cases[:10]
            self.update_recent_cases_dropdown()
            self.save_recent_cases()
    
    def browse_download_location(self):
        """Browse for download location"""
        folder = filedialog.askdirectory(
            title="Select Download Location",
            initialdir=self.download_path.get()
        )
        if folder:
            self.download_path.set(folder)
    
    def log_message(self, message, level="INFO"):
        """Add message to results log"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        # Insert at the end
        self.results_text.insert("end", formatted_message)
        self.results_text.see("end")
        
        # Update GUI
        self.root.update_idletasks()
    
    def clear_log(self):
        """Clear the results log"""
        self.results_text.delete("1.0", "end")
    
    def progress_callback(self, progress_data):
        """Handle progress updates from scraper"""
        try:
            phase = progress_data.get('phase', 'working')
            step = progress_data.get('step', 0)
            total_steps = progress_data.get('total_steps', 1)
            message = progress_data.get('message', 'Processing...')
            percentage = progress_data.get('percentage', 0)
            
            # Update progress bar
            self.progress_bar.set(percentage / 100.0)
            
            # Update progress text
            if phase == 'navigation':
                self.progress_text.configure(text=f"Step {step}/{total_steps}: {message}")
            elif phase == 'download':
                self.progress_text.configure(text=f"Downloading: {message}")
            else:
                self.progress_text.configure(text=message)
                
            # Log the progress
            self.log_message(message)
            
        except Exception as e:
            self.log_message(f"Progress update error: {e}", "ERROR")
    
    def validate_case_number(self, case_num):
        """Validate case number format"""
        import re
        pattern = r'^\d{2}-[A-Z]{2,3}-\d{3,5}$'
        return bool(re.match(pattern, case_num))
    
    def start_download(self):
        """Start the download process"""
        if self.is_downloading:
            messagebox.showwarning("Download in Progress", "A download is already in progress. Please wait for it to complete.")
            return
        
        case_num = self.case_number.get().strip().upper()
        download_location = self.download_path.get().strip()
        
        # Validation
        if not case_num:
            messagebox.showerror("Invalid Input", "Please enter a case number.")
            return
        
        if not self.validate_case_number(case_num):
            result = messagebox.askyesno(
                "Case Number Format", 
                f"The case number '{case_num}' doesn't match the expected format (e.g., 25-CV-0880).\n\nDo you want to continue anyway?"
            )
            if not result:
                return
        
        if not download_location:
            messagebox.showerror("Invalid Input", "Please select a download location.")
            return
        
        # Create download directory if it doesn't exist
        try:
            Path(download_location).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Directory Error", f"Cannot create download directory:\n{e}")
            return
        
        # Add to recent cases
        self.add_recent_case(case_num)
        
        # Start download in separate thread
        self.download_thread = threading.Thread(target=self.download_documents, args=(case_num, download_location))
        self.download_thread.daemon = True
        self.download_thread.start()
    
    def download_documents(self, case_number, download_location):
        """Download documents in separate thread"""
        try:
            self.is_downloading = True
            
            # Update UI
            self.download_button.configure(text="⏳ Downloading...", state="disabled")
            self.open_folder_button.configure(state="disabled")
            
            # Clear previous results
            self.clear_log()
            
            self.log_message(f"🚀 Starting download for case: {case_number}")
            self.log_message(f"📁 Download location: {download_location}")
            
            # Create case-specific folder
            case_folder = Path(download_location) / case_number.replace('/', '_').replace('\\', '_')
            case_folder.mkdir(parents=True, exist_ok=True)
            
            # Initialize scraper with progress callback
            self.scraper = GalvestonCourtScraper(
                headless=True,  # Always run headless for GUI
                verbose=False,
                progress_callback=self.progress_callback
            )
            
            # Start scraping
            result = self.scraper.scrape_case(case_number, case_folder)
            
            # Handle results
            if result["success"]:
                self.log_message(f"✅ SUCCESS! Downloaded {result['documents']} documents")
                self.log_message(f"📊 Summary: {result['successful']} successful, {result['secured']} secured, {result['failed']} failed, {result['skipped']} skipped")
                self.log_message(f"📂 Files saved to: {case_folder}")
                
                self.progress_bar.set(1.0)
                self.progress_text.configure(text=f"✅ Complete! Downloaded {result['documents']} documents")
                
                # Enable open folder button
                self.open_folder_button.configure(state="normal")
                
                # Show success message
                messagebox.showinfo(
                    "Download Complete",
                    f"Successfully downloaded {result['documents']} documents for case {case_number}.\n\nFiles saved to:\n{case_folder}"
                )
                
            else:
                error_msg = result.get("error", "Unknown error occurred")
                self.log_message(f"❌ FAILED: {error_msg}")
                self.progress_text.configure(text="❌ Download failed")
                
                messagebox.showerror(
                    "Download Failed",
                    f"Failed to download documents for case {case_number}.\n\nError: {error_msg}\n\nCheck the log for more details."
                )
        
        except Exception as e:
            self.log_message(f"❌ ERROR: {str(e)}")
            self.progress_text.configure(text="❌ Error occurred")
            messagebox.showerror("Error", f"An error occurred during download:\n\n{str(e)}")
        
        finally:
            # Reset UI
            self.is_downloading = False
            self.download_button.configure(text="📥 Download Court Documents", state="normal")
            
    def open_download_folder(self):
        """Open the download folder in file explorer"""
        try:
            download_location = self.download_path.get()
            if sys.platform == "darwin":  # macOS
                os.system(f'open "{download_location}"')
            elif sys.platform == "win32":  # Windows
                os.startfile(download_location)
            else:  # Linux
                os.system(f'xdg-open "{download_location}"')
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open folder:\n{e}")
    
    def on_closing(self):
        """Handle window closing"""
        if self.is_downloading:
            result = messagebox.askyesno(
                "Download in Progress",
                "A download is currently in progress. Are you sure you want to exit?"
            )
            if not result:
                return
        
        # Cleanup
        if self.scraper:
            try:
                self.scraper.close_driver()
            except:
                pass
        
        self.root.destroy()
    
    def run(self):
        """Start the GUI application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

def main():
    """Main function to start the GUI"""
    try:
        app = CourtScraperGUI()
        app.run()
    except Exception as e:
        print(f"Error starting GUI: {e}")
        messagebox.showerror("Startup Error", f"Failed to start the application:\n\n{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()