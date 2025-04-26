#https://korben.info/steel-api-navigation-web-agents-ia.html
from JO_analyse_gpt import response_me

from flask import Blueprint, request, jsonify

from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
import tempfile
import os
import requests
from fpdf import FPDF
import tkinter as tk
from tkinter import messagebox
from paths import GetRoot

Steal = Blueprint('ST_steal', __name__)

@Steal.route('/scrape_url', methods=['POST'])
def scrape_url():
    try:
        data = request.get_json()
        
        num_job = data.get('num_job') 
        url_to_scrape = data.get('item_url')
        if not url_to_scrape or not num_job:
            return jsonify({"status": "error", "message": "Missing parameters"}), 400
        #os.system(f'start {url_to_scrape}')
        # req = "Est ce que la page est correctement afficher. peux tu faire une réponse tres courte "
        # role="tu es expert html/css, capable d'examiner une page web et de définir le contenu de la page web"
        # reponds_moi=response_me(req,url_to_scrape,role)
        # if show_popup(reponds_moi)=="Stop":
        #     return jsonify({"status": "success", "message": "traitement interrompu."}), 202
        
        

        api_url = "http://localhost:3000/v1/pdf"
        headers = {
            'Content-Type': 'application/json'
        }
        payload = {
            "url": url_to_scrape,
            "waitFor": 3000
        }
        print(f"DBG01------payload : {payload}")

        response = requests.post(api_url, headers=headers, json=payload)
        
        
        if response.status_code == 200:
            try:
                directory_path = os.path.join(GetRoot(), num_job)
                if not os.path.exists(directory_path):
                    os.makedirs(directory_path)
                    
                
                pdf_file_path = os.path.join(directory_path, f"{num_job}_annonce_steal.pdf")
                
                # Create temporary files
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as url_temp_file:
                    # Create URL page
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    pdf.multi_cell(0, 10, f"<-\n{url_to_scrape}\n->")
                    pdf.output(url_temp_file.name)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as content_temp_file:
                    # Save content to temp file
                    content_temp_file.write(response.content)
                    content_temp_file.flush()
                
                # Merge PDFs
                output_pdf = PdfWriter()
                
                # Add URL page
                url_pdf = PdfReader(url_temp_file.name)
                output_pdf.add_page(url_pdf.pages[0])
                
                # Add content pages
                content_pdf = PdfReader(content_temp_file.name)
                for page in content_pdf.pages:
                    output_pdf.add_page(page)
                
                # Write final PDF
                with open(pdf_file_path, 'wb') as output_file:
                    output_pdf.write(output_file)
                
                # Clean up temp files
                os.unlink(url_temp_file.name)
                os.unlink(content_temp_file.name)
                
                return jsonify({"status": "success", "data": "Success"}), 200
              
            except Exception as e:
                print(f"Error details: {str(e)}")
                return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500
        else:
            return jsonify({"status": "error", "message": response.text}), response.status_code
    except Exception as e:
        print(f"Cyr_error_616 An error occurred in scrape_url: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500 
 
 
 
def show_popup(reponds_moi):
    def on_continue():
        popup.destroy()
        # Continue processing
        print("Continuing processing...")

    def on_stop():
        popup.destroy()
        # Stop processing
        print("Stopping processing...")
        return "Stop"

    popup = tk.Tk()
    popup.title("Popup")
    label = tk.Label(popup, text=reponds_moi)
    label.pack(pady=10)

    continue_button = tk.Button(popup, text="Continue", command=on_continue)
    continue_button.pack(side=tk.LEFT, padx=10, pady=10)

    stop_button = tk.Button(popup, text="Stop", command=on_stop)
    stop_button.pack(side=tk.RIGHT, padx=10, pady=10)

    popup.mainloop()